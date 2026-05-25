"""Step definitions for geocoding.feature."""
from __future__ import annotations

import pytest
from pytest_bdd import scenarios, given, then, parsers

scenarios("../features/geocoding.feature")


@then(parsers.parse("the latitude is between {lo:f} and {hi:f}"))
def check_latitude(response_store, lo, hi):
    body = response_store["response"].json()
    lat = body["context"]["lat"]
    assert lo <= lat <= hi, f"Latitude {lat} not in [{lo}, {hi}]"


@then(parsers.parse("the longitude is between {lo:f} and {hi:f}"))
def check_longitude(response_store, lo, hi):
    body = response_store["response"].json()
    lng = body["context"]["lng"]
    assert lo <= lng <= hi, f"Longitude {lng} not in [{lo}, {hi}]"
