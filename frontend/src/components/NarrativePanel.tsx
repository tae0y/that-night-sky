import type { Lang, SkyData } from '../types'
import { t } from '../i18n'

const MAX_NARRATIVES = 3

interface Props {
  lang: Lang
  skyData: SkyData
  narrative: string | null
  narrativeCount: number
  loading: boolean
  onGenerate: () => void
}

export function NarrativePanel({ lang, narrative, narrativeCount, loading, onGenerate }: Props) {
  const exhausted = narrativeCount >= MAX_NARRATIVES

  return (
    <div className="px-4 py-3 border-t border-[var(--gold-dim)] bg-[var(--surface)]">
      {narrative ? (
        <p className="text-[var(--text)] text-sm leading-relaxed">{narrative}</p>
      ) : (
        <div className="flex items-center gap-3">
          <button
            data-testid="narrative-btn"
            className="btn-gold text-xs"
            disabled={exhausted || loading}
            onClick={onGenerate}
          >
            {loading ? '…' : t('btn_narrative', lang)}
          </button>
          {exhausted && (
            <span className="text-[var(--text-dim)] text-xs">{t('narrative_limit', lang)}</span>
          )}
        </div>
      )}
    </div>
  )
}
