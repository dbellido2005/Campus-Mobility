#!/usr/bin/env python3

import asyncio
import sys
import os

# Set API key
os.environ['GOOGLE_ROUTES_API_KEY'] = '***REMOVED***'

from services.google_routes import GoogleRoutesService

async def test_google_routes():
    """Test Google Routes service with real coordinates"""
    
    service = GoogleRoutesService()
    
    # Test with Pomona College to LAX
    print("🧪 Testing Google Routes API service...")
    
    route_info = await service.get_route_info(
        34.0969, -117.7078,  # Pomona College
        33.9425, -118.4081   # LAX Airport
    )
    
    if route_info:
        print("✅ Google Routes API working correctly!")
        print(f"📏 Distance: {route_info.get('formatted_distance', 'N/A')}")
        print(f"⏱️  Duration: {route_info.get('formatted_duration', 'N/A')}")
        print(f"🔢 Raw distance: {route_info.get('distance_meters', 'N/A')} meters")
        print(f"🔢 Raw duration: {route_info.get('duration_minutes', 'N/A')} minutes")
        
        # Test the data structure
        expected_fields = ['distance_meters', 'distance_miles', 'formatted_distance', 
                          'duration_seconds', 'duration_minutes', 'formatted_duration', 
                          'polyline', 'source']
        
        missing_fields = [field for field in expected_fields if field not in route_info]
        if missing_fields:
            print(f"⚠️  Missing fields in response: {missing_fields}")
        else:
            print("✅ All expected fields present in response")
        
        return True
    else:
        print("❌ Google Routes API failed to return data")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_google_routes())
    sys.exit(0 if result else 1)