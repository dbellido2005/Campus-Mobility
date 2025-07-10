#!/usr/bin/env python3
"""
Test script for AI-powered university detection system
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

try:
    from services.university_detection import university_service
    from utils.email_utils import validate_college_email
    
    def test_university_detection():
        """Test university detection with various email domains"""
        
        print("🔍 Testing AI-Powered University Detection System")
        print("=" * 50)
        
        # Test cases
        test_emails = [
            "student@mit.edu",
            "user@andrew.cmu.edu",
            "test@stanford.edu",
            "person@harvard.edu",
            "someone@ucla.edu",
            "user@pomona.edu",  # Known Claremont College
            "invalid@notauniversity.edu",
            "test@fakeuni.edu"
        ]
        
        for email in test_emails:
            print(f"\n🎓 Testing: {email}")
            print("-" * 30)
            
            try:
                # Test direct university detection
                result = university_service.detect_university_from_email(email)
                
                if result.get('valid'):
                    print(f"✅ University: {result.get('university_name')}")
                    print(f"   Short name: {result.get('short_name')}")
                    print(f"   Location: {result.get('city')}, {result.get('state')}")
                    print(f"   Type: {result.get('university_type')}")
                    
                    nearby = result.get('nearby_universities', [])
                    if nearby:
                        print(f"   Nearby universities: {len(nearby)}")
                        for univ in nearby[:3]:  # Show first 3
                            print(f"     - {univ.get('name')} ({univ.get('distance_miles')} miles)")
                    else:
                        print("   No nearby universities found")
                else:
                    print(f"❌ Error: {result.get('error')}")
                    
            except Exception as e:
                print(f"🚨 Exception: {e}")
        
        print("\n" + "=" * 50)
        print("🧪 Testing Enhanced Email Validation")
        print("=" * 50)
        
        # Test enhanced email validation
        for email in test_emails[:4]:  # Test first 4 emails
            print(f"\n📧 Testing validation: {email}")
            print("-" * 30)
            
            try:
                validation_result = validate_college_email(email)
                
                if validation_result.get('valid'):
                    print(f"✅ Valid: {validation_result.get('college')}")
                    university_info = validation_result.get('university_info', {})
                    if university_info.get('legacy'):
                        print("   Source: Legacy mapping")
                    else:
                        print("   Source: AI detection")
                        print(f"   Location: {university_info.get('city')}, {university_info.get('state')}")
                else:
                    print(f"❌ Invalid: {validation_result.get('error')}")
                    
            except Exception as e:
                print(f"🚨 Exception: {e}")
    
    if __name__ == "__main__":
        test_university_detection()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the backend directory and all dependencies are installed.")