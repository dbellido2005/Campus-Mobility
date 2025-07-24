#!/usr/bin/env python3
"""
Test script for Gmail API email functionality
Usage: python test_gmail.py <recipient_email>
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.gmail_service import gmail_service
from utils.email_utils import send_verification_email, send_password_reset_email

def test_gmail_service():
    """Test Gmail API service initialization"""
    print("=== Gmail Service Test ===")
    print(f"Service initialized: {gmail_service.service is not None}")
    print(f"Credentials valid: {gmail_service.credentials and gmail_service.credentials.valid}")
    
    if gmail_service.credentials:
        print(f"Scopes: {gmail_service.credentials.scopes}")
    else:
        print("No credentials found")
    
    return gmail_service.service is not None

def test_verification_email(recipient_email: str):
    """Test verification email sending"""
    print(f"\n=== Verification Email Test ===")
    print(f"Sending to: {recipient_email}")
    
    success = send_verification_email(
        email=recipient_email,
        code="123456",
        college="Test College"
    )
    
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    return success

def test_password_reset_email(recipient_email: str):
    """Test password reset email sending"""
    print(f"\n=== Password Reset Email Test ===")
    print(f"Sending to: {recipient_email}")
    
    success = send_password_reset_email(
        email=recipient_email,
        reset_code="654321",
        college="Test College"
    )
    
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    return success

def test_direct_gmail_send(recipient_email: str):
    """Test direct Gmail API sending"""
    print(f"\n=== Direct Gmail API Test ===")
    print(f"Sending to: {recipient_email}")
    
    if not gmail_service.service:
        print("Gmail service not available")
        return False
    
    success = gmail_service.send_verification_email(
        email=recipient_email,
        code="999888",
        college="Direct Test College"
    )
    
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    return success

def main():
    """Main test function"""
    if len(sys.argv) != 2:
        print("Usage: python test_gmail.py <recipient_email>")
        print("Example: python test_gmail.py your-email@gmail.com")
        sys.exit(1)
    
    recipient_email = sys.argv[1]
    
    print("Campus Mobility - Gmail API Test Script")
    print("======================================")
    
    # Test Gmail service initialization
    service_ok = test_gmail_service()
    
    # Test email functions
    verification_ok = test_verification_email(recipient_email)
    reset_ok = test_password_reset_email(recipient_email)
    
    if service_ok:
        direct_ok = test_direct_gmail_send(recipient_email)
    else:
        direct_ok = False
        print("\nSkipping direct Gmail test - service not initialized")
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Gmail Service: {'✓' if service_ok else '✗'}")
    print(f"Verification Email: {'✓' if verification_ok else '✗'}")
    print(f"Password Reset Email: {'✓' if reset_ok else '✗'}")
    print(f"Direct Gmail Send: {'✓' if direct_ok else '✗'}")
    
    if service_ok:
        print("\n✅ Gmail API is working!")
    else:
        print("\n❌ Gmail API needs configuration")
        print("\nTo set up Gmail API:")
        print("1. Go to Google Cloud Console")
        print("2. Enable Gmail API")
        print("3. Create OAuth2 credentials")
        print("4. Set environment variables:")
        print("   - GMAIL_CREDENTIALS_JSON")
        print("   - GMAIL_TOKEN_JSON")
        print("   - GMAIL_FROM_EMAIL")

if __name__ == "__main__":
    main()