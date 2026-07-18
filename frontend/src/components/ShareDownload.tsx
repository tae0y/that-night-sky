// frontend/src/components/ShareDownload.tsx
import { useState, type RefObject } from "react";
import { t, type Lang } from "../i18n";

export function buildFilename(whenStr: string, theme: string): string {
  const datePart = whenStr.slice(0, 10).replace(/-/g, "");
  const hhPart = whenStr.slice(11, 13);
  const themePart = theme.trim() ? `_${theme.trim().replace(/\s+/g, "_")}` : "";
  return `${datePart}_${hhPart}00${themePart}.png`;
}

export function downloadChartOnly(canvas: HTMLCanvasElement, filename: string) {
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, "image/png");
}

interface Props {
  canvasRef: RefObject<HTMLCanvasElement | null>;
  narrative: string | null;
  lang: Lang;
  whenStr: string;
  theme: string;
}

export function ShareDownload({ canvasRef, whenStr, theme, lang }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);

  function handleDownloadChart() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    downloadChartOnly(canvas, buildFilename(whenStr, theme));
    setMenuOpen(false);
  }

  return (
    <div className="share-download">
      <button onClick={() => setMenuOpen((v) => !v)}>{t("btn_save_menu", lang)} ▾</button>
      {menuOpen && (
        <div className="save-menu">
          <button onClick={handleDownloadChart}>{t("btn_download_chart", lang)}</button>
        </div>
      )}
    </div>
  );
}
