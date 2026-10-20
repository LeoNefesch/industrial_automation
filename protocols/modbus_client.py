from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient

from core.data_source import SensorDataSource
from core.logger import logger
from core.settings import settings


class ModbusDataSource(SensorDataSource):
    """Читает значения с Modbus TCP-устройства (симулятора или реального шлюза)."""

    def __init__(self) -> None:
        self._client: AsyncModbusTcpClient | None = None

    async def connect(self) -> bool:
        """Возвращает True, если соединение установлено."""
        if self._client is None:
            self._client = AsyncModbusTcpClient(
                host=settings.modbus.host,
                port=settings.modbus.port,
                timeout=settings.modbus.timeout,
            )
        if not self._client.connected:
            return await self._client.connect()
        return True

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    async def read_all(self) -> dict[str, float]:
        if not await self.connect() or self._client is None:
            return {}
        try:
            rr = await self._client.read_holding_registers(
                address=settings.modbus.temp_register,
                count=2,
                device_id=settings.modbus.unit_id,
            )
        except ModbusException as exc:
            logger.error(f"[modbus] read error: {exc!r}")
            await self.close()
            return {}

        if rr.isError():
            logger.error(f"[modbus] device returned error: {rr}")
            return {}

        raw_temp, raw_hum = rr.registers
        temp = self._to_s16(raw_temp) / settings.modbus.scale
        hum = self._to_s16(raw_hum) / settings.modbus.scale
        return {
            "temperature": temp,
            "humidity": hum,
        }

    @staticmethod
    def _to_s16(value: int) -> int:
        """Интерпретировать беззнаковое 16-битное значение как знаковое."""
        if value >= 0x8000:
            return value - 0x10000
        return value
