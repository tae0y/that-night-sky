"""Astronomy computation layer — geocoding, skyfield calculations, and constellation data loading."""

import math
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import httpx
from pytz import timezone, utc
from skyfield.api import Loader, Star, wgs84
from skyfield.data import hipparcos
from skyfield.projections import build_stereographic_projection
from timezonefinder import TimezoneFinder

from thatnightsky.models import (
    ConstellationLine,
    ConstellationPosition,
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
    """Geocoder call failure."""


def _geocode_vworld(address: str, addr_type: str) -> dict | None:
    """Single vworld API call. Returns None on NOT_FOUND, raises on ERROR."""
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


def _geocode_nominatim(address: str) -> tuple[float, float, str] | None:
    """Nominatim (OpenStreetMap) geocoder. Returns (lat, lng, display_name) or None."""
    params = {"q": address, "format": "json", "limit": 1}
    headers = {
        "User-Agent": "ThatNightSky/1.0 (https://github.com/tae0y/that-night-sky)"
    }
    resp = httpx.get(
        "https://nominatim.openstreetmap.org/search",
        params=params,
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        return None
    r = results[0]
    return float(r["lat"]), float(r["lon"]), r["display_name"]


def geocode_address(address: str, when: str, lang: str = "en") -> ObserverContext:
    """Resolve an address string and time string to an ObserverContext.

    For Korean (lang='ko'): tries vworld (ROAD → PARCEL), falls back to Nominatim.
    For other languages: uses Nominatim directly.

    Args:
        address: Address string in any language.
        when: Local time string in "YYYY-MM-DD HH:MM" format.
        lang: Language code ('ko' or 'en'). Determines geocoder strategy.

    Returns:
        ObserverContext containing lat/lng, UTC datetime, and normalized address.

    Raises:
        GeocodingError: On API error or when address cannot be found.
    """
    lat: float | None = None
    lng: float | None = None
    address_display: str = address

    if lang == "ko" and os.environ.get("VWORLD_API_KEY"):
        try:
            data = _geocode_vworld(address, "ROAD") or _geocode_vworld(
                address, "PARCEL"
            )
            if data is not None:
                point = data["result"]["point"]
                lng = float(point["x"])
                lat = float(point["y"])
                address_display = data["refined"]["text"]
        except GeocodingError:
            pass  # fall through to Nominatim

    if lat is None:
        result = _geocode_nominatim(address)
        if result is None:
            raise GeocodingError(f"Address not found: {address}")
        lat, lng, address_display = result

    assert lng is not None
    dt = datetime.strptime(when, "%Y-%m-%d %H:%M")
    tz_str = _tf.timezone_at(lat=lat, lng=lng)
    if tz_str is None:
        raise GeocodingError(f"Timezone not found: lat={lat}, lng={lng}")
    local_tz = timezone(tz_str)
    utc_dt = local_tz.localize(dt, is_dst=None).astimezone(utc)

    return ObserverContext(
        lat=lat, lng=lng, utc_dt=utc_dt, address_display=address_display
    )


def compute_sky_data(
    context: ObserverContext,
    limiting_magnitude: float = 6.5,
) -> SkyData:
    """Compute celestial positions using skyfield and return a SkyData object.

    Args:
        context: Geocoding result (lat/lng, UTC datetime).
        limiting_magnitude: Maximum magnitude to include (default 6.5).

    Returns:
        SkyData containing star list and constellation line segments.
    """
    ts = _loader.timescale()
    t = ts.from_datetime(context.utc_dt)

    observer = wgs84.latlon(
        latitude_degrees=context.lat,
        longitude_degrees=context.lng,
    ).at(t)

    ra, dec, _ = observer.radec()
    center = _earth.at(t).observe(Star(ra=ra, dec=dec))  # type: ignore[union-attr]
    projection = build_stereographic_projection(center)

    stars_df = _stars_df.copy()
    bright = stars_df["magnitude"] <= limiting_magnitude
    stars_df = stars_df[bright]
    stars_df = stars_df.dropna(subset=["ra_degrees", "dec_degrees"])

    ground = _eph["earth"] + wgs84.latlon(
        latitude_degrees=context.lat, longitude_degrees=context.lng
    )
    star_positions = _earth.at(t).observe(Star.from_dataframe(stars_df))  # type: ignore[union-attr]
    x_arr, y_arr = projection(star_positions)

    # Altitude/azimuth: must observe from ground observer (earth + latlon) to use altaz()
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

    visible_hip_set = {r.hip for r in records if r.alt_deg >= 0}
    all_lines = load_constellation_lines()
    visible_lines = tuple(
        line
        for line in all_lines
        if line.hip_from in visible_hip_set and line.hip_to in visible_hip_set
    )
    visible_names = tuple(dict.fromkeys(line.name for line in visible_lines))
    constellation_positions = _compute_constellation_positions(records, visible_names)

    return SkyData(
        context=context,
        stars=tuple(records),
        constellation_lines=visible_lines,
        limiting_magnitude=limiting_magnitude,
        constellation_positions=constellation_positions,
    )


def _compute_constellation_positions(
    records: list[StarRecord],
    visible_names: tuple[str, ...],
) -> tuple[ConstellationPosition, ...]:
    """Compute brightness-weighted mean az/alt for each visible constellation.

    Azimuth uses circular mean (sin/cos components) to handle the 0°/360° wrap.
    Only stars with alt_deg >= 0 are included.
    """
    hip_to_record: dict[int, StarRecord] = {r.hip: r for r in records if r.alt_deg >= 0}
    all_lines = load_constellation_lines()

    # Group stars by constellation via line segments
    constellation_stars: dict[str, set[int]] = defaultdict(set)
    for line in all_lines:
        if line.name in visible_names:
            if line.hip_from in hip_to_record:
                constellation_stars[line.name].add(line.hip_from)
            if line.hip_to in hip_to_record:
                constellation_stars[line.name].add(line.hip_to)

    positions: list[ConstellationPosition] = []
    for name in visible_names:
        hips = constellation_stars.get(name)
        if not hips:
            continue
        stars = [hip_to_record[h] for h in hips]
        # Brightness weight: dimmer magnitude = brighter star; weight = 1 / (mag + offset)
        weights = [1.0 / (s.magnitude + 3.0) for s in stars]
        total_w = sum(weights)
        # Circular mean for azimuth
        sin_sum = sum(
            w * math.sin(math.radians(s.az_deg)) for w, s in zip(weights, stars)
        )
        cos_sum = sum(
            w * math.cos(math.radians(s.az_deg)) for w, s in zip(weights, stars)
        )
        az_mean = math.degrees(math.atan2(sin_sum / total_w, cos_sum / total_w)) % 360
        alt_mean = sum(w * s.alt_deg for w, s in zip(weights, stars)) / total_w
        positions.append(
            ConstellationPosition(
                name=name, az_deg=round(az_mean, 1), alt_deg=round(alt_mean, 1)
            )
        )

    return tuple(positions)


def load_constellation_lines() -> tuple[ConstellationLine, ...]:
    """Parse resources/constellationship.fab and return constellation line segments.

    File format: ``IAU_abbr line_pair_count HIP1 HIP2 HIP3 HIP4 ...``
    Consecutive HIP number pairs form individual line segments.

    Returns:
        Tuple of ConstellationLine objects. Each is a hip_from → hip_to segment.
    """
    fab_path = _ROOT / "resources" / "constellationship.fab"
    lines: list[ConstellationLine] = []
    with fab_path.open(encoding="utf-8") as f:
        for raw in f:
            parts = raw.split()
            if len(parts) < 4:
                continue
            name = parts[0]
            hips = [int(p) for p in parts[2:]]
            for i in range(0, len(hips) - 1, 2):
                lines.append(
                    ConstellationLine(hip_from=hips[i], hip_to=hips[i + 1], name=name)
                )
    return tuple(lines)


def run(
    query: QueryInput, limiting_magnitude: float = 6.5, lang: str = "en"
) -> SkyData:
    """Top-level entry point: takes a QueryInput and returns a SkyData.

    Args:
        query: User input (address, time string).
        limiting_magnitude: Maximum magnitude to include.
        lang: Language code ('ko' or 'en'). Determines geocoder strategy.

    Returns:
        Fully computed SkyData.
    """
    context = geocode_address(query.address, query.when, lang=lang)
    return compute_sky_data(context, limiting_magnitude)
