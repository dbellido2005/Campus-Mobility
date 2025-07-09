#!/usr/bin/env python3

import asyncio
import sys
from database import users_collection

async def test_db_connection():
    """Test if we can connect to the database"""
    try:
        # Try to count users in the collection
        count = await users_collection.count_documents({})
        print(f"✅ Database connection successful! Found {count} users.")
        
        # Try to find one user
        user = await users_collection.find_one({})
        if user:
            print(f"✅ Sample user found: {user.get('email', 'No email')}")
        else:
            print("ℹ️  No users found in database")
            
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_db_connection())
    sys.exit(0 if result else 1)