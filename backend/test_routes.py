#!/usr/bin/env python3

import asyncio
import sys
import os

# Set API key for testing
os.environ['GOOGLE_ROUTES_API_KEY'] = '***REMOVED***'

from services.google_routes import GoogleRoutesService

# Create service instance after setting env var
google_routes_service = GoogleRoutesService()

async def test_routes_service():
    """Test Google Routes API service"""
    try:
        print("🧪 Testing Google Routes API...")
        
        # Test coordinates for Pomona College to LAX Airport
        origin_lat = 34.0969
        origin_lng = -117.7078
        dest_lat = 33.9425
        dest_lng = -118.4081
        
        print(f"📍 Origin: Pomona College ({origin_lat}, {origin_lng})")
        print(f"📍 Destination: LAX Airport ({dest_lat}, {dest_lng})")
        
        # Get route information
        route_info = await google_routes_service.get_route_info(
            origin_lat, origin_lng, dest_lat, dest_lng
        )
        
        if route_info:
            print("✅ Google Routes API call successful!")
            print(f"📏 Distance: {route_info.get('formatted_distance', 'N/A')}")
            print(f"⏱️  Duration: {route_info.get('formatted_duration', 'N/A')}")
            print(f"🛣️  Distance (meters): {route_info.get('distance_meters', 'N/A')}")
            print(f"⏰ Duration (minutes): {route_info.get('duration_minutes', 'N/A')}")
            print(f"🔗 Source: {route_info.get('source', 'N/A')}")
            return True
        else:
            print("❌ Google Routes API call failed")
            print("💡 Check your GOOGLE_ROUTES_API_KEY environment variable")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Google Routes API: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_routes_service())
    sys.exit(0 if result else 1)