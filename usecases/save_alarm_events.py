from db.models import AlarmEvent
from dependencies.uow import get_uow
from services.alarm_event_service import AlarmEventService


class SaveAlarmEventsUseCase:
    """Сохранить события алармов в БД."""

    async def execute(self, events: list[AlarmEvent]) -> None:
        if not events:
            return

        async with get_uow() as uow:
            service = AlarmEventService(uow.alarm_events)
            await service.save_events(events)
