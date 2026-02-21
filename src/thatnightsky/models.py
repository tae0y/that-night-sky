"""Data model definitions — explicit boundaries between input, compute, and render layers."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class QueryInput:
    """Raw user input. Not yet validated."""

    address: str  # Korean address string ("부산광역시 가야동")
    when: str  # "YYYY-MM-DD HH:MM" format string


@dataclass(frozen=True)
class ObserverContext:
    """Result of geocoding + timezone conversion. Input to sky computation."""

    lat: float  # Latitude (decimal degrees)
    lng: float  # Longitude (decimal degrees)
    utc_dt: datetime  # UTC datetime (with tzinfo=utc)
    address_display: str  # Normalized address returned by geocoder (for display)


@dataclass(frozen=True)
class StarRecord:
    """Celestial coordinates + display attributes for a single star."""

    hip: int  # Hipparcos catalogue number
    ra_deg: float  # Right ascension (degrees)
    dec_deg: float  # Declination (degrees)
    magnitude: float  # Apparent magnitude
    x: float  # Stereographic projection x (for matplotlib)
    y: float  # Stereographic projection y (for matplotlib)
    az_deg: float  # Azimuth (degrees) — for Plotly 3D spherical coordinates
    alt_deg: float  # Altitude (degrees) — for Plotly 3D spherical coordinates


@dataclass(frozen=True)
class ConstellationLine:
    """A single constellation line segment. A pair of HIP numbers."""

    hip_from: int  # Starting star HIP number
    hip_to: int  # Ending star HIP number
    name: str  # Constellation IAU abbreviation ("ORI", "UMA", etc.)


@dataclass(frozen=True)
class ConstellationPosition:
    """Representative sky position for a single constellation."""

    name: str  # IAU abbreviation ("Ori", "UMa", etc.)
    az_deg: float  # Brightness-weighted mean azimuth (0=N, 90=E, 180=S, 270=W)
    alt_deg: float  # Brightness-weighted mean altitude (degrees)


@dataclass(frozen=True)
class SkyData:
    """The sole input to renderers. Fully computed state."""

    context: ObserverContext
    stars: tuple[StarRecord, ...]  # After magnitude filter
    constellation_lines: tuple[ConstellationLine, ...]
    limiting_magnitude: float  # Magnitude filter threshold
    constellation_positions: tuple[
        ConstellationPosition, ...
    ]  # Used for Claude narrative generation
