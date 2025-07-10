#!/usr/bin/env python3
"""
Debug script to investigate question/ride mismatches
"""
import asyncio
import requests
import json

API_BASE_URL = 'http://172.28.119.64:8000'

async def debug_questions():
    """Debug the questions issue"""
    
    # First, let's check what happens when we call the debug endpoint
    # You would need to get a valid token for the Mr. Gibbles account
    
    print("=== Question/Ride Mismatch Debug ===")
    print("To debug this issue, you need to:")
    print("1. Login as Mr. Gibbles account to get a JWT token")
    print("2. Call the debug endpoint with that token")
    print("3. Check the explore endpoint to see what rides are visible")
    print()
    print("Debug endpoints available:")
    print(f"GET {API_BASE_URL}/debug/question-ride-mismatch")
    print(f"GET {API_BASE_URL}/debug/user-info/[email]")
    print()
    print("Example curl commands (replace TOKEN with actual JWT):")
    print(f'curl -H "Authorization: Bearer TOKEN" "{API_BASE_URL}/debug/question-ride-mismatch"')
    print()
    print("This will show:")
    print("- All questions for the user")
    print("- Whether each ride still exists")
    print("- Ride status, communities, and visibility issues")
    print("- Why rides might not appear in explore")

if __name__ == "__main__":
    asyncio.run(debug_questions())