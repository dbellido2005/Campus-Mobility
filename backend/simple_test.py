#!/usr/bin/env python3
"""
Simple test for university detection
"""

import os
import sys

# Set environment variables directly
os.environ['GROQ_API_KEY'] = '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'

# Add the backend directory to the path
sys.path.insert(0, '/Users/danielabellido/campusMobility/backend')

try:
    from services.university_detection import university_service
    
    print("🔍 Testing AI-Powered University Detection")
    print("=" * 40)
    
    # Test MIT
    print("\n🎓 Testing MIT (student@mit.edu)")
    result = university_service.detect_university_from_email('student@mit.edu')
    print(f"Valid: {result.get('valid')}")
    if result.get('valid'):
        print(f"University: {result.get('university_name')}")
        print(f"Location: {result.get('city')}, {result.get('state')}")
        nearby = result.get('nearby_universities', [])
        print(f"Nearby universities: {len(nearby)}")
        for univ in nearby[:3]:
            print(f"  - {univ.get('name')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Test Carnegie Mellon
    print("\n🎓 Testing Carnegie Mellon (student@andrew.cmu.edu)")
    result2 = university_service.detect_university_from_email('student@andrew.cmu.edu')
    print(f"Valid: {result2.get('valid')}")
    if result2.get('valid'):
        print(f"University: {result2.get('university_name')}")
        print(f"Location: {result2.get('city')}, {result2.get('state')}")
        nearby = result2.get('nearby_universities', [])
        print(f"Nearby universities: {len(nearby)}")
        for univ in nearby[:3]:
            print(f"  - {univ.get('name')}")
    else:
        print(f"Error: {result2.get('error')}")
        
    print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()