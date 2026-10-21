import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from alarms.config import ALARMS
from alarms.manager import AlarmManager
from core.constants import INTERVAL_SECONDS
from core.logger import logger
from db.models import AlarmEvent as AlarmEventDB
from protocols.modbus_client import ModbusDataSource
from usecases.collect_and_store import CollectAndStoreUseCase
from usecases.save_alarm_events import SaveAlarmEventsUseCase


async def collect_and_check(
    use_case: CollectAndStoreUseCase,
    alarm_manager: AlarmManager,
    save_events_uc: SaveAlarmEventsUseCase,
) -> None:
    measurements = await use_case.execute()
    if not measurements:
        return

    db_events = []
    for m in measurements:
        events = alarm_manager.process(m.sensor_id, m.value)
        for ev in events:
            logger.warning(f"[alarm] {ev.event} | {ev.sensor_id} | {ev.value}")
            db_events.append(
                AlarmEventDB(
                    time=ev.time,
                    sensor_id=ev.sensor_id,
                    event=ev.event,
                    state=ev.state,
                    value=ev.value,
                    priority=ev.priority,
                    ack_user=ev.ack_user,
                    ack_time=ev.ack_time,
                )
            )
    await save_events_uc.execute(db_events)


async def main() -> None:
    source = ModbusDataSource()
    await source.connect()
    use_case = CollectAndStoreUseCase(source)
    alarm_manager = AlarmManager(ALARMS)
    save_events_uc = SaveAlarmEventsUseCase()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        collect_and_check,
        IntervalTrigger(seconds=INTERVAL_SECONDS),
        args=[use_case, alarm_manager, save_events_uc],
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
