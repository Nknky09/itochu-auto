from playwright.sync_api import sync_playwright
from .login import login_mobile_if_needed
from .constants import MOBILE_URL
from shipper.utils import get_latest_shipment
from .steps.first_page import start_new_scan, fill_first_page
from .steps.unload import click_unload_icon

DEVICE_EMULATION = {
    "user_agent": "Mozilla/5.0 (Linux; Android 12; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Mobile Safari/537.36",
    "viewport": {"width": 430, "height": 932},
    "is_mobile": True,
    "has_touch": True,
}

def run_scanner_flow(headless: bool = False):
  shipment = get_latest_shipment()
  if not shipment:
    print("No shipments available in DB.")
    return None
  
  with sync_playwright() as p:
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context(
      user_agent=DEVICE_EMULATION["user_agent"],
      viewport=DEVICE_EMULATION["viewport"],
      is_mobile=DEVICE_EMULATION["is_mobile"],
      has_touch=DEVICE_EMULATION["has_touch"],
    )

    page = context.new_page()

    page.goto(MOBILE_URL)
    login_mobile_if_needed(page)

    start_new_scan(page)
    click_unload_icon(page)

    return shipment.id

if __name__ == "__main__":
  run_scanner_flow(headless=False)
