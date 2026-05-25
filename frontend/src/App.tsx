import { useEffect, useState } from 'react'
import type { Lang, SkyData } from './types'
import { fetchSky, fetchNarrative } from './api'
import { randomSample, t } from './i18n'
import { PrivacyDialog } from './components/PrivacyDialog'
import { StarChart } from './components/StarChart'
import { InputPanel } from './components/InputPanel'
import { NarrativePanel } from './components/NarrativePanel'
import './index.css'

const MAX_NARRATIVES = 3
const PRIVACY_KEY = 'tns_privacy_agreed'

function detectLang(): Lang {
  const nav = navigator.language ?? 'en'
  return nav.startsWith('ko') ? 'ko' : 'en'
}

export default function App() {
  const [lang] = useState<Lang>(detectLang)
  const [privacyAgreed, setPrivacyAgreed] = useState(
    () => sessionStorage.getItem(PRIVACY_KEY) === '1',
  )

  const sample = randomSample(lang)
  const [address, setAddress] = useState(sample.address)
  const [when, setWhen] = useState(sample.when)
  const [theme, setTheme] = useState(sample.theme)

  const [skyData, setSkyData] = useState<SkyData | null>(null)
  const [narrative, setNarrative] = useState<string | null>(null)
  const [narrativeCount, setNarrativeCount] = useState(0)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [loadingSky, setLoadingSky] = useState(false)
  const [loadingNarrative, setLoadingNarrative] = useState(false)

  useEffect(() => {
    document.title = t('page_title', lang)
  }, [lang])

  function confirmPrivacy() {
    sessionStorage.setItem(PRIVACY_KEY, '1')
    setPrivacyAgreed(true)
  }

  async function handleSubmit(addr: string, whn: string, thm: string) {
    setAddress(addr)
    setWhen(whn)
    setTheme(thm)
    setSkyData(null)
    setNarrative(null)
    setErrorMsg(null)
    setLoadingSky(true)

    try {
      const data = await fetchSky(addr, whn, lang)
      setSkyData(data)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : t('error_address', lang))
    } finally {
      setLoadingSky(false)
    }
  }

  async function handleGenerateNarrative() {
    if (!skyData || narrativeCount >= MAX_NARRATIVES) return
    setLoadingNarrative(true)
    try {
      const text = await fetchNarrative(
        skyData.context.address_display,
        skyData.context.utc_dt,
        skyData.constellation_positions,
        theme,
        lang,
      )
      setNarrative(text)
      setNarrativeCount(c => c + 1)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to generate narrative')
    } finally {
      setLoadingNarrative(false)
    }
  }

  return (
    <>
      {!privacyAgreed && (
        <PrivacyDialog lang={lang} onConfirm={confirmPrivacy} />
      )}

      {/* star chart area */}
      <div className="star-chart-wrap">
        {loadingSky && (
          <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg)]/80 z-10">
            <p className="text-[var(--gold)] tracking-widest text-sm animate-pulse">
              {t('loading_compute', lang)}
            </p>
          </div>
        )}

        {errorMsg && (
          <div
            data-testid="error-message"
            className="absolute inset-0 flex items-center justify-center bg-[var(--bg)]/90 z-10"
          >
            <div className="text-center px-6">
              <p className="text-red-400 text-sm">{errorMsg}</p>
              <button
                className="btn-gold mt-4 text-xs"
                onClick={() => setErrorMsg(null)}
              >
                {t('btn_edit', lang)}
              </button>
            </div>
          </div>
        )}

        {skyData ? (
          <StarChart skyData={skyData} />
        ) : (
          !loadingSky && !errorMsg && (
            <div className="w-full h-full flex items-center justify-center">
              <p className="text-[var(--text-dim)] text-xs tracking-widest">
                {t('page_title', lang)}
              </p>
            </div>
          )
        )}
      </div>

      {/* narrative strip */}
      {skyData && (
        <NarrativePanel
          lang={lang}
          skyData={skyData}
          narrative={narrative}
          narrativeCount={narrativeCount}
          loading={loadingNarrative}
          onGenerate={handleGenerateNarrative}
        />
      )}

      {/* input form at bottom */}
      <InputPanel
        lang={lang}
        initialAddress={address}
        initialWhen={when}
        initialTheme={theme}
        loading={loadingSky}
        disabled={!privacyAgreed}
        onSubmit={handleSubmit}
      />
    </>
  )
}
