"""
E2E tests using Playwright.
Run with: pytest tests/e2e/ --base-url=http://localhost:5173
Environment:
  FRONTEND_URL  default http://localhost:5173
  API_BASE_URL  default http://localhost:8000
"""
from __future__ import annotations

import os
import re
import pytest
from playwright.sync_api import Page, expect

FRONTEND = os.getenv("FRONTEND_URL", "http://localhost:5173")


@pytest.fixture(autouse=True)
def goto_home(page: Page):
    page.goto(FRONTEND)
    page.wait_for_load_state("networkidle")


# ---------------------------------------------------------------------------
# Story 5.2 — Privacy consent
# ---------------------------------------------------------------------------

class TestPrivacyConsent:
    def test_privacy_dialog_appears_on_first_visit(self, page: Page):
        dialog = page.locator("[data-testid='privacy-dialog']")
        expect(dialog).to_be_visible()

    def test_form_blocked_until_consent(self, page: Page):
        submit = page.locator("[data-testid='submit-btn']")
        expect(submit).to_be_disabled()

    def test_confirming_dismisses_dialog(self, page: Page):
        page.locator("[data-testid='privacy-confirm-btn']").click()
        dialog = page.locator("[data-testid='privacy-dialog']")
        expect(dialog).not_to_be_visible()

    def test_dialog_does_not_reappear_after_consent(self, page: Page):
        page.locator("[data-testid='privacy-confirm-btn']").click()
        page.reload()
        page.wait_for_load_state("networkidle")
        dialog = page.locator("[data-testid='privacy-dialog']")
        expect(dialog).not_to_be_visible()


# ---------------------------------------------------------------------------
# Story 5.3 — Sample input pre-fill
# ---------------------------------------------------------------------------

class TestSampleInput:
    def test_address_field_is_prefilled(self, page: Page):
        page.locator("[data-testid='privacy-confirm-btn']").click()
        address = page.locator("[data-testid='address-input']")
        expect(address).not_to_be_empty()

    def test_datetime_field_is_prefilled(self, page: Page):
        page.locator("[data-testid='privacy-confirm-btn']").click()
        when = page.locator("[data-testid='when-input']")
        expect(when).not_to_be_empty()


# ---------------------------------------------------------------------------
# Story 3.1 — Star chart rendered
# ---------------------------------------------------------------------------

class TestStarChartRendering:
    def test_star_chart_appears_after_submit(self, page: Page):
        page.locator("[data-testid='privacy-confirm-btn']").click()
        page.locator("[data-testid='address-input']").fill("Seoul, Korea")
        page.locator("[data-testid='when-input']").fill("2000-01-01 00:00")
        page.locator("[data-testid='submit-btn']").click()

        chart = page.locator("[data-testid='star-chart']")
        expect(chart).to_be_visible(timeout=15_000)

    def test_chart_contains_svg(self, page: Page):
        page.locator("[data-testid='privacy-confirm-btn']").click()
        page.locator("[data-testid='address-input']").fill("Seoul, Korea")
        page.locator("[data-testid='when-input']").fill("2000-01-01 00:00")
        page.locator("[data-testid='submit-btn']").click()
        page.wait_for_selector("[data-testid='star-chart']", timeout=15_000)

        svg = page.locator("[data-testid='star-chart'] svg")
        expect(svg).to_be_visible()


# ---------------------------------------------------------------------------
# Story 1.1 — Invalid address error
# ---------------------------------------------------------------------------

class TestGeocodeError:
    def test_invalid_address_shows_error(self, page: Page):
        page.locator("[data-testid='privacy-confirm-btn']").click()
        page.locator("[data-testid='address-input']").fill("asdfghjkl xyzzy qwerty")
        page.locator("[data-testid='when-input']").fill("2000-01-01 00:00")
        page.locator("[data-testid='submit-btn']").click()

        error = page.locator("[data-testid='error-message']")
        expect(error).to_be_visible(timeout=15_000)


# ---------------------------------------------------------------------------
# Story 5.1 — Language detection
# ---------------------------------------------------------------------------

class TestLanguageDetection:
    def test_korean_locale_shows_korean_ui(self, browser):
        ctx = browser.new_context(locale="ko-KR")
        page = ctx.new_page()
        page.goto(FRONTEND)
        page.wait_for_load_state("networkidle")

        submit = page.locator("[data-testid='submit-btn']")
        expect(submit).to_contain_text(re.compile(r"밤하늘보기|보기"))
        ctx.close()

    def test_english_locale_shows_english_ui(self, browser):
        ctx = browser.new_context(locale="en-US")
        page = ctx.new_page()
        page.goto(FRONTEND)
        page.wait_for_load_state("networkidle")

        submit = page.locator("[data-testid='submit-btn']")
        expect(submit).to_contain_text(re.compile(r"View Sky|View"))
        ctx.close()


# ---------------------------------------------------------------------------
# Story 4.3 — Narrative rate limiting (client-side)
# ---------------------------------------------------------------------------

class TestNarrativeRateLimit:
    def _submit_and_wait_for_chart(self, page: Page):
        page.locator("[data-testid='address-input']").fill("Seoul, Korea")
        page.locator("[data-testid='when-input']").fill("2000-01-01 00:00")
        page.locator("[data-testid='submit-btn']").click()
        page.wait_for_selector("[data-testid='star-chart']", timeout=15_000)

    def test_narrative_btn_disabled_after_3_uses(self, page: Page):
        page.locator("[data-testid='privacy-confirm-btn']").click()

        for _ in range(3):
            self._submit_and_wait_for_chart(page)
            narrative_btn = page.locator("[data-testid='narrative-btn']")
            if narrative_btn.is_visible():
                narrative_btn.click()
                page.wait_for_timeout(5_000)

        narrative_btn = page.locator("[data-testid='narrative-btn']")
        expect(narrative_btn).to_be_disabled()
