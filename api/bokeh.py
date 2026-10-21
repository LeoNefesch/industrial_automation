from fastapi import APIRouter, FastAPI
from fastapi.responses import RedirectResponse

from visual.bokeh_app import BokehDashboard


dashboard = BokehDashboard()

router = APIRouter(tags=["bokeh"])


@router.get("/", include_in_schema=False)
async def redirect_to_dashboard() -> RedirectResponse:
    return RedirectResponse(url=f"{BokehDashboard.MOUNT_PATH}{BokehDashboard.ROUTE}")


def mount_bokeh(app: FastAPI) -> None:
    """Bokeh — ASGI-приложение, его нельзя включить через APIRouter, только смонтировать."""
    app.mount(BokehDashboard.MOUNT_PATH, dashboard.asgi_app)
