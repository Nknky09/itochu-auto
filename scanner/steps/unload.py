from playwright.sync_api import Page
from .common import wait_for_idle

def click_unload_icon(page: Page):
    """On the second page, click the UNLOAD control via its icon (.v-icon)."""
    wait_for_idle(page)
    try:
        page.locator(".v-icon").first.wait_for(state="visible", timeout=7000)
        page.locator(".v-icon").first.click()
    except Exception:
        page.screenshot(path="mobile_unload_icon_timeout.png")
        raise
    wait_for_idle(page)
    page.locator(".v-icon").first.click()
    wait_for_idle(page)