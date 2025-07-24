import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
import logging

# Import Gmail service
try:
    from services.gmail_service import gmail_service
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("WARNING: Gmail API not available")

# Optional sendgrid imports - fallback to console if not available
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, From, To, Subject, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("WARNING: SendGrid not available - emails will be printed to console")

# Import AI-powered university detection service
from services.university_detection import university_service

# Legacy college domain mapping (fallback for known institutions)
LEGACY_COLLEGE_DOMAINS = {
    'pomona.edu': 'Pomona College',
    'hmc.edu': 'Harvey Mudd College',
    'scrippscollege.edu': 'Scripps College',
    'pitzer.edu': 'Pitzer College',
    'cmc.edu': 'Claremont McKenna College',
    'andrew.cmu.edu': 'Carnegie Mellon University'
}

def validate_college_email(email: str) -> Dict[str, any]:
    """
    Enhanced email validation with AI-powered university detection
    
    This function now uses Groq AI to detect universities from any .edu domain,
    with fallback to legacy hardcoded mappings for known institutions.
    """
    try:
        # Try AI-powered detection first
        result = university_service.validate_university_email(email)
        
        if result['valid']:
            # Transform AI result to match legacy format
            return {
                'valid': True,
                'college': result['university_name'],
                'university_info': result  # Include full AI data
            }
        else:
            # Fallback to legacy mapping for known domains
            domain = email.split('@')[1].lower() if '@' in email else ''
            
            if not domain.endswith('.edu'):
                return {
                    'valid': False,
                    'error': 'Only .edu email addresses are allowed'
                }
            
            college = LEGACY_COLLEGE_DOMAINS.get(domain)
            if college:
                return {
                    'valid': True,
                    'college': college,
                    'university_info': {
                        'university_name': college,
                        'short_name': college.split(' ')[0],  # Simple short name
                        'legacy': True
                    }
                }
            else:
                return {
                    'valid': False,
                    'error': f'Email domain not recognized. We now support all universities - please contact support if this error persists.'
                }
                
    except Exception as e:
        logging.error(f"Error in email validation: {e}")
        
        # Ultimate fallback to legacy system
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        if not domain.endswith('.edu'):
            return {
                'valid': False,
                'error': 'Only .edu email addresses are allowed'
            }
        
        college = LEGACY_COLLEGE_DOMAINS.get(domain)
        if college:
            return {
                'valid': True,
                'college': college,
                'university_info': {
                    'university_name': college,
                    'short_name': college.split(' ')[0],
                    'legacy': True,
                    'fallback': True
                }
            }
        else:
            return {
                'valid': False,
                'error': 'University detection service temporarily unavailable. Please try again later.'
            }

def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def get_verification_expiry() -> datetime:
    """Get expiry time for verification code (1 hour from now)"""
    return datetime.utcnow() + timedelta(hours=1)

