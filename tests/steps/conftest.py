"""Shared pytest fixtures for BDD step definitions."""
from __future__ import annotations

import os
import pytest
import httpx
from pytest_bdd import given, then, when, parsers

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
def api_client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def request_payload():
    return {}


@pytest.fixture
def response_store():
    return {}


# ---------------------------------------------------------------------------
# Shared Given steps
# ---------------------------------------------------------------------------

@given("the sky API is running")
def sky_api_running(api_client):
    r = api_client.get("/api/health")
    assert r.status_code == 200, f"API not healthy: {r.text}"


@given(parsers.parse('the address "{address}"'), target_fixture="request_payload")
def given_address(address, request_payload):
    request_payload["address"] = address
    return request_payload


@given(parsers.parse('the datetime "{when}"'), target_fixture="request_payload")
def given_datetime(when, request_payload):
    request_payload["when"] = when
    return request_payload


@given(
    parsers.parse('a valid sky_data payload for "{address}" at "{when}"'),
    target_fixture="sky_data_payload",
)
def given_sky_data_payload(api_client, address, when):
    r = api_client.post("/api/sky", json={"address": address, "when": when, "lang": "ko"})
    assert r.status_code == 200, f"Sky computation failed: {r.text}"
    return r.json()


@given(parsers.parse('the theme "{theme}"'), target_fixture="narrative_payload")
def given_theme(sky_data_payload, theme, narrative_payload=None):
    if narrative_payload is None:
        narrative_payload = {}
    data = sky_data_payload
    narrative_payload.update(
        {
            "address": data["context"]["address_display"],
            "when": data["context"]["utc_dt"],
            "constellation_positions": data["constellation_positions"],
            "theme": theme,
        }
    )
    return narrative_payload


@given(parsers.parse('the language "{lang}"'), target_fixture="narrative_payload")
def given_language(lang, narrative_payload):
    narrative_payload["lang"] = lang
    return narrative_payload


# ---------------------------------------------------------------------------
# Shared When steps
# ---------------------------------------------------------------------------

@when(parsers.parse('I POST to "{path}"'), target_fixture="response_store")
def post_to(api_client, path, request_payload):
    r = api_client.post(path, json=request_payload)
    return {"response": r}


@when(parsers.parse('I POST to "{path}" with narrative payload'), target_fixture="response_store")
def post_narrative(api_client, path, narrative_payload):
    r = api_client.post(path, json=narrative_payload)
    return {"response": r}


@when(parsers.parse('I GET "{path}"'), target_fixture="response_store")
def get_to(api_client, path):
    r = api_client.get(path)
    return {"response": r}


# ---------------------------------------------------------------------------
# Shared Then steps
# ---------------------------------------------------------------------------

@then(parsers.parse("the response status is {status:d}"))
def check_status(response_store, status):
    r = response_store["response"]
    assert r.status_code == status, f"Expected {status}, got {r.status_code}: {r.text}"


@then(parsers.parse('the response contains "{key}"'))
def response_contains_key(response_store, key):
    body = response_store["response"].json()
    assert key in body or key in str(body), f"Key '{key}' not found in response: {body}"
