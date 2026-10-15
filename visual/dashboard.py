from datetime import datetime, timezone

import matplotlib.pyplot as plt
import plotly.graph_objects as go  # type: ignore[import-untyped]
from plotly.subplots import make_subplots  # type: ignore[import-untyped]


class Dashboard:
    def __init__(self, measurements: list) -> None:
        self._measurements = measurements

    def plotly_trend(self) -> go.Figure | None:
        """Интерактивный график тренда через Plotly.

        Возвращает None, если измерений нет — вызывающий код сам решает,
        что показать пользователю.
        """
        if not self._measurements:
            return None

        sensor_ids = sorted({m.sensor_id for m in self._measurements})
        fig = make_subplots(rows=len(sensor_ids), cols=1, shared_xaxes=True)

        for i, sensor_id in enumerate(sensor_ids, start=1):
            data = [m for m in self._measurements if m.sensor_id == sensor_id]
            fig.add_trace(
                go.Scatter(
                    x=[m.time for m in data],
                    y=[m.value for m in data],
                    mode="lines+markers",
                    name=sensor_id,
                ),
                row=i,
                col=1,
            )

        fig.update_layout(title="Тренды датчиков", height=400 * len(sensor_ids))
        return fig

    def matplotlib_report(self, sensor_id: str, path: str) -> None:
        """Статический отчёт через Matplotlib."""
        data = [m for m in self._measurements if m.sensor_id == sensor_id]
        plt.figure(figsize=(12, 5))
        plt.plot([m.time for m in data], [m.value for m in data])
        plt.title(f"Датчик: {sensor_id}")
        plt.xlabel("Время")
        plt.ylabel("Значение")
        plt.grid(True)
        plt.savefig(path)
        plt.close()
