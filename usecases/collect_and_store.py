from datetime import datetime, timezone

from core.data_source import SensorDataSource
from db.models import Measurement
from dependencies.uow import get_uow
from services.measurement_service import MeasurementService


class CollectAndStoreUseCase:
    """Собрать данные с источника и сохранить в БД одной транзакцией."""

    def __init__(self, source: SensorDataSource) -> None:
        self._source = source

    async def execute(self) -> list[Measurement]:
        now = datetime.now(timezone.utc)
        values = await self._source.read_all()
        if not values:
            return []

        measurements = [Measurement(time=now, sensor_id=sensor_id, value=value) for sensor_id, value in values.items()]

        async with get_uow() as uow:
            service = MeasurementService(uow.measurements)
            await service.save_measurements(measurements)

        return measurements
