from fastapi import APIRouter

from .alarms import router as alarms_router
from .bokeh import router as bokeh_router


api_router = APIRouter(prefix="/api")
api_router.include_router(alarms_router)

all_routers = [bokeh_router, api_router]
