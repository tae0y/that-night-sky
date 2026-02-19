"""matplotlib 정적 PNG 렌더러."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from thatnightsky.models import SkyData

_ROOT = Path(__file__).parent.parent.parent.parent


def render_static_chart(sky_data: SkyData, chart_size: int = 10) -> Figure:
    """SkyData를 matplotlib 정적 이미지로 렌더링한다.

    Args:
        sky_data: 계산 완료된 천체 데이터.
        chart_size: 출력 이미지 크기 (인치).

    Returns:
        matplotlib Figure 객체.
    """
    fig, ax = plt.subplots(figsize=(chart_size, chart_size))
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")

    border = plt.Circle((0, 0), 1, color="black", fill=True)
    ax.add_patch(border)

    x_vals = np.array([s.x for s in sky_data.stars])
    y_vals = np.array([s.y for s in sky_data.stars])
    mags = np.array([s.magnitude for s in sky_data.stars])

    marker_size = 100 * 10 ** (mags / -2.5)
    ax.scatter(x_vals, y_vals, s=marker_size, color="white", marker=".", linewidths=0, zorder=2)

    horizon = Circle((0, 0), radius=1, transform=ax.transData)
    for col in ax.collections:
        col.set_clip_path(horizon)

    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis("off")

    return fig


def save_static_chart(sky_data: SkyData, output_path: Path | None = None) -> Path:
    """SkyData를 PNG 파일로 저장한다.

    Args:
        sky_data: 계산 완료된 천체 데이터.
        output_path: 저장 경로. None이면 results/ 아래 자동 생성.

    Returns:
        저장된 파일 경로.
    """
    if output_path is None:
        ctx = sky_data.context
        when_str = ctx.utc_dt.strftime("%Y_%m_%d_%H_%M")
        filename = f"{ctx.address_display}__{when_str}.png".replace(" ", "_")
        output_path = _ROOT / "results" / filename

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = render_static_chart(sky_data)
    fig.savefig(output_path, facecolor="black")
    plt.close(fig)
    return output_path
