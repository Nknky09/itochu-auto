from database.db import SessionLocal
from database.models import ShipmentExtract


def get_unprocessed_shipments():
  db = SessionLocal()
  try:
    return db.query(ShipmentExtract).filter_by(processed=0).all()
  finally: 
    db.close()

def mark_shipment_processed(shipment_id):
  db = SessionLocal()
  try:
    entry = db.query(ShipmentExtract).filter_by(id=shipment_id).first()
    if entry:
      entry.processed = 1
      db.commit()
  finally:
    db.close()

    