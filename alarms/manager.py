from datetime import datetime, timezone

from core.logger import logger

from .models import Alarm, AlarmState


class AlarmManager:
    def __init__(self, alarms: dict[str, Alarm]):
        self._alarms = alarms
        self._history: list[dict] = []  # для event log

    def process(self, sensor_id: str, value: float) -> list[dict]:
        """Проверить значение по уставке. Неизвестный датчик — не ошибка, а «нет аларма»."""
        alarm = self._alarms.get(sensor_id)
        if alarm is None:
            logger.warning(f"Alarm {sensor_id} not found")
            return []
        events: list[dict] = []

        if alarm.state == AlarmState.NORMAL:
            if alarm.high is not None and value > alarm.high:
                alarm.state = AlarmState.ACTIVE_UNACK
                alarm.active_since = datetime.now(timezone.utc)
                events.append(self._event(alarm, "ALARM_RAISED", value))
            elif alarm.low is not None and value < alarm.low:
                alarm.state = AlarmState.ACTIVE_UNACK
                alarm.active_since = datetime.now(timezone.utc)
                events.append(self._event(alarm, "ALARM_RAISED", value))

        elif alarm.state in (AlarmState.ACTIVE_UNACK, AlarmState.ACTIVE_ACK):
            in_normal = True
            if alarm.high is not None and value >= alarm.high - alarm.deadband:
                in_normal = False
            if alarm.low is not None and value <= alarm.low + alarm.deadband:
                in_normal = False
            if in_normal:
                alarm.state = AlarmState.NORMAL
                alarm.active_since = None
                events.append(self._event(alarm, "ALARM_CLEARED", value))

        self._history.extend(events)
        return events

    def acknowledge(self, sensor_id: str, user: str) -> bool:
        """Квитировать активный неквитированный аларм. False — если аларма нет или он не в том состоянии."""
        alarm = self._alarms.get(sensor_id)
        if alarm is None or alarm.state != AlarmState.ACTIVE_UNACK:
            return False
        alarm.state = AlarmState.ACTIVE_ACK
        alarm.ack_user = user
        alarm.ack_time = datetime.now(timezone.utc)
        self._history.append(self._event(alarm, "ALARM_ACKED", None))
        return True

    def _event(self, alarm: Alarm, kind: str, value: float | None) -> dict:
        return {
            "time": datetime.now(timezone.utc).isoformat(),
            "sensor_id": alarm.sensor_id,
            "event": kind,
            "state": alarm.state.value,
            "value": value,
            "priority": alarm.priority,
        }
