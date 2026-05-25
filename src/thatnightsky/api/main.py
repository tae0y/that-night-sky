"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from thatnightsky.api.routes import narrative, sky
from thatnightsky.api.schemas import HealthResponse

app = FastAPI(title="ThatNightSky API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(sky.router, prefix="/api")
app.include_router(narrative.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", ok=True)
