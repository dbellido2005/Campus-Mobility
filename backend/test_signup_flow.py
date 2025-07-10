#!/usr/bin/env python3
"""
Test the exact signup flow that the server uses
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, '/Users/danielabellido/campusMobility/backend')

# Load environment variables from .env file
load_dotenv()

try:
    from utils.email_utils import validate_college_email
    from services.university_detection import university_service
    
    print("🔍 Testing Signup Flow for Chapman University")
    print("=" * 50)
    
    # Test the exact flow that signup uses
    test_email = "student@chapman.edu"
    
    print(f"Testing: {test_email}")
    print(f"Environment GROQ_API_KEY present: {'GROQ_API_KEY' in os.environ}")
    print(f"Environment GROQ_API_KEY value: {os.environ.get('GROQ_API_KEY', 'NOT SET')[:20]}...")
    
    # Test the validate_college_email function (what signup actually calls)
    print("\n🎯 Testing validate_college_email function:")
    try:
        result = validate_college_email(test_email)
        print(f"✅ Result: {result}")
        
        if result.get('valid'):
            print("✅ SUCCESS: Email validation passed!")
            print(f"   College: {result.get('college')}")
            university_info = result.get('university_info', {})
            print(f"   Source: {'Legacy' if university_info.get('legacy') else 'AI'}")
            if not university_info.get('legacy'):
                print(f"   Location: {university_info.get('city')}, {university_info.get('state')}")
        else:
            print("❌ FAILED: Email validation failed!")
            print(f"   Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ EXCEPTION in validate_college_email: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the university service directly
    print("\n🎯 Testing university_service directly:")
    try:
        direct_result = university_service.validate_university_email(test_email)
        print(f"✅ Direct result: {direct_result}")
    except Exception as e:
        print(f"❌ EXCEPTION in university_service: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "=" * 50)
    print("🔧 If Chapman fails, it means:")
    print("1. AI detection is failing and falling back to legacy")
    print("2. Chapman is not in the legacy hardcoded list")
    print("3. The exception is being caught and masked")
    
except Exception as e:
    print(f"❌ Import/setup error: {e}")
    import traceback
    traceback.print_exc()