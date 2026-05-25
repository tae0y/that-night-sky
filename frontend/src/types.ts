export interface ObserverContext {
  lat: number
  lng: number
  utc_dt: string
  address_display: string
}

export interface StarRecord {
  hip: number
  magnitude: number
  x: number
  y: number
  az_deg: number
  alt_deg: number
}

export interface ConstellationLine {
  hip_from: number
  hip_to: number
  name: string
}

export interface ConstellationPosition {
  name: string
  az_deg: number
  alt_deg: number
}

export interface SkyData {
  context: ObserverContext
  stars: StarRecord[]
  constellation_lines: ConstellationLine[]
  constellation_positions: ConstellationPosition[]
  limiting_magnitude: number
}

export interface NarrativeResponse {
  narrative: string
}

export type Lang = 'ko' | 'en'
