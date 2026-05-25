"""POST /api/sky — geocode address and compute sky data."""

from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, HTTPException

from thatnightsky.api.schemas import (
    ConstellationLineSchema,
    ConstellationPositionSchema,
    ObserverContextSchema,
    SkyRequest,
    SkyResponse,
    StarRecordSchema,
)
from thatnightsky.compute import GeocodingError, run
from thatnightsky.models import QueryInput

router = APIRouter()

_WHEN_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


@router.post("/sky", response_model=SkyResponse)
def compute_sky(req: SkyRequest) -> SkyResponse:
    if not _WHEN_RE.match(req.when):
        raise HTTPException(
            status_code=422,
            detail={"error": "Invalid datetime format. Use YYYY-MM-DD HH:MM"},
        )

    try:
        datetime.strptime(req.when, "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": str(exc)}) from exc

    try:
        sky = run(
            QueryInput(address=req.address, when=req.when),
            req.limiting_magnitude,
            req.lang,
        )
    except GeocodingError as exc:
        raise HTTPException(status_code=422, detail={"error": str(exc)}) from exc

    hip_set = {s.hip for s in sky.stars}

    return SkyResponse(
        context=ObserverContextSchema(
            lat=sky.context.lat,
            lng=sky.context.lng,
            utc_dt=sky.context.utc_dt.isoformat(),
            address_display=sky.context.address_display,
        ),
        stars=[
            StarRecordSchema(
                hip=s.hip,
                magnitude=s.magnitude,
                x=s.x,
                y=s.y,
                az_deg=s.az_deg,
                alt_deg=s.alt_deg,
            )
            for s in sky.stars
        ],
        constellation_lines=[
            ConstellationLineSchema(
                hip_from=line.hip_from, hip_to=line.hip_to, name=line.name
            )
            for line in sky.constellation_lines
            if line.hip_from in hip_set and line.hip_to in hip_set
        ],
        constellation_positions=[
            ConstellationPositionSchema(name=p.name, az_deg=p.az_deg, alt_deg=p.alt_deg)
            for p in sky.constellation_positions
        ],
        limiting_magnitude=sky.limiting_magnitude,
    )
