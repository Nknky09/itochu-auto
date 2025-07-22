from playwright.sync_api import sync_playwright
from shipper.utils import get_unprocessed_shipments, mark_shipment_processed
from .login import login_if_needed
from .receive_consignments import click_receive_consignments, fill_new_rcn_reference, get_highest_rcn_reference, click_new_receive_consignments

TEST_URL = "https://www-kiltst.wisegrid.net/Portals/TWD/Desktop#"

def run_shipper_flow():

  shipments = get_unprocessed_shipments()
  if not shipments:
    print("No unprocessed shipments in database.")
    return

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(TEST_URL)
    login_if_needed(page)

    for shipment in shipments:
      click_receive_consignments(page)
      rcn_number = get_highest_rcn_reference(page)
      click_new_receive_consignments(page)

      fill_new_rcn_reference(page, shipment, rcn_number)

      mark_shipment_processed(shipment.id)
    
  browser.close()

if __name__ == "__main__":
  run_shipper_flow()