#!/usr/bin/env python3

import requests
import json

API_BASE_URL = "http://172.28.119.64:8000"

def test_api():
    print("=== Testing Ride Share API ===")
    
    # Test data for login
    login_data = {
        "email": "dbellido@pomona.edu",
        "password": "your_password_here"  # You'll need to provide the actual password
    }
    
    print("1. Testing login...")
    try:
        response = requests.post(f"{API_BASE_URL}/login", json=login_data)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            print(f"Login successful! Token: {token[:20]}...")
            
            # Test getting rides
            print("\n2. Testing get rides...")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            rides_response = requests.get(f"{API_BASE_URL}/ride-requests", headers=headers)
            print(f"Rides response status: {rides_response.status_code}")
            
            if rides_response.status_code == 200:
                rides = rides_response.json()
                print(f"Found {len(rides)} rides")
                for i, ride in enumerate(rides):
                    print(f"  Ride {i+1}: {ride.get('origin', {}).get('description', 'N/A')} → {ride.get('destination', {}).get('description', 'N/A')}")
                    print(f"    Communities: {ride.get('communities', [])}")
                    print(f"    Creator: {ride.get('creator_email', 'N/A')}")
            else:
                print(f"Error getting rides: {rides_response.text}")
                
            # Test getting user profile
            print("\n3. Testing get profile...")
            profile_response = requests.get(f"{API_BASE_URL}/profile", headers=headers)
            print(f"Profile response status: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                profile = profile_response.json()
                print(f"User college: {profile.get('college', 'N/A')}")
                print(f"User email: {profile.get('email', 'N/A')}")
            else:
                print(f"Error getting profile: {profile_response.text}")
        else:
            print(f"Login failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()