export interface StarRecord {
  hip: number;
  raDeg: number;
  decDeg: number;
  magnitude: number;
  x: number;
  y: number;
  azDeg: number;
  altDeg: number;
}

export interface ConstellationLine {
  hipFrom: number;
  hipTo: number;
  name: string;
}

export interface ConstellationPosition {
  name: string;
  azDeg: number;
  altDeg: number;
}

export interface SkyData {
  lat: number;
  lng: number;
  addressDisplay: string;
  utcDt: string;
  stars: StarRecord[];
  constellationLines: ConstellationLine[];
  limitingMagnitude: number;
  constellationPositions: ConstellationPosition[];
}
