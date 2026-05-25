"""Pydantic schemas for FastAPI request/response bodies."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class SkyRequest(BaseModel):
    address: str = Field(..., min_length=1, max_length=200)
    when: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
    lang: str = Field("en", pattern=r"^(ko|en)$")
    limiting_magnitude: float = Field(6.5, ge=1.0, le=8.0)


class NarrativeRequest(BaseModel):
    address: str
    when: str
    constellation_positions: list[ConstellationPositionSchema]
    theme: str = ""
    lang: str = Field("en", pattern=r"^(ko|en)$")


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------


class ObserverContextSchema(BaseModel):
    lat: float
    lng: float
    utc_dt: str
    address_display: str


class StarRecordSchema(BaseModel):
    hip: int
    magnitude: float
    x: float
    y: float
    az_deg: float
    alt_deg: float


class ConstellationLineSchema(BaseModel):
    hip_from: int
    hip_to: int
    name: str


class ConstellationPositionSchema(BaseModel):
    name: str
    az_deg: float
    alt_deg: float


class SkyResponse(BaseModel):
    context: ObserverContextSchema
    stars: list[StarRecordSchema]
    constellation_lines: list[ConstellationLineSchema]
    constellation_positions: list[ConstellationPositionSchema]
    limiting_magnitude: float


class NarrativeResponse(BaseModel):
    narrative: str


class HealthResponse(BaseModel):
    status: str
    ok: bool


class ErrorResponse(BaseModel):
    error: str
