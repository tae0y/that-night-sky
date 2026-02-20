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
    # viewBox="-1 0 2 1": center=(0,1), radius=1 → upper half arc only
    # SVG y-axis is top-down, so y=1 is the bottom edge of the viewBox.
    horizon_path = "M -1,1 A 1,1 0 0 1 1,1"
    # Below-horizon overlay: fill the viewBox rect minus the semicircle interior.
    # evenodd rule: outer rect (CW) ∪ inner arc (CCW) → only the ring outside the arc is filled.
    # Outer rect: top-left → top-right → bottom-right → bottom-left (clockwise)
    # Inner arc: right → left (counter-clockwise, sweep=0)
    horizon_overlay_path = "M -1,0 L 1,0 L 1,1 L -1,1 Z M 1,1 A 1,1 0 0 0 -1,1 Z"

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
    cursor: grab;
    touch-action: none;
    position: relative;
    z-index: 0;
}}
svg#sky.grabbing {{
    cursor: grabbing;
}}
#reset-btn {{
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    background: rgba(0,0,0,0.7);
    color: #aac8e8;
    border: 1px solid #334466;
    border-radius: 6px;
    padding: 0.4rem 0.9rem;
    font-size: 0.85rem;
    cursor: pointer;
    display: none;
    z-index: 100;
    user-select: none;
    pointer-events: auto;
}}
#reset-btn:hover {{
    background: rgba(51,68,102,0.85);
}}
</style>
</head>
<body>
<svg id="sky" viewBox="-1 0 2 1" xmlns="http://www.w3.org/2000/svg"
     preserveAspectRatio="xMidYMax meet">
  <rect x="-1" y="0" width="2" height="1" fill="{_BG}"/>
  <g id="scene">
    <g id="lines">
      {lines_svg}
    </g>
    <g id="stars">
      {stars_svg}
    </g>
    <path d="{horizon_path}" fill="none" stroke="{_HORIZON_COLOR}" stroke-width="0.004"/>
  </g>
