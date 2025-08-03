def fill_consignor(page, shipment):
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

    dialog = page.get_by_role('dialog')
    dialog.locator('.g-search-list-mask').wait_for(state='hidden', timeout=2000)
    dialog.locator('.gwSearchBox-description').dblclick()
    page.keyboard.press("Delete")
    page.wait_for_timeout(500)

    input_field = dialog.locator('input.gwSearchBox-text:not([readonly])')
    page.keyboard.press("Tab")
    input_field.click()
    input_field.type(company.strip(), delay=50)
    page.wait_for_timeout(1000)

    page.get_by_role("link", name=company.strip()).click(timeout=3000)
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Find").click()
    dialog.locator(".g-search-list-mask").wait_for(state="hidden", timeout=10000)
    print("Overlay cleared, ready to click address.")
    dialog.locator(".koGrid").wait_for(timeout=6000)

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
    page.get_by_role("button", name="Select").click()
    print(f"Consignor: Selected address '{db_address}' and close dialog.")
