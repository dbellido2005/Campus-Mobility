# Email Setup Guide for Campus Mobility

This guide explains how to configure email sending functionality for verification emails.

## Overview

The Campus Mobility backend now supports sending professional HTML-formatted verification emails via Gmail SMTP. If SMTP is not configured, the system gracefully falls back to console output for development.

## Setup Instructions

### 1. Install Dependencies

Make sure you have the required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Gmail Configuration

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to [Google Account Security Settings](https://myaccount.google.com/security)
   - Navigate to "2-Step Verification"
   - Click "App Passwords"
   - Generate a new app password for "Mail"
   - Copy the 16-character password (remove spaces)

### 3. Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your Gmail credentials:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-gmail@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_FROM_NAME=Campus Mobility
   ```

### 4. Test the Implementation

Start your FastAPI server and test the signup endpoint:

```bash
uvicorn main:app --reload
```

## Email Features

### Professional HTML Design
- Campus Mobility branding with gradient header
- Clear verification code display with monospace font
- College information prominently displayed
- Mobile-responsive design
- Professional styling with consistent colors

### Robust Error Handling
- Graceful fallback to console output if SMTP fails
- Detailed error logging for debugging
- Authentication error handling
- Network connectivity error handling
- Invalid recipient error handling

### Security Features
- TLS encryption for email transmission
- App password authentication (more secure than regular passwords)
- Environment variable configuration (credentials not in code)

## Email Template Preview

The verification email includes:
- **Campus Mobility branding** with car emoji
- **College identification** based on email domain
- **Large, prominent verification code** in monospace font
- **1-hour expiry notice** highlighted in red
- **Clear instructions** for users
- **Professional footer** with team information

## Troubleshooting

### Common Issues

1. **Authentication Error**
   - Verify 2FA is enabled on Google account
   - Ensure you're using an App Password, not your regular password
   - Check that SMTP_USERNAME matches the Gmail account

2. **Connection Error**
   - Verify your network connection
   - Check if your firewall allows SMTP traffic on port 587
   - Ensure SMTP_SERVER and SMTP_PORT are correct

3. **Fallback Mode**
   - If emails aren't being sent, check console output
   - The system will print verification codes to console as fallback
   - Check server logs for specific error messages

### Development Mode

For development, you can run without email configuration:
- Leave SMTP_USERNAME and SMTP_PASSWORD empty in .env
- Verification codes will be printed to console
- The signup process will continue normally

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMTP_SERVER` | SMTP server address | smtp.gmail.com | No |
| `SMTP_PORT` | SMTP server port | 587 | No |
| `SMTP_USERNAME` | Your Gmail address | - | Yes (for email) |
| `SMTP_PASSWORD` | Gmail App Password | - | Yes (for email) |
| `SMTP_FROM_NAME` | Display name for emails | Campus Mobility | No |

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use App Passwords** instead of regular Gmail passwords
3. **Regularly rotate** your App Passwords
4. **Monitor** your Gmail account for unusual activity
5. **Use different credentials** for production vs development

## Production Considerations

For production deployment:
- Use a dedicated Gmail account for sending emails
- Consider using professional email services (SendGrid, SES, etc.)
- Set up proper logging and monitoring
- Configure rate limiting for email sending
- Add email templates for different notification types