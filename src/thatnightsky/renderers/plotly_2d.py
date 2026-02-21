"""Plotly 2D interactive star chart renderer.

Uses skyfield stereographic projection output (x, y) directly.
Supports wheel zoom and drag panning to explore the sky.
"""

import numpy as np
import plotly.graph_objects as go

from thatnightsky.models import SkyData

_BG = "#050a1a"
_STAR_COLOR = "#ffffff"
_LINE_COLOR = "#7ec8e3"


def render_plotly_chart(sky_data: SkyData) -> go.Figure:
    """Render SkyData as a Plotly 2D interactive star chart.

    Only stars above the horizon (alt >= 0) are shown, with constellation
    lines overlaid. Wheel zoom and drag panning are enabled.
    Projection: skyfield stereographic (conformal, preserves constellation shapes).

    Args:
        sky_data: Fully computed celestial data.

    Returns:
        Plotly Figure object.
    """
    visible = [s for s in sky_data.stars if s.alt_deg >= 0]

    # Star size: magnitude → marker size
    mags = np.array([s.magnitude for s in visible])
    sizes = np.clip(6 - mags, 1, 8)

    # Figure is 2:1 aspect (xrange 2, yrange 1), no scaleanchor
    # To avoid distorting constellation shapes, y is scaled ×2 to restore visual 1:1 ratio
    x_vals = [s.x for s in visible]
    y_vals = [s.y * 2 for s in visible]

    star_trace = go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers",
        marker=dict(
            size=list(sizes),
            color=_STAR_COLOR,
            opacity=0.9,
            line=dict(width=0),
        ),
        hoverinfo="skip",
        name="stars",
    )

    # Constellation lines: single trace using None separators
    hip_to_xy: dict[int, tuple[float, float]] = {s.hip: (s.x, s.y * 2) for s in visible}
    lx: list[float | None] = []
    ly: list[float | None] = []
    for line in sky_data.constellation_lines:
        if line.hip_from in hip_to_xy and line.hip_to in hip_to_xy:
            x0, y0 = hip_to_xy[line.hip_from]
            x1, y1 = hip_to_xy[line.hip_to]
            lx += [x0, x1, None]
            ly += [y0, y1, None]

    line_trace = go.Scatter(
        x=lx,
        y=ly,
        mode="lines",
        line=dict(color=_LINE_COLOR, width=1),
        opacity=0.5,
        hoverinfo="skip",
        name="constellations",
    )

    fig = go.Figure(data=[line_trace, star_trace])

    # Works with use_container_width=False + CSS square container.
    # width/height are reference values; CSS controls actual size.
    fig.update_layout(
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        width=800,
        height=400,
        dragmode="pan",
        xaxis=dict(
            visible=False,
            range=[-1.0, 1.0],
            autorange=False,
            fixedrange=False,
        ),
        yaxis=dict(
            visible=False,
            range=[0.0, 2.0],
            autorange=False,
            fixedrange=False,
        ),
        # Horizon arc: paper-coordinate SVG path (always an exact semicircle without scaleanchor)
        # Paper coordinates: x=0~1, y=0~1 (independent of data coordinates)
        # Semicircle: bottom-left (0,0) → bottom-right (1,0), arc center=(0.5,0), radius=0.5
        shapes=[
            dict(
                type="path",
                xref="paper",
                yref="paper",
                path="M 0,0 A 0.5,0.5 0 0 1 1,0",
                line=dict(color="#334466", width=1),
                fillcolor="rgba(0,0,0,0)",
            )
        ],
    )

    # scrollZoom set as Figure default config
    # st.plotly_chart call also requires config={"scrollZoom": True}
    fig._config = {"scrollZoom": True, "displayModeBar": False}  # type: ignore[attr-defined]

    return fig
