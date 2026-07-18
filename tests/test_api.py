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


def test_narrative_returns_text_and_sets_cookie():
    with patch("thatnightsky.api.generate_night_description", return_value="a poem"):
        response = client.post(
            "/api/narrative",
            json={
                "address": "Seoul",
                "when": "2024-01-01 20:00",
                "constellationPositions": [
                    {"name": "Ori", "azDeg": 90.0, "altDeg": 45.0}
                ],
                "theme": "",
                "lang": "en",
            },
        )
    assert response.status_code == 200
    assert response.json() == {"text": "a poem"}
    assert "tns_session" in response.cookies


def test_narrative_429_after_three_calls():
    session_client = TestClient(app)
    with patch("thatnightsky.api.generate_night_description", return_value="a poem"):
        for _ in range(3):
            r = session_client.post(
                "/api/narrative",
                json={
                    "address": "Seoul",
                    "when": "2024-01-01 20:00",
                    "constellationPositions": [],
                    "theme": "",
                    "lang": "en",
                },
            )
            assert r.status_code == 200
        r4 = session_client.post(
            "/api/narrative",
            json={
                "address": "Seoul",
                "when": "2024-01-01 20:00",
                "constellationPositions": [],
                "theme": "",
                "lang": "en",
            },
        )
    assert r4.status_code == 429


def test_narrative_falls_back_on_claude_error():
    with patch(
        "thatnightsky.api.generate_night_description", side_effect=RuntimeError("boom")
    ):
        response = client.post(
            "/api/narrative",
            json={
                "address": "Seoul",
                "when": "2024-01-01 20:00",
                "constellationPositions": [],
                "theme": "",
                "lang": "en",
            },
        )
    assert response.status_code == 200
    assert response.json()["text"] in ("That night. The sky.",)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
