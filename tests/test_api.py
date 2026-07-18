"""Tests for the FastAPI endpoints in thatnightsky.api."""

from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from thatnightsky.api import app
from thatnightsky.compute import GeocodingError
from thatnightsky.models import ObserverContext

client = TestClient(app)

_FAKE_CONTEXT = ObserverContext(
    lat=35.1796,
    lng=129.0756,
    utc_dt=datetime(1995, 1, 14, 21, 0, tzinfo=timezone.utc),
    address_display="부산 가야동",
)


def test_sky_data_returns_stars_and_lines():
    with patch("thatnightsky.compute.geocode_address", return_value=_FAKE_CONTEXT):
        response = client.post(
            "/api/sky-data",
            json={"address": "부산 가야동", "when": "1995-01-15 06:00", "lang": "ko"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["addressDisplay"]
    assert isinstance(body["stars"], list)
    assert len(body["stars"]) > 0
    first_star = body["stars"][0]
    assert set(first_star.keys()) == {
        "hip",
        "raDeg",
        "decDeg",
        "magnitude",
        "x",
        "y",
        "azDeg",
        "altDeg",
    }
    assert isinstance(body["constellationLines"], list)
    assert isinstance(body["constellationPositions"], list)
    assert body["limitingMagnitude"] == 6.5


def test_sky_data_invalid_address_returns_422():
    with patch(
        "thatnightsky.compute.geocode_address",
        side_effect=GeocodingError("주소를 찾을 수 없습니다"),
    ):
        response = client.post(
            "/api/sky-data",
            json={
                "address": "이런주소는존재하지않습니다아아아",
                "when": "2024-01-01 00:00",
                "lang": "ko",
            },
        )
    assert response.status_code == 422
    assert "detail" in response.json()
