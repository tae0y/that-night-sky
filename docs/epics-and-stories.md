# ThatNightSky — Epics & User Stories

## Overview

ThatNightSky renders a personalized, interactive star chart for any date and location, enriched with a poetic Claude-generated narrative. This document captures requirements in Epic → User Story → Acceptance Criteria form, and serves as the source of truth for BDD test scenarios.

---

## Epic 1: 위치 및 시간 입력 (Location & Time Input)

사용자가 관측 위치(주소)와 날짜/시간을 입력하면 시스템이 좌표 및 UTC 시각으로 변환한다.

### Story 1.1 — 한국어 주소 지오코딩

**As a** Korean user,  
**I want to** enter a Korean address (road or parcel format),  
**so that** the system resolves it to coordinates without me knowing the lat/lng.

**Acceptance Criteria:**
- Given a valid Korean road address (e.g., "서울특별시 종로구 창경궁로 185"), the system returns a lat/lng pair within South Korea bounds (lat 33–38, lng 125–130).
- Given a valid Korean parcel address (e.g., "부산광역시 해운대구 중동"), the system also resolves correctly (PARCEL fallback).
- Given an address that cannot be resolved, the API returns HTTP 422 with an error message.
- The resolved display address is included in the response for the UI to show.

### Story 1.2 — 영어/국제 주소 지오코딩

**As a** non-Korean user,  
**I want to** enter an international address in English,  
**so that** I can generate a star chart for any location worldwide.

**Acceptance Criteria:**
- Given "New York, USA", the system returns coordinates near (40.7, -74.0).
- Given a partial or ambiguous address, the system returns the best-matching result via Nominatim.
- Given a completely invalid string (e.g., "asdfghjkl"), the API returns HTTP 422.

### Story 1.3 — 날짜/시간 입력 및 시간대 변환

**As a** user,  
**I want to** enter a local date and time in "YYYY-MM-DD HH:MM" format,  
**so that** the system correctly converts it to UTC for astronomical calculations.

**Acceptance Criteria:**
- Given address "Seoul" and time "2000-01-01 00:00", the UTC datetime is 1999-12-31 15:00:00 UTC (KST = UTC+9).
- Given an address in UTC-5 and time "2000-01-01 00:00", the UTC datetime is 2000-01-01 05:00:00 UTC.
- Given an invalid datetime string (e.g., "not-a-date"), the API returns HTTP 422.

---

## Epic 2: 밤하늘 계산 (Sky Computation)

입력된 위치·시간에서 별의 위치, 별자리 선, 지평선 위 천체를 계산한다.

### Story 2.1 — 별 위치 계산

**As a** user,  
**I want** the star chart to show correct positions for stars above the horizon,  
**so that** the chart accurately represents what was visible that night.

**Acceptance Criteria:**
- Only stars with `alt_deg >= 0` are included in the response.
- Stars are filtered to limiting magnitude 6.5 by default.
- Each star record includes: `hip` (Hipparcos ID), `magnitude`, `x`, `y` (stereographic projection), `az_deg`, `alt_deg`.
- For Seoul at 2000-01-01 00:00 KST, Orion stars (HIP 27989 = Betelgeuse) appear above the horizon.

### Story 2.2 — 별자리 선 계산

**As a** user,  
**I want** constellation lines drawn between connected stars,  
**so that** I can identify constellations in the chart.

**Acceptance Criteria:**
- The response includes constellation line segments (hip_from, hip_to, name).
- Only constellation lines where both stars are visible (alt_deg >= 0) are included in the rendering data.
- The IAU abbreviation (e.g., "Ori") is included per line for labeling.

### Story 2.3 — 별자리 위치 집계 (내러티브용)

**As a** narrative generation module,  
**I want** the brightness-weighted mean az/alt for each visible constellation,  
**so that** the Claude prompt can reference which constellations are prominent.

**Acceptance Criteria:**
- `constellation_positions` contains only constellations with at least one visible star.
- Azimuth mean correctly wraps around 0°/360° boundary (circular mean).
- Brighter stars (lower magnitude) are weighted more heavily.
- Up to 10 constellations are passed to the narrative endpoint.

---

## Epic 3: 인터랙티브 별자리 차트 시각화 (Interactive Star Chart)

계산된 밤하늘 데이터를 SVG 기반 인터랙티브 차트로 표현한다.

### Story 3.1 — 별자리 차트 표시

**As a** user,  
**I want** to see an interactive star chart rendered in the browser,  
**so that** I can visually explore the night sky for that moment.

**Acceptance Criteria:**
- The chart renders within 3 seconds of receiving sky data.
- Stars are shown as circles; brighter stars (lower magnitude) have larger radii and higher opacity.
- Constellation lines connect stars using the Hipparcos IDs.
- The chart uses a dark background with a visible horizon arc at the bottom.
- The chart is viewBox-based and scales responsively to any screen size.

### Story 3.2 — 확대/축소 및 이동

**As a** user,  
**I want** to pan and zoom the star chart,  
**so that** I can inspect individual stars and constellations in detail.

**Acceptance Criteria:**
- Mouse wheel zooms in/out (range: 0.25× to 8×).
- Click-and-drag pans the chart.
- Two-finger pinch on mobile zooms toward the midpoint.
- A reset button restores the default view.

### Story 3.3 — 이미지 저장

