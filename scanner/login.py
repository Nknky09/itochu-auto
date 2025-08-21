import os, re
from playwright.sync_api import Page
from dotenv import load_dotenv
load_dotenv()
from .constants import (
    MOBILE_URL,
    DASHBOARD_TEXT,
    ALREADY_LOGGED_IN_TEXT,
    YES_BUTTON_NAME,
)
from .steps.common import wait_for_idle


def login_mobile_if_needed(page: Page):
    """Handle not-logged-in, already-logged-in, and modal collision cases."""
    try:
        if not page.url.startswith(MOBILE_URL):
            page.goto(MOBILE_URL)
    except Exception:
        page.goto(MOBILE_URL)

    wait_for_idle(page)

    # Handle 'already logged in elsewhere' style modal if it appears
    try:
        page.get_by_text(ALREADY_LOGGED_IN_TEXT).wait_for(timeout=3000)
        page.get_by_role("button", name=YES_BUTTON_NAME).click()
        wait_for_idle(page)
    except Exception:
        pass

    # Are we already logged in? Check dashboard marker
    try:
        page.get_by_text(DASHBOARD_TEXT).wait_for(timeout=3000)
        return
    except Exception:
        pass

    # Perform login using env vars
    user = os.getenv("CW1_USER")
    pw = os.getenv("CW1_PASS")
    if not user or not pw:
        raise RuntimeError("CW1_USER/CW1_PASS env vars not set")

    try:
        page.get_by_role("textbox", name="Username").wait_for(timeout=7000)
        page.get_by_role("textbox", name="Username").fill(user)
        page.get_by_role("textbox", name="Password").fill(pw)

        # Sometimes a modal appears instead of login button
        try:
            page.locator("div").filter(has_text=re.compile(r"^YesYesCancelNo$")).nth(1).click()
        except Exception:
            pass

        # Try robust click on Log In
        btn = page.get_by_role("button", name="Log In")
        try:
            btn.wait_for(timeout=5000)
            try:
                btn.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                btn.click(timeout=4000)
            except Exception:
                # Fallback to CSS text selector
                page.locator('button:has-text("Log In")').first.click(timeout=4000)
        except Exception:
            # Final fallback: press Enter on password field
            try:
                page.get_by_role("textbox", name="Password").press("Enter")
            except Exception:
                pass

        # If the Yes/Cancel/No confirmation appears after clicking login, accept it
        try:
            page.locator("div").filter(has_text=re.compile(r"^YesYesCancelNo$")).nth(1).click()
        except Exception:
            pass

        # Wait for login fields to disappear as a signal of successful navigation
        try:
            page.get_by_role("textbox", name="Username").wait_for(state="hidden", timeout=8000)
        except Exception:
            pass

        # As a secondary success signal, wait for a common post-login element if available
        try:
            page.locator(".v-icon").first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

        try:
            page.get_by_text(ALREADY_LOGGED_IN_TEXT).wait_for(timeout=3000)
            page.get_by_role("button", name=YES_BUTTON_NAME).click()
        except Exception:
            pass

        wait_for_idle(page)
    except Exception:
        try:
            page.get_by_text(DASHBOARD_TEXT).wait_for(timeout=4000)
        except Exception:
            page.screenshot(path="mobile_login_error.png")
            raise
