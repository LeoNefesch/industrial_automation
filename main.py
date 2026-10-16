import asyncio
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route

from core.constants import INTERVAL_SECONDS, SENSORS
from core.logger import logger
from simulator.random_simulator import RandomSimulator
from usecases.generate_and_store import GenerateAndStoreUseCase
from visual.bokeh_app import BokehDashboard


dashboard = BokehDashboard()
use_case = GenerateAndStoreUseCase(RandomSimulator(SENSORS))


async def _generate_loop() -> None:
    logger.info("[generator] started")
    while True:
        try:
            measurements = await use_case.execute()
            await dashboard.push(measurements)
        except Exception as exc:
            logger.error(f"[generator] error: {exc!r}")
        await asyncio.sleep(INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: Starlette):
    await dashboard.start()
    app.state.generator_task = asyncio.create_task(_generate_loop())
    try:
        yield
    finally:
        app.state.generator_task.cancel()
        try:
            await app.state.generator_task
        except asyncio.CancelledError:
            pass
        await dashboard.stop()


async def homepage(request):
    return HTMLResponse(
        f'<meta http-equiv="refresh" content="0; url={BokehDashboard.MOUNT_PATH}{BokehDashboard.ROUTE}">'
    )


app = Starlette(
    routes=[
        Route("/", homepage),
        Mount(BokehDashboard.MOUNT_PATH, dashboard.asgi_app),
    ],
    lifespan=lifespan,
)
