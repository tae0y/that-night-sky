"""POST /api/narrative — generate Claude poetic narrative."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from thatnightsky.api.schemas import NarrativeRequest, NarrativeResponse
from thatnightsky.models import ConstellationPosition
from thatnightsky.narrative import generate_night_description

router = APIRouter()


@router.post("/narrative", response_model=NarrativeResponse)
def create_narrative(req: NarrativeRequest) -> NarrativeResponse:
    positions = tuple(
        ConstellationPosition(name=p.name, az_deg=p.az_deg, alt_deg=p.alt_deg)
        for p in req.constellation_positions
    )

    try:
        text = generate_night_description(
            address=req.address,
            when=req.when,
            constellation_positions=positions,
            theme=req.theme,
            lang=req.lang,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": str(exc)}) from exc

    return NarrativeResponse(narrative=text)
