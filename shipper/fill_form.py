import datetime

def fill_new_shipment_form(page, shipment, rcn_number):
  
  # 1 RCN #
  page.get_by_role("textbox", name="RCN Reference").fill(str(rcn_number))

  # 2 Transport Mode - Air Freight
  page.get_by_role("combobox").nth(1).click()
  page.get_by_role("listbox").get_by_text("Air Freight", exact=True).click()

  # 3 Service level - fill STD and select
  page.get_by_role("textbox", name="Service Level").click()
  page.get_by_role("textbox", name="Service Level").fill("STD")
  page.get_by_role("link", name="STD Standard").click()

  # 4 Expect Arrival - today's date
  page.locator(
        "#d9d0f211-e5cf-40cf-979f-13714f483d78_0_13 > .gwDatePicker > .input-group-addon > .icon-calendar"
    ).click()
  page.get_by_role("button", name="Now").click()

  # 5 Booking Party - K Line
  page.get_by_role("heading", name="Booking Party").click()
  page.locator(".gwSearchBox.gwAddressSearchBox > label").first.click()
  page.get_by_role("textbox", name="Company Name").first.fill("KLINELUS001")
  page.get_by_role("link", name='"K" LINE LOGISTICS (U.S.A.) INC. (KLINELUS001) 145-68 228TH STREET, UNIT 145-68').click()

  # 6 Consigner - used shipped_from data - company
