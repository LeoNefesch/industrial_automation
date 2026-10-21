from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AlarmState(str, Enum):
    NORMAL = "NORMAL"  # значение в норме
    ACTIVE_UNACK = "ACTIVE_UNACK"  # выход за уставку, оператор не квитировал
    ACTIVE_ACK = "ACTIVE_ACK"  # всё ещё за уставкой, оператор подтвердил


@dataclass
class Alarm:
    """Уставка и состояние аларма одного датчика.

    NORMAL → ACTIVE_UNACK  при value > high или value < low
    ACTIVE_UNACK → ACTIVE_ACK  после acknowledge()
    ACTIVE_UNACK / ACTIVE_ACK → NORMAL  при возврате в норму с учётом гистерезис (deadband)
    """

    sensor_id: str
    high: float | None = None  # верхняя уставка; None — не контролируется
    low: float | None = None  # нижняя уставка; None — не контролируется
    deadband: float = 2.0  # гистерезис: снятие на high−deadband / low+deadband
    priority: str = "HIGH"  # HIGH / MEDIUM / LOW
    state: AlarmState = AlarmState.NORMAL
    active_since: datetime | None = None  # UTC-момент выхода за уставку
    ack_time: datetime | None = None  # UTC-момент квитирования
    ack_user: str | None = None  # кто квитировал (для аудита)


@dataclass
class AlarmEventRecord:
    """Типизированное событие аларма для сохранения в БД."""

    time: datetime
    sensor_id: str
    event: str
    state: str
    value: float | None
    priority: str
    ack_user: str | None = None
    ack_time: datetime | None = None
