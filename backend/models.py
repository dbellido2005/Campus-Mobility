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

class ProfilePictureUpload(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image data")

# Uber Share Statistics Models
class FrequentRider(BaseModel):
    user_email: str
    user_name: Optional[str] = None
    ride_count: int

class FrequentDestination(BaseModel):
    destination: str
    trip_count: int

class UberShareStats(BaseModel):
    times_uber_share_last_month: int = 0
    most_frequent_riders: List[FrequentRider] = []
    most_frequent_destinations: List[FrequentDestination] = []
    stats_last_updated: Optional[datetime] = None

class UserProfileResponse(BaseModel):
    name: Optional[str] = None
    email: str
    college: str
    year: Optional[str] = None
    major: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    
    # Uber Share Statistics
    uber_share_stats: UberShareStats

class LocationData(BaseModel):
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RideRequest(BaseModel):
    origin: LocationData
    destination: LocationData
    departure_date: datetime
    earliest_time: int          # Time in minutes from midnight (e.g., 480 = 8:00 AM)
    latest_time: int           # Time in minutes from midnight (e.g., 600 = 10:00 AM)
    communities: List[str]     # Communities this ride is available to
    creator_email: str         # Email of the person who created the ride
    user_ids: List[str] = []   # Users who have joined the ride
    max_participants: int = 4  # Maximum number of people in the ride
    estimated_price_per_person: Optional[float] = None
    estimated_travel_time: Optional[int] = None  # Travel time in minutes
    product_id: Optional[str] = None  # Uber product id (optional)
    ride_type: str = "uber_share"     # Type of ride (uber_share, driver, rider)
    status: str = "active"     # active, full, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class RidePost(BaseModel):
    origin: LocationData
    destination: LocationData
    departure_date: str  # Accept as string from frontend
    earliest_time: int
    latest_time: int
    communities: List[str]
    max_participants: int = 4

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