# routes/messaging.py
from fastapi import APIRouter, HTTPException, status, Depends
from models import (
    SendMessageRequest, SendQuestionRequest, SendPrivateResponseRequest,
    MessageResponse, GroupChatResponse, QuestionResponse, PrivateResponseDisplay,
    Message, RideGroupChat, QuestionToRide, PrivateResponse
)
from database import rides_collection, group_chats_collection, questions_collection, private_responses_collection, users_collection
from utils.auth_utils import get_current_user
from datetime import datetime
from typing import List
from bson import ObjectId
from services.university_detection import university_service

router = APIRouter()

async def get_user_info(email: str) -> dict:
    """Get user's display name and profile picture from email"""
    user = await users_collection.find_one({"email": email})
    if user:
        # Try to get firstName + lastName first (preferred)
        first_name = user.get('firstName', '').strip()
        last_name = user.get('lastName', '').strip()
        
        # Debug logging
        print(f"DEBUG: get_user_info for {email}")
        print(f"  firstName: '{first_name}'")
        print(f"  lastName: '{last_name}'")
        print(f"  name: '{user.get('name', '')}'")
        
        if first_name and last_name:
            name = f"{first_name} {last_name}"
            print(f"  returning: '{name}'")
        elif first_name:
            name = first_name
            print(f"  returning firstName: '{name}'")
        elif last_name:
            name = last_name
            print(f"  returning lastName: '{name}'")
        else:
            # Fallback to generic 'name' field
            name = user.get('name', '').strip()
            if name:
                print(f"  returning name: '{name}'")
            else:
                # Last resort: use email prefix
                name = email.split('@')[0]
                print(f"  returning email prefix: '{name}'")
        
        return {
            "name": name,
            "profile_picture": user.get('profile_picture')
        }
    
    fallback_name = email.split('@')[0]
    print(f"DEBUG: User not found for {email}, returning: '{fallback_name}'")
    return {
        "name": fallback_name,
        "profile_picture": None
    }

async def get_user_name(email: str) -> str:
    """Get user's display name from email"""
    user = await users_collection.find_one({"email": email})
    if user:
        # Try to get firstName + lastName first (preferred)
        first_name = user.get('firstName', '').strip()
        last_name = user.get('lastName', '').strip()
        
        # Debug logging
        print(f"DEBUG: get_user_name for {email}")
        print(f"  firstName: '{first_name}'")
        print(f"  lastName: '{last_name}'")
        print(f"  name: '{user.get('name', '')}'")
        
        if first_name and last_name:
            result = f"{first_name} {last_name}"
            print(f"  returning: '{result}'")
            return result
        elif first_name:
            print(f"  returning firstName: '{first_name}'")
            return first_name
        elif last_name:
            print(f"  returning lastName: '{last_name}'")
            return last_name
        
        # Fallback to generic 'name' field
        name = user.get('name', '').strip()
        if name:
            print(f"  returning name: '{name}'")
            return name
        
        # Last resort: use email prefix
        fallback = email.split('@')[0]
        print(f"  returning email prefix: '{fallback}'")
        return fallback
    
    fallback = email.split('@')[0]
    print(f"DEBUG: User not found for {email}, returning: '{fallback}'")
    return fallback

async def is_user_in_ride(user_email: str, ride_id: str) -> bool:
    """Check if user is a member of the ride"""
    ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    if not ride:
        return False
    return user_email in ride.get("user_ids", []) or user_email == ride.get("creator_email")

async def get_or_create_group_chat(ride_id: str) -> dict:
    """Get existing group chat or create new one"""
    # Try to find existing group chat
    chat = await group_chats_collection.find_one({"ride_id": ride_id})
    
    if not chat:
        # Get ride details to initialize participants
        ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        # Create new group chat
        participants = list(set([ride["creator_email"]] + ride.get("user_ids", [])))
        
        new_chat = RideGroupChat(
            ride_id=ride_id,
            participant_emails=participants,
            messages=[]
        )
        
        result = await group_chats_collection.insert_one(new_chat.dict())
        chat = await group_chats_collection.find_one({"_id": result.inserted_id})
    
    return chat

