import re
from playwright.sync_api import Page

def open_packages_edit(page):
    try:
        try:
            page.locator('.gwOptionButton').first.click(timeout=1000)
            page.wait_for_timeout(400)
        except Exception:
            try:
                packages_label = page.locator('label').filter(has_text='Packages').first
                packages_label.click(timeout=1000)
                page.wait_for_timeout(400)
            except Exception as e:
                print(f"Failed to click Packages tab/button: {e}")
                return

        try:
            container = page.locator('.kgRow.kgFixedRow.kgRow--selected').first
            container.wait_for(state='visible', timeout=1000)
            container.click()
            page.wait_for_timeout(400)
        except Exception as e:
            print(f"Container row not found or clickable: {e}")

        try:
            action_button = page.get_by_role('button', name='')
            action_button.wait_for(state='visible', timeout=1000)
            action_button.click()
            page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Failed to click action button '': {e}")
            return

        try:
            edit_link = page.get_by_role('link', name='Edit Package', exact=True)
            edit_link.wait_for(state='visible', timeout=5000)
            edit_link.click()
            page.wait_for_timeout(1500)
            print("Navigated to Edit Package page successfully.")
        except Exception as e:
            print(f"Failed to click 'Edit Package' link: {e}")
            return

    except Exception as e:
        print(f"Unexpected error in open_packages_edit: {e}")


def fill_edit_package_and_complete(page:Page, shipment, *, do_print: bool = True, printer_name: str = "KUS-CW1-NYC - US_NYC_CANON"):
    try:
        # 1 Package Type
        page.locator('.gwSearchBox-description').first.click()
        page.keyboard.press("Control+a")
        page.keyboard.press("Delete")
        page.get_by_role('textbox', name='Package Type').fill('CTN')
        page.wait_for_timeout(1000)

        # 2 Gross Weight
        page.get_by_text('Gross Weight').first.click()
        weight_input = page.locator('.form-control.g-measure-magnitude').first
        weight_input.click()
        page.keyboard.press("Control+a")
        page.keyboard.press("Delete")
        weight_value = shipment.carton_weight or "0"
        # Extract just number part (e.g. '25' from '25 lb')
        weight_number = re.findall(r"[\d\.]+", weight_value)
        weight_number = weight_number[0] if weight_number else "0"
        weight_input.fill(weight_number)

        # Step 2: Click Gross Weight label and input again to activate unit field
        page.keyboard.press("Tab")
        page.keyboard.type("lb")

        # 3 Parse carton_dimensions
        dims = shipment.carton_dimensions or "0x0x0"
        dims = dims.lower().replace(" ", "").replace("×", "x").replace("X", "x")
        length, width, height = dims.split("x")

        # Length
        length_label = page.get_by_text('Booked Length').first
        length_input = length_label.locator('xpath=following::input[contains(@class,"g-measure-magnitude")]').first
        length_input.click()
        length_input.fill(length)

        # Width
        width_label = page.get_by_text('Booked Width').first
        width_input = width_label.locator('xpath=following::input[contains(@class,"g-measure-magnitude")]').first
        width_input.click()
        width_input.fill(width)

        # Height
        height_label = page.get_by_text('Booked Height').first
        height_input = height_label.locator('xpath=following::input[contains(@class,"g-measure-magnitude")]').first
        height_input.click()
        height_input.fill(height)


        # 7 Save and Complete
        page.get_by_role('button', name='Save', exact=True).click()
        page.wait_for_timeout(1000)
        

        # 8 Navigate to Documents and Deliver
        if do_print:
            try:
                #Open Documents dropdown menu
                page.get_by_role('button', name='Documents').click()
                # Click 'US'
                page.get_by_role('menuitem', name='US', exact=True).click()
                page.get_by_text('US', exact=True).click()
                #Select Receipt Instruction
                page.get_by_role('menuitem', name='Receipt Instruction - KUS').click()
                page.get_by_text('Receipt Instruction - KUS').click()
                page.wait_for_timeout(5000)
                #Printer dropdown select printer
                page.locator('.wtg-input').first.click()
                page.get_by_text('.wtg-input__content').first.click()
                page.get_by_role('textbox', name='Printer').click()
                #Select printer by name
                page.get_by_text(printer_name).click()
                #Deliver / Print doc
                #page.get_by_role('button', name='Deliver').click()
                #small wait
                page.wait_for_timeout(3500)
                print(f"[PRINT] 'Receipt Instruction - KUS' sent to '{printer_name}'.")
            except Exception as e:
                print(f"[PRINT] Failed to print 'Receipt Instruction - KUS': {e}'")


        #9 Complete
        page.get_by_role('button', name='Complete').click()
        page.wait_for_timeout(3000)
        
    except Exception as e:
        print(f"Error in fill_edit_package_and_complete: {e}")
