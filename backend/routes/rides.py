from fastapi import APIRouter, HTTPException
from models import RideRequest
from database import rides_collection
from bson import ObjectId
from typing import List

router = APIRouter()

@router.post("/ride-request")
async def create_ride_request(ride: RideRequest):
    ride_dict = ride.dict()
    result = await rides_collection.insert_one(ride_dict)
    ride_dict["_id"] = str(result.inserted_id)
    return ride_dict

@router.get("/ride-request/{ride_id}")
async def get_ride_request(ride_id: str):
    ride = await rides_collection.find_one({"_id": ObjectId(ride_id)})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    ride["_id"] = str(ride["_id"])
    return ride

@router.get("/ride-request")
async def list_ride_requests():
    rides = []
    cursor = rides_collection.find({})
    async for ride in cursor:
        ride["_id"] = str(ride["_id"])
        rides.append(ride)
    return rides
