from __future__ import annotations

from pathlib import Path
import plotly.graph_objects as go

from stockbot.saxo.client import SaxoClient
from stockbot.saxo.prices import get_chart_data


def build_price_chart_html(
    client: SaxoClient,
    uic: int,
    title: str,
    out_path: str = "reports/price.html",
    horizon: int = 1440,
    count: int = 365,
) -> str:
    raw = get_chart_data(client, uic=uic, horizon_minutes=horizon, count=count)

    # Saxo chart data indeholder typisk "Data" -> liste af punkter.
    # Vi gør det robust ved at håndtere et par almindelige feltnavne.
    points = raw.get("Data", [])
    if not points:
        raise RuntimeError(f"No chart data returned. Response keys: {list(raw.keys())}")

    # forventede felter: Time / DateTime og Close (eller Price)
    xs = []
    ys = []
    for p in points:
        t = p.get("Time") or p.get("DateTime") or p.get("Timestamp")
        y = p.get("Close") or p.get("Price") or p.get("Last") or p.get("Value")
        if t is not None and y is not None:
            xs.append(t)
            ys.append(y)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name="Price"))
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Price",
        hovermode="x unified",
    )

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_path, include_plotlyjs="cdn")
    return out_path
