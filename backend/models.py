# models.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class UniversityInfo(BaseModel):
    university_name: str
    short_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    university_type: Optional[str] = None  # "public" or "private"
    student_population: Optional[int] = None
    founded_year: Optional[int] = None
    notable_programs: Optional[List[str]] = []
    coordinates: Optional[dict] = None  # {"latitude": float, "longitude": float}
    nearby_universities: Optional[List[dict]] = []
    legacy: Optional[bool] = False  # True if from legacy hardcoded mapping
    fallback: Optional[bool] = False  # True if fallback was used

class User(BaseModel):
    name: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: EmailStr
    password: str
    college: str  # Keep for backward compatibility
    university_info: Optional[UniversityInfo] = None  # New AI-powered university data
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

class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    college: Optional[str] = None  # Make college optional since AI will detect it

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class EmailVerification(BaseModel):
    email: EmailStr
    code: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str

class ResendVerification(BaseModel):
    email: EmailStr

# Profile Management Models
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    year: Optional[str] = None
    major: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None

class ProfilePictureUpload(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image data")


class UserProfileResponse(BaseModel):
    name: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: str
    college: str
    year: Optional[str] = None
    major: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    

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
    ride_type: str = "ride_share"     # Type of ride (ride_share, driver, rider)
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

# Messaging Models
class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(ObjectId()))
    ride_id: str
    sender_email: str
    sender_name: Optional[str] = None
    content: str
    message_type: str = "group_chat"  # "group_chat", "question", "private_response"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_visible_to_non_members: bool = False  # Only true for questions from non-members
    question_id: Optional[str] = None  # Links private responses to original questions
    
class RideGroupChat(BaseModel):
    ride_id: str
    participant_emails: List[str]  # All ride members
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class QuestionToRide(BaseModel):
    question_id: str = Field(default_factory=lambda: str(ObjectId()))
    ride_id: str
    asker_email: str
    asker_name: Optional[str] = None
    question: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    responses: List[str] = []  # List of message_ids for private responses
    is_answered: bool = False

class PrivateResponse(BaseModel):
    response_id: str = Field(default_factory=lambda: str(ObjectId()))
    question_id: str
    ride_id: str
    responder_email: str
    responder_name: Optional[str] = None
    asker_email: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Request/Response Models for API
class SendMessageRequest(BaseModel):
    ride_id: str
    content: str

class SendQuestionRequest(BaseModel):
    ride_id: str
    question: str

class SendPrivateResponseRequest(BaseModel):
    question_id: str
    response: str

class MessageResponse(BaseModel):
    message_id: str
    sender_email: str
    sender_name: Optional[str]
    sender_profile_picture: Optional[str] = None  # Profile picture URL or base64
    content: str
    timestamp: str  # Changed to str since we serialize it
    message_type: str
    question_id: Optional[str] = None  # For question-type messages

class GroupChatResponse(BaseModel):
    ride_id: str
    messages: List[MessageResponse]
    participant_count: int

class QuestionResponse(BaseModel):
    question_id: str
    asker_email: str
    asker_name: Optional[str]
    question: str
    timestamp: str  # Changed to str since we serialize it
    response_count: int
    # Trip information
    ride_id: str
    ride_origin: Optional[str] = None
    ride_destination: Optional[str] = None
    departure_date: Optional[str] = None
    ride_deleted: bool = False  # Indicates if the ride post was deleted
    # Detailed status information
    ride_status: Optional[str] = None  # "active", "full", "completed", "cancelled"
    ride_communities: Optional[List[str]] = None  # Communities the ride is available to
    user_can_access: bool = True  # Whether current user can access this ride
    unavailable_reason: Optional[str] = None  # Reason why ride is unavailable

class PrivateResponseDisplay(BaseModel):
    response_id: str
    responder_name: Optional[str]
    response: str
    timestamp: str  # Changed to str since we serialize it