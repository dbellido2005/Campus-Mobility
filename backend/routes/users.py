# routes/users.py
from fastapi import APIRouter, HTTPException, status, Depends
from models import User, UserSignUp, UserLogin, EmailVerification, ResendVerification, UserProfileUpdate, UserProfileResponse, ProfilePictureUpload, UberShareStats, FrequentRider, FrequentDestination
from database import users_collection, rides_collection
from utils.email_utils import validate_college_email, generate_verification_code, get_verification_expiry, send_verification_email
from utils.auth_utils import hash_password, verify_password, create_access_token, get_current_user
from datetime import datetime, timedelta
from collections import Counter
from typing import List

router = APIRouter()

async def calculate_uber_share_stats(user_email: str) -> UberShareStats:
    """Calculate Uber Share statistics for a user"""
    try:
        # Get date range for last month
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        
        # Find all uber share rides for this user in the last month
        uber_rides = []
        cursor = rides_collection.find({
            "user_ids": user_email,
            "ride_type": "uber_share",
            "created_at": {"$gte": one_month_ago}
        })
        
        async for ride in cursor:
            uber_rides.append(ride)
        
        # Count total rides
        total_rides = len(uber_rides)
        
        # Calculate most frequent riders (other users in the same rides)
        other_users = []
        destinations = []
        
        for ride in uber_rides:
            # Get other users in this ride
            for user_id in ride.get("user_ids", []):
                if user_id != user_email:
                    other_users.append(user_id)
            
            # Get destination
            destination = ride.get("destination", "")
            if destination:
                # Handle both string and dict formats
                if isinstance(destination, dict):
                    dest_description = destination.get("description", "")
                else:
                    dest_description = str(destination)
                
                if dest_description:
                    destinations.append(dest_description)
        
        # Count frequent riders
        user_counts = Counter(other_users)
        frequent_riders = []
        
        for user_id, count in user_counts.most_common(2):  # Top 2 riders
            # Get user details
            user_doc = await users_collection.find_one({"email": user_id})
            user_name = user_doc.get("name") if user_doc else None
            
            frequent_riders.append(FrequentRider(
                user_email=user_id,
                user_name=user_name,
                ride_count=count
            ))
        
        # Count frequent destinations
        destination_counts = Counter(destinations)
        frequent_destinations = []
        
        for destination, count in destination_counts.most_common(2):  # Top 2 destinations
            frequent_destinations.append(FrequentDestination(
                destination=destination,
                trip_count=count
            ))
    
        return UberShareStats(
            times_uber_share_last_month=total_rides,
            most_frequent_riders=frequent_riders,
            most_frequent_destinations=frequent_destinations,
            stats_last_updated=datetime.utcnow()
        )
    except Exception as e:
        print(f"ERROR in calculate_uber_share_stats: {e}")
        # Return empty stats on error
        return UberShareStats(
            times_uber_share_last_month=0,
            most_frequent_riders=[],
            most_frequent_destinations=[],
            stats_last_updated=datetime.utcnow()
        )

@router.post("/signup")
async def sign_up(user_data: UserSignUp):
    """Sign up a new user with email verification"""
    
    # Validate college email
    email_validation = validate_college_email(user_data.email)
    if not email_validation['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=email_validation['error']
        )
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email.lower()})
    if existing_user:
        if existing_user.get('is_verified'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists and is verified"
            )
        else:
            # User exists but not verified, update verification code
            verification_code = generate_verification_code()
            verification_expires = get_verification_expiry()
            
            await users_collection.update_one(
                {"email": user_data.email.lower()},
                {
                    "$set": {
                        "verification_code": verification_code,
                        "verification_expires": verification_expires,
                        "password": hash_password(user_data.password)
                    }
                }
            )
            
            send_verification_email(user_data.email, verification_code, email_validation['college'])
            
            return {
                "message": "Verification email sent",
                "email": user_data.email.lower()
            }
    
    # Create new user
    verification_code = generate_verification_code()
    verification_expires = get_verification_expiry()
    hashed_password = hash_password(user_data.password)
    
    user = User(
        email=user_data.email.lower(),
        password=hashed_password,
        college=email_validation['college'],
        verification_code=verification_code,
        verification_expires=verification_expires
    )
    
    await users_collection.insert_one(user.dict())
    
    # Send verification email
    send_verification_email(user_data.email, verification_code, email_validation['college'])
    
    return {
        "message": "User created successfully. Please check your email for verification code.",
        "email": user_data.email.lower()
    }