</svg>
<button id="reset-btn">↺ 초기화</button>
<script>
(function() {{
  // ── iframe fit ──────────────────────────────────────────────
  var p = window.parent;
  function fit() {{
    var h = p.innerHeight;
    var iframe = p.document.querySelector('iframe[title="components.v1.html"]');
    if (!iframe) {{
      var frames = p.document.querySelectorAll('iframe');
      for (var i = 0; i < frames.length; i++) {{
        if (frames[i].contentWindow === window) {{ iframe = frames[i]; break; }}
      }}
    }}
    if (iframe) {{
      var w = h * 2;
      iframe.style.height = h + 'px';
      iframe.style.width = w + 'px';
      iframe.style.position = 'fixed';
      iframe.style.top = '0';
      iframe.style.left = Math.round((p.innerWidth - w) / 2) + 'px';
      iframe.style.zIndex = '0';
      iframe.style.border = 'none';
      document.getElementById('sky').style.visibility = 'visible';
    }}
  }}
  requestAnimationFrame(function() {{ requestAnimationFrame(fit); }});
  p.addEventListener('resize', fit);

  // ── pan + zoom ───────────────────────────────────────────────
  var svg = document.getElementById('sky');
  var scene = document.getElementById('scene');
  var resetBtn = document.getElementById('reset-btn');

  // transform state in SVG data-units
  var tx = 0, ty = 0, scale = 1;

  function applyTransform() {{
    scene.setAttribute('transform', 'translate(' + tx + ',' + ty + ') scale(' + scale + ')');
    var changed = (tx !== 0 || ty !== 0 || scale !== 1);
    resetBtn.style.display = changed ? 'block' : 'none';
  }}

  // convert mouse/touch clientX/Y → SVG data-unit coords
  function clientToSVG(clientX, clientY) {{
    var pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    // Use the inverse CTM of the scene's parent (the svg element)
    var ctm = svg.getScreenCTM();
    if (!ctm) return {{ x: 0, y: 0 }};
    var inv = ctm.inverse();
    return pt.matrixTransform(inv);
  }}

  // ── mouse pan ────────────────────────────────────────────────
  var dragging = false;
  var dragStart = {{ x: 0, y: 0 }};
  var txAtDrag = 0, tyAtDrag = 0;

  svg.addEventListener('mousedown', function(e) {{
    if (e.button !== 0) return;
    dragging = true;
    svg.classList.add('grabbing');
    var svgPt = clientToSVG(e.clientX, e.clientY);
    dragStart = svgPt;
    txAtDrag = tx;
    tyAtDrag = ty;
    e.preventDefault();
  }});

  window.addEventListener('mousemove', function(e) {{
    if (!dragging) return;
    var svgPt = clientToSVG(e.clientX, e.clientY);
    tx = txAtDrag + (svgPt.x - dragStart.x);
    ty = tyAtDrag + (svgPt.y - dragStart.y);
    applyTransform();
  }});

  window.addEventListener('mouseup', function() {{
    dragging = false;
    svg.classList.remove('grabbing');
  }});

  // ── wheel zoom ───────────────────────────────────────────────
  svg.addEventListener('wheel', function(e) {{
    e.preventDefault();
    // deltaY varies wildly by device/mode (1 line ≈ 3–40px, 1 page ≈ 800px).
    // Normalise to a fixed step per notch so trackpad doesn't feel 10× faster.
    var delta = e.deltaY;
    if (e.deltaMode === 0) {{ delta = delta / 120; }}  // pixel mode → notch units
    else if (e.deltaMode === 2) {{ delta = delta * 3; }} // page mode → notch units
    // clamp per-event step to ±3 notches to prevent runaway acceleration
    delta = Math.max(-3, Math.min(3, delta));
    var factor = Math.pow(1.06, -delta);
    var pivot = clientToSVG(e.clientX, e.clientY);
    // zoom toward pivot: translate so pivot stays fixed
    tx = pivot.x + (tx - pivot.x) * factor;
    ty = pivot.y + (ty - pivot.y) * factor;
    scale *= factor;
    // clamp zoom
    if (scale < 0.25) {{ var r = 0.25 / scale; scale = 0.25; tx *= r; ty *= r; }}
    if (scale > 8)    {{ var r = 8 / scale;    scale = 8;    tx *= r; ty *= r; }}
    applyTransform();
  }}, {{ passive: false }});

  // ── touch pan + pinch ────────────────────────────────────────
  var touches = {{}};
  var pinchDist0 = null;
  var scaleAtPinch = 1;
  var txAtPinch = 0, tyAtPinch = 0;
  var midAtPinch = null;

  function touchDist(t1, t2) {{
    var dx = t1.clientX - t2.clientX;
    var dy = t1.clientY - t2.clientY;
    return Math.sqrt(dx*dx + dy*dy);
  }}

  svg.addEventListener('touchstart', function(e) {{
    e.preventDefault();
    for (var i = 0; i < e.changedTouches.length; i++) {{
      var t = e.changedTouches[i];
      touches[t.identifier] = t;
    }}
    var ids = Object.keys(touches);
    if (ids.length === 1) {{
      var t = touches[ids[0]];
      dragging = true;
      dragStart = clientToSVG(t.clientX, t.clientY);
      txAtDrag = tx;
      tyAtDrag = ty;
    }} else if (ids.length === 2) {{
      dragging = false;
      var t1 = touches[ids[0]], t2 = touches[ids[1]];
      pinchDist0 = touchDist(t1, t2);
      scaleAtPinch = scale;
      txAtPinch = tx;
      tyAtPinch = ty;
      midAtPinch = clientToSVG(
        (t1.clientX + t2.clientX) / 2,
        (t1.clientY + t2.clientY) / 2
      );
    }}
  }}, {{ passive: false }});

  svg.addEventListener('touchmove', function(e) {{
    e.preventDefault();
    for (var i = 0; i < e.changedTouches.length; i++) {{
      var t = e.changedTouches[i];
      touches[t.identifier] = t;
    }}
    var ids = Object.keys(touches);
    if (ids.length === 1 && dragging) {{
      var t = touches[ids[0]];
      var svgPt = clientToSVG(t.clientX, t.clientY);
      tx = txAtDrag + (svgPt.x - dragStart.x);
      ty = tyAtDrag + (svgPt.y - dragStart.y);
      applyTransform();
    }} else if (ids.length === 2 && pinchDist0 !== null) {{
      var t1 = touches[ids[0]], t2 = touches[ids[1]];
      var dist = touchDist(t1, t2);
      var factor = dist / pinchDist0;
      scale = scaleAtPinch * factor;
      if (scale < 0.25) scale = 0.25;
      if (scale > 8)    scale = 8;
      // keep pinch midpoint fixed
      tx = midAtPinch.x * (1 - scale) + txAtPinch * (scale / scaleAtPinch);
      ty = midAtPinch.y * (1 - scale) + tyAtPinch * (scale / scaleAtPinch);
      applyTransform();
    }}
  }}, {{ passive: false }});

  svg.addEventListener('touchend', function(e) {{
    for (var i = 0; i < e.changedTouches.length; i++) {{
      delete touches[e.changedTouches[i].identifier];
    }}
    var ids = Object.keys(touches);
    if (ids.length < 2) {{
      pinchDist0 = null;
    }}
    if (ids.length === 1) {{
      var t = touches[ids[0]];
      dragging = true;
      dragStart = clientToSVG(t.clientX, t.clientY);
      txAtDrag = tx;
      tyAtDrag = ty;
    }} else if (ids.length === 0) {{
      dragging = false;
    }}
  }}, {{ passive: false }});

  // ── reset ────────────────────────────────────────────────────
  resetBtn.addEventListener('click', function() {{
    tx = 0; ty = 0; scale = 1;
    applyTransform();
  }});
}})();
</script>
</body>
</html>"""
