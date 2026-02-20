# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Streamlit web app that renders an interactive star chart for a given date and location. Enter a Korean address, and the app resolves coordinates via vworld API, computes celestial positions with skyfield, and generates a poetic narrative using the Claude API.

## Run

```shell
# Streamlit app (main entry point)
uv run streamlit run src/thatnightsky/app.py

# Legacy static PNG script
uv run python src/thatnightsky/starchart.py
```

## Environment Variables

Requires a `.env` file:
```
VWORLD_API_KEY=...       # Korean Spatial Information Open Platform (https://www.vworld.kr)
ANTHROPIC_API_KEY=...    # Claude API (used for narrative text generation)
```

## Architecture

`src/thatnightsky/` contains all code including the Streamlit entry point (`app.py`).

Data flow: `QueryInput` → `compute.run()` → `SkyData` → `renderers/*.render_*()` → Plotly Figure

**`models.py`** — Immutable dataclasses defining layer boundaries:
- `QueryInput`: Raw user input (address, time string)
- `ObserverContext`: Geocoding result (lat/lng, UTC datetime)
- `StarRecord`: Single star's coordinates + projection output
- `ConstellationLine`: Constellation line segment (HIP pair)
- `SkyData`: Fully computed state passed to renderers

**`compute.py`** — External API calls and astronomy computation:
- Resolves Korean addresses to lat/lng via vworld API (ROAD → PARCEL fallback)
- Computes star positions using skyfield + stereographic projection
- Parses `resources/constellationship.fab` for constellation line segments
- Loads `de421.bsp` and `hip_main.dat` from `resources/` at module import time (non-trivial cost; incurred once per Streamlit process start, not per re-run)
- `_ROOT` is resolved as `Path(__file__).parent.parent.parent` (i.e., repo root)
- Public functions: `run()` (top-level), `geocode_address()`, `compute_sky_data()`, `load_constellation_lines()` — all callable independently

**`narrative.py`** — Generates Korean poetic prose using Anthropic `claude-sonnet-4-6` (model name hardcoded)
- `theme` (user-supplied "이 날의 의미") is sanitized via `_sanitize_theme()` before inclusion in the prompt — returns `None` on empty or injection-suspicious input; wrapped in `<user_input>` XML tags in the user message
- `_IAU_TO_KO`: IAU abbreviation → Korean name mapping dict (e.g. `"Ori"` → `"오리온"`); up to 10 visible constellations passed to the prompt

**`renderers/plotly_2d.py`** — Renders stereographic projection output (x, y) as a Plotly 2D interactive chart; the only renderer used by the Streamlit app. Only stars with `alt_deg >= 0` are shown. Horizon is drawn as a data-coordinate circle; CSS controls actual canvas size (not Plotly's width/height)

**`renderers/static.py`** — Matplotlib static PNG renderer; used only by `starchart.py` (legacy), not by the Streamlit app

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

No automated tests exist in this project. The pre-commit hooks (ruff, pyright, bandit) are the primary quality gate.

## Streamlit Session State

`app.py` stores all inter-run state in `st.session_state`:
- `sky_data`: `SkyData | None` — computed on form submit, persists across reruns
- `narrative`: `str | None` — Claude-generated text; cleared on each new submit
- `error_msg`: `str | None` — shown when geocoding fails
- `privacy_agreed`: `bool` — controls the one-time privacy dialog
- `narrative_count`: `int` — tracks Claude API calls per session; capped at `_MAX_NARRATIVES_PER_SESSION = 3`

## Dependency Management

Use `uv`. Never edit `pyproject.toml` directly to add packages:
```shell
uv add <package>
```
