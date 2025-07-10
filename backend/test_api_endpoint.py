#!/usr/bin/env python3
"""
Test the community-options API endpoint directly
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import httpx
from database import users_collection
from services.university_detection import university_service
from utils.auth_utils import create_access_token

async def test_api_endpoint():
    """Test the /community-options endpoint"""
    
    print("🔍 Testing /community-options API endpoint...")
    
    # Create a test user with CMU email
    test_email = "student@cmu.edu"
    
    # Create JWT token for test user
    token = create_access_token(data={"email": test_email})
    print(f"🔐 Created test token for: {test_email}")
    
    # Test university detection and save to database
    university_info = university_service.detect_university_from_email(test_email)
    
    if university_info.get('valid'):
        print("✅ University detected, updating database...")
        
        # Update or create user with university_info
        await users_collection.update_one(
            {"email": test_email},
            {
                "$set": {
                    "email": test_email,
                    "university_info": university_info,
                    "college": university_info.get('university_name', 'Unknown')
                }
            },
            upsert=True
        )
        
        print(f"   University: {university_info['university_name']}")
        print(f"   Communities available: {len(university_info.get('nearby_universities', []))} nearby")
        
        # Test the API endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/community-options",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API endpoint working!")
                print(f"   Communities: {data['communities']}")
                print(f"   Source: {data['source']}")
                print(f"   User university: {data['user_university']['name']}")
                print(f"   Nearby universities: {len(data['nearby_universities'])}")
                
                # Show nearby universities
                for uni in data['nearby_universities']:
                    print(f"     • {uni['name']} (~{uni['distance_miles']} mi)")
                    
            else:
                print(f"❌ API endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
    else:
        print("❌ University detection failed!")
        print(f"   Error: {university_info.get('error', 'Unknown error')}")

if __name__ == "__main__":
    print("🎓 Testing Community Options API Endpoint")
    print("=" * 60)
    
    asyncio.run(test_api_endpoint())
    
    print("\n" + "="*60)
    print("✨ Testing completed!")