"""SVG 2D interactive star chart renderer.

Produces a self-contained HTML string (SVG + JS) for embedding via
st.components.v1.html(). Uses viewBox="-1 0 2 1" with CSS
width/height 100% so the browser handles all scaling — no Plotly
relayout hacks required.

Coordinate system (matches plotly_2d.py):
  x ∈ [-1, 1]  (stereographic projection, East-West)
  y ∈ [ 0, 1]  (stereographic projection, 0=horizon, 1=zenith)
"""

from __future__ import annotations

from thatnightsky.models import SkyData

_BG = "#050a1a"
_STAR_COLOR = "#ffffff"
_LINE_COLOR = "#7ec8e3"
_HORIZON_COLOR = "#334466"


def _star_radius(magnitude: float) -> float:
    """Map Hipparcos magnitude to SVG circle radius in data-units."""
    # viewBox width=2, so radius 0.01 ≈ 1% of chart width
    r = (6 - magnitude) / 800
    return max(0.002, min(r, 0.012))


def render_svg_html(sky_data: SkyData) -> str:
    """Return a self-contained HTML page with an SVG star chart.

    The SVG fills the viewport via CSS. A semicircle represents the
    horizon. Stars above the horizon (alt_deg >= 0) are drawn as
    white circles scaled by magnitude. Constellation lines are drawn
    as thin cyan strokes.

    Args:
        sky_data: Fully computed celestial data.

    Returns:
        HTML string suitable for st.components.v1.html().
    """
    visible = [s for s in sky_data.stars if s.alt_deg >= 0]

    # --- Constellation lines ---
    hip_to_xy: dict[int, tuple[float, float]] = {s.hip: (s.x, s.y) for s in visible}
    line_parts: list[str] = []
    for line in sky_data.constellation_lines:
        if line.hip_from in hip_to_xy and line.hip_to in hip_to_xy:
            x0, y0 = hip_to_xy[line.hip_from]
            x1, y1 = hip_to_xy[line.hip_to]
            # SVG y-axis is top-down; data y=0 → SVG bottom, y=1 → SVG top
            # viewBox="-1 0 2 1": SVG y=0 is top, SVG y=1 is bottom
            # → flip: svg_y = 1 - data_y
            sy0 = 1 - y0
            sy1 = 1 - y1
            line_parts.append(
                f'<line x1="{x0:.4f}" y1="{sy0:.4f}" x2="{x1:.4f}" y2="{sy1:.4f}"'
                f' stroke="{_LINE_COLOR}" stroke-width="0.002" stroke-opacity="0.5"/>'
            )

    # --- Stars ---
    star_parts: list[str] = []
    for s in visible:
        r = _star_radius(s.magnitude)
        sy = 1 - s.y
        star_parts.append(
            f'<circle cx="{s.x:.4f}" cy="{sy:.4f}" r="{r:.4f}"'
            f' fill="{_STAR_COLOR}" opacity="0.9"/>'
        )

    # --- Horizon semicircle ---
    # viewBox="-1 0 2 1": data y=0 → svg y=1 (bottom edge)
    # Semicircle: center=(0,1), radius=1, upper half only
    # SVG arc: M -1,1 A 1,1 0 0 1 1,1  (large-arc=0, sweep=1 = clockwise upper arc)
    horizon_path = 'M -1,1 A 1,1 0 0 1 1,1'

    lines_svg = "\n    ".join(line_parts)
    stars_svg = "\n    ".join(star_parts)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{
    width: 100%;
    height: 100%;
    background: {_BG};
    overflow: hidden;
}}
svg#sky {{
    display: block;
    width: 100%;
    height: 100%;
    visibility: hidden;
}}
</style>
</head>
<body>
<svg id="sky" viewBox="-1 0 2 1" xmlns="http://www.w3.org/2000/svg"
     preserveAspectRatio="xMidYMax meet">
  <rect x="-1" y="0" width="2" height="1" fill="{_BG}"/>
  <g id="lines">
    {lines_svg}
  </g>
  <g id="stars">
    {stars_svg}
  </g>
  <path d="{horizon_path}" fill="none" stroke="{_HORIZON_COLOR}" stroke-width="0.004"/>
</svg>
<script>
(function() {{
  // iframe 자체를 부모 뷰포트 높이로 맞춤
  var p = window.parent;
  function fit() {{
    var h = p.innerHeight;
    var iframe = p.document.querySelector('iframe[title="components.v1.html"]');
    if (!iframe) {{
      // Streamlit은 title 없이 data-testid로도 찾을 수 있음
      var frames = p.document.querySelectorAll('iframe');
      for (var i = 0; i < frames.length; i++) {{
        if (frames[i].contentWindow === window) {{ iframe = frames[i]; break; }}
      }}
    }}
    if (iframe) {{
      // viewBox="-1 0 2 1" → 가로:세로 = 2:1
      // 반지름=높이 고정: iframe 너비를 정확히 h*2로 맞춤
      var w = h * 2;
      iframe.style.height = h + 'px';
      iframe.style.width = w + 'px';
      iframe.style.position = 'fixed';
      iframe.style.top = '0';
      iframe.style.left = Math.round((p.innerWidth - w) / 2) + 'px';
      iframe.style.zIndex = '0';
      iframe.style.border = 'none';
      // iframe 크기가 확정된 후 SVG를 보임
      document.getElementById('sky').style.visibility = 'visible';
    }}
  }}
  requestAnimationFrame(function() {{ requestAnimationFrame(fit); }});
  p.addEventListener('resize', fit);
}})();
</script>
</body>
</html>"""
