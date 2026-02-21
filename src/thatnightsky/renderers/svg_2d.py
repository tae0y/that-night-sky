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

_BG = "#0d1b35"
_STAR_COLOR = "#f0e0b0"
_LINE_COLOR = "#c9a96e"
_HORIZON_COLOR = "#c9a96e"


def _star_radius(magnitude: float) -> float:
    """Map Hipparcos magnitude to SVG circle radius in data-units."""
    # viewBox width=2, so radius 0.01 ≈ 1% of chart width.
    # Wider dynamic range than before: bright stars (mag<2) are notably larger.
    r = (6 - magnitude) / 600
    return max(0.0018, min(r, 0.018))


def _star_opacity(magnitude: float) -> float:
    """Dimmer stars are more transparent, reinforcing magnitude difference."""
    return max(0.35, min(1.0, (6 - magnitude) / 6))


def render_svg_html(
    sky_data: SkyData,
    filename: str = "that-night-sky.png",
    narrative: str = "",
    lang: str = "en",
) -> str:
    """Return a self-contained HTML page with an SVG star chart.

    The SVG fills the viewport via CSS. A semicircle represents the
    horizon. Stars above the horizon (alt_deg >= 0) are drawn as
    white circles scaled by magnitude. Constellation lines are drawn
    as thin cyan strokes.

    When `narrative` is set, it is embedded as a JS string and drawn
    as wrapped text at the bottom of the captured PNG on `tns_save`.

    Args:
        sky_data: Fully computed celestial data.
        filename: Suggested filename for the downloaded PNG.
        narrative: Optional narrative text to draw on PNG.
        lang: Language code ('ko' or 'en') for button labels.

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
                f' stroke="{_LINE_COLOR}" stroke-width="0.0025" stroke-opacity="0.55"/>'
            )

    # --- Stars ---
    # 10 shared radialGradient levels keyed by opacity bucket — avoids one gradient
    # per star which would bloat the HTML and break iframe rendering.
    _N_GLOW_LEVELS = 10
    grad_defs: list[str] = []
    for lvl in range(_N_GLOW_LEVELS):
        op_lvl = 0.35 + lvl * (0.65 / (_N_GLOW_LEVELS - 1))
        grad_defs.append(
            f'<radialGradient id="sg{lvl}" cx="50%" cy="50%" r="50%">'
            f'<stop offset="0%" stop-color="{_STAR_COLOR}" stop-opacity="{op_lvl * 0.55:.2f}"/>'
            f'<stop offset="40%" stop-color="{_STAR_COLOR}" stop-opacity="{op_lvl * 0.18:.2f}"/>'
            f'<stop offset="100%" stop-color="{_STAR_COLOR}" stop-opacity="0"/>'
            f"</radialGradient>"
        )

    star_parts: list[str] = []
    for s in visible:
        r = _star_radius(s.magnitude)
        op = _star_opacity(s.magnitude)
        sy = 1 - s.y
        glow_r = r * 4.5
        lvl = round((op - 0.35) / 0.65 * (_N_GLOW_LEVELS - 1))
        lvl = max(0, min(_N_GLOW_LEVELS - 1, lvl))
        star_parts.append(
            f'<circle cx="{s.x:.4f}" cy="{sy:.4f}" r="{glow_r:.4f}"'
            f' fill="url(#sg{lvl})"/>'
        )
        star_parts.append(
            f'<circle cx="{s.x:.4f}" cy="{sy:.4f}" r="{r:.4f}"'
            f' fill="{_STAR_COLOR}" opacity="{op:.2f}"/>'
        )

    # --- Horizon circle ---
    # Full circle centred at (0,1) with radius 1.
    # viewBox="-1 0 2 1": only the upper half is visible (y<1); lower half is clipped.
    # SVG y-axis is top-down, so y=1 is the bottom edge of the viewBox.
    # Two strokes: outer glow (wide, low opacity) + sharp inner line.
    horizon_path = "M -1,1 A 1,1 0 1 1 1,1 A 1,1 0 1 1 -1,1 Z"

    lines_svg = "\n    ".join(line_parts)
    defs_svg = "\n    ".join(grad_defs)
    stars_svg = "\n    ".join(star_parts)

    # Escape narrative for safe embedding as a JS string literal.
    narrative_js = (
        "null"
        if not narrative
        else '"'
        + narrative.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "")
        + '"'
    )

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
canvas#starfield {{
    position: fixed;
    top: 0; left: 0;
    pointer-events: none;
    z-index: 0;
}}
svg#sky {{
    display: block;
    position: fixed;
    visibility: hidden;
    cursor: grab;
    touch-action: none;
    z-index: 1;
}}
svg#sky.grabbing {{
    cursor: grabbing;
}}
#reset-btn {{
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    background: rgba(13,27,53,0.85);
    color: #c9a96e;
    border: 1px solid rgba(201,169,110,0.4);
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
    background: rgba(201,169,110,0.15);
}}
#save-btn {{ display: none; }}
</style>
</head>
<body>
<canvas id="starfield"></canvas>
<svg id="sky" viewBox="-1 0 2 1" xmlns="http://www.w3.org/2000/svg"
     preserveAspectRatio="none" overflow="visible">
  <defs>
    {defs_svg}
  </defs>
  <rect x="-1" y="0" width="2" height="1" fill="{_BG}"/>
  <g id="scene">
    <g id="rotating">
      <g id="lines">
        {lines_svg}
      </g>
      <g id="stars">
        {stars_svg}
      </g>
    </g>
    <!-- horizon: wide glow stroke + sharp gold line -->
    <path d="{horizon_path}" fill="none" stroke="{_HORIZON_COLOR}" stroke-width="0.018" stroke-opacity="0.12"/>
    <path d="{horizon_path}" fill="none" stroke="{_HORIZON_COLOR}" stroke-width="0.005" stroke-opacity="0.85"/>
  </g>
</svg>
<button id="reset-btn">↺ {"초기화" if lang == "ko" else "Reset"}</button>
<button id="save-btn">↓ {"저장" if lang == "ko" else "Save"}</button>
<script>
(function() {{
  // ── iframe + SVG fit ─────────────────────────────────────────
  // viewBox="-1 0 2 1": data y=0 (zenith) → SVG top, data y=1 (horizon centre) → SVG bottom.
  // preserveAspectRatio="none" requires pixel ratio to match viewBox ratio exactly (2:1)
  // so the horizon arc remains a true semicircle.
  // SVG width=2R, height=R → ratio 2:1 ✓
  // SVG top = CENTRE_TOP_PX - R → screen y of SVG bottom edge = CENTRE_TOP_PX ✓
  // overflow="visible" on the SVG lets the horizon arc stroke paint outside the box.
  var CENTRE_TOP_PX = 50;
  var sky = document.getElementById('sky');
  var sfCanvas = document.getElementById('starfield');
  var p = window.parent;

  // ── starfield canvas ──────────────────────────────────────────
  // Called after fit() sets SVG geometry. Uses the same R/svgTop/vw/vh
  // values so particles land exactly in the visible screen area.
  // seededRand: simple deterministic LCG so particles are stable across redraws.
  function drawStarfield(vw, vh, R, svgTop) {{
    var dpr = window.devicePixelRatio || 1;
    sfCanvas.width  = Math.round(vw * dpr);
    sfCanvas.height = Math.round(vh * dpr);
    sfCanvas.style.width  = vw + 'px';
    sfCanvas.style.height = vh + 'px';
    var ctx = sfCanvas.getContext('2d');
    ctx.fillStyle = '{_BG}';
    ctx.fillRect(0, 0, sfCanvas.width, sfCanvas.height);

    // Deterministic PRNG (seeded) so the field doesn't flicker on resize
    var s = 12345;
    function rand() {{ s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; }}
    function gauss() {{
      return Math.sqrt(-2 * Math.log(rand() + 1e-9)) * Math.cos(2 * Math.PI * rand());
    }}

    // Screen-space dome centre (horizon arc centre): x=vw/2, y=CENTRE_TOP_PX
    // SVG top = svgTop (negative), so screen y=0 maps to SVG pixel y = -svgTop.
    // Dome arc centre in screen px: (vw/2, CENTRE_TOP_PX).
    // Dome radius in screen px: R.
    var cx = vw / 2 * dpr;
    var cy = CENTRE_TOP_PX * dpr;  // horizon centre in physical px
    var cR = R * dpr;

    // Pass 1: sparse uniform across full screen
    for (var i = 0; i < 2000; i++) {{
      var px = rand() * sfCanvas.width;
      var py = rand() * sfCanvas.height;
      var r  = (0.4 + rand() * 0.6) * dpr;
      var op = 0.06 + rand() * 0.18;
      ctx.beginPath(); ctx.arc(px, py, r, 0, 6.283);
      ctx.fillStyle = 'rgba(210,225,255,' + op.toFixed(2) + ')';
      ctx.fill();
    }}

    // Pass 2: blob clusters — 16 centres, each 200 particles, tight sigma
    for (var b = 0; b < 16; b++) {{
      var bx = cx + gauss() * cR * 0.7;
      var by = cy - rand() * cR;  // above horizon (screen y < cy)
      for (var j = 0; j < 200; j++) {{
        var px2 = bx + gauss() * cR * 0.08;
        var py2 = by + gauss() * cR * 0.06;
        if (px2 < 0 || py2 < 0 || px2 > sfCanvas.width || py2 > sfCanvas.height) continue;
        var r2  = (0.4 + rand() * 0.7) * dpr;
        var op2 = 0.15 + rand() * 0.35;
        ctx.beginPath(); ctx.arc(px2, py2, r2, 0, 6.283);
        ctx.fillStyle = 'rgba(210,225,255,' + op2.toFixed(2) + ')';
        ctx.fill();
      }}
    }}

    // Pass 3: brighter accent dots
    for (var k = 0; k < 600; k++) {{
      var px3 = rand() * sfCanvas.width;
      var py3 = rand() * sfCanvas.height;
      var r3  = (0.7 + rand() * 1.0) * dpr;
      var op3 = 0.22 + rand() * 0.33;
      ctx.beginPath(); ctx.arc(px3, py3, r3, 0, 6.283);
      ctx.fillStyle = 'rgba(230,240,255,' + op3.toFixed(2) + ')';
      ctx.fill();
    }}
  }}

  function fit() {{
    var vw = p.innerWidth;
    var vh = p.innerHeight;
    // R: dome radius = 60% of viewport height
    var R = Math.round(vh * 0.6);
    var svgLeft = Math.round((vw - 2 * R) / 2);
    var svgTop  = CENTRE_TOP_PX - R;
    sky.style.width  = (2 * R) + 'px';
    sky.style.height = R + 'px';
    sky.style.left   = svgLeft + 'px';
    sky.style.top    = svgTop  + 'px';
    drawStarfield(vw, vh, R, svgTop);

    // Sync iframe to full parent viewport
    var iframe = null;
    var frames = p.document.querySelectorAll('iframe');
    for (var i = 0; i < frames.length; i++) {{
      if (frames[i].contentWindow === window) {{ iframe = frames[i]; break; }}
    }}
    if (iframe) {{
      iframe.style.width    = vw + 'px';
      iframe.style.height   = vh + 'px';
      iframe.style.position = 'fixed';
      iframe.style.top      = '0';
      iframe.style.left     = '0';
      iframe.style.zIndex   = '0';
      iframe.style.border   = 'none';
    }}
    sky.style.visibility = 'visible';
  }}
  requestAnimationFrame(function() {{
    requestAnimationFrame(function() {{
      fit();
      // Watch parent DOM for tns-save-trigger marker injected by Streamlit
      // when the save button is clicked. chart iframe has allow-same-origin
      // so p.document is accessible.
      try {{
        // tns-save-trigger is always in the DOM when sky_data exists.
        // data-seq=0 means no save yet; seq>=1 means a save was requested.
        // Strategy: watch for attribute changes on the trigger node (seq increments),
        // and also handle the case where the node is added after iframe loads.
        // Initialise _lastSeq from the current data-seq so a seq already in the
        // DOM when this iframe loads is treated as "already handled".
        // Only a seq that increments *after* this iframe loaded triggers capture.
        var _initEl = p.document.getElementById('tns-save-trigger');
        var _lastSeq = _initEl ? parseInt(_initEl.getAttribute('data-seq') || '0', 10) : 0;

        function _checkTrigger() {{
          var el = p.document.getElementById('tns-save-trigger');
          if (!el) return;
          var seq = parseInt(el.getAttribute('data-seq') || '0', 10);
          if (seq > _lastSeq) {{
            _lastSeq = seq;
            _doCapture(null);
          }}
        }}

        var mo = new MutationObserver(function(records) {{
          for (var ri = 0; ri < records.length; ri++) {{
            var r = records[ri];
            // attribute change on the trigger node itself
            if (r.type === 'attributes' && r.target.id === 'tns-save-trigger') {{
              _checkTrigger(); return;
            }}
            // node added: trigger node newly inserted (e.g. first chart load)
            var nodes = r.addedNodes;
            for (var ni = 0; ni < nodes.length; ni++) {{
              var n = nodes[ni];
              if ((n.id === 'tns-save-trigger') ||
                  (n.querySelector && n.querySelector('#tns-save-trigger'))) {{
                _checkTrigger(); return;
              }}
            }}
          }}
        }});
        mo.observe(p.document.body, {{ childList: true, subtree: true, attributes: true, attributeFilter: ['data-seq'] }});
      }} catch(e) {{}}
    }});
  }});
  p.addEventListener('resize', fit);

  // ── pan + zoom ───────────────────────────────────────────────
  var svg = document.getElementById('sky');
  var scene = document.getElementById('scene');
  var rotating = document.getElementById('rotating');
  var resetBtn = document.getElementById('reset-btn');

  // transform state in SVG data-units
  var tx = 0, ty = 0, scale = 1;

  function applyTransform() {{
    scene.setAttribute('transform', 'translate(' + tx + ',' + ty + ') scale(' + scale + ')');
    var changed = (tx !== 0 || ty !== 0 || scale !== 1);
    resetBtn.style.display = changed ? 'block' : 'none';
  }}

  // ── auto-rotation ────────────────────────────────────────────
  // Rotate stars+lines around the horizon semicircle centre (SVG coords: cx=0, cy=1).
  // One full rotation every 10 minutes (600 seconds).
  var DEG_PER_MS = 360 / (600 * 1000);
  var rotAngle = 0;
  var lastTs = null;

  function rotationLoop(ts) {{
    if (lastTs !== null) {{
      rotAngle += (ts - lastTs) * DEG_PER_MS;
      if (rotAngle >= 360) rotAngle -= 360;
    }}
    lastTs = ts;
    rotating.setAttribute('transform', 'rotate(' + rotAngle + ',0,1)');
    requestAnimationFrame(rotationLoop);
  }}
  requestAnimationFrame(rotationLoop);

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

  // ── save button ──────────────────────────────────────────────
  var saveBtn = document.getElementById('save-btn');
  saveBtn.addEventListener('click', function() {{
    saveBtn.disabled = true;
    _doCapture(function() {{ saveBtn.disabled = false; }});
  }});

  // ── PNG capture ──────────────────────────────────────────────
  // Strategy: SVG data URI → <img> → Canvas drawImage (no external deps)
  //
  // html2canvas: Edge renders position:fixed SVG as blank.
  // SVG Blob URL: fragment IDs (url(#sg0)) lose document context in Blob origin
  //   → radialGradient lookup fails → stars are transparent.
  // data URI: fragment IDs resolve within the inline SVG <defs> → gradients work.
  //
  // SVG position: top = CENTRE_TOP_PX - R, typically negative.
  // Use 9-arg drawImage to crop only the on-screen slice from the SVG image,
  // avoiding the off-screen negative-top portion that causes canvas clipping.
  //
  // Composite: background fill → starfield canvas → SVG crop → narrative text.
  var _NARRATIVE = {narrative_js};

  function _doCapture(onDone) {{
    var vp = window.parent || window;
    var pw = vp.innerWidth;
    var ph = vp.innerHeight;
    var dpr = window.devicePixelRatio || 1;

    // SVG geometry as set by fit() (CSS pixels)
    var svgW    = parseFloat(sky.style.width)  || pw;
    var svgH    = parseFloat(sky.style.height) || (pw / 2);
    var svgLeft = parseFloat(sky.style.left)   || 0;
    var svgTop  = parseFloat(sky.style.top)    || 0;  // typically negative

    // Output canvas: full viewport in physical pixels
    var out = document.createElement('canvas');
    out.width  = Math.round(pw * dpr);
    out.height = Math.round(ph * dpr);
    var ctx = out.getContext('2d');

    // Step 1: background + starfield canvas
    ctx.fillStyle = '{_BG}';
    ctx.fillRect(0, 0, out.width, out.height);
    try {{
      if (sfCanvas && sfCanvas.width > 0) {{
        ctx.drawImage(sfCanvas, 0, 0, out.width, out.height);
      }}
    }} catch(e) {{}}

    // Step 2: serialize live SVG into data URI, snapshotting current transforms.
    //
    // The SVG element has:  top = svgTop (negative), height = R.
    // overflow="visible" means the horizon arc stroke (at y=1 in data-units, the
    // very bottom of the viewBox) extends slightly below the SVG's pixel boundary.
    // When the browser rasterises a <img> from an SVG data URI it clips to the
    // declared pixel height — so we must give the clone extra height to prevent
    // the stroke from being cut off.
    //
    // Strategy: extend viewBox height (y stays at 0) so overflow="visible" horizon
    // stroke is included in the rasterised image, while keeping the 1 data-unit = R px
    // scale intact (width/height change together with the same pixel:data ratio).
    //
    // Original: width=2R, height=R, viewBox="-1 0 2 1"  → 1 data-unit = R px
    // Extended: width=2R, height=extH, viewBox="-1 0 2 vbH"
    //   vbH = extH / R  → still 1 data-unit = R px, so content positions unchanged.
    //   y=1 (horizon) still maps to pixel y=R; overflow stroke lands in y=R…extH.
    //
    // extH = ph - svgTop  (svgTop < 0, so extH > ph; the image covers svgTop…ph)
    // drawImage source:
    //   sx = 0 (svgLeft >= 0, no horizontal off-screen; centred dome fits in viewport)
    //   sy = -svgTop  (skip the above-screen portion; image top = screen y=svgTop)
    //   sw = pw, sh = ph  (paint exactly the full viewport)
    //   dx=0, dy=0, dw=pw*dpr, dh=ph*dpr
    var R    = svgH;                  // svgH = R from fit()
    var extH = ph - svgTop;           // svgTop <= 0 → extH >= ph
    var vbH  = extH / R;              // viewBox height in data-units

    var svgEl    = document.getElementById('sky');
    var clone    = svgEl.cloneNode(true);
    clone.setAttribute('width',  svgW);   // keep original pixel width (= 2R)
    clone.setAttribute('height', extH);
    clone.setAttribute('viewBox', '-1 0 2 ' + vbH.toFixed(6));
    var rotEl    = svgEl.querySelector('#rotating');
    var cloneRot = clone.querySelector('#rotating');
    if (rotEl && cloneRot) {{
      cloneRot.setAttribute('transform', rotEl.getAttribute('transform') || '');
    }}
    var sceneEl    = svgEl.querySelector('#scene');
    var cloneScene = clone.querySelector('#scene');
    if (sceneEl && cloneScene) {{
      cloneScene.setAttribute('transform', sceneEl.getAttribute('transform') || '');
    }}

    var svgStr  = new XMLSerializer().serializeToString(clone);
    // btoa handles only single-byte chars; URI-encode then unescape covers UTF-8
    var dataUri = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));

    // Step 3: ensure the custom font is loaded in this canvas context before drawing.
    // Canvas 2D does not inherit @font-face from CSS unless the font is already loaded.
    var _fontSpec = 'italic 16px "NostalgicPoliceHumanRights"';
    var _fontUrl  = 'https://cdn.jsdelivr.net/gh/projectnoonnu/2601-6@1.0/Griun_PolHumanrights-Rg.woff2';
    function _drawWithFont(drawFn) {{
      if (!_NARRATIVE) {{ drawFn(); return; }}
      // FontFace API available in all modern browsers
      if (typeof FontFace !== 'undefined' && document.fonts) {{
        var ff = new FontFace('NostalgicPoliceHumanRights', 'url(' + _fontUrl + ')', {{ style: 'italic' }});
        ff.load().then(function(loaded) {{
          document.fonts.add(loaded);
          drawFn();
        }}).catch(function() {{ drawFn(); }});
      }} else {{
        drawFn();
      }}
    }}

    var img = new Image();
    img.onload = function() {{
      // 9-arg drawImage.
      // Image size: svgW × extH.  Image top-left is at screen (svgLeft, svgTop).
      // svgTop < 0: image extends above screen top; sy=-svgTop skips that portion.
      // svgLeft < 0: dome wider than viewport; sx=-svgLeft skips off-screen left portion.
      // svgLeft > 0: dome narrower than viewport; dx=svgLeft*dpr offsets onto canvas.
      var sx = svgLeft < 0 ? -svgLeft : 0;
      var sy = -svgTop;
      var sw = Math.min(svgW - sx, pw - (svgLeft > 0 ? svgLeft : 0));
      var sh = ph;
      var dx = svgLeft > 0 ? Math.round(svgLeft * dpr) : 0;
      var dy = 0;
      var dw = sw * dpr;
      var dh = ph * dpr;

      if (sw > 0 && sh > 0) {{
        ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh);
      }}

      _drawWithFont(function() {{
        // Step 4: narrative overlay at bottom
        if (_NARRATIVE) {{
          var padY     = Math.round(24 * dpr);
          var fontSize = Math.round(16 * dpr);
          var lineH    = Math.round(fontSize * 1.75);
          var maxW     = Math.min(Math.round(pw * dpr * 0.85), Math.round(640 * dpr));
          var font     = 'italic ' + fontSize + 'px "NostalgicPoliceHumanRights","Apple SD Gothic Neo","Malgun Gothic",sans-serif';
          ctx.font = font;

          var tokens = _NARRATIVE.split(/\\s+/);
          var lines = [], cur = '';
          for (var ti = 0; ti < tokens.length; ti++) {{
            var tok = tokens[ti];
            if (!tok) continue;
            var test = cur ? cur + ' ' + tok : tok;
            if (ctx.measureText(test).width > maxW && cur) {{
              lines.push(cur); cur = tok;
            }} else {{ cur = test; }}
          }}
          if (cur) lines.push(cur);

          var boxH = lines.length * lineH + padY * 2;
          var boxY = out.height - boxH;
          ctx.fillStyle = 'rgba(10,20,42,0.82)';
          ctx.fillRect(0, boxY, out.width, boxH);
          ctx.fillStyle = 'rgba(201,169,110,0.4)';
          ctx.fillRect(0, boxY, out.width, Math.round(dpr));
          ctx.font = font;
          ctx.fillStyle = '#e8d5a3';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          var ty2 = boxY + padY;
          for (var li = 0; li < lines.length; li++) {{
            ctx.fillText(lines[li], Math.round(out.width / 2), ty2);
            ty2 += lineH;
          }}
        }}

        // Step 5: trigger download
        var a = document.createElement('a');
        a.href = out.toDataURL('image/png');
        a.download = '{filename}';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        if (onDone) onDone();
      }});
    }};
    img.onerror = function() {{
      if (onDone) onDone();
    }};
    img.src = dataUri;
  }}

  window.addEventListener('message', function(e) {{
    if (!e.data || e.data.type !== 'tns_save') return;
    _doCapture(null);
  }});
}})();
</script>
</body>
</html>"""
