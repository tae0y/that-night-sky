// frontend/src/components/SkyChart.tsx
import { useEffect, type RefObject } from "react";
import type { SkyData } from "../types";

const BG = "#0d1b35";
const STAR_COLOR = "#f0e0b0";
const LINE_COLOR = "#c9a96e";
const HORIZON_COLOR = "#c9a96e";
// Bleed the ∪ dome's flat top slightly above the viewport so its straight top
// edge sits off-screen — otherwise the dome looks like it floats below a gap.
const TOP_BLEED_FRAC = 0.06;

function starRadius(magnitude: number): number {
  const r = (6 - magnitude) / 600;
  return Math.max(0.0018, Math.min(r, 0.018));
}

// Radial-gradient glow sprite (bright core → transparent edge), drawn once and
// stamped per star so each star reads as a translucent glow rather than a disc.
function makeGoldGlowSprite(): HTMLCanvasElement {
  const size = 64;
  const c = document.createElement("canvas");
  c.width = size;
  c.height = size;
  const g = c.getContext("2d")!;
  const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0, "rgba(255,244,206,0.85)");
  grad.addColorStop(0.28, "rgba(240,224,176,0.3)");
  grad.addColorStop(1, "rgba(240,224,176,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  return c;
}

function starOpacity(magnitude: number): number {
  return Math.max(0.35, Math.min(1.0, (6 - magnitude) / 6));
}

interface Props {
  skyData: SkyData;
  canvasRef: RefObject<HTMLCanvasElement | null>;
}

export function SkyChart({ skyData, canvasRef }: Props) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

    const glowSprite = makeGoldGlowSprite();
    const visible = skyData.stars.filter((s) => s.altDeg >= 0);
    const hipToXY = new Map<number, [number, number]>();
    for (const s of visible) hipToXY.set(s.hip, [s.x, s.y]);
    const visibleLines = skyData.constellationLines.filter(
      (l) => hipToXY.has(l.hipFrom) && hipToXY.has(l.hipTo),
    );

    function resize(): number {
      const dpr = window.devicePixelRatio || 1;
      const vh = window.innerHeight;
      const vw = window.innerWidth;
      // Height drives the dome on wide screens; on narrow/portrait viewports the
      // width cap keeps the full ∪ dome (2R wide) from being cropped off-screen.
      const R = Math.round(Math.min(vh * 0.6, vw * 0.56));
      canvas!.width = Math.round(2 * R * dpr);
      canvas!.height = Math.round(R * dpr);
      canvas!.style.width = `${2 * R}px`;
      canvas!.style.height = `${R}px`;
      canvas!.style.position = "fixed";
      canvas!.style.left = `${Math.round((vw - 2 * R) / 2)}px`;
      canvas!.style.top = `${-Math.round(R * TOP_BLEED_FRAC)}px`;
      canvas!.style.zIndex = "1"; // above the ambient .starfield-bg (z-index 0)
      return R;
    }

    function draw(R: number, rotAngle: number) {
      const dpr = window.devicePixelRatio || 1;
      const S = R * dpr;

      context!.setTransform(1, 0, 0, 1, 0, 0);
      context!.clearRect(0, 0, canvas!.width, canvas!.height);

      // data -> pixel: px = S*(x+1), py = S*y
      context!.setTransform(S, 0, 0, S, S, 0);

      // Confine the opaque sky to the horizon disc so the ambient background
      // starfield shows through the corners instead of a solid rectangle.
      context!.save();
      context!.beginPath();
      context!.arc(0, 0, 1, 0, Math.PI * 2);
      context!.clip();
      context!.fillStyle = BG;
      context!.fillRect(-1, 0, 2, 1);

      context!.save();
      context!.rotate((rotAngle * Math.PI) / 180);

      context!.strokeStyle = LINE_COLOR;
      context!.lineWidth = 0.0025;
      context!.globalAlpha = 0.55;
      for (const line of visibleLines) {
        const [x0, y0] = hipToXY.get(line.hipFrom)!;
        const [x1, y1] = hipToXY.get(line.hipTo)!;
        context!.beginPath();
        context!.moveTo(x0, y0);
        context!.lineTo(x1, y1);
        context!.stroke();
      }

      // Each star = translucent glow sprite + crisp core, so brighter stars
      // read as luminous points rather than flat dots.
      context!.fillStyle = STAR_COLOR;
      for (const s of visible) {
        const r = starRadius(s.magnitude);
        const op = starOpacity(s.magnitude);
        const gsize = r * 11;
        context!.globalAlpha = op * 0.6;
        context!.drawImage(glowSprite, s.x - gsize / 2, s.y - gsize / 2, gsize, gsize);
        context!.globalAlpha = op;
        context!.beginPath();
        context!.arc(s.x, s.y, r * 0.85, 0, Math.PI * 2);
        context!.fill();
      }
      context!.restore(); // rotation
      context!.restore(); // disc clip

      context!.globalAlpha = 0.85;
      context!.strokeStyle = HORIZON_COLOR;
      context!.lineWidth = 0.005;
      context!.beginPath();
      context!.arc(0, 0, 1, 0, Math.PI * 2);
      context!.stroke();
      context!.globalAlpha = 1;
    }

    const DEG_PER_MS = 360 / (600 * 1000); // one full rotation per 10 minutes
    let rotAngle = 0;
    let lastTs: number | null = null;
    let rafId = 0;
    let currentR = resize();

    function loop(ts: number) {
      if (lastTs !== null) {
        rotAngle = (rotAngle + (ts - lastTs) * DEG_PER_MS) % 360;
      }
      lastTs = ts;
      draw(currentR, rotAngle);
      rafId = requestAnimationFrame(loop);
    }

    function onResize() {
      currentR = resize();
    }
    window.addEventListener("resize", onResize);
    rafId = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(rafId);
    };
  }, [skyData, canvasRef]);

  return <canvas ref={canvasRef} />;
}
