import type { SkyData, ConstellationPosition } from "../types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function readErrorDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string };
    return body.detail ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function fetchSkyData(
  address: string,
  when: string,
  lang: string,
): Promise<SkyData> {
  const res = await fetch("/api/sky-data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ address, when, lang }),
  });
  if (!res.ok) throw new ApiError(res.status, await readErrorDetail(res));
  return (await res.json()) as SkyData;
}

export async function fetchNarrative(
  address: string,
  when: string,
  constellationPositions: ConstellationPosition[],
  theme: string,
  lang: string,
): Promise<string> {
  const res = await fetch("/api/narrative", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      address,
      when,
      constellationPositions,
      theme,
      lang,
    }),
  });
  if (!res.ok) throw new ApiError(res.status, await readErrorDetail(res));
  const data = (await res.json()) as { text: string };
  return data.text;
}
