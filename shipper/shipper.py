from playwright.sync_api import sync_playwright
from .login import login_if_needed
from .receive_consignments import click_receive_consignments, get_highest_rcn_reference, click_new_receive_consignments

TEST_URL = "https://www-kiltst.wisegrid.net/Portals/TWD/Desktop#"

def run_shipper_flow():
  with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(TEST_URL)

    login_if_needed(page)
    click_receive_consignments(page)
    rcn_number = get_highest_rcn_reference(page)
    print("Next RCN Reference:", rcn_number)
    click_new_receive_consignments(page)

    browser.close()

if __name__ == "__main__":
  run_shipper_flow()