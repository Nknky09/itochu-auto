import re
import io
from typing import Optional

import fitz
import tabula
import pandas as pd

# ---------------------- OCR (optional but recommended) ----------------------
_OCR_AVAILABLE = False
_OCR_REASON = "pytesseract not imported"
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    from PIL import Image

    try:
        # If Tesseract isn't on PATH, uncomment and set the path:
        # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        _ = pytesseract.get_tesseract_version()
        _OCR_AVAILABLE = True
        _OCR_REASON = "ok"
    except Exception as e:
        _OCR_AVAILABLE = False
        _OCR_REASON = f"Tesseract binary not found: {e}"
except Exception as e:
    _OCR_AVAILABLE = False
    _OCR_REASON = f"Import error: {e}"

# ---------------------- Core Patterns ----------------------
PH_REF_PATTERN = r"(PHCDT|PHBBT)[-\s]?\d{6,9}"
DIM_PATTERN = r"(\d{1,3}(?:\.\d{1,2})?\s*[Xx×]\s*\d{1,3}(?:\.\d{1,2})?\s*[Xx×]\s*\d{1,3}(?:\.\d{1,2})?)"
WEIGHT_PATTERN = r"CARTON\s+\d{1,3}(?:\.\d{1,2})?\s*[Xx×]\s*\d{1,3}(?:\.\d{1,2})?\s*[Xx×]\s*\d{1,3}(?:\.\d{1,2})?.*?(\d{1,4}(?:\.\d{1,2})?)\s*(?:\(?LBS?\)?|\(LBS\))"

ORDER_LABELS = [
    r"ORDER\s*NO", r"ORDER\s*#", r"ORDER\s*NUMBER",
    r"CUSTOMER\s*ORDER", r"CUST\s*PO", r"PO\s*#", r"PURCHASE\s*ORDER"
]
PHCDT_ORDER_PATTERN = r"\b8H\d{4}\b"                 # e.g., 8H2795
PHBBT_ORDER_PATTERN = r"\b[A-Z0-9]{6}-8H\d{4}\b"     # e.g., 507K20-8H3331
ORDERISH_TOKEN = r"\b([A-Z0-9][A-Z0-9\-_]{5,23})\b"

# UPS & FedEx
UPS_CANONICAL_LEN = 18  # "1Z" + 16 alnum
FEDEX_NUMERIC_PATTERN = r"\b(\d{12}|\d{15}|\d{20})\b"

# ---------------------- Utils ----------------------
def _u(s: str) -> str:
    return (s or "").upper()

def _clean(s: str) -> str:
    return (s or "").strip()

def _filename(pdf_path: str) -> str:
    return pdf_path.replace("\\", "/").split("/")[-1]

def _finditer_ignorecase(hay: str, needle: str):
    return re.finditer(re.escape(needle.upper()), hay, flags=re.IGNORECASE)

# ---------------------- Boeing address block ----------------------
def _extract_boeing_block_from_page_text(page_text: str) -> str:
    lines = [ln.strip() for ln in page_text.split("\n")]
    for i, raw in enumerate(lines):
        up = raw.strip().upper()
        if up.startswith("THE BOEING CO"):
            company = raw.split("C/O")[0].strip()
            addr = ""
            for j in range(i + 1, min(i + 7, len(lines))):
                cand = lines[j].strip()
                if cand and any(ch.isdigit() for ch in cand):
                    addr = cand
                    break
            if not addr:
                for j in range(i + 1, min(i + 7, len(lines))):
                    cand = lines[j].strip()
                    if cand:
                        addr = cand
                        break
            if company:
                return f"{company}\n{addr}".strip()
    return ""

# ---------------------- Tracking helpers (UPS/FedEx + OCR) ----------------------
def _normalize_ups(s: str) -> str:
    """Uppercase and strip everything except 0-9A-Z (so '1Z J22 141 03 1047 4033' -> '1ZJ221410310474033')."""
    return re.sub(r"[^0-9A-Z]", "", _u(s))

def _format_ups_readable(compact: str) -> str:
    """Keep compact to be safest for web inputs; change here if you want grouping."""
    return compact

