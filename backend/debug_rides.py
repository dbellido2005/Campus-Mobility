#!/usr/bin/env python3

import asyncio
import sys
import os

# Set API key for testing
os.environ['GOOGLE_ROUTES_API_KEY'] = 'AIzaSyAH5IR4dI-R3OXDobedXmyKJ4jz5mCYm64'

try:
    from database import rides_collection
    from services.google_routes import GoogleRoutesService
    
    # Create service instance after setting env var
    google_routes_service = GoogleRoutesService()
    
    async def debug_rides():
        """Debug ride data structure and coordinates"""
        try:
            print("🔍 Analyzing ride data structure...")
            
            # Count total rides
            total_rides = await rides_collection.count_documents({})
            print(f"📊 Total rides in database: {total_rides}")
            
            if total_rides == 0:
                print("ℹ️  No rides found in database")
                return
            
            # Get all rides to analyze
            cursor = rides_collection.find({})
            rides_with_coords = 0
            rides_without_coords = 0
            
            print("\n🔍 Analyzing each ride:")
            async for ride in cursor:
                ride_id = str(ride.get("_id", "unknown"))
                origin = ride.get("origin", {})
                destination = ride.get("destination", {})
                
                # Check if it's a dict or string
                if isinstance(origin, dict) and isinstance(destination, dict):
                    origin_desc = origin.get("description", "N/A")
                    dest_desc = destination.get("description", "N/A")
                    
                    has_origin_coords = origin.get("latitude") is not None and origin.get("longitude") is not None
                    has_dest_coords = destination.get("latitude") is not None and destination.get("longitude") is not None
                    
                    print(f"\n📍 Ride {ride_id[:8]}...")
                    print(f"   Origin: {origin_desc}")
                    print(f"   Origin coords: {origin.get('latitude', 'N/A')}, {origin.get('longitude', 'N/A')}")
                    print(f"   Destination: {dest_desc}")
                    print(f"   Dest coords: {destination.get('latitude', 'N/A')}, {destination.get('longitude', 'N/A')}")
                    print(f"   Has route_info: {'route_info' in ride}")
                    print(f"   Status: {ride.get('status', 'N/A')}")
                    
                    if has_origin_coords and has_dest_coords:
                        rides_with_coords += 1
                        print("   ✅ Has coordinates for route calculation")
                        
                        # Test route calculation for this ride
                        try:
                            route_info = await google_routes_service.get_route_info(
                                origin['latitude'],
                                origin['longitude'],
                                destination['latitude'],
                                destination['longitude']
                            )
                            
                            if route_info:
                                print(f"   🛣️  Route: {route_info.get('formatted_distance', 'N/A')} • {route_info.get('formatted_duration', 'N/A')}")
                            else:
                                print("   ❌ Failed to get route info from Google Routes API")
                        except Exception as e:
                            print(f"   ❌ Error calculating route: {str(e)}")
                    else:
                        rides_without_coords += 1
                        print("   ❌ Missing coordinates for route calculation")
                else:
                    print(f"\n📍 Ride {ride_id[:8]}... (legacy format)")
                    print(f"   Origin: {origin}")
                    print(f"   Destination: {destination}")
                    print("   ❌ Legacy string format - no coordinates")
                    rides_without_coords += 1
            
            print(f"\n📊 Summary:")
            print(f"   Rides with coordinates: {rides_with_coords}")
            print(f"   Rides without coordinates: {rides_without_coords}")
            print(f"   Total rides: {rides_with_coords + rides_without_coords}")
            
            if rides_without_coords > 0:
                print(f"\n💡 {rides_without_coords} rides need coordinate data for route calculation")
                
        except Exception as e:
            print(f"❌ Error analyzing rides: {str(e)}")
            return False
            
        return True

    if __name__ == "__main__":
        result = asyncio.run(debug_rides())
        sys.exit(0 if result else 1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure to install required packages: pip install motor pymongo")
    sys.exit(1)