def create_verification_email_html(code: str, college: str) -> str:
    """Create HTML-formatted verification email"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Campus Mobility - Email Verification</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            @media only screen and (max-width: 600px) {{
                .container {{
                    margin: 10px;
                    max-width: calc(100% - 20px);
                }}
                .content {{
                    padding: 20px 15px !important;
                }}
                .verification-code {{
                    font-size: 24px !important;
                    letter-spacing: 3px !important;
                }}
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 300;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .verification-code {{
                background-color: #f8f9fa;
                border: 2px dashed #667eea;
                border-radius: 10px;
                padding: 20px;
                margin: 30px 0;
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
                letter-spacing: 5px;
                font-family: 'Courier New', monospace;
            }}
            .college-info {{
                background-color: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
            .expiry-notice {{
                color: #dc3545;
                font-weight: bold;
                margin: 20px 0;
            }}
            .instructions {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
                color: #856404;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 Campus Mobility</h1>
                <p>Connecting Claremont Colleges</p>
            </div>
            
            <div class="content">
                <h2>Welcome to Campus Mobility!</h2>
                <p>Thank you for joining our ride-sharing community. To complete your registration, please verify your email address.</p>
                
                <div class="college-info">
                    <strong>📚 College:</strong> {college}
                </div>
                
                <div class="instructions">
                    <strong>Instructions:</strong><br>
                    Enter the verification code below in the Campus Mobility app to activate your account.
                </div>
                
                <div class="verification-code">
                    {code}
                </div>
                
                <div class="expiry-notice">
                    ⏰ This code will expire in 1 hour
                </div>
                
                <p>If you didn't request this verification, please ignore this email.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p><strong>Need help?</strong><br>
                If you're having trouble with verification, please contact our support team.</p>
            </div>
            
            <div class="footer">
                <p>Campus Mobility Team<br>
                Connecting students across the 5C community</p>
                <p style="font-size: 12px; color: #adb5bd;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_verification_email(email: str, code: str, college: str) -> bool:
    """Send verification email using Gmail API (preferred) or SendGrid API (fallback)"""
    
    # Try Gmail API first
    if GMAIL_AVAILABLE and gmail_service.service:
        logging.info("Attempting to send verification email via Gmail API")
        success = gmail_service.send_verification_email(email, code, college)
        if success:
            logging.info(f"Verification email sent successfully to {email} via Gmail API")
            return True
        else:
            logging.warning("Gmail API failed, falling back to SendGrid")
    
    # Fall back to SendGrid
    if SENDGRID_AVAILABLE:
        logging.info("Attempting to send verification email via SendGrid")
        return _send_verification_email_sendgrid(email, code, college)
    
    # Final fallback: Console output
    logging.warning("No email service available, falling back to console output")
    print(f"=== EMAIL VERIFICATION (CONSOLE FALLBACK) ===")
    print(f"To: {email}")
    print(f"College: {college}")
    print(f"Verification Code: {code}")
    print(f"============================================")
    return True

def _send_verification_email_sendgrid(email: str, code: str, college: str) -> bool:
    """Send verification email using SendGrid API"""
    
    # Get SendGrid configuration from environment variables
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('SENDGRID_FROM_EMAIL')
    from_name = os.getenv('SENDGRID_FROM_NAME', 'Campus Mobility')
    
    # Check if credentials are configured
    if not sendgrid_api_key or not from_email:
        logging.warning("SendGrid credentials not configured")
        return False
    
    try:
        # Create plain text version as fallback
        text_body = f"""
        Welcome to Campus Mobility!
        
        Thank you for joining our ride-sharing community for the Claremont Colleges.
        
        Your verification code is: {code}
        College: {college}
        
        This code will expire in 1 hour.
        
        If you didn't request this verification, please ignore this email.
        
        Thanks,
        Campus Mobility Team
        Connecting students across the 5C community
        """
        
        # Create HTML version
        html_body = create_verification_email_html(code, college)
        
        # Create SendGrid message
        message = Mail(
            from_email=From(from_email, from_name),
            to_emails=To(email),
            subject=Subject("🚗 Campus Mobility - Verify Your Email"),
            plain_text_content=Content("text/plain", text_body.strip()),
            html_content=Content("text/html", html_body)
        )
        
        # Send email using SendGrid
        sg = SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg.send(message)
        
        # Check if email was sent successfully
        if response.status_code in [200, 201, 202]:
            logging.info(f"Verification email sent successfully to {email} via SendGrid")
            return True
        else:
            logging.warning(f"SendGrid returned status code {response.status_code}")
            return False
        
    except Exception as e:
        logging.error(f"SendGrid API error: {e}")
        return False

def generate_reset_code() -> str:
    """Generate a 6-digit password reset code"""
    return ''.join(random.choices(string.digits, k=6))

def get_reset_expiry() -> datetime:
    """Get expiry time for password reset code (1 hour from now)"""
    return datetime.utcnow() + timedelta(hours=1)

def create_password_reset_email_html(code: str, college: str) -> str:
    """Create HTML-formatted password reset email"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Campus Mobility - Password Reset</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: bold;
            }}
            .header p {{
                margin: 5px 0 0 0;
                opacity: 0.9;
                font-size: 16px;
            }}
            .content {{
                padding: 30px;
            }}
            .content h2 {{
                color: #333;
                margin-top: 0;
                font-size: 24px;
            }}
            .content p {{
                color: #666;
                margin-bottom: 20px;
                font-size: 16px;
            }}
            .reset-code {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-size: 32px;
                font-weight: bold;
                text-align: center;
                padding: 20px;
                border-radius: 10px;
                letter-spacing: 4px;
                margin: 25px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .college-info {{
                background-color: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                color: #1565c0;
            }}
            .instructions {{
                background-color: #fff3e0;
                border-left: 4px solid #ff9800;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                color: #e65100;
            }}
            .expiry-notice {{
                background-color: #fff9c4;
                border-left: 4px solid #fbc02d;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
                color: #856404;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
            }}
            .security-notice {{
                background-color: #ffebee;
                border-left: 4px solid #f44336;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                color: #c62828;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Campus Mobility</h1>
                <p>Password Reset Request</p>
            </div>
            
            <div class="content">
                <h2>Reset Your Password</h2>
                <p>We received a request to reset the password for your Campus Mobility account.</p>
                
                <div class="college-info">
                    <strong>📚 College:</strong> {college}
                </div>
                
                <div class="instructions">
                    <strong>Instructions:</strong><br>
                    Enter the reset code below in the Campus Mobility app to create a new password.
                </div>
                
                <div class="reset-code">
                    {code}
                </div>
                
                <div class="expiry-notice">
                    ⏰ This code will expire in 1 hour
                </div>
                
                <div class="security-notice">
                    <strong>⚠️ Security Notice:</strong><br>
                    If you didn't request this password reset, please ignore this email. Your account remains secure.
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p><strong>Need help?</strong><br>
                If you're having trouble resetting your password, please contact our support team.</p>
            </div>
            
            <div class="footer">
                <p>Campus Mobility Team<br>
                Connecting students across college communities</p>
                <p style="font-size: 12px; color: #adb5bd;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_password_reset_email(email: str, reset_code: str, college: str) -> bool:
    """Send password reset email using Gmail API (preferred) or SendGrid API (fallback)"""
    
    # Try Gmail API first
    if GMAIL_AVAILABLE and gmail_service.service:
        logging.info("Attempting to send password reset email via Gmail API")
        success = gmail_service.send_password_reset_email(email, reset_code, college)
        if success:
            logging.info(f"Password reset email sent successfully to {email} via Gmail API")
            return True
        else:
            logging.warning("Gmail API failed, falling back to SendGrid")
    
    # Fall back to SendGrid
    if SENDGRID_AVAILABLE:
        logging.info("Attempting to send password reset email via SendGrid")
        return _send_password_reset_email_sendgrid(email, reset_code, college)
    
    # Final fallback: Console output
    logging.warning("No email service available, falling back to console output")
    print(f"=== PASSWORD RESET EMAIL (CONSOLE FALLBACK) ===")
    print(f"To: {email}")
    print(f"College: {college}")
    print(f"Reset Code: {reset_code}")
    print(f"===============================================")
    return True

def _send_password_reset_email_sendgrid(email: str, reset_code: str, college: str) -> bool:
    """Send password reset email using SendGrid API"""
    
    # Get SendGrid configuration
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('SENDGRID_FROM_EMAIL')
    from_name = os.getenv('SENDGRID_FROM_NAME', 'Campus Mobility')
    
    if not sendgrid_api_key or not from_email:
        logging.warning("SendGrid credentials not configured")
        return False
    
    try:
        # Create HTML email content
        html_body = create_password_reset_email_html(reset_code, college)
        
        # Create plain text version
        text_body = f"""
        Campus Mobility - Password Reset Request
        
        We received a request to reset the password for your Campus Mobility account.
        
        College: {college}
        Reset Code: {reset_code}
        
        This code will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        Campus Mobility Team
        """
        
        # Create SendGrid email message
        message = Mail(
            from_email=From(from_email, from_name),
            to_emails=To(email),
            subject=Subject("🔐 Campus Mobility - Password Reset Request"),
            plain_text_content=Content("text/plain", text_body.strip()),
            html_content=Content("text/html", html_body)
        )
        
        # Send email using SendGrid
        sg = SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg.send(message)
        
        # Check if email was sent successfully
        if response.status_code in [200, 201, 202]:
            logging.info(f"Password reset email sent successfully to {email} via SendGrid")
            return True
        else:
            logging.warning(f"SendGrid returned status code {response.status_code}")
            return False
        
    except Exception as e:
        logging.error(f"SendGrid API error: {e}")
        return False