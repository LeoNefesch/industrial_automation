from datetime import datetime, timezone

from db.models import Measurement
from dependencies.uow import get_uow
from services.measurement_service import MeasurementService
from simulator.random_simulator import RandomSimulator


class GenerateAndStoreUseCase:
    """Сгенерировать значения датчиков и сохранить их в БД одной транзакцией."""

    def __init__(self, simulator: RandomSimulator) -> None:
        self._simulator = simulator

    async def execute(self) -> list[Measurement]:
        now = datetime.now(timezone.utc)
        values = self._simulator.generate()

        measurements = [Measurement(time=now, sensor_id=sensor_id, value=value) for sensor_id, value in values.items()]

        async with get_uow() as uow:
            service = MeasurementService(uow.measurements)
            await service.save_measurements(measurements)
        return measurements
