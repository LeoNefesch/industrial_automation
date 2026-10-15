from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dao.base import AbstractMeasurementDAO
from db.models import Measurement


class MeasurementDAO(AbstractMeasurementDAO):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_many(self, measurements: list[Measurement]) -> None:
        self._session.add_all(measurements)
        await self._session.flush()

    async def get_by_sensor(
        self,
        sensor_id: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Measurement]:
        stmt = (
            select(Measurement)
            .where(Measurement.sensor_id == sensor_id)
            .where(Measurement.time.between(start, end))
            .order_by(Measurement.time)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_all(
        self,
        start: datetime,
        end: datetime,
    ) -> Sequence[Measurement]:
        stmt = select(Measurement).where(Measurement.time.between(start, end)).order_by(Measurement.time)
        result = await self._session.execute(stmt)
        return result.scalars().all()
