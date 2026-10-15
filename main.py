import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.logger import logger
from dependencies.uow import get_uow
from services.measurement_service import MeasurementService
from simulator.random_simulator import RandomSimulator
from usecases.generate_and_store import GenerateAndStoreUseCase
from web.broadcaster import Broadcaster


SENSORS = ["temperature", "pressure", "flow_rate"]
INTERVAL_SECONDS = 5
HISTORY_HOURS = 1

INDEX_HTML = (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")

simulator = RandomSimulator(SENSORS)
use_case = GenerateAndStoreUseCase(simulator)


async def _generate_loop(broadcaster: Broadcaster) -> None:
    logger.info("[generator] started")
    while True:
        try:
            measurements = await use_case.execute()
            broadcaster.publish(measurements)
        except Exception as exc:
            logger.error(f"[generator] error: {exc!r}")
        await asyncio.sleep(INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: Starlette):
    app.state.broadcaster = Broadcaster()
    app.state.generator_task = asyncio.create_task(_generate_loop(app.state.broadcaster))
    try:
        yield
    finally:
        app.state.generator_task.cancel()
        try:
            await app.state.generator_task
        except asyncio.CancelledError:
            pass


async def homepage(request):
    return HTMLResponse(INDEX_HTML)


async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    broadcaster: Broadcaster = websocket.app.state.broadcaster

    end = datetime.now(timezone.utc)  # 1. Начальный срез — история за последний час.
    start = end - timedelta(hours=HISTORY_HOURS)
    async with get_uow() as uow:
        service = MeasurementService(uow.measurements)
        history = await service.get_all(start, end)

    await websocket.send_json(
        {
            "type": "init",
            "data": [{"time": m.time.isoformat(), "sensor_id": m.sensor_id, "value": m.value} for m in history],
        }
    )

    try:  # 2. Поток новых точек.
        async with broadcaster.subscribe() as queue:
            while True:
                payload = await queue.get()
                await websocket.send_json({"type": "update", "data": payload})
    except WebSocketDisconnect:
        logger.info("[ws] client disconnected")


app = Starlette(
    routes=[
        Route("/", homepage),
        WebSocketRoute("/ws", ws_endpoint),
    ],
    lifespan=lifespan,
)