def _format_fedex12_readable(d12: str) -> str:
    return f"{d12[0:4]} {d12[4:8]} {d12[8:12]}"

def _parse_tracking_candidate(s: str) -> Optional[str]:
    """
    Try UPS first, then FedEx. Accept spaces/hyphens/newlines in UPS, normalize and validate.
    """
    su = _u(s)

    # UPS: tolerate whitespace/hyphens after 1Z and up to 50 chars window
    if "1Z" in su:
        m = re.search(r"1Z[\s0-9A-Z\-]{8,50}", su)
        if m:
            compact = _normalize_ups(m.group(0))
            if compact.startswith("1Z") and len(compact) == UPS_CANONICAL_LEN:
                return _format_ups_readable(compact)

    # FedEx numeric (12/15/20)
    mfx = re.search(FEDEX_NUMERIC_PATTERN, su)
    if mfx:
        rawn = mfx.group(1)
        if len(rawn) == 12:
            return _format_fedex12_readable(rawn)
        return rawn

    # Original spaced 4-4-4 pattern
    m444 = re.search(r"\b(\d{4}\s\d{4}\s\d{4})\b", su)
    if m444:
        return m444.group(1)

    return None

def _ocr_page_for_tracking(doc, page_index: int) -> str:
    """Render page to image, OCR it, and run the same parsing heuristics."""
    if not _OCR_AVAILABLE:
        return ""
    try:
        page = doc[page_index]
        # Render at higher DPI for better OCR (zoom x2)
        mat = fitz.Matrix(2, 2)
        pm = page.get_pixmap(matrix=mat, alpha=False)
        from PIL import Image  # ensure PIL is present even if import moved
        img = Image.open(io.BytesIO(pm.tobytes("png")))
        text = pytesseract.image_to_string(img)
    except Exception as e:
        print(f"[extractor] OCR failed on page {page_index+1}: {e}")
        return ""

    lines = [ln.rstrip() for ln in text.split("\n") if ln.strip()]

    # Label-driven search first (the docs use 'TRACKING #:' on labels)  :contentReference[oaicite:2]{index=2}
    label_regex = re.compile(r"(UPS\s+GROUND|TRACKING\s*#?|TRK#)", re.IGNORECASE)
    for i, line in enumerate(lines):
        if not label_regex.search(line):
            continue

        # same line after ':' or '#'
        same_line = re.split(r"[:#]", line, maxsplit=1)
        if len(same_line) > 1:
            candidate = same_line[1].strip()
            trk = _parse_tracking_candidate(candidate)
            if trk:
                return trk

        # next 2 lines
        for j in range(i + 1, min(i + 4, len(lines))):
            nxt = lines[j].strip()
            trk = _parse_tracking_candidate(nxt)
            if trk:
                return trk
            if j + 1 < len(lines):
                nxt2 = (nxt + " " + lines[j + 1].strip()).strip()
                trk = _parse_tracking_candidate(nxt2)
                if trk:
                    return trk

    # Anywhere on the OCR page
    page_text_u = _u(" ".join(lines))
    for m in re.finditer(r"1Z[\s0-9A-Z\-]{8,50}", page_text_u):
        compact = _normalize_ups(m.group(0))
        if compact.startswith("1Z") and len(compact) == UPS_CANONICAL_LEN:
            return _format_ups_readable(compact)

    mfx = re.search(FEDEX_NUMERIC_PATTERN, page_text_u)
    if mfx:
        rawn = mfx.group(1)
        if len(rawn) == 12:
            return _format_fedex12_readable(rawn)
        return rawn

    m444 = re.search(r"\b(\d{4}\s\d{4}\s\d{4})\b", page_text_u)
    if m444:
        return m444.group(1)

    return ""

