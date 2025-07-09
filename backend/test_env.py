#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables like main.py does
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

print("=== Environment Variables Check ===")
print(f"GOOGLE_PLACES_API_KEY: {os.getenv('GOOGLE_PLACES_API_KEY', 'NOT FOUND')[:20]}...")
print(f"GOOGLE_ROUTES_API_KEY: {os.getenv('GOOGLE_ROUTES_API_KEY', 'NOT FOUND')[:20]}...")

# Test the service initialization
try:
    from services.google_routes import google_routes_service
    print(f"Google Routes Service API Key: {google_routes_service.api_key[:20] if google_routes_service.api_key else 'NOT FOUND'}...")
except Exception as e:
    print(f"Error importing google_routes_service: {e}")