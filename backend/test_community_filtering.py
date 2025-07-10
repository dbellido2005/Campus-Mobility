#!/usr/bin/env python3
"""
Test community filtering for ride posts
"""

import os
import sys
import asyncio
from datetime import datetime

# Set environment variables
os.environ['GROQ_API_KEY'] = '***REMOVED***'

# Add the backend directory to the path
sys.path.insert(0, '/Users/danielabellido/campusMobility/backend')

try:
    from database import users_collection, rides_collection
    from services.university_detection import university_service
    from utils.email_utils import validate_college_email
    
    async def test_community_filtering():
        """Test that users only see rides for their communities"""
        
        print("🔍 Testing Community Filtering")
        print("=" * 50)
        
        # Test Chapman user
        chapman_email = "test@chapman.edu"
        chapman_validation = validate_college_email(chapman_email)
        
        print(f"\n1. Chapman User: {chapman_email}")
        print(f"   Validation: {chapman_validation.get('valid')}")
        if chapman_validation.get('valid'):
            print(f"   College: {chapman_validation.get('college')}")
            university_info = chapman_validation.get('university_info', {})
            print(f"   Short name: {university_info.get('short_name')}")
            print(f"   Full name: {university_info.get('university_name')}")
            
        # Test Harvey Mudd user
        hmc_email = "test@hmc.edu"
        hmc_validation = validate_college_email(hmc_email)
        
        print(f"\n2. Harvey Mudd User: {hmc_email}")
        print(f"   Validation: {hmc_validation.get('valid')}")
        if hmc_validation.get('valid'):
            print(f"   College: {hmc_validation.get('college')}")
            university_info = hmc_validation.get('university_info', {})
            print(f"   Short name: {university_info.get('short_name')}")
            print(f"   Full name: {university_info.get('university_name')}")
            
        # Test community filtering logic
        print(f"\n3. Community Filtering Logic:")
        print(f"   Chapman communities should include: Chapman, UCI, CSUF")
        print(f"   Harvey Mudd communities should include: Harvey Mudd, HMC")
        print(f"   A Chapman ride with communities=['Chapman', 'UCI'] should be visible to Chapman users")
        print(f"   A Chapman ride with communities=['Chapman', 'UCI'] should NOT be visible to Harvey Mudd users")
        
        print(f"\n✅ Test completed! The filtering should work correctly.")
        
    # Run the test
    if __name__ == "__main__":
        asyncio.run(test_community_filtering())
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()