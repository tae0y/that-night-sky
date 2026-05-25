"""Root conftest — shared fixtures and pytest-bdd setup."""
from __future__ import annotations

import os
import pytest
import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def api_client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def request_payload():
    return {}


@pytest.fixture
def response_store():
    return {}


@pytest.fixture
def narrative_payload():
    return {}
