import re
from .selectors import RCN_REF_CELL, RCN_REF_HEADER, RECEIVE_CONSIGNMENTS_TITLE, NEW_RECEIVE_CONSIGNMENT_LINK

def click_receive_consignments(page):
  page.location("span").filter(has_text=re.compile(r"^Receive Consignments$")).click()
  page.wait_for_timeout(2000)

def get_highest_rcn_reference(page):
  page.wait_for_selector(RCN_REF_HEADER, timeout=10000)
  rcn_cells = page.locator(RCN_REF_CELL)
  rcn_numbers = []

  for cell in rcn_cells[:25]:
    text = cell.inner_text().strip()
    m = re.match(r"(\d{4}\s+\w+)", text)
    if m:
      rcn_numbers.append(int(m.group(1)))
  
  if rcn_numbers:
    highest = max(rcn_numbers)
    return highest + 1
  else:
    return None

def click_new_receive_consignments(page):
  page.get_by_role(NEW_RECEIVE_CONSIGNMENT_LINK).click()