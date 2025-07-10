#!/usr/bin/env python3
"""
Debug Chapman University communities issue
"""

import os
os.environ['GROQ_API_KEY'] = "***REMOVED***"

import sys
sys.path.append('.')
from services.university_detection import university_service

def debug_chapman_communities():
    print("🔍 Debugging Chapman University communities...")
    
    email = 'dbellido@chapman.edu'
    
    # Force fresh detection by clearing cache
    university_service.cache = {}
    
    # Get AI detection results
    print(f"\n1. Testing AI detection for {email}")
    university_info = university_service.detect_university_from_email(email)
    
    if university_info.get('valid'):
        print(f"✅ University: {university_info['university_name']}")
        print(f"📍 Location: {university_info['city']}, {university_info['state']}")
        
        nearby_unis = university_info.get('nearby_universities', [])
        print(f"\n2. Nearby universities found: {len(nearby_unis)}")
        for i, uni in enumerate(nearby_unis, 1):
            distance = uni.get('distance_miles', 0)
            print(f"   {i}. {uni['name']} ({uni['short_name']}) - {distance} miles")
            print(f"      Relationship: {uni['relationship']}")
        
        print(f"\n3. Community options:")
        communities = university_service.get_community_options_for_university(university_info)
        for i, community in enumerate(communities, 1):
            print(f"   {i}. {community}")
        
        # Check if any are over 10 miles
        print(f"\n4. Distance check:")
        far_universities = [uni for uni in nearby_unis if uni.get('distance_miles', 0) > 10]
        if far_universities:
            print("❌ Found universities over 10 miles:")
            for uni in far_universities:
                print(f"   • {uni['name']} - {uni['distance_miles']} miles")
        else:
            print("✅ All universities are within 10 miles")
            
    else:
        print("❌ University detection failed!")
        print(f"   Error: {university_info.get('error', 'Unknown error')}")

if __name__ == "__main__":
    debug_chapman_communities()