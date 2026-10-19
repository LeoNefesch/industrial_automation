from typing import Protocol


class SensorDataSource(Protocol):
    """Любой источник измерений: симулятор, Modbus, OPC UA и т.д."""

    async def read_all(self) -> dict[str, float]: ...
