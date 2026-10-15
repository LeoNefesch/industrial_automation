import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from core.logger import logger
from dependencies.uow import get_uow
from services.measurement_service import MeasurementService
from simulator.random_simulator import RandomSimulator
from usecases.generate_and_store import GenerateAndStoreUseCase
from visual.dashboard import Dashboard


SENSORS = ["temperature", "pressure", "flow_rate"]
INTERVAL_SECONDS = 5

simulator = RandomSimulator(SENSORS)
use_case = GenerateAndStoreUseCase(simulator)


async def _generate_loop() -> None:
    logger.info("[generator] started")
    while True:
        try:
            await use_case.execute()
        except Exception as exc:
            logger.error(f"[generator] error: {exc!r}")
        await asyncio.sleep(INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: Starlette):
    app.state.generator_task = asyncio.create_task(_generate_loop())
    try:
        yield
    finally:
        app.state.generator_task.cancel()
        try:
            await app.state.generator_task
        except asyncio.CancelledError:
            pass


async def homepage(request):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=1)

    async with get_uow() as uow:
        service = MeasurementService(uow.measurements)
        measurements = await service.get_all(start, end)

    fig = Dashboard(measurements).plotly_trend()
    if fig is None:
        return HTMLResponse(
            "<h1>Нет данных</h1>"
            "<p>Подождите несколько секунд — генератор пишет по одному измерению "
            "на датчик каждые 5 секунд.</p>"
        )
    return HTMLResponse(fig.to_html(include_plotlyjs="cdn"))


app = Starlette(
    routes=[Route("/", homepage)],
    lifespan=lifespan,
)
