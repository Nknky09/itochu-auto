def fill_booking_party(page):
    page.get_by_role("heading", name="Booking Party").click()
    page.locator(".gwSearchBox.gwAddressSearchBox > .input-group > .input-group-addon > .icon-search").first.click()

    dialog = page.get_by_role("dialog")
    dialog.locator(".g-search-list-mask").wait_for(state="hidden", timeout=10000)
    dialog.locator(".gwSearchBox-description").first.dblclick()
    page.keyboard.press("Delete")
    page.wait_for_timeout(500)

    input_field = dialog.locator('input.gwSearchBox-text:not([readonly])')
    page.keyboard.press("Tab")
    input_field.click()
    input_field.type("KLINELUS001", delay=50)
    page.wait_for_timeout(1000)

    page.get_by_role("link", name='KLINELUS001 "K" LINE').click(timeout=5000)
    dialog.get_by_role("button", name="Find").click()
    dialog.locator(".koGrid").wait_for(timeout=6000)
    dialog.get_by_text("145-68 228TH STREET, UNIT").first.click()
    dialog.get_by_role("button", name="Select").click()
    page.wait_for_timeout(1000)
