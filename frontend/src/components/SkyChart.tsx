// frontend/src/components/SkyChart.tsx
import { useEffect, type RefObject } from "react";
import type { SkyData } from "../types";

const BG = "#0d1b35";
const STAR_COLOR = "#f0e0b0";
const LINE_COLOR = "#c9a96e";
const HORIZON_COLOR = "#c9a96e";
const CENTRE_TOP_PX = 50;

function starRadius(magnitude: number): number {
  const r = (6 - magnitude) / 600;
  return Math.max(0.0018, Math.min(r, 0.018));
}

function starOpacity(magnitude: number): number {
  return Math.max(0.35, Math.min(1.0, (6 - magnitude) / 6));
}

interface Props {
  skyData: SkyData;
  canvasRef: RefObject<HTMLCanvasElement | null>;
  rotationDeg?: number;
}

export function SkyChart({ skyData, canvasRef, rotationDeg = 0 }: Props) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

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
      const R = Math.round(vh * 0.6);
      canvas!.width = Math.round(2 * R * dpr);
      canvas!.height = Math.round(R * dpr);
      canvas!.style.width = `${2 * R}px`;
      canvas!.style.height = `${R}px`;
      canvas!.style.position = "fixed";
      canvas!.style.left = `${Math.round((vw - 2 * R) / 2)}px`;
      canvas!.style.top = `${CENTRE_TOP_PX}px`;
      return R;
    }

    function draw(R: number) {
      const dpr = window.devicePixelRatio || 1;
      const S = R * dpr;

      context!.setTransform(1, 0, 0, 1, 0, 0);
      context!.fillStyle = BG;
      context!.fillRect(0, 0, canvas!.width, canvas!.height);

      // data -> pixel: px = S*(x+1), py = S*(1-y)
      context!.setTransform(S, 0, 0, -S, S, S);

      context!.save();
      context!.rotate((rotationDeg * Math.PI) / 180);

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

      context!.fillStyle = STAR_COLOR;
      for (const s of visible) {
        context!.globalAlpha = starOpacity(s.magnitude);
        context!.beginPath();
        context!.arc(s.x, s.y, starRadius(s.magnitude), 0, Math.PI * 2);
        context!.fill();
      }
      context!.restore();

      context!.globalAlpha = 0.85;
      context!.strokeStyle = HORIZON_COLOR;
      context!.lineWidth = 0.005;
      context!.beginPath();
      context!.arc(0, 0, 1, 0, Math.PI * 2);
      context!.stroke();
      context!.globalAlpha = 1;
    }

    const R = resize();
    draw(R);

    function onResize() {
      draw(resize());
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [skyData, rotationDeg, canvasRef]);

  return <canvas ref={canvasRef} />;
}
