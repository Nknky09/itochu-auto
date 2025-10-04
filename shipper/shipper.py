from playwright.sync_api import sync_playwright
from shipper.utils import get_latest_shipment
from .login import login_if_needed
from .receive_consignments import click_receive_consignments, get_highest_rcn_reference, click_new_receive_consignments
from .fill_form import fill_new_shipment_form

TEST_URL = "https://www-kiltst.wisegrid.net/Portals/TWD/Desktop#"

def run_shipper_flow():

  shipment = get_latest_shipment()
  if not shipment:
    print("No unprocessed shipments in database.")
    return None, None

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(TEST_URL)
    login_if_needed(page)

    click_receive_consignments(page)
    rcn_number = get_highest_rcn_reference(page)
    click_new_receive_consignments(page)

    rc_num = fill_new_shipment_form(page, shipment, rcn_number)      

    return rcn_number, rc_num

if __name__ == "__main__":
  run_shipper_flow()