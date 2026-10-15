from pymodbus.client import AsyncModbusTcpClient

from core.settings import settings


class ModbusReader:
    def __init__(self):
        self._client = AsyncModbusTcpClient(
            host=settings.modbus.host,
            port=settings.modbus.port,
        )

    async def connect(self) -> None:
        await self._client.connect()

    async def read_all(self) -> dict[str, float]:
        # Чтение holding registers (адреса 0-9)
        result = await self._client.read_holding_registers(
            address=0,
            count=10,
            slave=settings.modbus.unit,
        )
        if result.isError():
            return {}
        return {f"modbus_reg_{i}": float(v) for i, v in enumerate(result.registers)}

    async def close(self) -> None:
        self._client.close()
