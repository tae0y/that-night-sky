"""FastAPI application — JSON API over compute.py/narrative.py, plus static frontend serving."""

from __future__ import annotations

import secrets
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, ConfigDict  # noqa: E402
from pydantic.alias_generators import to_camel  # noqa: E402

from thatnightsky.compute import GeocodingError, run  # noqa: E402
from thatnightsky.models import ConstellationPosition, QueryInput  # noqa: E402
from thatnightsky.narrative import generate_night_description  # noqa: E402

app = FastAPI(title="ThatNightSky API")


class CamelModel(BaseModel):
    """Base model that serializes/accepts camelCase on the wire, snake_case in Python."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SkyDataRequest(CamelModel):
    address: str
    when: str
    lang: str = "en"


class StarOut(CamelModel):
    hip: int
    ra_deg: float
    dec_deg: float
    magnitude: float
    x: float
    y: float
    az_deg: float
    alt_deg: float


class ConstellationLineOut(CamelModel):
    hip_from: int
    hip_to: int
    name: str


class ConstellationPositionOut(CamelModel):
    name: str
    az_deg: float
    alt_deg: float


class SkyDataResponse(CamelModel):
    lat: float
    lng: float
    address_display: str
    utc_dt: str
    stars: list[StarOut]
    constellation_lines: list[ConstellationLineOut]
    limiting_magnitude: float
    constellation_positions: list[ConstellationPositionOut]


@app.post("/api/sky-data", response_model=SkyDataResponse)
def post_sky_data(body: SkyDataRequest) -> SkyDataResponse:
    try:
        sky_data = run(QueryInput(address=body.address, when=body.when), lang=body.lang)
    except GeocodingError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return SkyDataResponse(
        lat=sky_data.context.lat,
        lng=sky_data.context.lng,
        address_display=sky_data.context.address_display,
        utc_dt=sky_data.context.utc_dt.isoformat(),
        stars=[StarOut(**asdict(s)) for s in sky_data.stars],
        constellation_lines=[
            ConstellationLineOut(**asdict(c)) for c in sky_data.constellation_lines
        ],
        limiting_magnitude=sky_data.limiting_magnitude,
        constellation_positions=[
            ConstellationPositionOut(**asdict(p))
            for p in sky_data.constellation_positions
        ],
    )


_SESSION_COOKIE = "tns_session"
_MAX_NARRATIVES_PER_SESSION = 3
_narrative_counts: dict[str, int] = {}
_NARRATIVE_FALLBACK = {
    "ko": "그날, 밤, 하늘입니다.",
    "en": "That night. The sky.",
}


class NarrativeRequest(CamelModel):
    address: str
    when: str
    constellation_positions: list[ConstellationPositionOut]
    theme: str = ""
    lang: str = "en"


class NarrativeResponse(CamelModel):
    text: str


def _get_session_id(request: Request, response: Response) -> str:
    session_id = request.cookies.get(_SESSION_COOKIE)
    if session_id is None:
        session_id = secrets.token_urlsafe(24)
        response.set_cookie(
            _SESSION_COOKIE,
            session_id,
            httponly=True,
            samesite="lax",
            max_age=86400,
        )
    return session_id


@app.post("/api/narrative", response_model=NarrativeResponse)
def post_narrative(
    body: NarrativeRequest, request: Request, response: Response
) -> NarrativeResponse:
    session_id = _get_session_id(request, response)
    count = _narrative_counts.get(session_id, 0)
    if count >= _MAX_NARRATIVES_PER_SESSION:
        raise HTTPException(status_code=429, detail="narrative limit reached")

    positions = tuple(
        ConstellationPosition(name=p.name, az_deg=p.az_deg, alt_deg=p.alt_deg)
        for p in body.constellation_positions
    )
    try:
        text = generate_night_description(
            address=body.address,
            when=body.when,
            constellation_positions=positions,
            theme=body.theme,
            lang=body.lang,
        )
    except Exception:
        text = _NARRATIVE_FALLBACK.get(body.lang, _NARRATIVE_FALLBACK["en"])
    else:
        _narrative_counts[session_id] = count + 1

    return NarrativeResponse(text=text)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


_FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
