import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import rides_collection, users_collection

async def check_rides():
    print('=== CHECKING RIDES DATABASE ===')
    
    # Check all rides
    rides = []
    cursor = rides_collection.find({})
    async for ride in cursor:
        rides.append(ride)
    
    print(f'Total rides in database: {len(rides)}')
    print()
    
    # Check rides for dbellido@pomona.edu
    user_rides = []
    cursor = rides_collection.find({'creator_email': 'dbellido@pomona.edu'})
    async for ride in cursor:
        user_rides.append(ride)
    
    print(f'Rides created by dbellido@pomona.edu: {len(user_rides)}')
    
    for i, ride in enumerate(user_rides):
        print(f'\nRide {i+1}:')
        print(f'  ID: {ride["_id"]}')
        print(f'  Origin: {ride.get("origin", "N/A")}')
        print(f'  Destination: {ride.get("destination", "N/A")}')
        print(f'  Communities: {ride.get("communities", [])}')
        print(f'  Status: {ride.get("status", "N/A")}')
        print(f'  Departure: {ride.get("departure_date", "N/A")}')
        print(f'  Creator: {ride.get("creator_email", "N/A")}')
        print(f'  User IDs: {ride.get("user_ids", [])}')
        print(f'  Max Participants: {ride.get("max_participants", "N/A")}')
        print(f'  Price per person: {ride.get("estimated_price_per_person", "N/A")}')
        print(f'  Travel time: {ride.get("estimated_travel_time", "N/A")}')
    
    # Check user college
    user = await users_collection.find_one({'email': 'dbellido@pomona.edu'})
    if user:
        print(f'\n=== USER INFO ===')
        print(f'Email: {user["email"]}')
        print(f'College: {user.get("college", "N/A")}')
    else:
        print('\nUser dbellido@pomona.edu not found!')
    
    # Check what rides should be visible to this user
    print(f'\n=== FILTERING CHECK ===')
    if user:
        user_college = user.get("college", "")
        college_to_community = {
            "Pomona College": "Pomona",
            "Harvey Mudd College": "Harvey Mudd",
            "Scripps College": "Scripps", 
            "Pitzer College": "Pitzer",
            "Claremont McKenna College": "CMC"
        }
        
        user_community = college_to_community.get(user_college, user_college)
        print(f'User college: {user_college}')
        print(f'User community: {user_community}')
        
        # Find rides this user should see
        visible_rides = []
        cursor = rides_collection.find({
            "communities": user_community,
            "status": "active"
        })
        async for ride in cursor:
            visible_rides.append(ride)
        
        print(f'Rides visible to this user: {len(visible_rides)}')
        for i, ride in enumerate(visible_rides):
            print(f'  Visible Ride {i+1}: {ride.get("origin", {}).get("description", "N/A")} → {ride.get("destination", {}).get("description", "N/A")}')

if __name__ == "__main__":
    asyncio.run(check_rides())