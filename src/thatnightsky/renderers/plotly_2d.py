"""Plotly 2D 인터랙티브 별자리 지도 렌더러.

skyfield stereographic 투영 결과(x, y)를 그대로 사용한다.
휠 줌 + 드래그 패닝으로 하늘을 둘러볼 수 있다.
"""

import numpy as np
import plotly.graph_objects as go

from thatnightsky.models import SkyData

_BG = "#050a1a"
_STAR_COLOR = "#ffffff"
_LINE_COLOR = "#7ec8e3"


def render_plotly_chart(sky_data: SkyData) -> go.Figure:
    """SkyData를 Plotly 2D 인터랙티브 별자리 지도로 렌더링한다.

    지평선 위 별(alt >= 0)만 표시하고 별자리 선분을 오버레이한다.
    휠로 줌인/줌아웃, 드래그로 패닝(둘러보기) 가능.
    투영: skyfield stereographic (등각, 별자리 형태 보존).

    Args:
        sky_data: 계산 완료된 천체 데이터.

    Returns:
        Plotly Figure 객체.
    """
    visible = [s for s in sky_data.stars if s.alt_deg >= 0]

    # --- 별 크기: 등급 → 마커 크기 ---
    mags = np.array([s.magnitude for s in visible])
    sizes = np.clip(6 - mags, 1, 8)

    x_vals = [s.x for s in visible]
    y_vals = [s.y for s in visible]

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

    # --- 별자리 선분: None 구분 방식 단일 trace ---
    hip_to_xy: dict[int, tuple[float, float]] = {s.hip: (s.x, s.y) for s in visible}
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

    # use_container_width=False + CSS 정사각형 컨테이너 환경에서 동작.
    # width/height는 기준점이며 CSS가 최종 크기를 결정.
    fig.update_layout(
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        width=1200,
        height=1200,
        dragmode="pan",
        xaxis=dict(
            visible=False,
            range=[-1.0, 1.0],
            autorange=False,
            fixedrange=False,
            scaleanchor="y",
            scaleratio=1,
        ),
        yaxis=dict(
            visible=False,
            range=[-1.0, 1.0],
            autorange=False,
            fixedrange=False,
        ),
        # 지평선 원: 데이터 좌표 기반 (scaleanchor로 정원 보장)
        shapes=[
            dict(
                type="circle",
                xref="x",
                yref="y",
                x0=-1,
                y0=-1,
                x1=1,
                y1=1,
                line=dict(color="#334466", width=1),
                fillcolor="rgba(0,0,0,0)",
            )
        ],
    )

    # scrollZoom을 Figure 기본 config로 설정
    # st.plotly_chart 호출 시에도 config={"scrollZoom": True} 필요
    fig._config = {"scrollZoom": True, "displayModeBar": False}  # type: ignore[attr-defined]

    return fig
