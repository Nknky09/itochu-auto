from .models import ShipmentExtract
from .db import SessionLocal

def save_shipment(data: dict, filename: str):
  db = SessionLocal()
  try:
    entry = ShipmentExtract(
      filename=filename,
      reference_no=data.get("reference_no"),
      order_no=data.get("order_no"),
      shipped_from=data.get("shipped_from"),
      carton_dimensions=data.get("carton_dimensions"),
      carton_weight=data.get("carton_weight"),
      tracking_number=data.get("tracking_number"),
      carrier=data.get("carrier"),
    )

    db.add(entry)
    db.commit()
  finally:
    db.close()