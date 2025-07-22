# routes/users.py
from fastapi import APIRouter, HTTPException, status, Depends
from models import User, UserSignUp, UserLogin, EmailVerification, ResendVerification, ForgotPassword, ResetPassword, UserProfileUpdate, UserProfileResponse, ProfilePictureUpload
from database import users_collection, rides_collection
from utils.email_utils import validate_college_email, generate_verification_code, get_verification_expiry, send_verification_email, generate_reset_code, get_reset_expiry, send_password_reset_email
from utils.auth_utils import hash_password, verify_password, create_access_token, get_current_user
from datetime import datetime, timedelta
from collections import Counter
from typing import List

router = APIRouter()


@router.post("/signup")
async def sign_up(user_data: UserSignUp):
    """Sign up a new user with email verification"""
    
    # Validate college email with AI-powered detection
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
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists. Please use the login screen or try 'Forgot Password' if you can't remember your password"
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
                        "password": hash_password(user_data.password),
                        "college": email_validation['college']  # Update with AI-detected college
                    }
                }
            )
            
            send_verification_email(user_data.email, verification_code, email_validation['college'])
            
            return {
                "message": "Verification email sent",
                "email": user_data.email.lower()
            }
    
    # Create new user with enhanced university information
    verification_code = generate_verification_code()
    verification_expires = get_verification_expiry()
    hashed_password = hash_password(user_data.password)
    
    # Create university_info from AI detection result
    university_info = None
    if 'university_info' in email_validation:
        from models import UniversityInfo
        university_info = UniversityInfo(**email_validation['university_info'])
    
    user = User(
        email=user_data.email.lower(),
        password=hashed_password,
        college=email_validation['college'],  # AI-detected college
        university_info=university_info,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please check your email or sign up for a new account"
        )
    
    if not user.get('is_verified'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for the verification code"
        )
    
    if not verify_password(login_data.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please check your password or use 'Forgot Password' to reset it"
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
        driver_rating=user.get('driver_rating', 0.0),
        driver_rating_count=user.get('driver_rating_count', 0),
        passenger_rating=user.get('passenger_rating', 0.0),
        passenger_rating_count=user.get('passenger_rating_count', 0)
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
        driver_rating=updated_user.get('driver_rating', 0.0),
        driver_rating_count=updated_user.get('driver_rating_count', 0),
        passenger_rating=updated_user.get('passenger_rating', 0.0),
        passenger_rating_count=updated_user.get('passenger_rating_count', 0)
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
            driver_rating=updated_user.get('driver_rating', 0.0),
            driver_rating_count=updated_user.get('driver_rating_count', 0),
            passenger_rating=updated_user.get('passenger_rating', 0.0),
            passenger_rating_count=updated_user.get('passenger_rating_count', 0)
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

@router.post("/forgot-password")
async def forgot_password(forgot_data: ForgotPassword):
    """Send password reset code to user's email"""
    try:
        # Check if user exists
        user = await users_collection.find_one({"email": forgot_data.email.lower()})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address"
            )
        
        # Check if user is verified
        if not user.get('is_verified', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account not verified. Please verify your email first"
            )
        
        # Generate reset code
        reset_code = generate_reset_code()
        reset_expires = get_reset_expiry()
        
        # Update user with reset code
        await users_collection.update_one(
            {"email": forgot_data.email.lower()},
            {
                "$set": {
                    "reset_code": reset_code,
                    "reset_expires": reset_expires
                }
            }
        )
        
        # Send reset email
        college = user.get('college', 'Unknown')
        send_password_reset_email(forgot_data.email, reset_code, college)
        
        return {
            "message": "Password reset code sent to your email",
            "email": forgot_data.email.lower()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )

@router.post("/reset-password")
async def reset_password(reset_data: ResetPassword):
    """Reset user's password using reset code"""
    try:
        # Find user by email
        user = await users_collection.find_one({"email": reset_data.email.lower()})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address"
            )
        
        # Check if user has reset code
        if not user.get('reset_code'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No password reset request found. Please request a new reset code"
            )
        
        # Check if reset code matches
        if user.get('reset_code') != reset_data.reset_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset code"
            )
        
        # Check if reset code has expired
        reset_expires = user.get('reset_expires')
        if not reset_expires or datetime.utcnow() > reset_expires:
            # Clear expired reset code
            await users_collection.update_one(
                {"email": reset_data.email.lower()},
                {"$unset": {"reset_code": "", "reset_expires": ""}}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset code has expired. Please request a new one"
            )
        
        # Validate new password (basic validation)
        if len(reset_data.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        # Hash new password
        hashed_password = hash_password(reset_data.new_password)
        
        # Update user's password and clear reset code
        await users_collection.update_one(
            {"email": reset_data.email.lower()},
            {
                "$set": {"password": hashed_password},
                "$unset": {"reset_code": "", "reset_expires": ""}
            }
        )
        
        return {
            "message": "Password reset successfully. You can now log in with your new password",
            "email": reset_data.email.lower()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )
