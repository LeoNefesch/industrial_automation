from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AlarmEvent, Measurement


class AbstractMeasurementDAO(ABC):
    """Абстракция работы с данными измерений."""

    @abstractmethod
    async def insert_many(self, measurements: list[Measurement]) -> None: ...

    @abstractmethod
    async def get_by_sensor(
        self,
        sensor_id: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Measurement]: ...

    @abstractmethod
    async def get_all(
        self,
        start: datetime,
        end: datetime,
    ) -> Sequence[Measurement]: ...


class AbstractAlarmEventDAO(ABC):
    @abstractmethod
    async def insert_many(self, events: list[AlarmEvent]) -> None: ...
