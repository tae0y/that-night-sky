"""FastAPI application — JSON API over compute.py/narrative.py, plus static frontend serving."""

from __future__ import annotations

from dataclasses import asdict

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel, ConfigDict  # noqa: E402
from pydantic.alias_generators import to_camel  # noqa: E402

from thatnightsky.compute import GeocodingError, run  # noqa: E402
from thatnightsky.models import QueryInput  # noqa: E402

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
        sky_data = run(
            QueryInput(address=body.address, when=body.when), lang=body.lang
        )
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
