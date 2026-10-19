import asyncio
import random

from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice


def _s16(value: int) -> int:
    """Преобразовать знаковое значение в беззнаковое для хранения в регистре."""
    return value & 0xFFFF


async def _update_loop(server: ModbusTcpServer) -> None:
    """Каждые 2 секунды обновлять регистры температуры и влажности."""
    await server.async_setValues(
        device_id=1,
        func_code=3,
        address=1,
        values=[_s16(250), _s16(500)],
    )

    while True:
        await asyncio.sleep(2)
        temp_raw = _s16(int(random.uniform(15.0, 30.0) * 10))
        hum_raw = _s16(int(random.uniform(30.0, 70.0) * 10))
        await server.async_setValues(
            device_id=1,
            func_code=3,
            address=1,
            values=[temp_raw, hum_raw],
        )


async def main() -> None:
    """SimData описывает блок регистров, SimDevice — устройство."""
    block = SimData(
        address=0,
        values=[0] * 100,
        datatype=DataType.REGISTERS,
    )
    device = SimDevice(id=1, simdata=[block])
    server = ModbusTcpServer([device], address=("0.0.0.0", 502))
    await server.serve_forever(background=True)
    await _update_loop(server)


if __name__ == "__main__":
    asyncio.run(main())
