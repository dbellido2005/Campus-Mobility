from fastapi import APIRouter, HTTPException, Depends
from models import RideRequest, RidePost, LocationData
from database import rides_collection, users_collection
from utils.auth_utils import get_current_user
from services.google_routes import google_routes_service
from services.university_detection import university_service
from bson import ObjectId
from typing import List
from datetime import datetime
import random

router = APIRouter()


@router.post("/ride-request")
async def create_ride_request(ride_post: RidePost, current_user: dict = Depends(get_current_user)):
    """Create a new ride request"""
    
    try:
        # Parse the departure date from ISO string
        departure_date = datetime.fromisoformat(ride_post.departure_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid departure_date format")
    
    # Get estimated travel time and price from Uber API only
    estimated_time, estimated_price, pricing_data = await estimate_price_and_time(ride_post.origin, ride_post.destination)
    
    # Get route information from Google Routes API
    route_info = None
    if (ride_post.origin.latitude is not None and ride_post.origin.longitude is not None and
        ride_post.destination.latitude is not None and ride_post.destination.longitude is not None):
        
        try:
            route_info = await google_routes_service.get_route_info(
                ride_post.origin.latitude,
                ride_post.origin.longitude,
                ride_post.destination.latitude,
                ride_post.destination.longitude
            )
        except Exception as e:
            pass  # Route info is optional
    
    # Create ride request (with None values if APIs unavailable)
    ride_request_data = {
        "origin": ride_post.origin.dict(),
        "destination": ride_post.destination.dict(),
        "departure_date": departure_date,
        "earliest_time": ride_post.earliest_time,
        "latest_time": ride_post.latest_time,
        "communities": ride_post.communities,
        "creator_email": current_user["email"],
        "user_ids": [current_user["email"]],  # Creator automatically joins
        "max_participants": ride_post.max_participants,
        "status": "active",
        "created_at": datetime.utcnow()
    }
    
    # Add pricing data only if available
    if estimated_price is not None:
        ride_request_data["estimated_total_price"] = estimated_price
        ride_request_data["estimated_price_per_person"] = estimated_price / ride_post.max_participants
    if estimated_time is not None:
        ride_request_data["estimated_travel_time"] = estimated_time
    
    # Add route information if available
    if route_info:
        ride_request_data["route_info"] = route_info
    
    result = await rides_collection.insert_one(ride_request_data)
    ride_request_data["_id"] = str(result.inserted_id)
    return ride_request_data

@router.get("/ride-request/{ride_id}")
async def get_ride_request(ride_id: str):
    ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    ride["_id"] = str(ride["_id"])
    
    # Add route information if not already present and coordinates are available
    if "route_info" not in ride:
        origin = ride.get('origin', {})
        destination = ride.get('destination', {})
        
        if (isinstance(origin, dict) and isinstance(destination, dict) and
            origin.get('latitude') is not None and origin.get('longitude') is not None and
            destination.get('latitude') is not None and destination.get('longitude') is not None):
            
            try:
                route_info = await google_routes_service.get_route_info(
                    float(origin['latitude']),
                    float(origin['longitude']),
                    float(destination['latitude']),
                    float(destination['longitude'])
                )
                
                if route_info:
                    ride["route_info"] = route_info
                    # Also update the database with the route info
                    await rides_collection.update_one(
                        {"_id": ObjectId(ride_id)},
                        {"$set": {"route_info": route_info}}
                    )
            except Exception as e:
                print(f"Error fetching route info: {e}")
    
    return ride

@router.get("/ride-requests")
async def list_ride_requests(current_user: dict = Depends(get_current_user)):
    """List all active ride requests that the user can see based on their college"""
    
    # Get user's college to filter rides
    user_doc = await users_collection.find_one({"email": current_user["email"]})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_college = user_doc["college"]
    
    # Get user's normalized community name for filtering
    user_community = None
    
    # Try to get community from university_info (AI detection)
    university_info = user_doc.get("university_info")
    if university_info:
        raw_community = university_info.get("short_name", university_info.get("university_name"))
        user_community = university_service.normalize_community_name(raw_community) if raw_community else None
    
    # Fallback to normalizing the college field directly
    if not user_community:
        user_community = university_service.normalize_community_name(user_college) if user_college else None
    
    # Final fallback: use the college name directly (normalized)
    if not user_community:
        user_community = user_college
    
    # Debug logging
    print(f"DEBUG: User {current_user['email']} looking for rides")
    print(f"  Raw college: '{user_college}'")
    print(f"  Normalized community: '{user_community}'")
    
    # Find rides and check both original and normalized community names
    rides = []
    
    # Get all active rides first, then filter with normalization
    cursor = rides_collection.find({"status": "active"}).sort("departure_date", 1)
    
    async for ride in cursor:
        ride_communities = ride.get("communities", [])
        
        # Normalize ride communities for comparison
        normalized_ride_communities = [
            university_service.normalize_community_name(community) 
            for community in ride_communities
        ]
        
        # Check if user's normalized community matches any normalized ride community
        if user_community in normalized_ride_communities:
            # Convert ObjectId to string and add to results
            ride["_id"] = str(ride["_id"])
            
            # Calculate available spots
            ride["available_spots"] = ride["max_participants"] - len(ride["user_ids"])
            
            # Get creator details
            creator = await users_collection.find_one({"email": ride["creator_email"]})
            ride["creator_name"] = creator.get("name") if creator else None
            
            rides.append(ride)
            print(f"  ✓ Including ride {ride['_id']}: {ride_communities} -> {normalized_ride_communities}")
        else:
            print(f"  ✗ Excluding ride {ride.get('_id', 'unknown')}: {ride_communities} -> {normalized_ride_communities}")
    
    print(f"  Total matching rides: {len(rides)}")
    return rides

@router.get("/debug/all-rides")
async def debug_all_rides():
    """Debug endpoint to see all rides in the database"""
    rides = []
    cursor = rides_collection.find({})
    async for ride in cursor:
        ride["_id"] = str(ride["_id"])
        rides.append(ride)
    
    return {
        "total_rides": len(rides),
        "rides": rides
    }

@router.get("/debug/user-rides/{email}")
async def debug_user_rides(email: str):
    """Debug endpoint to see all rides created by a specific user"""
    rides = []
    cursor = rides_collection.find({"creator_email": email})
    async for ride in cursor:
        ride["_id"] = str(ride["_id"])
        rides.append(ride)
    
    return {
        "user_email": email,
        "total_rides": len(rides),
        "rides": rides
    }

@router.get("/debug/rides-for-community/{community}")
async def debug_rides_for_community(community: str):
    """Debug endpoint to see rides available for a specific community"""
    rides = []
    query = {"communities": {"$in": [community]}, "status": "active"}
    
    cursor = rides_collection.find(query)
    async for ride in cursor:
        ride["_id"] = str(ride["_id"])
        rides.append(ride)
    
    return {
        "community": community,
        "query": query,
        "total_rides": len(rides),
        "rides": rides
    }

@router.post("/ride-request/{ride_id}/join")
async def join_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Join an existing ride"""
    
    # Find the ride
    ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Check if ride is still active
    if ride["status"] != "active":
        raise HTTPException(status_code=400, detail="Ride is no longer active")
    
    # Check if user is already in the ride (either as participant or creator)
    if (current_user["email"] in ride["user_ids"] or 
        current_user["email"] == ride["creator_email"]):
        raise HTTPException(status_code=400, detail="You are already in this ride")
    
    # Check if ride is full
    if len(ride["user_ids"]) >= ride["max_participants"]:
        raise HTTPException(status_code=400, detail="Ride is full")
    
    # Check if user's college is allowed for this ride
    user_doc = await users_collection.find_one({"email": current_user["email"]})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_college = user_doc["college"]
    college_to_community = {
        "Pomona College": "Pomona",
        "Harvey Mudd College": "Harvey Mudd", 
        "Scripps College": "Scripps",
        "Pitzer College": "Pitzer",
        "Claremont McKenna College": "CMC"
    }
    
    user_community = college_to_community.get(user_college, user_college)
    if user_community not in ride["communities"]:
        raise HTTPException(status_code=403, detail="This ride is not available to your college")
    
    # Add user to the ride
    new_user_ids = ride["user_ids"] + [current_user["email"]]
    
    # Check if ride becomes full
    new_status = "full" if len(new_user_ids) >= ride["max_participants"] else "active"
    
    # Update the ride
    result = await rides_collection.update_one(
        {"_id": ObjectId(ride_id)},
        {
            "$set": {
                "user_ids": new_user_ids,
                "status": new_status
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Return updated ride
    updated_ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    updated_ride["_id"] = str(updated_ride["_id"])
    updated_ride["available_spots"] = updated_ride["max_participants"] - len(updated_ride["user_ids"])
    
    return {
        "message": "Successfully joined the ride",
        "ride": updated_ride
    }

@router.post("/ride-request/{ride_id}/leave")
async def leave_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Leave an existing ride"""
    
    # Find the ride
    ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Check if user is the creator
    if current_user["email"] == ride["creator_email"]:
        raise HTTPException(status_code=400, detail="You are the creator of this ride. Use delete instead of leave.")
    
    # Check if user is in the ride
    if current_user["email"] not in ride["user_ids"]:
        raise HTTPException(status_code=400, detail="You are not in this ride")
    
    # Remove user from the ride
    new_user_ids = [user_id for user_id in ride["user_ids"] if user_id != current_user["email"]]
    
    # Update status based on remaining participants
    if len(new_user_ids) == 0:
        # If no participants left, mark as cancelled
        new_status = "cancelled"
    else:
        # If there are still participants, set to active (unless it was already cancelled/completed)
        new_status = "active" if ride["status"] in ["active", "full"] else ride["status"]
    
    # Update the ride
    result = await rides_collection.update_one(
        {"_id": ObjectId(ride_id)},
        {
            "$set": {
                "user_ids": new_user_ids,
                "status": new_status
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Return updated ride
    updated_ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    updated_ride["_id"] = str(updated_ride["_id"])
    updated_ride["available_spots"] = updated_ride["max_participants"] - len(updated_ride["user_ids"])
    
    return {
        "message": "Successfully left the ride",
        "ride": updated_ride
    }

@router.get("/my-rides")
async def get_my_rides(current_user: dict = Depends(get_current_user)):
    """Get all rides that the current user has joined"""
    
    user_email = current_user["email"]
    
    # Find all rides where the user is a participant
    rides = []
    cursor = rides_collection.find({
        "user_ids": user_email,
        "status": {"$in": ["active", "full"]}  # Only show active rides
    }).sort("departure_date", 1)  # Sort by departure date
    
    async for ride in cursor:
        ride["_id"] = str(ride["_id"])
        
        # Get creator details
        creator = await users_collection.find_one({"email": ride["creator_email"]})
        ride["creator_name"] = creator.get("name") if creator else None
        
        # Calculate available spots
        ride["available_spots"] = ride["max_participants"] - len(ride["user_ids"])
        
        rides.append(ride)
    
    return rides


@router.post("/route-info")
async def get_route_info(
    origin: LocationData,
    destination: LocationData,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed route information using Google Routes API"""
    
    try:
        # Validate coordinates
        if not (origin.latitude and origin.longitude and destination.latitude and destination.longitude):
            raise HTTPException(
                status_code=400,
                detail="Both origin and destination must have latitude and longitude coordinates"
            )
        
        # Get route info from Google Routes API
        route_info = await google_routes_service.get_route_info(
            origin.latitude,
            origin.longitude,
            destination.latitude,
            destination.longitude
        )
        
        if not route_info:
            raise HTTPException(
                status_code=503,
                detail="Unable to calculate route information. Google Routes API may be unavailable."
            )
        
        # Add location descriptions to the response
        return {
            "origin": {
                "description": origin.description,
                "latitude": origin.latitude,
                "longitude": origin.longitude
            },
            "destination": {
                "description": destination.description,
                "latitude": destination.latitude,
                "longitude": destination.longitude
            },
            "route_info": route_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating route information: {str(e)}"
        )

@router.post("/batch-update-route-info")
async def batch_update_route_info(current_user: dict = Depends(get_current_user)):
    """Batch update existing rides with route information"""
    
    try:
        # Find all rides without route_info that have coordinates
        query = {
            "route_info": {"$exists": False},
            "origin.latitude": {"$exists": True, "$ne": None},
            "origin.longitude": {"$exists": True, "$ne": None},
            "destination.latitude": {"$exists": True, "$ne": None},
            "destination.longitude": {"$exists": True, "$ne": None}
        }
        
        cursor = rides_collection.find(query)
        updated_count = 0
        error_count = 0
        
        async for ride in cursor:
            ride_id = str(ride["_id"])
            origin = ride.get('origin', {})
            destination = ride.get('destination', {})
            
            try:
                route_info = await google_routes_service.get_route_info(
                    float(origin['latitude']),
                    float(origin['longitude']),
                    float(destination['latitude']),
                    float(destination['longitude'])
                )
                
                if route_info:
                    await rides_collection.update_one(
                        {"_id": ride["_id"]},
                        {"$set": {"route_info": route_info}}
                    )
                    updated_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
        
        return {
            "message": f"Batch update completed",
            "updated_rides": updated_count,
            "errors": error_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error batch updating route information: {str(e)}"
        )

@router.delete("/ride-request/{ride_id}")
async def delete_ride_request(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a ride request (only by creator)"""
    
    try:
        # First, check if the ride exists
        ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        # Check if the current user is the creator
        if ride["creator_email"] != current_user["email"]:
            raise HTTPException(
                status_code=403, 
                detail="Only the ride creator can delete this ride"
            )
        
        # Check if there are other participants (besides creator)
        other_participants = [email for email in ride["user_ids"] if email != current_user["email"]]
        if other_participants:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete ride with {len(other_participants)} other participant(s). Ask them to leave first."
            )
        
        # Delete the ride
        result = await rides_collection.delete_one({"_id": ObjectId(ride_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        return {
            "message": "Ride deleted successfully",
            "ride_id": ride_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting ride: {str(e)}"
        )
