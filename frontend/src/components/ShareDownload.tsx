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

const CARD_FONT_FAMILY = "NostalgicPoliceHumanRights";
const CARD_LETTER_SPACING_PX = 1; // unscaled; multiplied by dpr where applied

let cardFontLoadPromise: Promise<void> | null = null;

// document.fonts.check() returns true for a CSS-declared-but-not-yet-fetched
// font (the d9dc369 regression) — document.fonts.load() must be awaited before
// buildCompositeCanvas draws text, or it silently falls back to the default font.
export function ensureCardFontLoaded(): Promise<void> {
  if (!cardFontLoadPromise) {
    cardFontLoadPromise = document.fonts.load(`16px "${CARD_FONT_FAMILY}"`).then(() => undefined);
  }
  return cardFontLoadPromise;
}

export function buildCompositeCanvas(source: HTMLCanvasElement, narrative: string): HTMLCanvasElement {
  const dpr = window.devicePixelRatio || 1;
  const padY = Math.round(24 * dpr);
  const fontSize = Math.round(16 * dpr);
  const lineH = Math.round(fontSize * 1.75);
  const maxW = Math.min(Math.round(source.width * 0.85), Math.round(640 * dpr));
  const font = `${fontSize}px "${CARD_FONT_FAMILY}","Apple SD Gothic Neo","Malgun Gothic",sans-serif`;
  const letterSpacing = `${Math.round(CARD_LETTER_SPACING_PX * dpr)}px`;

  const measureCanvas = document.createElement("canvas");
  const measureCtx = measureCanvas.getContext("2d")!;
  measureCtx.font = font;
  // letterSpacing is broadly supported (Chrome/Edge/Firefox/Safari 17+); measurement
  // and drawing must both set it so wrapped line widths stay accurate.
  (measureCtx as CanvasRenderingContext2D & { letterSpacing: string }).letterSpacing = letterSpacing;

  const tokens = narrative.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let cur = "";
  for (const tok of tokens) {
    const test = cur ? `${cur} ${tok}` : tok;
    if (measureCtx.measureText(test).width > maxW && cur) {
      lines.push(cur);
      cur = tok;
    } else {
      cur = test;
    }
  }
  if (cur) lines.push(cur);

  const boxH = lines.length * lineH + padY * 2;
  const out = document.createElement("canvas");
  out.width = source.width;
  out.height = source.height + boxH;
  const ctx = out.getContext("2d")!;

  ctx.fillStyle = "#0d1b35";
  ctx.fillRect(0, 0, out.width, out.height);
  ctx.drawImage(source, 0, 0);

  ctx.fillStyle = "rgba(10,20,42,0.92)";
  ctx.fillRect(0, source.height, out.width, boxH);
  ctx.fillStyle = "rgba(201,169,110,0.4)";
  ctx.fillRect(0, source.height, out.width, Math.round(dpr));

  ctx.font = font;
  (ctx as CanvasRenderingContext2D & { letterSpacing: string }).letterSpacing = letterSpacing;
  ctx.fillStyle = "#e8d5a3";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  let ty = source.height + padY;
  for (const line of lines) {
    ctx.fillText(line, out.width / 2, ty);
    ty += lineH;
  }
  return out;
}

// Caller must `await ensureCardFontLoaded()` before calling this — buildCompositeCanvas
// itself stays synchronous so it can be reused as-is by both this function and tryShare (Task 14).
export function downloadCompositeCard(canvas: HTMLCanvasElement, narrative: string, filename: string) {
  const composite = buildCompositeCanvas(canvas, narrative);
  composite.toBlob((blob) => {
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

async function tryShare(
  canvas: HTMLCanvasElement,
  narrative: string,
): Promise<"shared" | "cancelled" | "unsupported"> {
  if (typeof navigator.share !== "function") return "unsupported";

  await ensureCardFontLoaded();
  const composite = buildCompositeCanvas(canvas, narrative);
  const blob: Blob | null = await new Promise((resolve) =>
    composite.toBlob(resolve, "image/png"),
  );
  if (!blob) return "unsupported";

  const file = new File([blob], "that-night-sky.png", { type: "image/png" });
  const shareData: ShareData = { title: "ThatNightSky", text: narrative };
  if (typeof navigator.canShare === "function" && navigator.canShare({ files: [file] })) {
    shareData.files = [file];
  } else {
    shareData.url = window.location.href;
  }

  try {
    await navigator.share(shareData);
    return "shared";
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") return "cancelled";
    return "unsupported";
  }
}

interface Props {
  canvasRef: RefObject<HTMLCanvasElement | null>;
  narrative: string | null;
  lang: Lang;
  whenStr: string;
  theme: string;
}

export function ShareDownload({ canvasRef, narrative, whenStr, theme, lang }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [shareUnsupported, setShareUnsupported] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  function handleDownloadChart() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    downloadChartOnly(canvas, buildFilename(whenStr, theme));
    setMenuOpen(false);
  }

  async function handleDownloadCard() {
    const canvas = canvasRef.current;
    if (!canvas || !narrative) return;
    await ensureCardFontLoaded();
    downloadCompositeCard(canvas, narrative, `card_${buildFilename(whenStr, theme)}`);
    setMenuOpen(false);
  }

  async function handleShare() {
    const canvas = canvasRef.current;
    if (!canvas || !narrative) return;
    const result = await tryShare(canvas, narrative);
    if (result === "unsupported") setShareUnsupported(true);
  }

  async function handleCopyLink() {
    await navigator.clipboard.writeText(window.location.href);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  }

  return (
    <div className="share-download">
      <button onClick={() => setMenuOpen((v) => !v)}>{t("btn_save_menu", lang)} ▾</button>
      {menuOpen && (
        <div className="save-menu">
          <button onClick={handleDownloadChart}>{t("btn_download_chart", lang)}</button>
          {narrative && (
            <button onClick={handleDownloadCard}>{t("btn_download_card", lang)}</button>
          )}
        </div>
      )}
      {narrative && (
        <>
          <button onClick={handleShare}>{t("btn_share", lang)}</button>
          {shareUnsupported && (
            <>
              <button onClick={handleCopyLink}>
                {linkCopied ? t("share_copied", lang) : t("btn_copy_link", lang)}
              </button>
              <button onClick={handleDownloadCard}>{t("btn_download_card", lang)}</button>
            </>
          )}
        </>
      )}
    </div>
  );
}
