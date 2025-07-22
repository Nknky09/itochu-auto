import re
from .selectors import RCN_REF_CELL, RCN_REF_HEADER, RECEIVE_CONSIGNMENTS_TITLE, NEW_RECEIVE_CONSIGNMENT_LINK
import time

def click_receive_consignments(page):

  try:
    page.get_by_text(re.compile(r"Today.*Receive Consignments.*Total Open")).click()
  except Exception:
    page.get_by_text(re.compile(r"Receive Consignments")).nth(0).click()  
  page.wait_for_selector(RCN_REF_HEADER, timeout=10000)



def get_highest_rcn_reference(page):
    page.wait_for_selector(".koGrid", timeout=20000)

    time.sleep(1)

    rcn_cells = page.locator('.kgCell.col1.kgCellText')
    count = rcn_cells.count()
    print(f'Found {count} RCN Reference cells.')

    rcn_numbers = []
    for i in range(min(count, 25)):
       cell_text = rcn_cells.nth(i).inner_text().strip()
       print(f"Row {i} cell: '{cell_text}'")
       m = re.match(r"^(\d{4})\s+\w+", cell_text)
       if m:
          rcn_numbers.append(int(m.group(1)))

    if rcn_numbers:
        highest = max(rcn_numbers)
        print(f"Extracted RCN numbers: {rcn_numbers}")
        return highest + 1
    else:
        print("No RCN values found in first 25 rows.")
        return None


def click_new_receive_consignments(page):
  page.get_by_role("link", name="New Receive Consignment", exact=True).click()

def fill_new_rcn_reference(page, rcn_number):
   page.get_by_role("textbox", name="RCN Reference").fill(str(rcn_number))