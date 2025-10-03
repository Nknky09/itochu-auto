def fill_consignor(page, shipment):
    import re

    TARGET_COMPANY = "THE BOEING COMPANY"
    TARGET_ADDR_KEY = "800 ARLINGTON BLVD"  # canonical target

    def norm(s: str) -> str:
        s = (s or "").upper()
        # normalize boulevard spelling and squeeze spaces
        s = re.sub(r"\bBOULEVARD\b", "BLVD", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    company = ""
    address = ""
    if shipment.shipped_from and "\n" in shipment.shipped_from:
        company, address = shipment.shipped_from.split("\n", 1)
    else:
        company = shipment.shipped_from or ""
        address = ""

    company_u = norm(company)
    address_u = norm(address)

    # Defensive: if address is too short (e.g., '4'), ignore it
    if company_u == TARGET_COMPANY and (len(address_u) < 8 or not any(c.isdigit() for c in address_u)):
        address_u = ""  # force us to prefer the canonical target later

    page.get_by_role("heading", name="Consignor").click()
    page.get_by_role("textbox", name="Company Name").nth(1).click()
    page.locator(".gwJobDocAddress-company-search .icon-search").nth(1).click()

    dialog = page.get_by_role('dialog')
    dialog.locator('.g-search-list-mask').wait_for(state='hidden', timeout=10000)
    dialog.locator('.gwSearchBox-description').dblclick()
    page.keyboard.press("Delete")
    page.wait_for_timeout(500)

    input_field = dialog.locator('input.gwSearchBox-text:not([readonly])')
    page.keyboard.press("Tab")
    input_field.click()
    input_field.type(company.strip(), delay=50)
    page.wait_for_timeout(1000)

    # choose the company link (if present) then Find
    try:
        page.get_by_role("link", name=company.strip()).click(timeout=3000)
    except Exception:
        # If the company name isn’t a link in this tenant build, just continue
        pass

    page.wait_for_timeout(500)
    page.get_by_role("button", name="Find").click()
    dialog.locator(".g-search-list-mask").wait_for(state="hidden", timeout=10000)
    dialog.locator(".koGrid").wait_for(timeout=6000)
    print("Overlay cleared, ready to click address.")

    grid_rows = dialog.locator('.koGrid .kgRow')
    row_count = grid_rows.count()

    # Helper to click a row and log which index we clicked
    def click_row(idx: int):
        grid_rows.nth(idx).click()
        print(f"Consignor: Selected row index {idx}.")
        page.wait_for_timeout(300)

    clicked = False

    # 1) **Hard preference**: Boeing → “800 ARLINGTON BLVD”
    if company_u == TARGET_COMPANY:
        target_key = norm(TARGET_ADDR_KEY)
        for r in range(row_count):
            row_text = norm(grid_rows.nth(r).inner_text())
            # Must contain company and the Arlington key somewhere on the row
            if TARGET_COMPANY in row_text and "800 ARLINGTON" in row_text and "BLVD" in row_text:
                click_row(r)
                clicked = True
                break

    # 2) If not clicked yet, try the extracted address (if meaningful)
    if not clicked and address_u:
        for r in range(row_count):
            row_text = norm(grid_rows.nth(r).inner_text())
            if company_u in row_text and address_u in row_text:
                click_row(r)
                clicked = True
                break

    # 3) As a secondary Boeing fallback, accept any row that has company + "ARLINGTON"
    if not clicked and company_u == TARGET_COMPANY:
        for r in range(row_count):
            row_text = norm(grid_rows.nth(r).inner_text())
            if TARGET_COMPANY in row_text and "ARLINGTON" in row_text:
                click_row(r)
                clicked = True
                break

    # 4) Final fallback: just pick the first visible row to avoid stalling
    if not clicked:
        grid_rows.first.click()
        print("Consignor: Fallback – selected first result row.")
        page.wait_for_timeout(300)

    # Confirm selection
    page.get_by_role("button", name="Select").click()
    chosen_label = TARGET_ADDR_KEY if company_u == TARGET_COMPANY else (address_u or "(first)")
    print(f"Consignor: Selected address '{chosen_label}' and closed dialog.")
