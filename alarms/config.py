from .models import Alarm


ALARMS = {
    "temperature": Alarm(
        sensor_id="temperature",
        high=28.0,
        low=16.0,
        deadband=1.0,
        priority="HIGH",
    ),
    "humidity": Alarm(
        sensor_id="humidity",
        high=65.0,
        low=35.0,
        deadband=2.0,
        priority="MEDIUM",
    ),
}
