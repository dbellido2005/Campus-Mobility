#\!/usr/bin/env python3
"""
Test Chapman University detection
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.university_detection import university_service

def test_chapman_detection():
    """Test university detection for Chapman University"""
    
    print("🔍 Testing Chapman University detection...")
    
    # Test Chapman email detection
    chapman_emails = [
        "student@chapman.edu",
        "dbellido@chapman.edu",  # Your actual email
        "test@chapman.edu"
    ]
    
    for email in chapman_emails:
        print(f"\n📧 Testing email: {email}")
        
        university_info = university_service.detect_university_from_email(email)
        
        if university_info.get('valid'):
            print("✅ University detected successfully\!")
            print(f"   University: {university_info['university_name']}")
            print(f"   Short name: {university_info['short_name']}")
            print(f"   Location: {university_info['city']}, {university_info['state']}")
            print(f"   Type: {university_info.get('university_type', 'Unknown')}")
            print(f"   Population: {university_info.get('student_population', 'Unknown')}")
            
            # Test community options
            communities = university_service.get_community_options_for_university(university_info)
            print(f"\n🏫 Community options for Chapman students:")
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
            print("❌ University detection failed\!")
            print(f"   Error: {university_info.get('error', 'Unknown error')}")

if __name__ == "__main__":
    # Set the environment variable
    os.environ['GROQ_API_KEY'] = "***REMOVED***"
    
    print("🎓 Testing Chapman University Detection")
    print("=" * 60)
    
    test_chapman_detection()
    
    print("\n" + "="*60)
    print("✨ Testing completed\!")
EOF < /dev/null