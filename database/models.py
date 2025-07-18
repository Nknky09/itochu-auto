from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ShipmentExtract(Base):
  __tablename__ = "shipment_extracts"

  id = Column(Integer, primary_key=True, autoincrement=True)
  filename = Column(String, nullable=False)
  reference_no = Column(String)
  order_no = Column(String)
  shipped_from = Column(String)
  carton_dimensions = Column(String)
  carton_weight = Column(String)
  tracking_number = Column(String)
  carrier = Column(String)
  processed_at = Column(DateTime, default=datetime.now)

  