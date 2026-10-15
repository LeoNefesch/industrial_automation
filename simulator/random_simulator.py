import random
from collections.abc import Mapping


class RandomSimulator:
    """Генерирует случайные значения для набора датчиков."""

    def __init__(self, sensor_ids: list[str]) -> None:
        self._sensor_ids = sensor_ids

    def generate(self) -> Mapping[str, float]:
        return {sensor_id: random.uniform(0.0, 100.0) for sensor_id in self._sensor_ids}
