import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI

from alarms.config import ALARMS
from alarms.manager import AlarmManager
from api import all_routers
from api.bokeh import dashboard, mount_bokeh
from dependencies.uow import get_uow
from services.measurement_service import MeasurementService


async def _poll_and_push() -> None:
    """Каждые 2 секунды читать последние измерения и обновлять Bokeh."""
    while True:
        now = datetime.now(timezone.utc)
        start = now - timedelta(seconds=10)
        async with get_uow() as uow:
            service = MeasurementService(uow.measurements)
            measurements = await service.get_all(start, now)
        if measurements:
            await dashboard.push(measurements)
        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.alarm_manager = AlarmManager(ALARMS)
    await dashboard.start()
    task = asyncio.create_task(_poll_and_push())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await dashboard.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Industrial Automation — Mini-SCADA (Web)",
        version="0.1.0",
        lifespan=lifespan,
    )
    for router in all_routers:
        app.include_router(router)
    mount_bokeh(app)
    return app


app = create_app()
