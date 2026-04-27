from core.database import Base
from sqlalchemy import Column, DateTime, Float, Integer, String


class Weight_entries(Base):
    __tablename__ = "weight_entries"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    date = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    image_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)