def add_reference_row(page, ref_code, ref_label, value):
    page.get_by_role("button", name="").nth(2).click()
    page.wait_for_timeout(300)

    searchbox = page.locator('input.select2-search__field')
    searchbox.wait_for(timeout=3000)
    searchbox.fill(ref_code)
    page.wait_for_timeout(200)
    page.get_by_role("option").get_by_text(ref_label, exact=True).click()

    table_headers = page.locator('text=Reference Numbers')
    ref_table = table_headers.nth(0).locator('xpath=following::div[contains(@class,"koGrid")]').first
    table_rows = ref_table.locator('.kgRow.kgNonFixedRow:not(.add-row)')
    table_rows.first.wait_for(timeout=3000)

    target_row = table_rows.last
    ref_cell = target_row.locator('div.kgCell.col1')
    ref_input = ref_cell.locator('input[type="text"].form-control.g-widget-border')
    ref_input.wait_for(timeout=3000)
    ref_input.fill(value)
    page.wait_for_timeout(200)
    print(f"Filled reference value '{value}' in new row")


def fill_references(page, shipment, rcn_number):
    try:
        page.locator('.gwOptionButtonGrid__wrap > div:nth-child(4)').click(timeout=2000)
        page.wait_for_timeout(400)
    except Exception:
        pass
    try:
        references_label = page.get_by_text('References', exact=True)
        references_label.wait_for(timeout=3000)
        if not references_label.is_visible():
            references_label.click()
            page.wait_for_timeout(400)
    except Exception:
        pass
    try:
        ref_numbers_label = page.get_by_text("Order References")
        ref_numbers_label.wait_for(state="visible", timeout=10000)
        ref_numbers_label.click()
        page.wait_for_timeout(500)
    except Exception:
        try:
            alt_ref_numbers_label = page.get_by_text("Order References (0)")
            alt_ref_numbers_label.wait_for(state="visible", timeout=5000)
            alt_ref_numbers_label.click()
            page.wait_for_timeout(500)
        except Exception:
            pass

    add_reference_row(page, "SHR", "Shipper Reference Number", f"{rcn_number} BOEING")
    add_reference_row(page, "OTH", "Other", shipment.reference_no)
    add_reference_row(page, "OTH", "Other", shipment.order_no)
    add_reference_row(page, "MAB", "Master Bill", f"{shipment.carrier} {shipment.tracking_number}")
