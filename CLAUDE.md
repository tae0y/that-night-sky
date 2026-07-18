# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A React + FastAPI web app that renders an interactive star chart for a given date and location. Enter a Korean address, and the app resolves coordinates via vworld API, computes celestial positions with skyfield, and generates a poetic narrative using the Claude API.

## Run

```shell
# FastAPI backend (serves /api/sky-data, /api/narrative, /healthz)
uv run uvicorn thatnightsky.api:app --port 8000

# React frontend (dev server)
cd frontend && npm run dev
```

## Deploy (Docker + Cloudflare Tunnel)

```shell
# Build and start (always pass --env-file; CLOUDFLARE_TUNNEL_TOKEN lives in .env at repo root,
# but compose files are under docker/ so Docker Compose won't auto-load it otherwise)
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

## Architecture

`src/thatnightsky/` contains the FastAPI backend (`api.py`); `frontend/` contains the React app.

Data flow: `QueryInput` → `compute.run()` → `SkyData` → `api.py` (serialized to JSON via `CamelModel`) → React `SkyChart` (canvas rendering)

**`models.py`** — Immutable dataclasses defining layer boundaries:
- `QueryInput`: Raw user input (address, time string)
- `ObserverContext`: Geocoding result (lat/lng, UTC datetime)
- `StarRecord`: Single star's coordinates + projection output
- `ConstellationLine`: Constellation line segment (HIP pair + IAU name)
- `ConstellationPosition`: Brightness-weighted mean az/alt for a single constellation (used for narrative)
- `SkyData`: Fully computed state passed to renderers

**`compute.py`** — External API calls and astronomy computation:
- Resolves Korean addresses to lat/lng via vworld API (ROAD → PARCEL fallback)
- Computes star positions using skyfield + stereographic projection
- Parses `resources/constellationship.fab` for constellation line segments
- Loads `de421.bsp` and `hip_main.dat` from `resources/` at module import time (non-trivial cost; incurred once per process start, not per request)
- `_ROOT` is resolved as `Path(__file__).parent.parent.parent` (i.e., repo root)
- Public functions: `run()` (top-level), `geocode_address()`, `compute_sky_data()`, `load_constellation_lines()` — all callable independently

**`narrative.py`** — Generates Korean poetic prose using Anthropic `claude-sonnet-4-6` (model name hardcoded)
- `theme` (user-supplied "이 날의 의미") is sanitized via `_sanitize_theme()` before inclusion in the prompt — returns `None` on empty or injection-suspicious input; wrapped in `<user_input>` XML tags in the user message
- `_IAU_TO_KO`: IAU abbreviation → Korean name mapping dict (e.g. `"Ori"` → `"오리온"`); up to 10 visible constellations passed to the prompt

The Streamlit app (`app.py`), the SVG/Plotly/Matplotlib renderers (`renderers/svg_2d.py`, `renderers/plotly_2d.py`, `renderers/static.py`), the legacy static PNG script (`starchart.py`), and the `i18n.py` translation helper have been removed — fully replaced by the FastAPI backend (`api.py`) and the React frontend (`frontend/`).

**`resources/`** — Binary data files (committed to repo):
- `de421.bsp`: NASA JPL ephemeris
- `hip_main.dat`: Hipparcos star catalogue
- `constellationship.fab`: Constellation line definitions (Stellarium format)

## Checks

Lint, format, and type checks without modifying files:
```shell
uv run ruff check src/
uv run ruff format --check src/
uv run pyright src/
uv run bandit -r src/ -c pyproject.toml
```

Pre-commit hooks run automatically on commit:
- `ruff` (lint + format, with auto-fix)
- `pyright` (type checking)
- `bandit` (security scan, configured via `pyproject.toml`)
- `pip-audit` (manual stage only, run with `--hook-stage manual`)

Run manually:
```shell
pre-commit run --all-files
pre-commit run pip-audit --hook-stage manual
```

## Tests

`tests/test_api.py` contains pytest tests covering `api.py`'s FastAPI endpoints (run with `uv run pytest tests/ -v`); it does not cover `compute.py`, `narrative.py`, or the frontend. The pre-commit hooks (ruff, pyright, bandit) remain the primary quality gate alongside this suite.

## Frontend State

The React frontend (`frontend/src/`) holds UI state in component `useState`. Form inputs (address, date/time, theme) reset to hardcoded `DEFAULT_VALUES` in `App.tsx` on reload — they are not persisted. Only the privacy-agreement flag persists across reloads, via `localStorage` (`PrivacyDialog.tsx`). The narrative call-count cap is tracked server-side via a session cookie set by `api.py`.

## Dependency Management

Use `uv`. Never edit `pyproject.toml` directly to add packages:
```shell
uv add <package>
```
