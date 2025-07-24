# Gmail API Setup Guide

This guide will help you set up Gmail API for sending verification and password reset emails in Campus Mobility.

## Prerequisites

- Google account
- Access to Google Cloud Console
- Python dependencies installed (`pip install -r requirements.txt`)

## Step 1: Google Cloud Console Setup

### 1.1 Create/Select a Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID

### 1.2 Enable Gmail API
1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click on "Gmail API" and click "Enable"

### 1.3 Create OAuth2 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (App name: "Campus Mobility", User support email, Developer contact)
   - Add your email to test users
4. For Application type, choose "Desktop application"
5. Name it "Campus Mobility Gmail Client"
6. Click "Create"
7. Download the JSON file (it will be named something like `client_secret_xxx.json`)

## Step 2: Generate Access Token

### 2.1 Initial Authentication (Development)
1. Rename the downloaded credentials file to `gmail_credentials.json` and place it in the `backend/` directory
2. Run the test script to generate your token:
   ```bash
   cd backend
   python test_gmail.py your-email@gmail.com
   ```
3. This will open a browser window for authentication
4. Grant permissions to send emails
5. A `gmail_token.json` file will be created

### 2.2 Production Setup (Environment Variables)
For production, convert the JSON files to environment variables:

```bash
# Read the credentials file
GMAIL_CREDENTIALS_JSON=$(cat gmail_credentials.json)

# Read the token file
GMAIL_TOKEN_JSON=$(cat gmail_token.json)

# Set environment variables
export GMAIL_CREDENTIALS_JSON='<paste credentials json here>'
export GMAIL_TOKEN_JSON='<paste token json here>'
export GMAIL_FROM_EMAIL='your-app-email@gmail.com'
```

## Step 3: Environment Variables

Add these to your `.env` file or environment:

```env
# Gmail API Configuration
GMAIL_CREDENTIALS_JSON={"installed":{"client_id":"...","client_secret":"...","auth_uri":"...","token_uri":"..."}}
GMAIL_TOKEN_JSON={"token":"...","refresh_token":"...","token_uri":"...","client_id":"...","client_secret":"...",...}
GMAIL_FROM_EMAIL=noreply@yourdomain.com

# Optional: Keep SendGrid as fallback
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=Campus Mobility
```

## Step 4: Test the Setup

Run the test script:
```bash
cd backend
python test_gmail.py recipient@example.com
```

Expected output:
```
Campus Mobility - Gmail API Test Script
======================================
=== Gmail Service Test ===
Service initialized: True
Credentials valid: True
Scopes: ['https://www.googleapis.com/auth/gmail.send']

=== Verification Email Test ===
Sending to: recipient@example.com
Result: SUCCESS

=== Password Reset Email Test ===
Sending to: recipient@example.com
Result: SUCCESS

=== Direct Gmail API Test ===
Sending to: recipient@example.com
Result: SUCCESS

=== Test Summary ===
Gmail Service: ✓
Verification Email: ✓
Password Reset Email: ✓
Direct Gmail Send: ✓

✅ Gmail API is working!
```

## Step 5: Security Considerations

### 5.1 Credential Security
- Never commit `gmail_credentials.json` or `gmail_token.json` to version control
- Add them to `.gitignore`
- In production, use environment variables only

### 5.2 OAuth Consent Screen
- For production, submit your app for verification
- Add proper privacy policy and terms of service
- Limit scopes to only what's needed (`gmail.send`)

### 5.3 Rate Limits
- Gmail API has rate limits (250 requests/user/second)
- The service handles errors gracefully with SendGrid fallback

## Troubleshooting

### Common Issues

1. **"Gmail service not initialized"**
   - Check that credentials are properly set
   - Verify Gmail API is enabled
   - Check credential file format

2. **"Credentials not valid"**
   - Token may have expired
   - Re-run authentication flow
   - Check refresh token

3. **"Access forbidden"**
   - Check OAuth consent screen configuration
   - Verify user is added to test users
   - Ensure proper scopes are granted

4. **"Rate limit exceeded"**
   - Service automatically falls back to SendGrid
   - Consider implementing retry logic with exponential backoff

### Debug Mode
Set logging to DEBUG level to see detailed Gmail API calls:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Fallback Strategy

The system is designed with multiple fallbacks:
1. **Primary**: Gmail API
2. **Secondary**: SendGrid API  
3. **Tertiary**: Console output (development)

If Gmail API fails, the system automatically tries SendGrid, then console output, ensuring emails are never completely lost.

## Production Deployment

For production deployment:
1. Set environment variables securely
2. Never include credential files in Docker images
3. Use secrets management (AWS Secrets Manager, Google Secret Manager, etc.)
4. Monitor API quotas and usage
5. Set up alerts for email sending failures