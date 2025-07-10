#!/usr/bin/env python3
"""
Test script to verify AI-powered university detection and community options
for Carnegie Mellon University
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.university_detection import university_service

async def test_cmu_detection():
    """Test university detection for Carnegie Mellon"""
    
    print("🔍 Testing Carnegie Mellon University detection...")
    
    # Test email detection
    cmu_email = "student@cmu.edu"
    print(f"\n📧 Testing email: {cmu_email}")
    
    university_info = university_service.detect_university_from_email(cmu_email)
    
    if university_info.get('valid'):
        print("✅ University detected successfully!")
        print(f"   University: {university_info['university_name']}")
        print(f"   Short name: {university_info['short_name']}")
        print(f"   Location: {university_info['city']}, {university_info['state']}")
        print(f"   Type: {university_info.get('university_type', 'Unknown')}")
        print(f"   Population: {university_info.get('student_population', 'Unknown')}")
        
        # Test community options
        communities = university_service.get_community_options_for_university(university_info)
        print(f"\n🏫 Community options for CMU students:")
        for i, community in enumerate(communities, 1):
            print(f"   {i}. {community}")
        
        # Show nearby universities
        nearby_unis = university_info.get('nearby_universities', [])
        if nearby_unis:
            print(f"\n🗺️  Nearby universities ({len(nearby_unis)} found):")
            for uni in nearby_unis:
                print(f"   • {uni['name']} ({uni['short_name']})")
                print(f"     Distance: ~{uni['distance_miles']} miles")
                print(f"     Relationship: {uni['relationship']}")
                print()
    else:
        print("❌ University detection failed!")
        print(f"   Error: {university_info.get('error', 'Unknown error')}")

async def test_other_universities():
    """Test with other university examples"""
    
    test_emails = [
        "student@andrew.cmu.edu",  # Another CMU domain
        "student@pitt.edu",        # University of Pittsburgh
        "student@duq.edu",         # Duquesne
        "student@mit.edu",         # MIT
        "student@harvard.edu",     # Harvard
    ]
    
    print("\n" + "="*60)
    print("🧪 Testing other universities...")
    
    for email in test_emails:
        print(f"\n📧 Testing: {email}")
        university_info = university_service.detect_university_from_email(email)
        
        if university_info.get('valid'):
            print(f"   ✅ {university_info['university_name']} ({university_info['short_name']})")
            print(f"   📍 {university_info['city']}, {university_info['state']}")
            
            communities = university_service.get_community_options_for_university(university_info)
            print(f"   🏫 Communities: {', '.join(communities[:3])}{'...' if len(communities) > 3 else ''}")
        else:
            print(f"   ❌ {university_info.get('error', 'Detection failed')}")

if __name__ == "__main__":
    print("🎓 Testing AI-Powered University Detection System")
    print("=" * 60)
    
    asyncio.run(test_cmu_detection())
    asyncio.run(test_other_universities())
    
    print("\n" + "="*60)
    print("✨ Testing completed!")