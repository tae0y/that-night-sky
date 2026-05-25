# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

An interactive star chart app for a given date and location.  
Enter a Korean (or international) address and a datetime; the app resolves coordinates, computes celestial positions with skyfield, and generates a poetic narrative using the Claude API.

**Stack:** FastAPI (Python) backend + React/Vite (TypeScript) frontend.

---

## Run

```shell
# FastAPI backend (port 8000)
uv run uvicorn thatnightsky.api.main:app --reload --port 8000

# React frontend (port 5173, proxies /api → 8000)
cd frontend && npm run dev
```

## Deploy (Docker + Cloudflare Tunnel)

```shell
# Build and start (always pass --env-file)
docker compose -f docker/docker-compose.yml --env-file .env up -d --build

# Restart without rebuild
docker compose -f docker/docker-compose.yml --env-file .env up -d

# Stop
docker compose -f docker/docker-compose.yml --env-file .env down
```

## Environment Variables

Requires a `.env` file:
```
VWORLD_API_KEY=...       # Korean Spatial Information Open Platform (https://www.vworld.kr)
ANTHROPIC_API_KEY=...    # Claude API (used for narrative text generation)
```

---

## Architecture

```
src/thatnightsky/
├── api/
│   ├── main.py          # FastAPI app with CORS, mounts routes
│   ├── schemas.py       # Pydantic request/response models
│   └── routes/
│       ├── sky.py       # POST /api/sky — geocode + compute
│       └── narrative.py # POST /api/narrative — Claude prose
├── models.py            # Frozen dataclasses (QueryInput, SkyData, …)
├── compute.py           # Geocoding + skyfield astronomy
├── narrative.py         # Claude API narrative generation
├── i18n.py              # ko/en translation helper (backend only)
└── renderers/
    ├── svg_2d.py        # SVG renderer (used for PNG export endpoint, future)
    ├── plotly_2d.py     # Unused — kept for reference
    └── static.py        # Matplotlib PNG renderer

frontend/src/
├── App.tsx              # Root component — state management
├── api.ts               # Typed fetch wrappers (fetchSky, fetchNarrative)
├── i18n.ts              # ko/en strings + sample inputs
├── types.ts             # TypeScript interfaces matching API schemas
└── components/
    ├── StarChart.tsx    # SVG star chart with pan/zoom/auto-rotate
    ├── InputPanel.tsx   # Address / datetime / theme form
    ├── NarrativePanel.tsx  # Story display + generate button
    └── PrivacyDialog.tsx   # First-visit consent modal
```

**API surface:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/sky` | Geocode + compute SkyData |
| POST | `/api/narrative` | Generate Claude prose |

**Data flow:**  
`InputPanel` → `POST /api/sky` → `SkyData` JSON → `StarChart` (SVG)  
`NarrativePanel` → `POST /api/narrative` → prose string

---

## Backend Details

**`models.py`** — Immutable dataclasses:
- `QueryInput(address, when)` — raw user input
- `ObserverContext(lat, lng, utc_dt, address_display)` — geocoding result
- `StarRecord` — single star (HIP, mag, x/y projection, az/alt)
- `ConstellationLine(hip_from, hip_to, name)` — line segment
- `ConstellationPosition(name, az_deg, alt_deg)` — brightness-weighted mean position
- `SkyData` — fully computed state

**`compute.py`** — Astronomy + geocoding:
- VWorld API (Korean) → Nominatim fallback for geocoding
- Skyfield + de421.bsp + hip_main.dat for celestial positions
- Stereographic projection: `viewBox="-1 0 2 1"` (x ∈ [-1,1], y ∈ [0,1])
- `_ROOT = Path(__file__).parent.parent.parent` (repo root)
- Module-level globals: `_eph`, `_stars_df`, `_tf` (loaded once at import)
- `GeocodingError` raised on lookup failure

**`narrative.py`** — Claude API:
- Model: `claude-sonnet-4-6`, max_tokens: 900
- `_sanitize_theme()`: truncates to 20 chars, strips control chars, rejects injection patterns
- `<user_input>` XML tags isolate user theme in the prompt

**`api/schemas.py`** — Pydantic v2:
- `SkyRequest`: validates `when` pattern `\d{4}-\d{2}-\d{2} \d{2}:\d{2}`
- `NarrativeRequest/Response`, `SkyResponse`, `HealthResponse`

**`api/routes/sky.py`** — Filters constellation lines to only visible stars before returning.

---

## Frontend Details

**`StarChart.tsx`** — Pure SVG:
- `viewBox="-1 0 2 1"`, stars plotted at stereographic (x, y)
- Auto-rotation: 0.6°/s (full revolution every 10 min) via `requestAnimationFrame`
- Pan (mouse drag / single-touch), zoom (wheel / pinch), reset button
- `data-testid="star-chart"` for E2E tests

**`InputPanel.tsx`** — Disabled while `privacyAgreed=false`; collapsible on mobile.

**`NarrativePanel.tsx`** — Rate-limited: max 3 generates per session (client-side).

**`PrivacyDialog.tsx`** — Blocks submit until confirmed; agreement stored in `sessionStorage`.

---

## Checks

```shell
uv run ruff check src/
uv run ruff format --check src/
uv run pyright src/
uv run bandit -r src/ -c pyproject.toml
```

Pre-commit hooks: ruff (lint + format), pyright, bandit, pip-audit (manual).

---

## Tests

```shell
# BDD backend tests (requires API running on :8000)
API_BASE_URL=http://localhost:8000 uv run pytest tests/steps/ -v

# E2E tests (requires frontend on :5173 + backend on :8000)
FRONTEND_URL=http://localhost:5173 uv run pytest tests/e2e/ -v
```

Feature files: `tests/features/*.feature`  
Step definitions: `tests/steps/test_*.py`  
E2E: `tests/e2e/test_app_flow.py` (Playwright)  
Requirements: `docs/epics-and-stories.md`

---

## Dependency Management

Use `uv`. Never edit `pyproject.toml` directly to add packages:
```shell
uv add <package>
cd frontend && npm install <package>
```