def _extract_tracking_from_doc(doc) -> str:
    """
    A) TEXT path on any page: 'TRACKING', 'TRACKING #', or 'TRK#' (same line or next line or split).
    B) Whole-doc TEXT fallback: UPS 1Z (with spaces/hyphens) or FedEx numeric (12/15/20).
    C) OCR fallback: page images (p1–2 first, then others).
    """
    label_regex = re.compile(r"(TRACKING\s*#?|TRK#)", re.IGNORECASE)

    # ----- A: label-driven, text-based -----
    for p in range(len(doc)):
        raw = doc[p].get_text()
        lines = [ln.rstrip() for ln in raw.split("\n")]

        for i, line in enumerate(lines):
            if not label_regex.search(line):
                continue

            # same line after ':' or '#'
            same_line = re.split(r"[:#]", line, maxsplit=1)
            if len(same_line) > 1:
                candidate = same_line[1].strip()
                trk = _parse_tracking_candidate(candidate)
                if trk:
                    return trk

            # next non-empty lines
            for j in range(i + 1, min(i + 4, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                trk = _parse_tracking_candidate(nxt)
                if trk:
                    return trk
                # Sometimes the value is broken across two lines:
                if j + 1 < len(lines):
                    nxt2 = (nxt + " " + lines[j + 1].strip()).strip()
                    trk = _parse_tracking_candidate(nxt2)
                    if trk:
                        return trk

    # ----- B: anywhere in TEXT -----
    all_text = " ".join(doc[p].get_text() for p in range(len(doc)))
    all_text_u = _u(re.sub(r"\s+", " ", all_text))

    # UPS anywhere (spaces/hyphens tolerated)
    for m in re.finditer(r"1Z[\s0-9A-Z\-]{8,50}", all_text_u):
        compact = _normalize_ups(m.group(0))
        if compact.startswith("1Z") and len(compact) == UPS_CANONICAL_LEN:
            return _format_ups_readable(compact)

    # FedEx numeric anywhere (12/15/20)
    mfx2 = re.search(FEDEX_NUMERIC_PATTERN, all_text_u)
    if mfx2:
        rawn = mfx2.group(1)
        if len(rawn) == 12:
            return _format_fedex12_readable(rawn)
        return rawn

    # Spaced 4-4-4 anywhere
    m444 = re.search(r"\b(\d{4}\s\d{4}\s\d{4})\b", all_text_u)
    if m444:
        return m444.group(1)

    # ----- C: OCR fallbacks -----
    if not _OCR_AVAILABLE:
        print(f"[extractor] OCR unavailable ({_OCR_REASON}). Install Tesseract + pytesseract + pillow for UPS label images.")
        return ""

    # OCR first 1–2 pages (labels are typically early)
    for p in range(min(2, len(doc))):
        trk = _ocr_page_for_tracking(doc, p)
        if trk:
            return trk

    # If still nothing, OCR the rest
    for p in range(2, len(doc)):
        trk = _ocr_page_for_tracking(doc, p)
        if trk:
            return trk

    return ""

def _infer_carrier(trk: str) -> str:
    if not trk:
        return "UNDEFINED"
    raw = _u(trk).replace(" ", "")
    if raw.startswith("1Z") and len(raw) == UPS_CANONICAL_LEN:
        return "UPS"
    if raw.isdigit() and len(raw) in (12, 15, 20):
        return "FEDEX"
    return "UNDEFINED"

# ---------------------- ORDER helpers (tables/text/filename) ----------------------
def _table_rows_upper(pdf_path: str):
    try:
        tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True, lattice=True)
    except Exception as e:
        print(f"Tabula PDF table extraction failed: {e}")
        return []
    rows = []
    for df in tables:
        try:
            df = df.fillna("").astype(str)
            for row in df.values.tolist():
                rows.append(" ".join(cell for cell in row if cell).upper())
        except Exception:
            continue
    return rows

def _order_from_tables_by_pattern(pdf_path: str, pattern: str, label_hint: str | None = None) -> str:
    rows = _table_rows_upper(pdf_path)
    if label_hint:
        for txt in rows:
            if label_hint.upper() in txt:
                m = re.search(pattern, txt, flags=re.IGNORECASE)
                if m:
                    return m.group(0)
    for txt in rows:
        m = re.search(pattern, txt, flags=re.IGNORECASE)
        if m:
            return m.group(0)
    return ""

def _order_from_text_by_pattern(full_text_upper: str, pattern: str, label_hint: str | None = None, window_after: int = 250) -> str:
    if label_hint:
        for m in _finditer_ignorecase(full_text_upper, label_hint):
            window = full_text_upper[m.end(): m.end() + window_after]
            m2 = re.search(pattern, window, flags=re.IGNORECASE)
            if m2:
                return m2.group(0)
    m3 = re.search(pattern, full_text_upper, flags=re.IGNORECASE)
    if m3:
        return m3.group(0)
    return ""

def _order_from_filename_by_pattern(pdf_path: str, pattern: str) -> str:
    fname = _u(_filename(pdf_path))
    m = re.search(pattern, fname, flags=re.IGNORECASE)
    return m.group(0) if m else ""

def _any_orderish_from_tables_or_text(pdf_path: str, full_text_upper: str) -> str:
    rows = _table_rows_upper(pdf_path)
    for txt in rows:
        for lab in ORDER_LABELS:
            if re.search(lab, txt, flags=re.IGNORECASE):
                m = re.search(ORDERISH_TOKEN, txt)
                if m:
                    return m.group(1)
    for lab in ORDER_LABELS:
        for mm in re.finditer(lab, full_text_upper, flags=re.IGNORECASE):
            window = full_text_upper[mm.end(): mm.end() + 200]
            m = re.search(ORDERISH_TOKEN, window)
            if m:
                return m.group(1)
    m2 = re.search(ORDERISH_TOKEN, full_text_upper)
    if m2:
        return m2.group(1)
    return ""

def _order_between_totalPrice_internaluse(full_text_upper: str) -> str:
    if not full_text_upper:
        return ""
    
    start_lbl = "26. TOTAL PRICE"
    end_lbl = "27. BOEING INTERNAL USE"

    s = full_text_upper.find(start_lbl)
    if s == -1:
        return ""
    e = full_text_upper.find(end_lbl, s)
    if e == -1:
        segment = full_text_upper[s + len(start_lbl):]
    else:
        segment = full_text_upper[s + len(start_lbl):e]
    
    preferred = re.search(r"\b(507\d{3})[-\s]?((?:8H)[A-Z0-9]{4})\b", segment)
    if preferred:
        left, right = preferred.group(1), preferred.group(2)
        return f"{left}-{right}"
    
    generic = re.search(r"\b([0-9]{6})[-\s]?([A-Z0-9]{6})\b", segment)
    if generic:
        left, right = generic.group(1), generic.group(2)
        return f"{left}-{right}"
    
    return ""

# ---------------------- ORDER dispatcher by doc type ----------------------
def _extract_order_no(pdf_path: str, full_text_upper: str, doc_type: str | None) -> str:
    if doc_type == "PHBBT":
        label_hint = "10 CHARGE LINE"
        v = _order_from_tables_by_pattern(pdf_path, PHBBT_ORDER_PATTERN, label_hint=label_hint)
        if v: return v
        v = _order_from_text_by_pattern(full_text_upper, PHBBT_ORDER_PATTERN, label_hint=label_hint)
        if v: return v
        v = _order_from_tables_by_pattern(pdf_path, PHBBT_ORDER_PATTERN)
        if v: return v
        v = _order_from_text_by_pattern(full_text_upper, PHBBT_ORDER_PATTERN)
        if v: return v
        v = _order_from_filename_by_pattern(pdf_path, PHBBT_ORDER_PATTERN)
        if v: return v
        # bare 8H#### soft fallback
        v = _order_from_text_by_pattern(full_text_upper, PHCDT_ORDER_PATTERN)
        if v: return v
        v = _order_from_tables_by_pattern(pdf_path, PHCDT_ORDER_PATTERN)
        if v: return v
        v = _order_between_totalPrice_internaluse(full_text_upper)
        if v: return v
        return _any_orderish_from_tables_or_text(pdf_path, full_text_upper)

    # Default / PHCDT
    label_hint = "9 ORDER NO."
    v = _order_from_tables_by_pattern(pdf_path, PHCDT_ORDER_PATTERN, label_hint=label_hint)
    if v: return v
    v = _order_from_text_by_pattern(full_text_upper, PHCDT_ORDER_PATTERN, label_hint=label_hint)
    if v: return v
    v = _order_from_tables_by_pattern(pdf_path, PHCDT_ORDER_PATTERN)
    if v: return v
    v = _order_from_text_by_pattern(full_text_upper, PHCDT_ORDER_PATTERN)
    if v: return v
    v = _order_from_filename_by_pattern(pdf_path, PHCDT_ORDER_PATTERN)
    if v: return v
    # optional legacy 6 digits
    legacy_six = r"\b\d{6}\b"
    v = _order_from_text_by_pattern(full_text_upper, legacy_six, label_hint=label_hint)
    if v: return v
    v = _order_from_tables_by_pattern(pdf_path, legacy_six)
    if v: return v
    v = _order_from_filename_by_pattern(pdf_path, legacy_six)
    if v: return v
    v = _order_between_totalPrice_internaluse(full_text_upper)
    if v: return v
    return _any_orderish_from_tables_or_text(pdf_path, full_text_upper)

# ---------------------- Main entrypoint ----------------------
def extract_pdf_data(pdf_path: str) -> dict:
    data = {
        "reference_no": None,
        "order_no": None,
        "shipped_from": None,
        "carton_dimensions": None,
        "carton_weight": None,
        "tracking_number": None,
        "carrier": "UNKNOWN",
    }

    full_text_upper = ""
    doc_type = None

    # Read all text up-front (this part should never throw a Tesseract error)
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                full_text_upper += page.get_text().upper()

            # reference_no & doc_type (PHCDT/PHBBT anywhere)
            mref = re.search(PH_REF_PATTERN, full_text_upper)
            if mref:
                ref = mref.group(0).replace(" ", "").upper()
                data["reference_no"] = ref
                if ref.startswith("PHCDT"):
                    doc_type = "PHCDT"
                elif ref.startswith("PHBBT"):
                    doc_type = "PHBBT"

            # shipped_from: Boeing block on any page  :contentReference[oaicite:3]{index=3}
            shipped_from = ""
            for p in range(len(doc)):
                block = _extract_boeing_block_from_page_text(doc[p].get_text())
                if block:
                    shipped_from = block
                    break
            if shipped_from:
                data["shipped_from"] = shipped_from

            # dimensions / weight
            md = re.search(DIM_PATTERN, full_text_upper)
            if md:
                data["carton_dimensions"] = md.group(0).replace(" ", "").upper()

            mw = re.search(WEIGHT_PATTERN, full_text_upper, flags=re.IGNORECASE | re.DOTALL)
            if mw:
                data["carton_weight"] = f"{mw.group(1)} LB"

            # tracking + carrier (text → fallback OCR if needed)
            trk = _extract_tracking_from_doc(doc)
            if trk:
                data["tracking_number"] = trk
                data["carrier"] = _infer_carrier(trk)
            else:
                data["carrier"] = "UNDEFINED"

    except Exception as e:
        # Only genuine PyMuPDF errors should land here now
        print(f"PyMuPDF text extraction failed: {e}")

    # If doc_type missing, infer from filename
    if not doc_type:
        fn = _u(_filename(pdf_path))
        if "PHBBT" in fn:
            doc_type = "PHBBT"
        elif "PHCDT" in fn:
            doc_type = "PHCDT"

    # Order no via doc-type rules (keeps your PHCDT/PHBBT logic)  :contentReference[oaicite:4]{index=4}
    order_no = _extract_order_no(pdf_path, full_text_upper, doc_type)
    if order_no:
        data["order_no"] = order_no.strip().upper()

    # Print and validate
    print("\n[PDF Extract] ===============================")
    print(f"File: {_filename(pdf_path)}")
    for k in ["reference_no", "order_no", "shipped_from", "carton_dimensions", "carton_weight", "tracking_number", "carrier"]:
        print(f"  {k}: {data.get(k)}")
    if not _OCR_AVAILABLE:
        print(f"  [NOTE] OCR disabled: {_OCR_REASON}  --> UPS label text/images will not be parsed.")
    print("===========================================\n")

    missing = [k for k, v in data.items() if not v or (isinstance(v, str) and not v.strip())]
    if missing:
        raise ValueError(f"Missing required extracted fields: {', '.join(missing)}")
    return data
