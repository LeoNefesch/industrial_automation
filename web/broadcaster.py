import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from db.models import Measurement


class Broadcaster:
    """Простой in-memory pub/sub для WebSocket-клиентов.

    Работает только при одном процессе приложения (workers=1).
    Для нескольких воркеров понадобился бы внешний брокер (Redis pub/sub и т.п.).
    """

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[list[dict[str, Any]]]] = set()

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[list[dict[str, Any]]]]:
        queue: asyncio.Queue[list[dict[str, Any]]] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)

    def publish(self, measurements: list[Measurement]) -> None:
        if not self._subscribers:
            return
        payload = [{"time": m.time.isoformat(), "sensor_id": m.sensor_id, "value": m.value} for m in measurements]
        for queue in self._subscribers:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                # Медленный клиент: пропускаем апдейт, чтобы не блокировать генератор.
                pass
