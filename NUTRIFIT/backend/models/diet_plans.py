from core.database import Base
from sqlalchemy import Column, DateTime, Float, Integer, String


class Diet_plans(Base):
    __tablename__ = "diet_plans"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)
    activity_level = Column(String, nullable=False)
    goal = Column(String, nullable=True)
    daily_calories = Column(Integer, nullable=True)
    plan_text = Column(String, nullable=True)
    workout_text = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)