@router.post("/verify-email")
async def verify_email(verification_data: EmailVerification):
    """Verify user email with verification code"""
    
    user = await users_collection.find_one({"email": verification_data.email.lower()})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.get('is_verified'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Check verification code
    if user.get('verification_code') != verification_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Check if code expired
    if user.get('verification_expires') and datetime.utcnow() > user['verification_expires']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired"
        )
    
    # Mark user as verified
    await users_collection.update_one(
        {"email": verification_data.email.lower()},
        {
            "$set": {
                "is_verified": True,
                "verification_code": None,
                "verification_expires": None
            }
        }
    )
    
    # Create access token
    token = create_access_token({"email": user['email'], "college": user['college']})
    
    return {
        "message": "Email verified successfully",
        "token": token,
        "user": {
            "email": user['email'],
            "college": user['college'],
            "is_verified": True
        }
    }

@router.post("/resend-verification")
async def resend_verification(resend_data: ResendVerification):
    """Resend verification email"""
    
    user = await users_collection.find_one({"email": resend_data.email.lower()})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.get('is_verified'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new verification code
    verification_code = generate_verification_code()
    verification_expires = get_verification_expiry()
    
    await users_collection.update_one(
        {"email": resend_data.email.lower()},
        {
            "$set": {
                "verification_code": verification_code,
                "verification_expires": verification_expires
            }
        }
    )
    
    # Send verification email
    send_verification_email(resend_data.email, verification_code, user['college'])
    
    return {"message": "Verification email sent"}

@router.post("/login")
async def login(login_data: UserLogin):
    """Login user"""
    
    user = await users_collection.find_one({"email": login_data.email.lower()})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.get('is_verified'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified"
        )
    
    if not verify_password(login_data.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    token = create_access_token({"email": user['email'], "college": user['college']})
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "email": user['email'],
            "college": user['college'],
            "is_verified": user['is_verified']
        }
    }

