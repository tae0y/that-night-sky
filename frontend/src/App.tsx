// frontend/src/App.tsx
import { useEffect, useRef, useState } from "react";
import { SkyChart } from "./components/SkyChart";
import { Starfield } from "./components/Starfield";
import { InputPanel, type DefaultValues } from "./components/InputPanel";
import { NarrativeBox } from "./components/NarrativeBox";
import { ShareDownload } from "./components/ShareDownload";
import { PrivacyDialog, hasAgreedToPrivacy } from "./components/PrivacyDialog";
import { fetchSkyData, fetchNarrative, ApiError } from "./api/client";
import { t, detectLang } from "./i18n";
import type { SkyData } from "./types";

const DEFAULT_VALUES: DefaultValues = {
  address: "Gahoedong, Jongno-gu, Seoul, South Korea",
  date: "1900-01-01",
  time: "01:00",
  theme: "Birthday",
};

export default function App() {
  const lang = detectLang();

  useEffect(() => {
    document.title = t("page_title", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const starfieldRef = useRef<HTMLCanvasElement>(null);
  const [privacyAgreed, setPrivacyAgreed] = useState(hasAgreedToPrivacy());
  const [skyData, setSkyData] = useState<SkyData | null>(null);
  const [narrative, setNarrative] = useState<string | null>(null);
  const [narrativeLimitReached, setNarrativeLimitReached] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [theme, setThemeUsed] = useState("");
  const [whenStr, setWhenStr] = useState("");
  const [inputOpen, setInputOpen] = useState(true);

  async function handleSubmit(address: string, when: string, submittedTheme: string) {
    setErrorMsg(null);
    setNarrative(null);
    setNarrativeLimitReached(false);
    setThemeUsed(submittedTheme);
    setWhenStr(when);
    setLoadingMessage(t("loading_compute", lang));

    let data: SkyData;
    try {
      data = await fetchSkyData(address, when, lang);
    } catch (err) {
      setLoadingMessage(null);
      setErrorMsg(
        t("error_address", lang).replace(
          "{error}",
          err instanceof Error ? err.message : "unknown",
        ),
      );
      return;
    }
    setSkyData(data);

    setLoadingMessage(t("loading_narrative", lang));
    try {
      const text = await fetchNarrative(
        data.addressDisplay,
        when,
        data.constellationPositions,
        submittedTheme,
        lang,
      );
      setNarrative(text);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setNarrativeLimitReached(true);
      } else {
        // Non-429 failures (network down, 500, etc.) never reach the server-side
        // fallback in Task 2 — that fallback only covers Claude API errors inside
        // a *successful* HTTP response. Show a fixed client-side fallback message
        // instead of leaving the narrative area silently empty.
        setErrorMsg(t("narrative_error", lang));
      }
    }
    setLoadingMessage(null);
    setInputOpen(false);
  }

  if (!privacyAgreed) {
    return <PrivacyDialog lang={lang} onConfirm={() => setPrivacyAgreed(true)} />;
  }

  return (
    <div className="app">
      <Starfield canvasRef={starfieldRef} />

      {skyData ? (
        <SkyChart skyData={skyData} canvasRef={canvasRef} />
      ) : (
        <div className="placeholder">
          <div className="wordmark">✦ {t("page_title", lang)}</div>
          <p className="placeholder-hint">{t("placeholder", lang)}</p>
        </div>
      )}

      {loadingMessage && <div className="loading-overlay">{loadingMessage}</div>}
      {errorMsg && <div className="error-box">{errorMsg}</div>}

      {!inputOpen && (
        <NarrativeBox text={narrative} limitReached={narrativeLimitReached} lang={lang} />
      )}

      {skyData && !inputOpen && (
        <ShareDownload
          canvasRef={canvasRef}
          starfieldRef={starfieldRef}
          narrative={narrative}
          lang={lang}
          whenStr={whenStr}
          theme={theme}
        />
      )}

      {inputOpen ? (
        <InputPanel
          lang={lang}
          defaultValues={DEFAULT_VALUES}
          onSubmit={handleSubmit}
          disabled={loadingMessage !== null}
        />
      ) : (
        <button className="edit-btn" onClick={() => setInputOpen(true)}>
          {t("btn_edit", lang)}
        </button>
      )}
    </div>
  );
}
