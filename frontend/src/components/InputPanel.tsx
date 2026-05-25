import { useState } from 'react'
import type { Lang } from '../types'
import { t } from '../i18n'

interface Props {
  lang: Lang
  initialAddress: string
  initialWhen: string
  initialTheme: string
  loading: boolean
  disabled: boolean
  onSubmit: (address: string, when: string, theme: string) => void
}

export function InputPanel({
  lang,
  initialAddress,
  initialWhen,
  initialTheme,
  loading,
  disabled,
  onSubmit,
}: Props) {
  const [address, setAddress] = useState(initialAddress)
  const [when, setWhen] = useState(initialWhen)
  const [theme, setTheme] = useState(initialTheme)
  const [open, setOpen] = useState(true)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit(address.trim(), when.trim(), theme.trim())
  }

  return (
    <div className="input-panel">
      {/* mobile toggle */}
      <button
        className="md:hidden text-[var(--gold-dim)] text-xs tracking-widest mb-2"
        onClick={() => setOpen(o => !o)}
      >
        {open ? '▾ 입력 닫기' : '▸ 입력 열기'}
      </button>

      {open && (
        <form
          onSubmit={handleSubmit}
          className="flex flex-col md:flex-row gap-3 md:items-end"
        >
          <div className="flex-1">
            <label className="field-label">{t('label_place', lang)}</label>
            <input
              data-testid="address-input"
              className="field-input"
              type="text"
              value={address}
              onChange={e => setAddress(e.target.value)}
              placeholder={t('placeholder_place', lang)}
              required
            />
          </div>

          <div className="flex-1">
            <label className="field-label">{t('label_date', lang)}</label>
            <input
              data-testid="when-input"
              className="field-input"
              type="text"
              value={when}
              onChange={e => setWhen(e.target.value)}
              placeholder={t('placeholder_date', lang)}
              pattern="\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
              required
            />
          </div>

          <div className="flex-1">
            <label className="field-label">{t('label_theme', lang)}</label>
            <input
              data-testid="theme-input"
              className="field-input"
              type="text"
              value={theme}
              onChange={e => setTheme(e.target.value)}
              placeholder={t('placeholder_theme', lang)}
              maxLength={20}
            />
          </div>

          <button
            data-testid="submit-btn"
            type="submit"
            className="btn-gold whitespace-nowrap"
            disabled={disabled || loading}
          >
            {loading ? '…' : t('btn_view_sky', lang)}
          </button>
        </form>
      )}
    </div>
  )
}