**As a** user,  
**I want** to download the star chart as a PNG image,  
**so that** I can keep a memento of that night sky.

**Acceptance Criteria:**
- Clicking the save/download button exports a PNG containing the star chart and starfield background.
- If a narrative exists, it is overlaid at the bottom of the PNG.
- The default filename is language-dependent ("그날밤하늘.png" / "that-night-sky.png").
- The export works on all major browsers (Chrome, Safari, Firefox).

---

## Epic 4: 시적 내러티브 생성 (Poetic Narrative)

사용자가 입력한 날의 의미와 밤하늘 데이터를 바탕으로 Claude가 한국어/영어 산문을 생성한다.

### Story 4.1 — 날의 의미 입력

**As a** user,  
**I want** to optionally enter an "occasion" or theme for that night (e.g., "생일", "졸업"),  
**so that** the narrative is emotionally personalized.

**Acceptance Criteria:**
- The theme field is optional; leaving it blank still generates a narrative.
- Theme input is sanitized: limited to 20 characters, control characters stripped.
- Prompt injection patterns (system:, ignore:, <script> etc.) cause the theme to be discarded silently.

### Story 4.2 — 내러티브 생성

**As a** user,  
**I want** to receive a short poetic prose passage about that night sky,  
**so that** the star chart becomes emotionally meaningful.

**Acceptance Criteria:**
- The narrative is 3–5 sentences (one paragraph) in the requested language (ko/en).
- The narrative weaves in at least one visible constellation by its localized name.
- The narrative references the occasion theme if one was provided (and safe).
- The API responds within 10 seconds under normal conditions.
- The response is plain text (no markdown, no headings).

### Story 4.3 — 내러티브 횟수 제한

**As a** system,  
**I want** to limit narrative generation to 3 times per user session,  
**so that** Claude API costs are controlled.

**Acceptance Criteria:**
- The first 3 narrative requests in a session succeed.
- The 4th request in the same session returns an error (HTTP 429 or frontend guard).
- The limit is tracked client-side (session-based) and enforced before calling the API.

---

## Epic 5: 사용자 경험 (User Experience)

### Story 5.1 — 다국어 지원 (한국어 / 영어)

**As a** user with a Korean browser,  
**I want** the UI to display in Korean by default,  
**so that** I don't need to switch languages manually.

**Acceptance Criteria:**
- The UI language is detected from `navigator.language` on first load.
- All labels, placeholders, buttons, and error messages are translated.
- The narrative is generated in the detected language.
- Switching between ko/en is possible without page reload.

### Story 5.2 — 개인정보 동의

**As a** new user,  
**I want** to be shown a privacy notice before submitting any data,  
**so that** I understand how my address input is used.

**Acceptance Criteria:**
- The privacy dialog appears on first interaction (before form submit).
- The user must click "확인" / "Confirm" to proceed.
- After confirming once per session, the dialog does not reappear.
- The dialog links to the privacy policy URL.

### Story 5.3 — 샘플 입력 제안

**As a** new user,  
**I want** to see a pre-filled sample address and date on first load,  
**so that** I can try the app immediately without thinking of an input.

**Acceptance Criteria:**
- A random sample input (address, date/time, theme) is shown in the form on first load.
- The sample is appropriate to the detected language (Korean samples for ko, English for en).
- Submitting the sample input produces a valid star chart.

### Story 5.4 — 반응형 UI (모바일/데스크톱)

**As a** mobile user,  
**I want** the input form and chart to be usable on a small screen,  
**so that** I can use the app on my phone.

**Acceptance Criteria:**
- On desktop (>= 768px), the input panel is displayed horizontally at the bottom.
- On mobile (< 768px), the input panel stacks vertically.
- The input panel can be collapsed/expanded on mobile.
- The star chart fills the available screen height on all devices.

---

## API Surface (FastAPI Backend)

The following endpoints will be implemented in the FastAPI backend:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sky` | Geocode address + compute sky data |
| POST | `/api/narrative` | Generate poetic narrative |
| GET | `/api/health` | Health check |

### `POST /api/sky` Request

```json
{
  "address": "서울특별시 종로구 창경궁로 185",
  "when": "2000-01-01 00:00",
  "lang": "ko",
  "limiting_magnitude": 6.5
}
```

### `POST /api/sky` Response

```json
{
  "context": {
    "lat": 37.57,
    "lng": 127.00,
    "utc_dt": "1999-12-31T15:00:00Z",
    "address_display": "서울특별시 종로구..."
  },
  "stars": [
    {"hip": 27989, "magnitude": 0.42, "x": 0.12, "y": 0.45, "az_deg": 180.0, "alt_deg": 30.0}
  ],
  "constellation_lines": [
    {"hip_from": 27989, "hip_to": 26727, "name": "Ori"}
  ],
  "constellation_positions": [
    {"name": "Ori", "az_deg": 200.0, "alt_deg": 35.0}
  ],
  "limiting_magnitude": 6.5
}
```

### `POST /api/narrative` Request

```json
{
  "address": "서울특별시 종로구",
  "when": "2000-01-01 00:00",
  "constellation_positions": [...],
  "theme": "생일",
  "lang": "ko"
}
```

### `POST /api/narrative` Response

```json
{
  "narrative": "그날 밤, 오리온이 남쪽 하늘을 가득 채우고..."
}
```
