import datetime
import re
import time


def fill_new_shipment_form(page, shipment, rcn_number):
  
  # 1 RCN #
  page.get_by_role("textbox", name="RCN Reference").fill(str(f"{rcn_number} BOEING"))

  # 2 Transport Mode - Air Freight
  page.get_by_role("combobox").nth(1).click()
  page.get_by_role("listbox").get_by_text("Air Freight", exact=True).click()

  # 3 Service level - fill STD and select
  page.get_by_role("textbox", name="Service Level").click()
  page.get_by_role("textbox", name="Service Level").fill("STD")

  # 4 Expect Arrival - today's date
  today = datetime.datetime.today().strftime('%d-%b-%y %H:%M')

  page.get_by_role("textbox", name="Expected Arrival").click()
  page.get_by_role("textbox", name="Expected Arrival").fill(today)

  # 5 Booking Party - K Line
  page.get_by_role("heading", name="Booking Party").click()

  page.locator(".gwSearchBox.gwAddressSearchBox > .input-group > .input-group-addon > .icon-search").first.click()

  # Open dialog (you already have this)

  dialog = page.get_by_role("dialog")

  # Wait for overlay to clear
  dialog.locator(".g-search-list-mask").wait_for(state="hidden", timeout=10000)

  # Clear the existing org text
  dialog.locator(".gwSearchBox-description").first.dblclick()
  page.keyboard.press("Delete")
  page.wait_for_timeout(500)

  # Now fill org input (safe field)
  input_field = dialog.locator('input.gwSearchBox-text:not([readonly])')
  page.keyboard.press("Tab")
  input_field.click()
  input_field.type("KLINELUS001", delay=50)
  page.wait_for_timeout(1000)

  page.get_by_role("link", name='KLINELUS001 "K" LINE').click(timeout=5000)


  dialog.get_by_role("button", name="Find").click()

  #Wait for results grid to load
  dialog.locator(".koGrid").wait_for(timeout=6000)
  #Click on matching row
  dialog.get_by_text("145-68 228TH STREET, UNIT").first.click()
  #Click select to submit
  dialog.get_by_role("button", name="Select").click()

  page.wait_for_timeout(1000)
  

  # 6 Consigner - used shipped_from data - company
  company = ""
  address = ""
  if shipment.shipped_from and "\n" in shipment.shipped_from:
    company, address = shipment.shipped_from.split("\n", 1)
  else:
    company = shipment.shipped_from or ""
    address = ""

  page.get_by_role("heading", name="Consignor").click()

  page.get_by_role("textbox", name="Company Name").nth(1).click()
  page.locator(".gwJobDocAddress-company-search .icon-search").nth(1).click()

  dialog=page.get_by_role('dialog')

  dialog.locator('.g-search-list-mask').wait_for(state='hidden', timeout=2000)

  dialog.locator('.gwSearchBox-description').dblclick()
  page.keyboard.press("Delete")
  page.wait_for_timeout(500)

  #1 Set org filter
  input_field = dialog.locator('input.gwSearchBox-text:not([readonly])')
  page.keyboard.press("Tab")
  input_field.click()
  input_field.type(company.strip(), delay=50)
  page.wait_for_timeout(1000)

  page.get_by_role("link", name=company.strip()).click(timeout=3000)


  # Choose org code
  page.wait_for_timeout(2000)

  page.get_by_role("button", name="Find").click()

  # 2. Wait for loading mask to disappear
  dialog.locator(".g-search-list-mask").wait_for(state="hidden", timeout=10000)
  print("Overlay cleared, ready to click address.")
  #Wait for results
  dialog.locator(".koGrid").wait_for(timeout=6000)
  # use db address
  db_address = address.strip()

  grid_rows = dialog.locator('.koGrid .kgRow')
  row_count = grid_rows.count()
  clicked = False

  for r in range(row_count):
    cells = grid_rows.nth(r).locator('.kgCellText')
    cell_texts = [cells.nth(i).inner_text().strip().upper() for i in range(cells.count())]

    if any(company.strip().upper() in t for t in cell_texts) and any(db_address in t for t in cell_texts):
      cells.first.click()
      clicked = True
      break
  
  if not clicked:
    grid_cells = dialog.locator('.koGrid .kgCellText')
    for i in range(grid_cells.count()):
      if db_address in grid_cells.nth(i).inner_text().strip().upper():
        grid_cells.nth(i).click()
        clicked = True
        break
  
  if not clicked:
    grid_cells.first.click()
  
  page.wait_for_timeout(1000)

  
  # select to confirm
  page.get_by_role("button", name="Select").click()

  print(f"Consignor: Selected address '{db_address}' and close dialog.")

  
  # -- 7 Reference Numbers Section ----
  page.get_by_text("Reference Numbers").click()
  page.wait_for_timeout(500)

  # 1 Shipper Reference #
  add_reference_row(page, 'SHR', "Shipper Reference Number", f"{rcn_number} BOEING")

  # 2 Other (reference_no)
  add_reference_row(page, "OTH", "Other", shipment.reference_no)

  # 3 Other (order_no)
  add_reference_row(page, "OTH", "Other", shipment.order_no)

  # 4 Master Bill (carrier)
  add_reference_row(page, "MAB", "Master Bill", shipment.carrier)


  time.sleep(60)


  def add_reference_row(page, ref_code, ref_label, value):
    page.get_by_role("button", name="").nth(2).click()

    searchbox = page.locator('input.select2-search_field')
    searchbox.wait_for(timeout=2000)
    searchbox.fill(ref_code)
    page.wait_for_timeout(500)

    page.get_by_role("option").get_by_text(ref_label, exact=True).click()

    page.locator('input[title="Reference"]').last.wait_for(timeout=1000)
    page.locator('input[title="Reference"]').last.fill(value)
    page.wait_for_timeout(500)


