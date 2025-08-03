import datetime
import time
import re

from shipper.forms.booking_party import fill_booking_party
from shipper.forms.consignor import fill_consignor
from shipper.forms.references import fill_references
from shipper.forms.packages import open_packages_edit, fill_edit_package_and_complete


def fill_new_shipment_form(page, shipment, rcn_number):
    # --- 1 RCN ---
    page.get_by_role("textbox", name="RCN Reference").fill(str(f"{rcn_number} BOEING"))

    # --- 2 Transport Mode - Air Freight ---
    page.get_by_role("combobox").nth(1).click()
    page.get_by_role("listbox").get_by_text("Air Freight", exact=True).click()

    # --- 3 Service level - fill STD and select ---
    page.get_by_role("textbox", name="Service Level").click()
    page.get_by_role("textbox", name="Service Level").fill("STD")

    # --- 4 Expect Arrival - today's date ---
    today = datetime.datetime.today().strftime('%d-%b-%y %H:%M')
    page.get_by_role("textbox", name="Expected Arrival").click()
    page.get_by_role("textbox", name="Expected Arrival").fill(today)

    # --- 5 Booking Party ---
    fill_booking_party(page)

    # --- 6 Consignor ---
    fill_consignor(page, shipment)

    # --- 7 References ---
    fill_references(page, shipment, rcn_number)

    # --- 8 Packages ---
    open_packages_edit(page)
    fill_edit_package_and_complete(page, shipment)

    time.sleep(2)