@router.get("/users")
async def list_users():
    """List all users (for admin/debugging)"""
    users = []
    cursor = users_collection.find({})
    async for user in cursor:
        user["_id"] = str(user["_id"])
        # Don't return password or verification code
        user.pop('password', None)
        user.pop('verification_code', None)
        users.append(user)
    return users

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    user = await users_collection.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate Uber Share statistics
    uber_share_stats = await calculate_uber_share_stats(current_user["email"])
    
    return UserProfileResponse(
        name=user.get('name'),
        firstName=user.get('firstName'),
        lastName=user.get('lastName'),
        email=user['email'],
        college=user['college'],
        year=user.get('year'),
        major=user.get('major'),
        bio=user.get('bio'),
        profile_picture=user.get('profile_picture'),
        created_at=user['created_at'],
        uber_share_stats=uber_share_stats
    )

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile"""
    
    # Build update document with only provided fields
    update_data = {}
    if profile_update.name is not None:
        update_data["name"] = profile_update.name
    if profile_update.firstName is not None:
        update_data["firstName"] = profile_update.firstName
    if profile_update.lastName is not None:
        update_data["lastName"] = profile_update.lastName
    if profile_update.year is not None:
        update_data["year"] = profile_update.year
    if profile_update.major is not None:
        update_data["major"] = profile_update.major
    if profile_update.bio is not None:
        update_data["bio"] = profile_update.bio
    if profile_update.profile_picture is not None:
        update_data["profile_picture"] = profile_update.profile_picture
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Update user in database
    result = await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return updated profile
    updated_user = await users_collection.find_one({"email": current_user["email"]})
    
    # Calculate Uber Share statistics
    uber_share_stats = await calculate_uber_share_stats(current_user["email"])
    
    return UserProfileResponse(
        name=updated_user.get('name'),
        firstName=updated_user.get('firstName'),
        lastName=updated_user.get('lastName'),
        email=updated_user['email'],
        college=updated_user['college'],
        year=updated_user.get('year'),
        major=updated_user.get('major'),
        bio=updated_user.get('bio'),
        profile_picture=updated_user.get('profile_picture'),
        created_at=updated_user['created_at'],
        uber_share_stats=uber_share_stats
    )

@router.post("/profile/picture", response_model=UserProfileResponse)
async def upload_profile_picture(
    picture_data: ProfilePictureUpload,
    current_user: dict = Depends(get_current_user)
):
    """Upload profile picture (base64 encoded image)"""
    
    try:
        # Validate base64 image data
        import base64
        import re
        
        # Check if it's a valid base64 data URL
        if not picture_data.image_data.startswith('data:image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Must be a base64 data URL."
            )
        
        # Extract base64 data
        base64_match = re.match(r'data:image/[^;]+;base64,(.+)', picture_data.image_data)
        if not base64_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 image format"
            )
        
        base64_data = base64_match.group(1)
        
        # Validate base64 data
        try:
            decoded_data = base64.b64decode(base64_data)
            
            # Check file size (limit to 5MB)
            if len(decoded_data) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image too large. Maximum size is 5MB."
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 image data"
            )
        
        # Update user profile with image
        result = await users_collection.update_one(
            {"email": current_user["email"]},
            {"$set": {"profile_picture": picture_data.image_data}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return updated profile
        updated_user = await users_collection.find_one({"email": current_user["email"]})
        
        # Calculate Uber Share statistics
        uber_share_stats = await calculate_uber_share_stats(current_user["email"])
        
        return UserProfileResponse(
            name=updated_user.get('name'),
            firstName=updated_user.get('firstName'),
            lastName=updated_user.get('lastName'),
            email=updated_user['email'],
            college=updated_user['college'],
            year=updated_user.get('year'),
            major=updated_user.get('major'),
            bio=updated_user.get('bio'),
            profile_picture=updated_user.get('profile_picture'),
            created_at=updated_user['created_at'],
            uber_share_stats=uber_share_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )

@router.delete("/delete-account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Delete current user's account and all associated data"""
    
    try:
        user_email = current_user["email"]
        
        # First, remove user from all rides they're part of
        # Find all rides where the user is a participant
        rides_to_update = []
        cursor = rides_collection.find({"user_ids": user_email})
        
        async for ride in cursor:
            rides_to_update.append(ride)
        
        # Update each ride to remove the user
        for ride in rides_to_update:
            new_user_ids = [uid for uid in ride["user_ids"] if uid != user_email]
            
            # Update status based on remaining participants
            if len(new_user_ids) == 0:
                # If no participants left, mark as cancelled
                new_status = "cancelled"
            else:
                # If there are still participants, keep existing status or set to active
                new_status = "active" if ride["status"] in ["active", "full"] else ride["status"]
            
            # Update the ride
            await rides_collection.update_one(
                {"_id": ride["_id"]},
                {
                    "$set": {
                        "user_ids": new_user_ids,
                        "status": new_status
                    }
                }
            )
        
        # Delete all rides created by the user
        await rides_collection.delete_many({"creator_email": user_email})
        
        # Delete the user account
        result = await users_collection.delete_one({"email": user_email})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "message": "Account deleted successfully",
            "rides_updated": len(rides_to_update),
            "rides_deleted": result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
