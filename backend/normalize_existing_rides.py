#!/usr/bin/env python3
"""
Script to normalize existing ride community names for consistency
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from services.university_detection import university_service
import os
from dotenv import load_dotenv

load_dotenv()

async def normalize_ride_communities():
    """Normalize community names in existing rides"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/campusmobility')
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_default_database()
    rides_collection = db.rides
    
    print("=== Normalizing Ride Communities ===")
    
    # Get all rides with communities
    cursor = rides_collection.find({"communities": {"$exists": True, "$ne": []}})
    updated_count = 0
    
    async for ride in cursor:
        original_communities = ride.get("communities", [])
        
        # Normalize each community name
        normalized_communities = []
        for community in original_communities:
            normalized = university_service.normalize_community_name(community)
            if normalized:  # Only add non-None values
                normalized_communities.append(normalized)
        
        # Remove duplicates while preserving order
        normalized_communities = list(dict.fromkeys(normalized_communities))
        
        # Update if communities changed
        if normalized_communities != original_communities:
            print(f"Ride {ride['_id']}:")
            print(f"  Old: {original_communities}")
            print(f"  New: {normalized_communities}")
            
            # Update the ride
            await rides_collection.update_one(
                {"_id": ride["_id"]},
                {"$set": {"communities": normalized_communities}}
            )
            updated_count += 1
    
    print(f"\n✅ Updated {updated_count} rides with normalized community names")
    
    # Show summary of all community names now in use
    pipeline = [
        {"$unwind": "$communities"},
        {"$group": {"_id": "$communities", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    print(f"\n📊 Community names currently in use:")
    async for result in rides_collection.aggregate(pipeline):
        print(f"  {result['_id']}: {result['count']} rides")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(normalize_ride_communities())