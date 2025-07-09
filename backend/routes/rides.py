from fastapi import APIRouter, HTTPException, Depends
from models import RideRequest, RidePost, LocationData
from database import rides_collection, users_collection
from utils.auth_utils import get_current_user
from services.uber_pricing import uber_pricing_service
from services.google_routes import google_routes_service
from bson import ObjectId
from typing import List
from datetime import datetime
import random

router = APIRouter()

async def estimate_price_and_time(origin: LocationData, destination: LocationData):
    """Uber API only pricing estimation - returns None if unavailable"""
    
    # Only try if we have coordinates
    if origin.latitude and origin.longitude and destination.latitude and destination.longitude:
        try:
            # Get price estimate from Uber API only
            pricing_data = await uber_pricing_service.get_price_estimate(
                origin.latitude, 
                origin.longitude,
                destination.latitude, 
                destination.longitude
            )
            
            if pricing_data:
                # Extract time and price from Uber response
                time_estimate = int(pricing_data.get('duration', 1800) / 60)  # Convert seconds to minutes
                price_estimate = pricing_data.get('estimate', 0)
                
                return time_estimate, price_estimate, pricing_data
            else:
                # Uber API unavailable
                return None, None, None
                
        except Exception as e:
            print(f"Error getting Uber pricing estimate: {str(e)}")
            return None, None, None
    
    # No coordinates available
    return None, None, None

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
            print(f"DEBUG: Getting route info for new ride...")
            route_info = await google_routes_service.get_route_info(
                ride_post.origin.latitude,
                ride_post.origin.longitude,
                ride_post.destination.latitude,
                ride_post.destination.longitude
            )
            
            if route_info:
                print(f"DEBUG: ✅ Route info obtained: {route_info.get('formatted_distance', 'N/A')}, {route_info.get('formatted_duration', 'N/A')}")
            else:
                print(f"DEBUG: ❌ Google Routes API returned no data for new ride")
        except Exception as e:
            print(f"DEBUG: ❌ Error getting route info for new ride: {str(e)}")
    else:
        print(f"DEBUG: ❌ Missing coordinates for new ride")
        print(f"DEBUG:   Origin: {ride_post.origin.latitude}, {ride_post.origin.longitude}")
        print(f"DEBUG:   Destination: {ride_post.destination.latitude}, {ride_post.destination.longitude}")
    
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
                print(f"DEBUG: Error getting route info for ride {ride_id}: {str(e)}")
    
    return ride

