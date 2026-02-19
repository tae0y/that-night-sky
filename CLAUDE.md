# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Streamlit web app that renders an interactive star chart for a given date and location. Enter a Korean address, and the app resolves coordinates via vworld API, computes celestial positions with skyfield, and generates a poetic narrative using the Claude API.

## Run

```shell
# Streamlit app (main entry point)
uv run streamlit run app.py

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

`src/thatnightsky/` contains all core logic. `app.py` is the Streamlit entry point that wires the package together.

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
- Loads `de421.bsp` and `hip_main.dat` from `resources/` at module import time (non-trivial import cost)

**`narrative.py`** — Generates Korean poetic prose using Anthropic claude-sonnet-4-6

**`renderers/plotly_2d.py`** — Renders stereographic projection output (x, y) as a Plotly 2D interactive chart

**`resources/`** — Binary data files (committed to repo):
- `de421.bsp`: NASA JPL ephemeris
- `hip_main.dat`: Hipparcos star catalogue
- `constellationship.fab`: Constellation line definitions (Stellarium format)

## Pre-commit Hooks

Run automatically on commit:
- `ruff` (lint + format, with auto-fix)
- `pyright` (type checking)
- `bandit` (security scan, configured via `pyproject.toml`)
- `pip-audit` (manual stage only, run with `--hook-stage manual`)

Run manually:
```shell
pre-commit run --all-files
pre-commit run pip-audit --hook-stage manual
```

## Dependency Management

Use `uv`. Never edit `pyproject.toml` directly to add packages:
```shell
uv add <package>
```
