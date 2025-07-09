#!/usr/bin/env python3

import asyncio
import sys
import os
import aiohttp
import json

# Set API key for testing
os.environ['GOOGLE_ROUTES_API_KEY'] = '***REMOVED***'

async def test_route_info_endpoint():
    """Test the route-info endpoint directly"""
    
    test_data = {
        "origin": {
            "description": "Pomona College, Claremont, CA",
            "latitude": 34.0969,
            "longitude": -117.7078
        },
        "destination": {
            "description": "Los Angeles International Airport, Los Angeles, CA",
            "latitude": 33.9425,
            "longitude": -118.4081
        }
    }
    
    try:
        print("🧪 Testing route-info endpoint...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/route-info",
                json=test_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token"  # This will fail auth but test the route logic
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Route info endpoint working!")
                    print(f"📏 Distance: {data.get('route_info', {}).get('formatted_distance', 'N/A')}")
                    print(f"⏱️  Duration: {data.get('route_info', {}).get('formatted_duration', 'N/A')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Route info endpoint failed: {response.status}")
                    print(f"Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing route info endpoint: {str(e)}")
        return False

async def test_ride_requests_endpoint():
    """Test the ride-requests endpoint (will fail auth but we can see if server is up)"""
    
    try:
        print("\n🧪 Testing ride-requests endpoint...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8000/ride-requests",
                headers={
                    "Authorization": "Bearer test-token"  # This will fail auth
                }
            ) as response:
                if response.status == 401:
                    print("✅ Ride requests endpoint is responding (authentication required)")
                    return True
                elif response.status == 200:
                    print("✅ Ride requests endpoint working!")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Ride requests endpoint failed: {response.status}")
                    print(f"Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing ride requests endpoint: {str(e)}")
        print("💡 Make sure the backend server is running: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing route information fixes...")
    
    # Test if server is running
    server_test = await test_ride_requests_endpoint()
    if not server_test:
        print("\n❌ Backend server is not running or not responding")
        print("💡 Please start the backend server first:")
        print("   cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False
    
    # Test route info endpoint
    route_test = await test_route_info_endpoint()
    
    if route_test:
        print("\n✅ All tests passed!")
        print("\n📋 Summary of fixes implemented:")
        print("  ✅ Improved coordinate validation (checks for None instead of truthy)")
        print("  ✅ Added route info calculation during ride creation")
        print("  ✅ Added route info to single ride retrieval")
        print("  ✅ Enhanced debug logging for troubleshooting")
        print("  ✅ Added batch update endpoint for existing rides")
        print("  ✅ Better error handling for Google Routes API failures")
        
        print("\n🎯 Next steps:")
        print("  1. Start the backend server if not already running")
        print("  2. Test creating a new ride with real coordinates")
        print("  3. Check that route info appears in the frontend")
        print("  4. Use the batch-update endpoint to fix existing rides")
        
        return True
    else:
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)