import type { SkyData, NarrativeResponse, ConstellationPosition, Lang } from './types'

const BASE = '/api'

export async function fetchSky(
  address: string,
  when: string,
  lang: Lang,
): Promise<SkyData> {
  const res = await fetch(`${BASE}/sky`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address, when, lang }),
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.detail?.error ?? json.detail ?? 'Failed to compute sky')
  return json as SkyData
}

export async function fetchNarrative(
  address: string,
  when: string,
  constellationPositions: ConstellationPosition[],
  theme: string,
  lang: Lang,
): Promise<string> {
  const res = await fetch(`${BASE}/narrative`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      address,
      when,
      constellation_positions: constellationPositions,
      theme,
      lang,
    }),
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.detail?.error ?? json.detail ?? 'Failed to generate narrative')
  return (json as NarrativeResponse).narrative
}
