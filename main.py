import asyncio
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route

from core.constants import INTERVAL_SECONDS
from core.logger import logger
from protocols.modbus_client import ModbusDataSource
from usecases.collect_and_store import CollectAndStoreUseCase
from visual.bokeh_app import BokehDashboard


dashboard = BokehDashboard()


async def _generate_loop(app: Starlette) -> None:
    logger.info("[generator] started")
    while True:
        try:
            use_case: CollectAndStoreUseCase = app.state.use_case
            measurements = await use_case.execute()
            await dashboard.push(measurements)
        except Exception as exc:
            logger.error(f"[generator] error: {exc!r}")
        await asyncio.sleep(INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: Starlette):
    source = ModbusDataSource()
    await source.connect()
    app.state.use_case = CollectAndStoreUseCase(source)
    app.state.generator_task = asyncio.create_task(_generate_loop(app))
    await dashboard.start()

    try:
        yield
    finally:
        app.state.generator_task.cancel()
        try:
            await app.state.generator_task
        except asyncio.CancelledError:
            pass
        await source.close()
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
