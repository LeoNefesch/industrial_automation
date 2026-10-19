from typing import Any, cast

from bokeh.document import Document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, Range1d, ResetTool
from bokeh.models.annotations import Title
from bokeh.plotting import figure
from bokeh.server.asgi import BokehASGI
from starlette.types import ASGIApp

from core.constants import COLORS, MAX_POINTS, SENSORS


class BokehDashboard:
    ROUTE = "/plot"
    MOUNT_PATH = "/bokeh"

    def __init__(self) -> None:
        self._app = BokehASGI({self.ROUTE: self._build_document})

    @property
    def asgi_app(self) -> ASGIApp:
        return cast(ASGIApp, cast(object, self._app))

    async def start(self) -> None:
        await self._app.core.start()

    async def stop(self) -> None:
        await self._app.core.stop()

    async def push(self, measurements: list[Any]) -> None:
        """Отправить измерения во все активные Bokeh-сессии."""
        if not measurements:
            return

        payload: dict[str, dict[str, list]] = {}
        for m in measurements:
            bucket = payload.setdefault(m.sensor_id, {"time": [], "value": []})
            bucket["time"].append(m.time)
            bucket["value"].append(m.value)

        def update_document(doc: Document) -> None:
            sources = doc.template_variables.get("sources", {})
            for sensor_id, new_data in payload.items():
                source = sources.get(sensor_id)
                if source is not None:
                    source.stream(new_data, rollover=MAX_POINTS)

        await self._app.update_sessions(self.ROUTE, update_document)

    @staticmethod
    def _build_document(doc: Document) -> None:
        """Создать документ с графиками для сенсоров из списка SENSORS. Вызывается Bokeh на каждую сессию."""
        sources: dict[str, ColumnDataSource] = {}

        for sensor_id in SENSORS:
            source = ColumnDataSource(data={"time": [], "value": []})
            sources[sensor_id] = source

            p = figure(
                title=Title(
                    text=sensor_id,
                    text_color="#ddd",
                    text_font_size="14px",
                ),
                x_axis_type="datetime",
                y_range=Range1d(start=0, end=100),
                height=320,
                sizing_mode="stretch_width",
                background_fill_color="#1e1e1e",
                border_fill_color="#1e1e1e",
                outline_line_color="#333",
                tools="pan,wheel_zoom,box_zoom,save,reset",
            )
            p.line(
                x="time",
                y="value",
                source=source,
                line_color=COLORS[sensor_id],
                line_width=2,
                line_join="round",
                line_cap="round",
            )
            p.scatter(
                x="time",
                y="value",
                source=source,
                color=COLORS[sensor_id],
                size=5,
                marker="circle",
            )
            p.grid.grid_line_color = "#333"
            p.axis.axis_line_color = "#888"
            p.axis.major_label_text_color = "#ddd"
            p.add_tools(
                HoverTool(
                    tooltips=[
                        ("Датчик", sensor_id),
                        ("Время", "@time{%H:%M:%S}"),
                        ("Значение", "@value{0.00}"),
                    ],
                    formatters={"@time": "datetime"},
                    mode="vline",
                ),
                ResetTool(),
            )
            doc.add_root(column(p, sizing_mode="stretch_width"))
        doc.template_variables["sources"] = sources
