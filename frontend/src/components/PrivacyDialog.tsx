import type { Lang } from '../types'
import { t } from '../i18n'

interface Props {
  lang: Lang
  onConfirm: () => void
}

export function PrivacyDialog({ lang, onConfirm }: Props) {
  return (
    <div
      data-testid="privacy-dialog"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
    >
      <div className="bg-[var(--surface)] border border-[var(--gold-dim)] max-w-sm w-full mx-4 p-6 text-center">
        <h2 className="text-[var(--gold)] text-sm tracking-widest uppercase mb-4">
          {t('privacy_title', lang)}
        </h2>
        <p className="text-[var(--text-dim)] text-sm leading-relaxed mb-6">
          {t('privacy_body', lang)}
        </p>
        <button
          data-testid="privacy-confirm-btn"
          className="btn-gold"
          onClick={onConfirm}
        >
          {t('btn_confirm', lang)}
        </button>
      </div>
    </div>
  )
}
