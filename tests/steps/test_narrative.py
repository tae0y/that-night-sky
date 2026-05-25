"""Step definitions for narrative.feature."""
from __future__ import annotations

import pytest
from pytest_bdd import scenarios, when, then, parsers

scenarios("../features/narrative.feature")


@when('I POST to "/api/narrative"', target_fixture="response_store")
def post_narrative_endpoint(api_client, narrative_payload):
    r = api_client.post("/api/narrative", json=narrative_payload)
    return {"response": r}


@then("the narrative is non-empty")
def narrative_non_empty(response_store):
    text = response_store["response"].json()["narrative"]
    assert text and text.strip(), "Narrative is empty"


@then("the narrative is a single paragraph (no blank lines)")
def narrative_single_paragraph(response_store):
    text = response_store["response"].json()["narrative"]
    assert "\n\n" not in text, f"Narrative has blank lines: {text!r}"


@then(parsers.parse('the narrative does not contain "{forbidden}"'))
def narrative_does_not_contain(response_store, forbidden):
    text = response_store["response"].json()["narrative"]
    assert forbidden not in text, f"Narrative contains forbidden text '{forbidden}': {text!r}"
