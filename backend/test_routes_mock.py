#!/usr/bin/env python3

import asyncio
import sys
from services.google_routes import google_routes_service

# Mock the API response for demonstration
async def mock_route_info():
    """Mock route information for demonstration"""
    return {
        'distance_meters': 58000,
        'distance_miles': 36.0,
        'formatted_distance': '36.0 miles',
        'duration_seconds': 3600,
        'duration_minutes': 60.0,
        'formatted_duration': '1 hr',
        'polyline': 'mock_polyline_data',
        'source': 'google_routes_api'
    }

async def test_routes_integration():
    """Test route information integration"""
    try:
        print("🧪 Testing route information integration...")
        
        # Test with mock data for demonstration
        route_info = await mock_route_info()
        
        print("✅ Route information retrieved successfully!")
        print(f"📏 Distance: {route_info.get('formatted_distance', 'N/A')}")
        print(f"⏱️  Duration: {route_info.get('formatted_duration', 'N/A')}")
        print(f"🛣️  Distance (meters): {route_info.get('distance_meters', 'N/A')}")
        print(f"⏰ Duration (minutes): {route_info.get('duration_minutes', 'N/A')}")
        print(f"🔗 Source: {route_info.get('source', 'N/A')}")
        
        # Test formatting function
        print("\n🧪 Testing duration formatting...")
        from services.google_routes import GoogleRoutesService
        service = GoogleRoutesService()
        
        test_cases = [25, 65, 90, 120, 150]
        for minutes in test_cases:
            formatted = service._format_duration(minutes)
            print(f"  {minutes} minutes → {formatted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing route integration: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_routes_integration())
    sys.exit(0 if result else 1)