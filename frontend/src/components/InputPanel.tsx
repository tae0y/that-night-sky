// frontend/src/components/InputPanel.tsx
import { useState } from "react";
import { t, type Lang } from "../i18n";

export interface DefaultValues {
  address: string;
  date: string; // "YYYY-MM-DD"
  time: string; // "HH:MM"
  theme: string;
}

interface Props {
  lang: Lang;
  defaultValues: DefaultValues;
  onSubmit: (address: string, when: string, theme: string) => void;
  disabled: boolean;
}

export function InputPanel({ lang, defaultValues, onSubmit, disabled }: Props) {
  const [address, setAddress] = useState(defaultValues.address);
  const [date, setDate] = useState(defaultValues.date);
  const [time, setTime] = useState(defaultValues.time);
  const [theme, setTheme] = useState(defaultValues.theme);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!address) return;
    onSubmit(address, `${date} ${time}`, theme);
  }

  return (
    <form className="input-panel" onSubmit={handleSubmit}>
      <label>
        {t("label_place", lang)}
        <input
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          disabled={disabled}
        />
      </label>
      <label>
        {t("label_date", lang)}
        <input
          type="date"
          value={date}
          min="1900-01-01"
          max={new Date().toISOString().slice(0, 10)}
          onChange={(e) => setDate(e.target.value)}
          disabled={disabled}
        />
      </label>
      <label>
        {t("label_time", lang)}
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          disabled={disabled}
        />
      </label>
      <label>
        {t("label_theme", lang)}
        <input
          value={theme}
          maxLength={20}
          onChange={(e) => setTheme(e.target.value)}
          disabled={disabled}
        />
      </label>
      <button type="submit" disabled={disabled || !address}>
        {t("btn_view_sky", lang)}
      </button>
    </form>
  );
}
