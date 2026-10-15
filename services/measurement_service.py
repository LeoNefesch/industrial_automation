from datetime import datetime

from dao.base import AbstractMeasurementDAO
from db.models import Measurement


class MeasurementService:
    def __init__(self, dao: AbstractMeasurementDAO):
        self._dao = dao

    async def save_measurements(self, measurements: list[Measurement]) -> None:
        await self._dao.insert_many(measurements)

    async def get_history(
        self,
        sensor_id: str,
        start: datetime,
        end: datetime,
    ) -> list[Measurement]:
        return list(await self._dao.get_by_sensor(sensor_id, start, end))

    async def get_all(
        self,
        start: datetime,
        end: datetime,
    ) -> list[Measurement]:
        return list(await self._dao.get_all(start, end))
