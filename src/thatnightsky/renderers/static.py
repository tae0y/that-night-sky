"""Matplotlib static PNG renderer."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from thatnightsky.models import SkyData

_ROOT = Path(__file__).parent.parent.parent.parent


def render_static_chart(sky_data: SkyData, chart_size: int = 10) -> Figure:
    """Render SkyData as a static matplotlib image.

    Args:
        sky_data: Fully computed celestial data.
        chart_size: Output image size in inches.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(chart_size, chart_size))
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")

    border = plt.Circle((0, 0), 1, color="black", fill=True)
    ax.add_patch(border)

    x_vals = np.array([s.x for s in sky_data.stars])
    y_vals = np.array([s.y for s in sky_data.stars])
    mags = np.array([s.magnitude for s in sky_data.stars])

    hip_to_xy = {s.hip: (s.x, s.y) for s in sky_data.stars}
    for line in sky_data.constellation_lines:
        if line.hip_from in hip_to_xy and line.hip_to in hip_to_xy:
            x0, y0 = hip_to_xy[line.hip_from]
            x1, y1 = hip_to_xy[line.hip_to]
            ax.plot(
                [x0, x1], [y0, y1], color="#7ec8e3", linewidth=0.5, alpha=0.6, zorder=1
            )

    marker_size = 100 * 10 ** (mags / -2.5)
    ax.scatter(
        x_vals, y_vals, s=marker_size, color="white", marker=".", linewidths=0, zorder=2
    )

    horizon = Circle((0, 0), radius=1, transform=ax.transData)
    for col in ax.collections:
        col.set_clip_path(horizon)

    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis("off")

    return fig


def save_static_chart(sky_data: SkyData, output_path: Path | None = None) -> Path:
    """Save SkyData as a PNG file.

    Args:
        sky_data: Fully computed celestial data.
        output_path: Destination path. Auto-generated under results/ if None.

    Returns:
        Path to the saved file.
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
