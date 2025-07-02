# models.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class User(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: str
    college: str
    is_verified: bool = False
    verification_code: Optional[str] = None
    verification_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Profile fields
    profile_picture: Optional[str] = None  # URL or base64 string
    year: Optional[str] = None  # e.g., "Freshman", "Sophomore", "Junior", "Senior", "Graduate"
    major: Optional[str] = None
    bio: Optional[str] = None
    
    # User statistics (updated monthly)
    stats_last_updated: Optional[datetime] = None
    times_driver_last_month: int = 0
    times_rider_last_month: int = 0
    times_uber_share_last_month: int = 0

class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    college: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class EmailVerification(BaseModel):
    email: EmailStr
    code: str

class ResendVerification(BaseModel):
    email: EmailStr

# Profile Management Models
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[str] = None
    major: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None

class UserProfileResponse(BaseModel):
    name: Optional[str] = None
    email: str
    college: str
    year: Optional[str] = None
    major: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    
    # Statistics
    times_driver_last_month: int = 0
    times_rider_last_month: int = 0
    times_uber_share_last_month: int = 0
    stats_last_updated: Optional[datetime] = None

class RideRequest(BaseModel):
    origin: str
    destination: str
    user_ids: List[str]           # Users involved in the ride
    product_id: Optional[str] = None  # Uber product id (optional)
    estimate: Optional[float] = None   # Price estimate (optional)

# Places API Models
class PlaceAutocompleteRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query for place autocomplete")

class PlaceSuggestion(BaseModel):
    place_id: str
    description: str

class PlaceAutocompleteResponse(BaseModel):
    suggestions: List[PlaceSuggestion]

class PlaceDetailsRequest(BaseModel):
    place_id: str = Field(..., description="Google Places place_id")

class PlaceLocation(BaseModel):
    latitude: float
    longitude: float

class PlaceDetailsResponse(BaseModel):
    name: str
    description: str
    location: Optional[PlaceLocation] = None