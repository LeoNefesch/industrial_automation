from datetime import datetime, timezone

from db.models import Measurement
from dependencies.uow import get_uow
from protocols.modbus_client import ModbusReader
from protocols.opcua_client import OpcUaReader
from services.measurement_service import MeasurementService


class CollectAndStoreUseCase:
    """
    Use case: собрать данные с Modbus и OPC UA,
    сохранить в БД в одной транзакции.
    """

    def __init__(
        self,
        modbus: ModbusReader,
        opcua: OpcUaReader,
    ):
        self._modbus = modbus
        self._opcua = opcua

    async def execute(self) -> None:
        modbus_values = await self._modbus.read_all()
        opcua_values = await self._opcua.read_all()

        now = datetime.now(timezone.utc)
        measurements: list[Measurement] = []

        for sensor_id, value in {**modbus_values, **opcua_values}.items():
            measurements.append(Measurement(time=now, sensor_id=sensor_id, value=value))

        async with get_uow() as uow:
            service = MeasurementService(uow.measurements)
            await service.save_measurements(measurements)
