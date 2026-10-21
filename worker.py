import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from alarms.config import ALARMS
from alarms.manager import AlarmManager
from core.constants import INTERVAL_SECONDS
from core.logger import logger
from protocols.modbus_client import ModbusDataSource
from usecases.collect_and_store import CollectAndStoreUseCase


async def collect_and_check(use_case: CollectAndStoreUseCase, alarm_manager: AlarmManager) -> None:
    measurements = await use_case.execute()
    if not measurements:
        return

    for m in measurements:
        events = alarm_manager.process(m.sensor_id, m.value)
        for ev in events:
            logger.warning(f"[alarm] {ev}")

    # Опционально: сохранить события алармов в БД (alarm_events)
    # await _save_alarm_events(events)


async def main() -> None:
    source = ModbusDataSource()
    await source.connect()
    use_case = CollectAndStoreUseCase(source)
    alarm_manager = AlarmManager(ALARMS)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        collect_and_check,
        IntervalTrigger(seconds=INTERVAL_SECONDS),
        args=[use_case, alarm_manager],
        id="collect_and_check",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("[worker] started")
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)
        await source.close()


if __name__ == "__main__":
    asyncio.run(main())
