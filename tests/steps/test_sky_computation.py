"""Step definitions for sky_computation.feature."""
from __future__ import annotations

import pytest
from pytest_bdd import scenarios, then, parsers

scenarios("../features/sky_computation.feature")


@then("all returned stars have alt_deg >= 0")
def all_stars_above_horizon(response_store):
    stars = response_store["response"].json()["stars"]
    below = [s for s in stars if s["alt_deg"] < 0]
    assert not below, f"Stars below horizon: {below[:3]}"


@then(parsers.parse("all returned stars have magnitude <= {limit:f}"))
def all_stars_within_magnitude(response_store, limit):
    stars = response_store["response"].json()["stars"]
    too_dim = [s for s in stars if s["magnitude"] > limit]
    assert not too_dim, f"Stars exceeding magnitude {limit}: {too_dim[:3]}"


@then(parsers.parse("a star with hip {hip:d} is present in the results"))
def star_hip_present(response_store, hip):
    stars = response_store["response"].json()["stars"]
    hips = {s["hip"] for s in stars}
    assert hip in hips, f"HIP {hip} not found in {sorted(hips)[:20]}"


@then(parsers.parse('the constellation "{name}" is present in constellation_lines'))
def constellation_in_lines(response_store, name):
    lines = response_store["response"].json()["constellation_lines"]
    names = {l["name"] for l in lines}
    assert name in names, f"Constellation '{name}' not in {sorted(names)}"


@then("all constellation lines reference stars present in the star list")
def constellation_lines_reference_visible_stars(response_store):
    body = response_store["response"].json()
    hip_set = {s["hip"] for s in body["stars"]}
    for line in body["constellation_lines"]:
        assert line["hip_from"] in hip_set, f"hip_from {line['hip_from']} not in visible stars"
        assert line["hip_to"] in hip_set, f"hip_to {line['hip_to']} not in visible stars"


@then("all constellation_positions have az_deg between 0 and 360")
def constellation_positions_valid_azimuth(response_store):
    positions = response_store["response"].json()["constellation_positions"]
    for p in positions:
        assert 0 <= p["az_deg"] <= 360, f"az_deg {p['az_deg']} out of range for {p['name']}"


@then("all constellation_positions have alt_deg >= 0")
def constellation_positions_above_horizon(response_store):
    positions = response_store["response"].json()["constellation_positions"]
    for p in positions:
        assert p["alt_deg"] >= 0, f"alt_deg {p['alt_deg']} below horizon for {p['name']}"


@then(parsers.parse('the utc_dt starts with "{prefix}"'))
def utc_dt_starts_with(response_store, prefix):
    utc_dt = response_store["response"].json()["context"]["utc_dt"]
    assert utc_dt.startswith(prefix), f"utc_dt '{utc_dt}' does not start with '{prefix}'"
