from sqlalchemy.ext.asyncio import AsyncSession

from dao.base import AbstractAlarmEventDAO
from db.models import AlarmEvent


class AlarmEventDAO(AbstractAlarmEventDAO):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_many(self, events: list[AlarmEvent]) -> None:
        self._session.add_all(events)
        await self._session.flush()
