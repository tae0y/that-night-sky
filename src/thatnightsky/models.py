"""데이터 모델 정의 — 입력→계산→렌더 사이의 경계를 명시한다."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class QueryInput:
    """사용자 입력 원시값. 검증 전."""

    address: str  # 한국어 주소 원문 ("부산광역시 가야동")
    when: str  # "YYYY-MM-DD HH:MM" 형식 문자열


@dataclass(frozen=True)
class ObserverContext:
    """geocoding + timezone 변환 결과. 천체 계산의 입력."""

    lat: float  # 위도 (십진도)
    lng: float  # 경도 (십진도)
    utc_dt: datetime  # UTC datetime (tzinfo=utc 포함)
    address_display: str  # 지오코더가 반환한 정규화 주소 (표시용)


@dataclass(frozen=True)
class StarRecord:
    """별 하나의 천구 좌표 + 표시 속성."""

    hip: int  # Hipparcos 번호
    ra_deg: float  # 적경 (도)
    dec_deg: float  # 적위 (도)
    magnitude: float  # 겉보기 등급
    x: float  # stereographic 투영 x (matplotlib용)
    y: float  # stereographic 투영 y (matplotlib용)
    az_deg: float  # 방위각 (도) — Plotly 3D 구면 좌표용
    alt_deg: float  # 고도 (도) — Plotly 3D 구면 좌표용


@dataclass(frozen=True)
class ConstellationLine:
    """별자리 선분 하나. HIP 번호 쌍."""

    hip_from: int  # 시작 별 HIP 번호
    hip_to: int  # 끝 별 HIP 번호
    name: str  # 별자리 IAU 약자 ("ORI", "UMA" 등)


@dataclass(frozen=True)
class SkyData:
    """렌더러가 받는 유일한 입력. 계산 완료 상태."""

    context: ObserverContext
    stars: tuple[StarRecord, ...]  # 등급 필터 적용 후
    constellation_lines: tuple[ConstellationLine, ...]
    limiting_magnitude: float  # 필터 기준 등급
    visible_constellation_names: tuple[str, ...]  # Claude 텍스트 생성용
