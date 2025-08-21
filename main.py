import os
import time
import shutil
from pathlib import Path
from dotenv import load_dotenv

from extractor.extractor import extract_pdf_data
from database.db import init_db
from database.utils import save_shipment
from shipper.shipper import run_shipper_flow
import smtplib
from email.message import EmailMessage

WATCH_FOLDER = os.getenv("WATCH_FOLDER", r"C:\Users\kosei\OneDrive - K Line Logistics U.S.A. Inc\Itochu Aviation (America) CH-47 - General\On Hand Report")

#home PC
# WATCH_FOLDER = r"C:\Users\Kosei\Projects\itochu-auto"

COMPLETED_FOLDER = Path(WATCH_FOLDER) / "completed"
ISSUE_FOLDER = Path(WATCH_FOLDER) / "issue"

for folder in [COMPLETED_FOLDER, ISSUE_FOLDER]:
  os.makedirs(folder, exist_ok=True)

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

def send_summary_email(successful, failed):
  if not successful and not failed:
    return
  
  subject = '[Itochu Auto] PDF to TW Shipment Processing'
  body = "The following shipments were processed:\n\n"
  if successful:
    body += "Completed:\n"
    for fname, data, rcn_number, rc_num in successful:
      body += f"RC #: {rc_num} | RCN Reference #: {rcn_number} BOEING\n\n"
      body += f"{fname}\n"
      for key, value in data.items():
        body += f" {key}: {value}\n"
      body += "\n"
  if failed:
    body += "\n Failed:\n" + "\n".join(failed) + "\n"

  msg = EmailMessage()
  msg["Subject"] = subject
  msg["From"] = EMAIL_USER
  msg["To"] = EMAIL_TO
  msg.set_content(body)

  try:
    with smtplib.SMTP("smtp.office365.com", 587) as smtp:
      smtp.starttls()
      smtp.login(EMAIL_USER, EMAIL_PASS)
      smtp.send_message(msg)
    print("Summary email sent.")
  except Exception as e:
    print(f"Failed to send email: {e}")


def process_new_pdfs():
  successful, failed = [], []
  for pdf in Path(WATCH_FOLDER).glob("*.pdf"):
    try:
      print(f"Processing {pdf}")
      data = extract_pdf_data(str(pdf))
      save_shipment(data, filename=pdf.name)
      rcn_number, rc_num = run_shipper_flow()
      shutil.move(str(pdf), COMPLETED_FOLDER / pdf.name)
      successful.append((pdf.name, data, rcn_number, rc_num))
    except Exception as e:
      print(f"Failed on {pdf}: {e}")
      shutil.move(str(pdf), ISSUE_FOLDER / pdf.name)
      failed.append(pdf.name)
  return successful, failed

def main():
  init_db()
  print(f"Watching folder: {WATCH_FOLDER}")
  while True:
    print("Checking for new PDF fiels...")
    successful, failed = process_new_pdfs()
    send_summary_email(successful, failed)
    print("Sleeping after 5 minutes")
    time.sleep(5 * 60)


if __name__ == "__main__":
  main()
  
  