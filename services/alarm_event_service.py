from dao.base import AbstractAlarmEventDAO
from db.models import AlarmEvent


class AlarmEventService:
    def __init__(self, dao: AbstractAlarmEventDAO):
        self._dao = dao

    async def save_events(self, events: list[AlarmEvent]) -> None:
        await self._dao.insert_many(events)
