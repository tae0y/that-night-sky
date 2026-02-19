# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

특정 날짜와 장소를 입력받아 그 밤의 별자리 지도를 인터랙티브하게 보여주는 Streamlit 웹앱.
한국 주소를 입력하면 vworld API로 좌표를 조회하고, skyfield로 천체 위치를 계산하며, Claude API로 감성 텍스트를 생성한다.

## 실행

```shell
# Streamlit 앱 (메인 진입점)
uv run streamlit run app.py

# 레거시 PNG 생성 스크립트
uv run python src/thatnightsky/starchart.py
```

## 환경 변수

`.env` 파일 필요:
```
VWORLD_API_KEY=...       # 한국 공간정보 오픈플랫폼 (https://www.vworld.kr)
ANTHROPIC_API_KEY=...    # Claude API (감성 텍스트 생성용)
```

## 아키텍처

`src/thatnightsky/` 패키지가 핵심 로직을 담는다. `app.py`는 Streamlit 진입점으로 패키지를 조합한다.

데이터 흐름: `QueryInput` → `compute.run()` → `SkyData` → `renderers/*.render_*()` → Plotly Figure

**`models.py`** — 레이어 경계를 정의하는 불변 dataclass:
- `QueryInput`: 사용자 입력 원시값 (주소, 시각 문자열)
- `ObserverContext`: geocoding 결과 (위경도, UTC datetime)
- `StarRecord`: 별 하나의 좌표 + 투영 결과
- `ConstellationLine`: 별자리 선분 (HIP 쌍)
- `SkyData`: 렌더러가 받는 완전한 계산 결과

**`compute.py`** — 외부 API 및 천체 계산:
- vworld API로 한국 주소 → 위경도 변환 (ROAD → PARCEL 순서로 재시도)
- skyfield + stereographic 투영으로 별 좌표 계산
- `resources/constellationship.fab` 파싱으로 별자리 선분 로드
- 모듈 로드 시 `de421.bsp`, `hip_main.dat`를 `resources/`에서 즉시 로드함 (import 비용 존재)

**`narrative.py`** — Anthropic claude-sonnet-4-6으로 한국어 감성 텍스트 생성

**`renderers/plotly_2d.py`** — stereographic 투영 결과(x, y)를 Plotly 2D 인터랙티브 차트로 렌더링

**`resources/`** — 바이너리 데이터 파일 (커밋됨):
- `de421.bsp`: NASA JPL 천문력
- `hip_main.dat`: Hipparcos 별 카탈로그
- `constellationship.fab`: 별자리 선분 정의 (Stellarium 포맷)

## pre-commit 훅

커밋 시 자동으로 실행:
- `ruff` (lint + format, auto-fix 포함)
- `pyright` (타입 검사)
- `bandit` (보안 검사, `pyproject.toml` 설정 참조)
- `pip-audit` (수동 단계 전용, `--hook-stage manual`로 실행)

수동 실행:
```shell
pre-commit run --all-files
pre-commit run pip-audit --hook-stage manual
```

## 의존성 관리

`uv`를 사용한다. 패키지 추가 시 `pyproject.toml`을 직접 편집하지 말고:
```shell
uv add <package>
```
