import os
from pathlib import Path
from extractor.extractor import extract_pdf_data
from database.db import init_db
from database.utils import save_shipment

WATCH_FOLDER = r"C:\Users\kosei\OneDrive - K Line Logistics U.S.A. Inc\Itochu Aviation (America) CH-47 - General\On Hand Report"

def get_latest_pdf(folder_path):
  pdf_files = [f for f in Path(folder_path).glob("*.pdf")]
  if not pdf_files:
    return None
  latest = max(pdf_files, key=os.path.getctime)
  return latest

def main():
  init_db()
  pdf_path = get_latest_pdf(WATCH_FOLDER)
  if not pdf_path:
    print("No PDF files found.")
    return
  
  print(f"Processing latest file: {pdf_path}")
  data = extract_pdf_data(str(pdf_path))
  print("Extracted Data:", data)
  save_shipment(data, filename=os.path.basename(pdf_path))
  print("Saved to database")

if __name__ == "__main__":
  main()
  
  