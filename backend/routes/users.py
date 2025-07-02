# routes/users.py
from fastapi import APIRouter, HTTPException, status
from models import User, UserSignUp, UserLogin, EmailVerification, ResendVerification
from database import users_collection
from utils.email_utils import validate_college_email, generate_verification_code, get_verification_expiry, send_verification_email
from utils.auth_utils import hash_password, verify_password, create_access_token
from datetime import datetime

router = APIRouter()

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
