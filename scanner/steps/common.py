from playwright.sync_api import Page
from ..constants import MASK_SELECTOR, TOAST_SELECTOR
import re

def wait_for_idle(page: Page, timeout: int = 8000):
  try:
    page.locator(MASK_SELECTOR).first.wait_for(state="hidden", timeout=timeout)
  except Exception:
    pass
  try:
    page.wait_for_load_state("networkidle", timeout=timeout)
  except Exception:
    pass

def click_by_text(page: Page, text: str, exact: bool = True, timeout: int = 4000):
    loc = page.get_by_text(text, exact=exact)
    loc.wait_for(timeout=timeout)
    loc.click()

def fill_textbox_by_role_name(page: Page, name: str, value: str, timeout: int = 4000):
  tb = page.get_by_role("textbox", name=name)
  tb.wait_for(timeout=timeout)
  tb.click()
  page.keyboard.press("Control+a")
  page.keyboard.press("Delete")
  tb.fill(value)

def safe_click_button(page: Page, name: str, timeout: int = 4000):
  btn = page.get_by_role("button", name=name)
  btn.wait_for(timeout=timeout)
  btn.click()

def any_visible(page: Page, selectors: list[str], timeout: int = 3000) -> bool:
  for css in selectors:
    try:
      if page.locator(css).first.is_visible():
        return True
    except Exception:
      pass
  page.wait_for_timeout(250)
  for css in selectors:
    try:
      if page.locator(css).first.is_visible():
        return True
    except Exception:
      pass
  return False

