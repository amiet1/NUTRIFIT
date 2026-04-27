from .base import Base
from .auth import User  # Change 'User' to whatever your class name is in auth.py
from .diet_plans import Diet_plans
from .meal_logs import Meal_logs
from .weight_entries import Weight_entries

# This helps the database 'discover' all models at once
__all__ = [
    "Base",
    "Diet_plans",
    "Meal_logs",
    "Weight_entries"
]