@router.get("/ride/{ride_id}/messages", response_model=GroupChatResponse)
async def get_ride_messages(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Get messages for a ride (only for ride members)"""
    
    # Check if user is in the ride
    if not await is_user_in_ride(current_user["email"], ride_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this ride to view messages"
        )
    
    # Get group chat
    chat = await get_or_create_group_chat(ride_id)
    
    # Convert messages to response format and refresh sender info
    message_responses = []
    for msg in chat.get("messages", []):
        # Always fetch fresh user info instead of using cached data
        user_info = await get_user_info(msg["sender_email"])
        
        # Ensure timestamp is properly formatted as ISO string with UTC timezone
        timestamp = msg["timestamp"]
        if hasattr(timestamp, 'isoformat'):
            # Convert datetime to UTC ISO format
            if hasattr(timestamp, 'replace') and timestamp.tzinfo is None:
                # Assume UTC if no timezone info
                timestamp = timestamp.replace(tzinfo=None)
            timestamp = timestamp.isoformat() + 'Z'  # Add Z to indicate UTC
        elif isinstance(timestamp, str):
            # Ensure string timestamps have proper UTC indicator
            if not (timestamp.endswith('Z') or '+' in timestamp or timestamp.endswith('UTC')):
                timestamp = timestamp + 'Z' if 'T' in timestamp else timestamp + 'T00:00:00Z'
            
        message_responses.append(MessageResponse(
            message_id=msg["message_id"],
            sender_email=msg["sender_email"],
            sender_name=user_info["name"],  # Use fresh name
            sender_profile_picture=user_info["profile_picture"],  # Include profile picture
            content=msg["content"],
            timestamp=timestamp,
            message_type=msg["message_type"],
            question_id=msg.get("question_id")  # Include question_id if present
        ))
    
    return GroupChatResponse(
        ride_id=ride_id,
        messages=message_responses,
        participant_count=len(chat["participant_emails"])
    )

@router.post("/ride/{ride_id}/message")
async def send_message_to_ride(
    ride_id: str,
    message_request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to a ride group chat (only for ride members)"""
    
    # Check if user is in the ride
    if not await is_user_in_ride(current_user["email"], ride_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this ride to send messages"
        )
    
    # Get user's display name
    sender_name = await get_user_name(current_user["email"])
    
    # Create message
    message = Message(
        ride_id=ride_id,
        sender_email=current_user["email"],
        sender_name=sender_name,
        content=message_request.content,
        message_type="group_chat"
    )
    
    # Get or create group chat
    chat = await get_or_create_group_chat(ride_id)
    
    # Add message to chat
    await group_chats_collection.update_one(
        {"ride_id": ride_id},
        {
            "$push": {"messages": message.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Message sent successfully", "message_id": message.message_id}

@router.post("/ride/{ride_id}/question")
async def ask_question_to_ride(
    ride_id: str,
    question_request: SendQuestionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Ask a question to a ride (for non-members)"""
    
    # Check if ride exists
    ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Check if user is already in the ride
    if await is_user_in_ride(current_user["email"], ride_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this ride. Use group chat instead."
        )
    
    # Get user's display name
    asker_name = await get_user_name(current_user["email"])
    
    # Create question
    question = QuestionToRide(
        ride_id=ride_id,
        asker_email=current_user["email"],
        asker_name=asker_name,
        question=question_request.question
    )
    
    # Save question
    await questions_collection.insert_one(question.dict())
    
    # Also add the question as a special message visible to ride members
    question_message = Message(
        ride_id=ride_id,
        sender_email=current_user["email"],
        sender_name=asker_name,
        content=f"QUESTION: {question_request.question}",
        message_type="question",
        is_visible_to_non_members=True,
        question_id=question.question_id
    )
    
    # Get or create group chat and add question message
    chat = await get_or_create_group_chat(ride_id)
    await group_chats_collection.update_one(
        {"ride_id": ride_id},
        {
            "$push": {"messages": question_message.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {
        "message": "Question sent to ride members",
        "question_id": question.question_id
    }

@router.get("/ride/{ride_id}/questions", response_model=List[QuestionResponse])
async def get_ride_questions(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Get all questions for a ride (only for ride members)"""
    
    # Check if user is in the ride
    if not await is_user_in_ride(current_user["email"], ride_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this ride to view questions"
        )
    
    # Get questions for this ride
    cursor = questions_collection.find({"ride_id": ride_id})
    questions = []
    
    async for question in cursor:
        # Count responses for this question
        response_count = await private_responses_collection.count_documents(
            {"question_id": question["question_id"]}
        )
        
        # Get ride information
        ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
        ride_origin = ride.get("origin", {}).get("description", "Unknown") if ride else "Unknown"
        ride_destination = ride.get("destination", {}).get("description", "Unknown") if ride else "Unknown"
        
        # Handle departure_date serialization
        departure_date = ride.get("departure_date") if ride else None
        if departure_date and hasattr(departure_date, 'isoformat'):
            departure_date = departure_date.isoformat()
        elif departure_date and isinstance(departure_date, str):
            # Already a string, keep as is
            pass
        else:
            departure_date = None
            
        # Handle question timestamp serialization
        question_timestamp = question["timestamp"]
        if hasattr(question_timestamp, 'isoformat'):
            question_timestamp = question_timestamp.isoformat() + 'Z'
        elif isinstance(question_timestamp, str) and not question_timestamp.endswith('Z'):
            question_timestamp = question_timestamp + 'Z' if 'T' in question_timestamp else question_timestamp + 'T00:00:00Z'
        
        questions.append(QuestionResponse(
            question_id=question["question_id"],
            asker_email=question["asker_email"],
            asker_name=question.get("asker_name"),
            question=question["question"],
            timestamp=question_timestamp,
            response_count=response_count,
            ride_id=ride_id,
            ride_origin=ride_origin,
            ride_destination=ride_destination,
            departure_date=departure_date
        ))
    
    return questions

@router.post("/question/{question_id}/respond")
async def respond_to_question(
    question_id: str,
    response_request: SendPrivateResponseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Respond privately to a question (only for ride members)"""
    
    # Get the question
    question = await questions_collection.find_one({"question_id": question_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if user is in the ride
    if not await is_user_in_ride(current_user["email"], question["ride_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this ride to respond to questions"
        )
    
    # Get user's display name
    responder_name = await get_user_name(current_user["email"])
    
    # Create private response
    response = PrivateResponse(
        question_id=question_id,
        ride_id=question["ride_id"],
        responder_email=current_user["email"],
        responder_name=responder_name,
        asker_email=question["asker_email"],
        response=response_request.response
    )
    
    # Save response
    result = await private_responses_collection.insert_one(response.dict())
    
    # Update question to mark as answered
    await questions_collection.update_one(
        {"question_id": question_id},
        {
            "$set": {"is_answered": True},
            "$push": {"responses": response.response_id}
        }
    )
    
    # Also add the response as a visible message in the group chat
    response_message = Message(
        ride_id=question["ride_id"],
        sender_email=current_user["email"],
        sender_name=responder_name,
        content=f"RESPONSE: {response_request.response}",
        message_type="response",
        is_visible_to_non_members=True,
        question_id=question_id
    )
    
    # Get or create group chat and add response message
    chat = await get_or_create_group_chat(question["ride_id"])
    await group_chats_collection.update_one(
        {"ride_id": question["ride_id"]},
        {
            "$push": {"messages": response_message.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {
        "message": "Response sent privately to the question asker and visible to all ride members",
        "response_id": response.response_id
    }

@router.get("/my-questions", response_model=List[QuestionResponse])
async def get_my_questions(current_user: dict = Depends(get_current_user)):
    """Get all questions asked by the current user"""
    
    cursor = questions_collection.find({"asker_email": current_user["email"]})
    questions = []
    
    async for question in cursor:
        # Count responses for this question
        response_count = await private_responses_collection.count_documents(
            {"question_id": question["question_id"]}
        )
        
        # Get ride information and analyze status
        ride = await rides_collection.find_one({"_id": ObjectId(question["ride_id"])})
        ride_deleted = ride is None
        
        # Initialize status variables
        ride_status = None
        ride_communities = None
        user_can_access = True
        unavailable_reason = None
        
        if ride_deleted:
            # Ride was deleted, use fallback values
            ride_origin = "Deleted Ride"
            ride_destination = "Deleted Ride"
            departure_date = None
            unavailable_reason = "Ride post was deleted"
            user_can_access = False
        else:
            # Ride exists, get actual values
            ride_origin = ride.get("origin", {}).get("description", "Unknown")
            ride_destination = ride.get("destination", {}).get("description", "Unknown")
            ride_status = ride.get("status", "unknown")
            ride_communities = ride.get("communities", [])
            
            # Handle departure_date serialization
            departure_date = ride.get("departure_date")
            if departure_date and hasattr(departure_date, 'isoformat'):
                departure_date = departure_date.isoformat()
            elif departure_date and isinstance(departure_date, str):
                # Already a string, keep as is
                pass
            else:
                departure_date = None
            
            # Check why user might not be able to access this ride
            # Get user's college/community info
            user = await users_collection.find_one({"email": current_user["email"]})
            user_college = user.get("college", "") if user else ""
            
            # Normalize both user college and ride communities for comparison
            normalized_user_college = university_service.normalize_community_name(user_college) if user_college else ""
            normalized_ride_communities = [
                university_service.normalize_community_name(community) 
                for community in ride_communities
            ] if ride_communities else []
            
            # Check if user's college is in ride communities (using normalized names)
            if normalized_user_college and normalized_ride_communities and normalized_user_college not in normalized_ride_communities:
                user_can_access = False
                unavailable_reason = f"Ride restricted to {', '.join(ride_communities)} (you're from {user_college})"
            elif ride_status == "full":
                user_can_access = False
                unavailable_reason = "Ride is full"
            elif ride_status == "completed":
                user_can_access = False
                unavailable_reason = "Ride has been completed"
            elif ride_status == "cancelled":
                user_can_access = False
                unavailable_reason = "Ride was cancelled"
            elif ride_status != "active":
                user_can_access = False
                unavailable_reason = f"Ride status is {ride_status}"
            
        # Handle question timestamp serialization
        question_timestamp = question["timestamp"]
        if hasattr(question_timestamp, 'isoformat'):
            question_timestamp = question_timestamp.isoformat() + 'Z'
        elif isinstance(question_timestamp, str) and not question_timestamp.endswith('Z'):
            question_timestamp = question_timestamp + 'Z' if 'T' in question_timestamp else question_timestamp + 'T00:00:00Z'
        
        questions.append(QuestionResponse(
            question_id=question["question_id"],
            asker_email=question["asker_email"],
            asker_name=question.get("asker_name"),
            question=question["question"],
            timestamp=question_timestamp,
            response_count=response_count,
            ride_id=question["ride_id"],
            ride_origin=ride_origin,
            ride_destination=ride_destination,
            departure_date=departure_date,
            ride_deleted=ride_deleted,
            ride_status=ride_status,
            ride_communities=ride_communities,
            user_can_access=user_can_access,
            unavailable_reason=unavailable_reason
        ))
    
    return questions

@router.get("/question/{question_id}/responses", response_model=List[PrivateResponseDisplay])
async def get_question_responses(question_id: str, current_user: dict = Depends(get_current_user)):
    """Get all responses to a question (only for the person who asked the question)"""
    
    # Get the question
    question = await questions_collection.find_one({"question_id": question_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if current user is the one who asked the question
    if question["asker_email"] != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view responses to your own questions"
        )
    
    # Get responses for this question
    cursor = private_responses_collection.find({"question_id": question_id})
    responses = []
    
    async for response in cursor:
        # Handle response timestamp serialization
        response_timestamp = response["timestamp"]
        if hasattr(response_timestamp, 'isoformat'):
            response_timestamp = response_timestamp.isoformat() + 'Z'
        elif isinstance(response_timestamp, str) and not response_timestamp.endswith('Z'):
            response_timestamp = response_timestamp + 'Z' if 'T' in response_timestamp else response_timestamp + 'T00:00:00Z'
            
        responses.append(PrivateResponseDisplay(
            response_id=response["response_id"],
            responder_name=response.get("responder_name"),
            response=response["response"],
            timestamp=response_timestamp
        ))
    
    return responses

@router.get("/ride/{ride_id}/chat-info")
async def get_chat_info(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Get basic info about the ride chat (for message button display)"""
    
    # Check if ride exists
    ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    is_member = await is_user_in_ride(current_user["email"], ride_id)
    
    # Get message count for members
    message_count = 0
    if is_member:
        chat = await group_chats_collection.find_one({"ride_id": ride_id})
        if chat:
            message_count = len(chat.get("messages", []))
    
    # Get question count (visible to everyone)
    question_count = await questions_collection.count_documents({"ride_id": ride_id})
    
    return {
        "is_member": is_member,
        "message_count": message_count,
        "question_count": question_count,
        "can_send_messages": is_member,
        "can_ask_questions": not is_member
    }

@router.get("/my-ride-chats")
async def get_my_ride_chats(current_user: dict = Depends(get_current_user)):
    """Get all ride chats for the current user"""
    
    try:
        user_email = current_user["email"]
        
        # Find only active rides where the user is a participant
        cursor = rides_collection.find({
            "$and": [
                {
                    "$or": [
                        {"user_ids": user_email},
                        {"creator_email": user_email}
                    ]
                },
                {"status": "active"}  # Only include active rides
            ]
        })
        
        ride_chats = []
        
        async for ride in cursor:
            # Get chat info for this ride
            chat = await group_chats_collection.find_one({"ride_id": str(ride["_id"])})
            
            # Count messages and get last message time
            message_count = 0
            last_message_time = None
            
            if chat and "messages" in chat:
                messages = chat["messages"]
                message_count = len(messages)
                if messages:
                    # Get the most recent message timestamp
                    last_message_time = max(msg["timestamp"] for msg in messages)
            
            # Format ride info
            ride_chat = {
                "ride_id": str(ride["_id"]),
                "ride_destination": ride.get("destination", {}).get("description", "Unknown destination"),
                "ride_origin": ride.get("origin", {}).get("description", "Unknown origin"),
                "departure_date": ride.get("departure_date"),
                "message_count": message_count,
                "last_message_time": last_message_time.isoformat() if last_message_time else None,
                "unread_count": 0  # TODO: Implement unread message tracking
            }
            
            ride_chats.append(ride_chat)
        
        # Sort by last activity (most recent first)
        ride_chats.sort(
            key=lambda x: x["last_message_time"] or "1970-01-01T00:00:00",
            reverse=True
        )
        
        return ride_chats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load ride chats: {str(e)}"
        )

@router.get("/debug/user-ride-status/{ride_id}")
async def debug_user_ride_status(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Debug endpoint to check user's status in a specific ride"""
    
    try:
        user_email = current_user["email"]
        
        # Get the ride
        ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
        if not ride:
            return {"error": "Ride not found"}
        
        # Check user status
        is_creator = ride.get("creator_email") == user_email
        is_in_user_ids = user_email in ride.get("user_ids", [])
        is_member = is_creator or is_in_user_ids
        
        return {
            "ride_id": str(ride["_id"]),
            "user_email": user_email,
            "ride_creator": ride.get("creator_email"),
            "ride_user_ids": ride.get("user_ids", []),
            "ride_status": ride.get("status"),
            "is_creator": is_creator,
            "is_in_user_ids": is_in_user_ids,
            "is_member": is_member,
            "available_spots": ride.get("max_participants", 0) - len(ride.get("user_ids", [])),
            "max_participants": ride.get("max_participants", 0)
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/user-info/{email}")
async def debug_user_info(email: str, current_user: dict = Depends(get_current_user)):
    """Debug endpoint to check user's profile information"""
    
    try:
        # Get the user
        user = await users_collection.find_one({"email": email})
        if not user:
            return {"error": "User not found"}
        
        # Remove sensitive information
        user.pop('password', None)
        user.pop('verification_code', None)
        user.pop('reset_code', None)
        
        # Convert ObjectId to string
        user['_id'] = str(user['_id'])
        
        return {
            "user_data": user,
            "computed_name": await get_user_name(email)
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/question-ride-mismatch")
async def debug_question_ride_mismatch(current_user: dict = Depends(get_current_user)):
    """Debug endpoint to find questions where rides are not visible in explore"""
    
    try:
        # Get all questions for current user
        questions_cursor = questions_collection.find({"asker_email": current_user["email"]})
        
        debug_info = []
        user = await users_collection.find_one({"email": current_user["email"]})
        user_college = user.get("college", "") if user else ""
        
        async for question in questions_cursor:
            ride_id = question["ride_id"]
            ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
            
            question_info = {
                "question_id": question["question_id"],
                "ride_id": ride_id,
                "question": question["question"],
                "user_college": user_college
            }
            
            if not ride:
                question_info["status"] = "RIDE_DELETED"
                question_info["reason"] = "Ride no longer exists in database"
            else:
                question_info["ride_exists"] = True
                question_info["ride_status"] = ride.get("status", "unknown")
                question_info["ride_communities"] = ride.get("communities", [])
                question_info["ride_origin"] = ride.get("origin", {}).get("description", "Unknown")
                question_info["ride_destination"] = ride.get("destination", {}).get("description", "Unknown")
                
                # Check visibility reasons
                issues = []
                if ride.get("status") != "active":
                    issues.append(f"Status is {ride.get('status')} (not active)")
                
                if user_college and ride.get("communities") and user_college not in ride.get("communities", []):
                    issues.append(f"User college '{user_college}' not in ride communities {ride.get('communities', [])}")
                
                if len(ride.get("user_ids", [])) >= ride.get("max_participants", 4):
                    issues.append("Ride is full")
                    
                question_info["visibility_issues"] = issues
                question_info["would_be_visible"] = len(issues) == 0
            
            debug_info.append(question_info)
        
        return {
            "user_email": current_user["email"],
            "user_college": user_college,
            "questions_analyzed": len(debug_info),
            "questions": debug_info
        }
        
    except Exception as e:
        return {"error": str(e)}