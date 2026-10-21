from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from dao.alarm_event import AlarmEventDAO
from dao.base import AbstractAlarmEventDAO, AbstractMeasurementDAO
from dao.measurement import MeasurementDAO
from db.session import async_session_factory


class UnitOfWork:
    """Unit of Work: одна транзакция — один контекст."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.measurements: AbstractMeasurementDAO = MeasurementDAO(session)
        self.alarm_events: AbstractAlarmEventDAO = AlarmEventDAO(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self._session.close()


@asynccontextmanager
async def get_uow() -> AsyncIterator[UnitOfWork]:
    """Контекстный менеджер для UoW."""
    session = async_session_factory()
    async with UnitOfWork(session) as uow:
        yield uow
