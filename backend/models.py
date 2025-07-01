# models.py
from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId

class User(BaseModel):
    name: str
    email: str
    password: str

class RideRequest(BaseModel):
    origin: str
    destination: str
    user_ids: List[str]  # users involved in the ride
    product_id: Optional[str] = None
    estimate: Optional[float] = None

class RideRequest(BaseModel):
    origin: str
    destination: str
    user_ids: List[str]           # Users involved in the ride
    product_id: Optional[str] = None  # Uber product id (optional)
    estimate: Optional[float] = None   # Price estimate (optional)