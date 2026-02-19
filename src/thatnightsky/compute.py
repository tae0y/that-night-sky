"""천체 계산 레이어 — geocoding, skyfield 계산, 별자리 데이터 로드."""

import os
from datetime import datetime
from pathlib import Path

import httpx
import numpy as np
from pytz import timezone, utc
from skyfield.api import Loader, Star, wgs84
from skyfield.data import hipparcos
from skyfield.projections import build_stereographic_projection
from timezonefinder import TimezoneFinder

from thatnightsky.models import (
    ConstellationLine,
    ObserverContext,
    QueryInput,
    SkyData,
    StarRecord,
)

_ROOT = Path(__file__).parent.parent.parent
_loader = Loader(str(_ROOT / "resources"))
_eph = _loader("de421.bsp")
_earth = _eph["earth"]
_tf = TimezoneFinder()

with _loader.open("hip_main.dat") as f:
    _stars_df = hipparcos.load_dataframe(f)


class GeocodingError(Exception):
    """vworld 지오코더 호출 실패."""


def _geocode_with_type(address: str, addr_type: str) -> dict | None:
    """vworld API 단일 호출. NOT_FOUND면 None, ERROR면 예외."""
    params = {
        "service": "address",
        "request": "getCoord",
        "version": "2.0",
        "crs": "EPSG:4326",
        "format": "json",
        "type": addr_type,
        "address": address,
        "key": os.environ["VWORLD_API_KEY"],
    }
    resp = httpx.get("https://api.vworld.kr/req/address", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()["response"]
    status = data["status"]
    if status == "OK":
        return data
    if status == "NOT_FOUND":
        return None
    raise GeocodingError(f"vworld error: {data.get('error', status)}")


def geocode_address(address: str, when: str) -> ObserverContext:
    """주소 문자열과 시각을 받아 ObserverContext를 반환한다.

    ROAD 타입으로 먼저 시도하고 NOT_FOUND면 PARCEL로 재시도한다.

    Args:
        address: 한국어 주소 원문.
        when: "YYYY-MM-DD HH:MM" 형식의 로컬 시각 문자열.

    Returns:
        위경도, UTC datetime, 정규화 주소를 담은 ObserverContext.

    Raises:
        GeocodingError: API 에러 또는 주소를 찾지 못한 경우.
    """
    data = _geocode_with_type(address, "ROAD") or _geocode_with_type(address, "PARCEL")
    if data is None:
        raise GeocodingError(f"주소를 찾을 수 없습니다: {address}")

    point = data["result"]["point"]
    lng = float(point["x"])
    lat = float(point["y"])
    address_display = data["refined"]["text"]

    dt = datetime.strptime(when, "%Y-%m-%d %H:%M")
    tz_str = _tf.timezone_at(lat=lat, lng=lng)
    if tz_str is None:
        raise GeocodingError(f"timezone을 찾을 수 없습니다: lat={lat}, lng={lng}")
    local_tz = timezone(tz_str)
    utc_dt = local_tz.localize(dt, is_dst=None).astimezone(utc)

    return ObserverContext(lat=lat, lng=lng, utc_dt=utc_dt, address_display=address_display)


def compute_sky_data(
    context: ObserverContext,
    limiting_magnitude: float = 6.5,
) -> SkyData:
    """skyfield로 천체 위치를 계산하고 SkyData를 반환한다.

    Args:
        context: geocoding 결과 (위경도, UTC datetime).
        limiting_magnitude: 표시할 최대 등급 (기본 6.5).

    Returns:
        별 목록과 별자리 선분을 담은 SkyData.
    """
    ts = _loader.timescale()
    t = ts.from_datetime(context.utc_dt)

    observer = wgs84.latlon(
        latitude_degrees=context.lat,
        longitude_degrees=context.lng,
    ).at(t)

    ra, dec, _ = observer.radec()
    center = _earth.at(t).observe(Star(ra=ra, dec=dec))
    projection = build_stereographic_projection(center)

    stars_df = _stars_df.copy()
    bright = stars_df["magnitude"] <= limiting_magnitude
    stars_df = stars_df[bright]

    ground = _eph["earth"] + wgs84.latlon(
        latitude_degrees=context.lat, longitude_degrees=context.lng
    )
    star_positions = _earth.at(t).observe(Star.from_dataframe(stars_df))
    x_arr, y_arr = projection(star_positions)

    # 고도/방위각: 지상 관측자(earth + latlon)로 observe해야 altaz() 사용 가능
    apparent = ground.at(t).observe(Star.from_dataframe(stars_df)).apparent()
    alt, az, _ = apparent.altaz()

    records: list[StarRecord] = []
    for i, (idx, row) in enumerate(stars_df.iterrows()):
        records.append(
            StarRecord(
                hip=int(idx),
                ra_deg=float(row["ra_degrees"]),
                dec_deg=float(row["dec_degrees"]),
                magnitude=float(row["magnitude"]),
                x=float(x_arr[i]),
                y=float(y_arr[i]),
                az_deg=float(az.degrees[i]),
                alt_deg=float(alt.degrees[i]),
            )
        )

    return SkyData(
        context=context,
        stars=tuple(records),
        constellation_lines=(),  # Step 3에서 채움
        limiting_magnitude=limiting_magnitude,
        visible_constellation_names=(),  # Step 3에서 채움
    )


def run(query: QueryInput, limiting_magnitude: float = 6.5) -> SkyData:
    """QueryInput을 받아 SkyData를 반환하는 최상위 진입점.

    Args:
        query: 사용자 입력 (주소, 시각).
        limiting_magnitude: 표시할 최대 등급.

    Returns:
        계산 완료된 SkyData.
    """
    context = geocode_address(query.address, query.when)
    return compute_sky_data(context, limiting_magnitude)
