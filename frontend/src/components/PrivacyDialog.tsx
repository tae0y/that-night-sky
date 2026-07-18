// frontend/src/components/PrivacyDialog.tsx
import { t, type Lang } from "../i18n";

const STORAGE_KEY = "tns_privacy_agreed";

export function hasAgreedToPrivacy(): boolean {
  return localStorage.getItem(STORAGE_KEY) === "true";
}

interface Props {
  lang: Lang;
  onConfirm: () => void;
}

export function PrivacyDialog({ lang, onConfirm }: Props) {
  function confirm() {
    localStorage.setItem(STORAGE_KEY, "true");
    onConfirm();
  }

  return (
    <div className="privacy-backdrop">
      <div className="privacy-dialog">
        <div className="wordmark">✦ {t("page_title", lang)}</div>
        <h3>{t("privacy_title", lang)}</h3>
        <p dangerouslySetInnerHTML={{ __html: t("privacy_body", lang) }} />
        <a
          href="https://www.anthropic.com/legal/privacy"
          target="_blank"
          rel="noreferrer"
        >
          {t("privacy_link", lang)}
        </a>
        <button onClick={confirm}>{t("btn_confirm", lang)}</button>
      </div>
    </div>
  );
}
