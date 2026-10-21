from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from alarms.models import Alarm


router = APIRouter(prefix="/alarms", tags=["alarms"])


def _serialize(alarm: Alarm) -> dict[str, Any]:
    return {
        "sensor_id": alarm.sensor_id,
        "state": alarm.state.value,
        "active_since": alarm.active_since.isoformat() if alarm.active_since else None,
        "priority": alarm.priority,
    }


@router.get("")
async def list_alarms(request: Request) -> list[dict[str, Any]]:
    am = request.app.state.alarm_manager
    return [_serialize(a) for a in am._alarms.values()]


@router.post("/{sensor_id}/ack")
async def ack_alarm(
    sensor_id: str,
    request: Request,
    user: str = Query(default="operator"),
) -> dict[str, bool]:
    ok = request.app.state.alarm_manager.acknowledge(sensor_id, user)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail="Unknown sensor or alarm is not in ACTIVE_UNACK state",
        )
    return {"ok": True}
