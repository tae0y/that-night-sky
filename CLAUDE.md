# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

특정 날짜와 장소를 입력받아 그 밤의 별자리 지도를 PNG로 생성하는 단일 스크립트 프로젝트.

- `starchart.py`: 핵심 스크립트. 상단 `where`/`when` 변수를 수정 후 실행.
- `de421.bsp`: NASA JPL 천문력 데이터 (바이너리, 커밋됨)
- `hip_main.dat`: Hipparcos 별 카탈로그 데이터
- `results/`: 생성된 PNG 저장 디렉토리

## 실행

```shell
python starchart.py
```

`starchart.py` 상단의 `where`, `when` 변수를 직접 수정하여 장소와 시간을 지정한다.

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
