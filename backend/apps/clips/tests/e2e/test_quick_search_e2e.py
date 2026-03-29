from __future__ import annotations

import time
import unittest
from collections.abc import Callable
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag

try:
    from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ModuleNotFoundError:
    PLAYWRIGHT_AVAILABLE = False

from apps.clips.models import Clip, Label


@tag("e2e")
@unittest.skipUnless(
    PLAYWRIGHT_AVAILABLE,
    "Playwright is not installed. Install backend dev dependencies to run e2e tests.",
)
class QuickSearchE2ETests(StaticLiveServerTestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="quick-search-e2e@example.com",
            username="quick-search-e2e@example.com",
            password="Password123!",
        )

        matching_label = Label.objects.create(user=self.user, name="orionlabel-fixture")

        matching_clip = Clip.objects.create(
            user=self.user,
            title="Orion clip fixture",
            url="https://example.com/orion-fixture",
            domain="example.com",
            raw_content="Orion fixture content for quick search",
            normalized_text="orion fixture content for quick search",
        )
        matching_clip.labels.add(matching_label)

        Clip.objects.create(
            user=self.user,
            title="Unrelated clip fixture",
            url="https://example.com/unrelated",
            domain="example.com",
            raw_content="Completely unrelated content",
            normalized_text="completely unrelated content",
        )

    @staticmethod
    def _wait_until(
        predicate: Callable[[], bool],
        *,
        timeout_seconds: float,
        message: str,
        interval_seconds: float = 0.05,
    ) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(interval_seconds)
        raise AssertionError(message)

    def _login(self, page: Page) -> None:
        page.goto(
            f"{self.live_server_url}/accounts/login/", wait_until="domcontentloaded"
        )
        page.fill("#id_username", self.user.email)
        page.fill("#id_password", "Password123!")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{self.live_server_url}/clips/", timeout=15_000)

    def test_quick_search_requests_and_results_render_for_clips_and_labels(
        self,
    ) -> None:
        with sync_playwright() as playwright:
            try:
                browser: Browser = playwright.chromium.launch(
                    channel="chromium",
                    headless=True,
                )
            except Exception:
                browser = playwright.chromium.launch(headless=True)
            context: BrowserContext = browser.new_context()
            page: Page = context.new_page()
            try:
                quick_search_requests: list[str] = []

                def capture_request(request: Any) -> None:
                    if "/api/clips/quick-search/" in request.url:
                        quick_search_requests.append(request.url)

                page.on("request", capture_request)

                self._login(page)
                page.wait_for_function(
                    """
                    () => {
                      const root = document.querySelector(
                        '[data-component="global-auth-quick-search"]'
                      )
                      return Boolean(
                        root &&
                          root.getAttribute("data-controller") &&
                          window.ClippyBackendStimulus
                      )
                    }
                    """,
                    timeout=10_000,
                )
                search_input = page.locator("#quick-search-input")
                search_input.wait_for(state="visible", timeout=10_000)

                quick_search_requests.clear()
                search_input.fill("or")
                page.wait_for_timeout(500)
                self.assertEqual(
                    quick_search_requests,
                    [],
                    "Quick search should not issue a backend request for fewer than 3 characters.",
                )

                quick_search_requests.clear()
                with page.expect_request(
                    lambda request: "/api/clips/quick-search/" in request.url,
                    timeout=10_000,
                ):
                    search_input.fill("orion")

                panel = page.locator("#quick-search-panel")
                panel.wait_for(state="visible", timeout=10_000)

                results = page.locator("#quick-search-results")
                results.locator("text=Orion clip fixture").first.wait_for(
                    state="visible",
                    timeout=10_000,
                )
                results.locator("text=orionlabel-fixture").first.wait_for(
                    state="visible",
                    timeout=10_000,
                )
            finally:
                context.close()
                browser.close()

    def test_clear_all_clears_label_and_url_filters_with_javascript_enabled(
        self,
    ) -> None:
        with sync_playwright() as playwright:
            try:
                browser: Browser = playwright.chromium.launch(
                    channel="chromium",
                    headless=True,
                )
            except Exception:
                browser = playwright.chromium.launch(headless=True)
            context: BrowserContext = browser.new_context()
            page: Page = context.new_page()
            try:
                self._login(page)
                page.wait_for_function(
                    "() => typeof window.ClipsListLabelFilters !== 'undefined'",
                    timeout=10_000,
                )

                page.goto(
                    (
                        f"{self.live_server_url}/clips/"
                        "?label=orionlabel-fixture"
                        "&url=https%3A%2F%2Fexample.com%2Forion-fixture"
                        "&panel=expanded"
                    ),
                    wait_until="domcontentloaded",
                )
                page.wait_for_function(
                    "() => typeof window.ClipsListLabelFilters !== 'undefined'",
                    timeout=10_000,
                )

                clear_all_button = page.locator(
                    '[data-action="clear-label-filters"]'
                ).first
                clear_all_button.wait_for(state="visible", timeout=10_000)
                clear_all_button.click()

                page.wait_for_url(
                    f"{self.live_server_url}/clips/?panel=expanded",
                    timeout=10_000,
                )
                self.assertEqual(
                    page.url,
                    f"{self.live_server_url}/clips/?panel=expanded",
                )
            finally:
                context.close()
                browser.close()

    def test_drawer_label_toggle_updates_query_with_multiple_filter_roots_present(
        self,
    ) -> None:
        with sync_playwright() as playwright:
            try:
                browser: Browser = playwright.chromium.launch(
                    channel="chromium",
                    headless=True,
                )
            except Exception:
                browser = playwright.chromium.launch(headless=True)
            context: BrowserContext = browser.new_context(
                viewport={"width": 390, "height": 844}
            )
            page: Page = context.new_page()
            try:
                self._login(page)
                page.wait_for_function(
                    "() => typeof window.ClipsListLabelFilters !== 'undefined'",
                    timeout=10_000,
                )

                drawer_trigger = page.locator("[data-filter-drawer-trigger]").first
                drawer_trigger.wait_for(state="visible", timeout=10_000)
                drawer_trigger.click()
                page.wait_for_selector(
                    '[data-component="filter-drawer"][aria-hidden="false"]',
                    timeout=10_000,
                )

                drawer_option = page.locator(
                    '[data-component="filter-drawer"] '
                    '[data-label-toggle][data-target-list="drawer"]'
                    '[data-label-slug="orionlabel-fixture"]'
                ).first
                drawer_option.wait_for(state="visible", timeout=10_000)
                drawer_option.click()

                page.wait_for_url(
                    (
                        f"{self.live_server_url}/clips/"
                        "?panel=open&label=orionlabel-fixture"
                    ),
                    timeout=10_000,
                )
                page.wait_for_function(
                    "() => typeof window.ClipsListLabelFilters !== 'undefined'",
                    timeout=10_000,
                )

                self.assertEqual(page.locator("[data-selected-label-pill]").count(), 1)
                self.assertEqual(
                    page.locator(
                        '[data-component="filter-drawer"] '
                        '[data-label-toggle][data-target-list="drawer"]'
                        '[data-label-slug="orionlabel-fixture"]'
                        '[data-label-selected="true"]'
                    ).count(),
                    1,
                )
                self.assertEqual(
                    page.locator(
                        '[data-component="filter-sidebar"] '
                        '[data-label-toggle][data-target-list="sidebar"]'
                        '[data-label-slug="orionlabel-fixture"]'
                        '[data-label-selected="true"]'
                    ).count(),
                    1,
                )
            finally:
                context.close()
                browser.close()
