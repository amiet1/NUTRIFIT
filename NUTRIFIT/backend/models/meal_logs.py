from core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class Meal_logs(Base):
    __tablename__ = "meal_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    diet_plan_id = Column(Integer, nullable=True)
    date = Column(String, nullable=False)
    meal_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    calories = Column(Integer, nullable=False)
    image_key = Column(String, nullable=True)
    from_plan = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)