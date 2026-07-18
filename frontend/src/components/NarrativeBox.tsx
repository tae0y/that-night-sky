// frontend/src/components/NarrativeBox.tsx
import { t, type Lang } from "../i18n";

interface Props {
  text: string | null;
  limitReached: boolean;
  lang: Lang;
}

export function NarrativeBox({ text, limitReached, lang }: Props) {
  if (limitReached) {
    return <div className="narrative-box narrative-limit">{t("narrative_limit", lang)}</div>;
  }
  if (!text) return null;
  return (
    <div className="narrative-box">
      <p className="narrative-text">{text}</p>
    </div>
  );
}
