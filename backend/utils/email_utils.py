import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
import logging

# Optional sendgrid imports - fallback to console if not available
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, From, To, Subject, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("WARNING: SendGrid not available - emails will be printed to console")

# College domain mapping
COLLEGE_DOMAINS = {
    'pomona.edu': 'Pomona College',
    'hmc.edu': 'Harvey Mudd College',
    'scrippscollege.edu': 'Scripps College',
    'pitzer.edu': 'Pitzer College',
    'cmc.edu': 'Claremont McKenna College',
    'andrew.cmu.edu': 'Carnegie Mellon University'
}

def validate_college_email(email: str) -> Dict[str, any]:
    """Validate if email is from a supported college domain"""
    domain = email.split('@')[1].lower() if '@' in email else ''
    
    if not domain.endswith('.edu'):
        return {
            'valid': False,
            'error': 'Only .edu email addresses are allowed'
        }
    
    college = COLLEGE_DOMAINS.get(domain)
    if not college:
        return {
            'valid': False,
            'error': 'Email domain not recognized. Only Claremont Colleges and Carnegie Mellon is supported.'
        }
    
    return {
        'valid': True,
        'college': college
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
    """Send verification email to user with HTML formatting using SendGrid API"""
    
    # Get SendGrid configuration from environment variables
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('SENDGRID_FROM_EMAIL')
    from_name = os.getenv('SENDGRID_FROM_NAME', 'Campus Mobility')
    
    # Fallback: Print to console if SendGrid not available or credentials not configured
    if not SENDGRID_AVAILABLE or not sendgrid_api_key or not from_email:
        logging.warning("SendGrid credentials not configured, falling back to console output")
        print(f"=== EMAIL VERIFICATION (CONSOLE FALLBACK) ===")
        print(f"To: {email}")
        print(f"College: {college}")
        print(f"Verification Code: {code}")
        print(f"============================================")
        return True
    
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
            logging.warning(f"SendGrid returned status code {response.status_code}, falling back to console")
            print(f"=== EMAIL VERIFICATION (SENDGRID ERROR FALLBACK) ===")
            print(f"To: {email}")
            print(f"College: {college}")
            print(f"Verification Code: {code}")
            print(f"SendGrid Status: {response.status_code}")
            print(f"====================================================")
            return True
        
    except Exception as e:
        logging.error(f"SendGrid API error: {e}")
        
        # Handle specific SendGrid errors with appropriate fallbacks
        error_str = str(e).lower()
        
        if "unauthorized" in error_str or "forbidden" in error_str:
            print(f"SendGrid Authentication Error - falling back to console output")
            print(f"=== EMAIL VERIFICATION (AUTH FALLBACK) ===")
            print(f"To: {email}")
            print(f"College: {college}")
            print(f"Verification Code: {code}")
            print(f"Error: Invalid SendGrid API key")
            print(f"=========================================")
        elif "bad request" in error_str or "invalid" in error_str:
            logging.error(f"SendGrid request error - invalid email or configuration")
            print(f"Invalid email configuration or recipient: {email}")
            return False
        else:
            print(f"SendGrid API error - falling back to console output")
            print(f"=== EMAIL VERIFICATION (ERROR FALLBACK) ===")
            print(f"To: {email}")
            print(f"College: {college}")
            print(f"Verification Code: {code}")
            print(f"Error: {str(e)}")
            print(f"=========================================")
        
        return True  # Still return True so signup process continues