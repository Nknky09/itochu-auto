import tabula   
import pandas as pd
import re
import fitz

def extract_pdf_data(pdf_path):
    data = {
        "reference_no": None,
        "order_no": None,
        "shipped_from": None,
        "carton_dimensions": None,
        "carton_weight": None,
        "tracking_number": None,
        "carrier": "UNKNOWN"
    }

    # --- Extract table data from page 1 using tabula ---
    try:
        tables = tabula.read_pdf(pdf_path, pages=1, multiple_tables=True, lattice=True)
        for df in tables:
            for row in df.values.tolist():
                row_text = ' '.join(str(cell) for cell in row if str(cell).strip()).upper()
                
                if "ORDER NO" in row_text and not data["order_no"]:
                    after_tag_match = re.search(r"ORDER NO[^\w]*([A-Z0-9]{6,10})", row_text)
                    if after_tag_match:
                        data["order_no"] = after_tag_match.group(1)
    except Exception as e:
        print(f"Tabula PDF table extraction failed: {e}")
    
    try: 
        with fitz.open(pdf_path) as doc:
            # --- Reference No and all-fields full text ---
            full_text = ""
            for page in doc:
                full_text += page.get_text().upper()

            match = re.search(r"PHCDT[-\s]?\d{6,9}", full_text)
            if match:
                data["reference_no"] = match.group(0).replace(' ', '').upper()

            # Shipped From extraction (page 2 only, new logic)
            page2_text = doc[1].get_text()
            lines = page2_text.split('\n')

            address_lines = []
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith("THE BOEING CO"):
                    # Split first line to remove "C/O GXO LOGISTICS"
                    main_company = line.split("C/O")[0].strip()
                    address_lines.append(main_company)
                    # Next lines: look for street address (should contain numbers)
                    for j in range(i+1, min(i+4, len(lines))):
                        candidate = lines[j].strip()
                        # Add the first line containing digits (street address)
                        if any(char.isdigit() for char in candidate):
                            address_lines.append(candidate)
                            break  # Only take the first address line
                    break  # Only first occurrence

            if address_lines:
                data["shipped_from"] = "\n".join(address_lines).strip()


            # --- Carton Dimensions ---
            match = re.search(r"(\d{1,3}(\.\d{1,2})?\s*[Xx×]\s*\d{1,3}(\.\d{1,2})?\s*[Xx×]\s*\d{1,3}(\.\d{1,2})?)", full_text)
            if match:
                data["carton_dimensions"] = match.group(0).replace(' ', '').upper()

            # --- Carton Weight ---
            page1_text = doc[0].get_text()

            # Find 'CARTON <dims> ... <weight> (lbs)'
            carton_pattern = re.compile(
                r"CARTON\s+(\d{1,3}(?:\.\d{1,2})?\s*[Xx×]\s*\d{1,3}(?:\.\d{1,2})?\s*[Xx×]\s*\d{1,3}(?:\.\d{1,2})?).*?(\d{1,4}(?:\.\d{1,2})?)\s*(?:\(?LBS?\)?|\(LBS\))",
                re.IGNORECASE
            )
            carton_match = carton_pattern.search(page1_text)
            if carton_match:
                weight = carton_match.group(2)
                data["carton_weight"] = f"{weight} LB"


            # --- Tracking Number ---
            page2_text = doc[1].get_text()
            lines = page2_text.split('\n')

            tracking_number = None
            for i, line in enumerate(lines):
                if 'TRK#' in line.upper():
                    # Look ahead for next non-empty line
                    for j in range(i+1, len(lines)):
                        next_line = lines[j].strip()
                        if next_line and re.match(r"(\d{4}\s\d{4}\s\d{4})", next_line):
                            tracking_number = next_line
                            break
                    break

            if tracking_number:
                data["tracking_number"] = tracking_number
            

            # Carrier
            carrier = "UNDEFINED"
            if data["tracking_number"]:
                num = data["tracking_number"].replace(" ", "")
                if re.match(r"^\d{12}$", num):
                    if re.match(r"^\d{4}\s\d{4}\s\d{4}$", data["tracking_number"]):
                        carrier = "FEDEX"
                elif num.startswith("1Z"):
                    carrier = "UPS"
            data["carrier"] = carrier


    except Exception as e:
        print(f"PyMuPDF text extraction failed: {e}")

    return data
