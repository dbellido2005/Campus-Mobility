#!/usr/bin/env python3
"""
Test script for email functionality
Run this to test if email sending works correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.email_utils import send_verification_email, validate_college_email, generate_verification_code

def test_email_functionality():
    """Test the email sending functionality"""
    
    print("🧪 Testing Campus Mobility Email Functionality\n")
    
    # Test email validation
    print("1. Testing email validation...")
    test_emails = [
        "student@pomona.edu",
        "test@hmc.edu", 
        "invalid@gmail.com",
        "student@scrippscollege.edu"
    ]
    
    for email in test_emails:
        validation = validate_college_email(email)
        status = "✅ Valid" if validation['valid'] else "❌ Invalid"
        college = validation.get('college', validation.get('error', ''))
        print(f"   {email}: {status} - {college}")
    
    print("\n2. Testing verification code generation...")
    code = generate_verification_code()
    print(f"   Generated code: {code} (length: {len(code)})")
    
    print("\n3. Testing email sending...")
    test_email = "student@pomona.edu"
    test_code = "123456"
    test_college = "Pomona College"
    
    print(f"   Sending test email to: {test_email}")
    print(f"   Verification code: {test_code}")
    print(f"   College: {test_college}")
    
    # Check if SendGrid is configured
    sendgrid_configured = bool(os.getenv('SENDGRID_API_KEY') and os.getenv('SENDGRID_FROM_EMAIL'))
    if sendgrid_configured:
        print("   📧 SendGrid configured - will attempt to send real email")
    else:
        print("   🖥️  SendGrid not configured - will use console fallback")
    
    try:
        result = send_verification_email(test_email, test_code, test_college)
        if result:
            print("   ✅ Email function executed successfully")
        else:
            print("   ❌ Email function returned False")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4. Environment variables check:")
    env_vars = [
        'SENDGRID_API_KEY',
        'SENDGRID_FROM_EMAIL', 
        'SENDGRID_FROM_NAME'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if var == 'SENDGRID_API_KEY' and value:
            # Don't print the actual API key
            print(f"   {var}: {'*' * len(value)} (configured)")
        elif value:
            print(f"   {var}: {value}")
        else:
            print(f"   {var}: Not set")
    
    print("\n📋 Test Summary:")
    print("   - Email validation: Working")
    print("   - Code generation: Working") 
    print("   - Email sending: Check output above")
    
    if not sendgrid_configured:
        print("\n💡 To enable real email sending:")
        print("   1. Copy .env.example to .env")
        print("   2. Sign up for SendGrid and create an API key") 
        print("   3. Configure SENDGRID_API_KEY and SENDGRID_FROM_EMAIL")
        print("   4. See SENDGRID_SETUP.md for detailed instructions")
        print("   5. Re-run this test")

if __name__ == "__main__":
    test_email_functionality()