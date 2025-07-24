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
    
    # Rating system
    driver_rating: float = 0.0        # Average driver rating (0-5 stars)
    driver_rating_count: int = 0      # Number of driver ratings received
    passenger_rating: float = 0.0     # Average passenger rating (0-5 stars)  
    passenger_rating_count: int = 0   # Number of passenger ratings received

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
    
    # Rating information
    driver_rating: float = 0.0
    driver_rating_count: int = 0
    passenger_rating: float = 0.0
    passenger_rating_count: int = 0
    

class LocationData(BaseModel):
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RideParticipant(BaseModel):
    email: str
    has_car: bool = False
    status: str = "joined"  # joined, pending, approved, declined

class RideRequest(BaseModel):
    origin: LocationData
    destination: LocationData
    departure_date: datetime
    earliest_time: int          # Time in minutes from midnight (e.g., 480 = 8:00 AM)
    latest_time: int           # Time in minutes from midnight (e.g., 600 = 10:00 AM)
    communities: List[str]     # Communities this ride is available to
    creator_email: str         # Email of the person who created the ride
    creator_has_car: bool = False  # Whether the creator has a car
    is_driver_ride: bool = False   # Whether this is a driver-led ride (creator driving)
    participants: List[RideParticipant] = []  # Participants with car status and approval status
    user_ids: List[str] = []   # Users who have joined the ride (for backward compatibility)
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
    creator_has_car: bool = False
    is_driver_ride: bool = False

class JoinRideRequest(BaseModel):
    ride_id: str
    has_car: bool = False

class JoinRideBody(BaseModel):
    has_car: bool = False

class ApprovalRequest(BaseModel):
    ride_id: str
    participant_email: str
    action: str  # "approve" or "decline"

class Rating(BaseModel):
    ride_id: str
    rated_user_email: str      # User being rated
    rating_user_email: str     # User giving the rating
    rating_type: str           # "driver" or "passenger" 
    score: int                 # 1-5 stars
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RideRatingRequest(BaseModel):
    ride_id: str
    ratings: List[Rating]      # List of ratings for all participants

# Report Models
class UserReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(ObjectId()))
    ride_id: str
    reporter_email: str         # User making the report
    reported_user_email: str    # User being reported
    report_type: str = "payment_issue"  # For now, only payment issues
    amount_owed: float         # Amount that was not paid back
    description: str           # Description of the issue
    receipt_url: Optional[str] = None  # URL to uploaded receipt
    receipt_metadata: Optional[dict] = None  # Metadata about uploaded receipt
    status: str = "open"       # "open", "in_review", "resolved", "closed"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    admin_notes: Optional[str] = None

class ReportRequest(BaseModel):
    ride_id: str
    reported_user_email: str
    amount_owed: float = Field(..., ge=0, description="Amount owed must be positive")
    description: str = Field(..., min_length=10, description="Please provide details about the issue")
    receipt_base64: Optional[str] = None  # Base64 encoded receipt image/PDF
    receipt_filename: Optional[str] = None  # Original filename
    receipt_type: Optional[str] = None  # MIME type (image/jpeg, application/pdf, etc.)

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