// frontend/src/components/Starfield.tsx
// Ambient, decorative starfield rendered behind everything. These stars are NOT
// the computed sky — they exist purely for atmosphere and fill the area "outside"
// the horizon dome (which SkyChart clips to a disc so this shows through).
import { useEffect, type RefObject } from "react";

interface Star {
  x: number;
  y: number;
  r: number;
  base: number; // baseline opacity
  phase: number; // twinkle phase offset
  speed: number; // twinkle speed
}

// A radial-gradient sprite (bright core → transparent edge) drawn once and
// stamped per star, so each star reads as a real glow rather than a flat disc.
function makeGlowSprite(): HTMLCanvasElement {
  const size = 64;
  const c = document.createElement("canvas");
  c.width = size;
  c.height = size;
  const g = c.getContext("2d")!;
  const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0, "rgba(244,246,255,0.9)");
  grad.addColorStop(0.25, "rgba(205,217,255,0.35)");
  grad.addColorStop(1, "rgba(205,217,255,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  return c;
}

interface Props {
  canvasRef: RefObject<HTMLCanvasElement | null>;
}

export function Starfield({ canvasRef }: Props) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const glow = makeGlowSprite();
    let stars: Star[] = [];
    let w = 0;
    let h = 0;
    let dpr = 1;

    function resize() {
      dpr = window.devicePixelRatio || 1;
      w = window.innerWidth;
      h = window.innerHeight;
      canvas!.width = Math.round(w * dpr);
      canvas!.height = Math.round(h * dpr);
      canvas!.style.width = `${w}px`;
      canvas!.style.height = `${h}px`;
      const count = Math.min(420, Math.round((w * h) / 5200));
      stars = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.1 + 0.35,
        base: Math.random() * 0.32 + 0.1,
        phase: Math.random() * Math.PI * 2,
        speed: Math.random() * 0.7 + 0.25,
      }));
    }

    let rafId = 0;
    let startTs: number | null = null;

    function loop(ts: number) {
      if (startTs === null) startTs = ts;
      const t = (ts - startTs) / 1000;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx!.clearRect(0, 0, w, h);
      for (const s of stars) {
        const alpha = Math.max(
          0,
          Math.min(1, s.base + Math.sin(t * s.speed + s.phase) * 0.14),
        );
        // translucent glow halo (gradient sprite) — reads as luminous, not a disc
        const gsize = s.r * 9;
        ctx!.globalAlpha = alpha * 0.7;
        ctx!.drawImage(glow, s.x - gsize / 2, s.y - gsize / 2, gsize, gsize);
        // crisp core point
        ctx!.globalAlpha = alpha;
        ctx!.fillStyle = "#f4f6ff";
        ctx!.beginPath();
        ctx!.arc(s.x, s.y, s.r * 0.7, 0, Math.PI * 2);
        ctx!.fill();
      }
      ctx!.globalAlpha = 1;
      rafId = requestAnimationFrame(loop);
    }

    resize();
    window.addEventListener("resize", resize);
    rafId = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(rafId);
    };
  }, [canvasRef]);

  return <canvas ref={canvasRef} className="starfield-bg" aria-hidden="true" />;
}