@router.get("/ride-requests")
async def list_ride_requests(current_user: dict = Depends(get_current_user)):
    """List all active ride requests that the user can see based on their college"""
    
    # Get user's college to filter rides
    user_doc = await users_collection.find_one({"email": current_user["email"]})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_college = user_doc["college"]
    
    # Map college names to community names (as they appear in the communities list)
    college_to_community = {
        "Pomona College": "Pomona",
        "Harvey Mudd College": "Harvey Mudd",
        "Scripps College": "Scripps", 
        "Pitzer College": "Pitzer",
        "Claremont McKenna College": "CMC"
    }
    
    user_community = college_to_community.get(user_college, user_college)
    
    # Debug logging
    print(f"DEBUG: User {current_user['email']} college: {user_college}")
    print(f"DEBUG: User community: {user_community}")
    
    # Find rides that include the user's community and are still active
    rides = []
    
    # Debug the query we're about to run
    query = {
        "communities": {"$in": [user_community]},
        "status": "active"
    }
    print(f"DEBUG: Running query: {query}")
    
    # Use MongoDB array query to find rides that include the user's community
    cursor = rides_collection.find(query).sort("departure_date", 1)
    
    async for ride in cursor:
        ride_id = str(ride["_id"])
        ride["_id"] = ride_id
        
        # Get creator details
        creator = await users_collection.find_one({"email": ride["creator_email"]})
        ride["creator_name"] = creator.get("name") if creator else None
        
        # Calculate available spots
        ride["available_spots"] = ride["max_participants"] - len(ride["user_ids"])
        
        # Safe handling for debug output
        origin = ride.get('origin', {})
        destination = ride.get('destination', {})
        
        origin_desc = origin.get('description', 'N/A') if isinstance(origin, dict) else str(origin)
        dest_desc = destination.get('description', 'N/A') if isinstance(destination, dict) else str(destination)
        
        print(f"DEBUG: Found matching ride: {origin_desc} -> {dest_desc}")
        print(f"  Communities: {ride.get('communities', [])}")
        print(f"  Status: {ride.get('status', 'N/A')}")
        
        # Add route information if coordinates are available
        if (isinstance(origin, dict) and isinstance(destination, dict) and
            origin.get('latitude') is not None and origin.get('longitude') is not None and
            destination.get('latitude') is not None and destination.get('longitude') is not None):
            
            try:
                print(f"DEBUG: Attempting route calculation for ride {ride_id[:8]}...")
                print(f"DEBUG: Origin coords: {origin.get('latitude')}, {origin.get('longitude')}")
                print(f"DEBUG: Dest coords: {destination.get('latitude')}, {destination.get('longitude')}")
                
                route_info = await google_routes_service.get_route_info(
                    float(origin['latitude']),
                    float(origin['longitude']),
                    float(destination['latitude']),
                    float(destination['longitude'])
                )
                
                if route_info:
                    ride["route_info"] = route_info
                    print(f"DEBUG: ✅ Added route info: {route_info.get('formatted_distance', 'N/A')}, {route_info.get('formatted_duration', 'N/A')}")
                else:
                    print(f"DEBUG: ❌ Google Routes API returned no data for ride {ride_id[:8]}")
            except Exception as e:
                print(f"DEBUG: ❌ Error getting route info for ride {ride_id[:8]}: {str(e)}")
        else:
            print(f"DEBUG: ❌ Missing coordinates for ride {ride_id[:8]}")
            if isinstance(origin, dict):
                print(f"DEBUG:   Origin lat/lng: {origin.get('latitude')}, {origin.get('longitude')}")
            if isinstance(destination, dict):
                print(f"DEBUG:   Dest lat/lng: {destination.get('latitude')}, {destination.get('longitude')}")
        
        rides.append(ride)
    
    print(f"DEBUG: Found {len(rides)} rides for user")
    
    # Also check all rides without filtering for debugging
    all_rides = []
    cursor = rides_collection.find({})  # No filter to see absolutely everything
    async for ride in cursor:
        # Handle both string and dict formats for origin/destination
        origin = ride.get("origin", {})
        destination = ride.get("destination", {})
        
        if isinstance(origin, dict):
            origin_desc = origin.get("description", "N/A")
        else:
            origin_desc = str(origin) if origin else "N/A"
            
        if isinstance(destination, dict):
            dest_desc = destination.get("description", "N/A")
        else:
            dest_desc = str(destination) if destination else "N/A"
        
        all_rides.append({
            "id": str(ride.get("_id", "")),
            "communities": ride.get("communities", []),
            "creator": ride.get("creator_email", ""),
            "status": ride.get("status", ""),
            "origin": origin_desc,
            "destination": dest_desc
        })
    
    print(f"DEBUG: Total rides in database (all statuses): {len(all_rides)}")
    for i, ride in enumerate(all_rides):
        print(f"  {i+1}. {ride['origin']} -> {ride['destination']}")
        print(f"     Communities: {ride['communities']}, Status: {ride['status']}, Creator: {ride['creator']}")
    
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
    
    # Check if user is already in the ride
    if current_user["email"] in ride["user_ids"]:
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

@router.post("/price-estimate")
async def get_detailed_price_estimate(
    estimate_request: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed price estimate for a potential ride
    Expected request format:
    {
        "origin": {"latitude": float, "longitude": float, "description": str},
        "destination": {"latitude": float, "longitude": float, "description": str},
        "product_type": "uberX" (optional)
    }
    """
    
    try:
        origin = estimate_request.get('origin', {})
        destination = estimate_request.get('destination', {})
        product_type = estimate_request.get('product_type', 'uberX')
        
        if not all([
            origin.get('latitude'), 
            origin.get('longitude'),
            destination.get('latitude'), 
            destination.get('longitude')
        ]):
            raise HTTPException(
                status_code=400, 
                detail="Origin and destination coordinates are required"
            )
        
        # Get pricing estimate from Uber API only
        pricing_data = await uber_pricing_service.get_price_estimate(
            origin['latitude'],
            origin['longitude'], 
            destination['latitude'],
            destination['longitude'],
            product_type
        )
        
        if pricing_data:
            return {
                "success": True,
                "pricing": pricing_data,
                "origin": origin,
                "destination": destination
            }
        else:
            return {
                "success": False,
                "message": "Price estimate unavailable - Uber API not accessible",
                "pricing": None,
                "origin": origin,
                "destination": destination
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating price estimate: {str(e)}"
        )

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
                    print(f"DEBUG: Updated ride {ride_id[:8]} with route info: {route_info.get('formatted_distance', 'N/A')}, {route_info.get('formatted_duration', 'N/A')}")
                else:
                    error_count += 1
                    print(f"DEBUG: Failed to get route info for ride {ride_id[:8]}")
                    
            except Exception as e:
                error_count += 1
                print(f"DEBUG: Error updating ride {ride_id[:8]}: {str(e)}")
        
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
