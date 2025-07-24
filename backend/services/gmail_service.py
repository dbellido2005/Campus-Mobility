import base64
import os
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logging.warning("Gmail API libraries not available - emails will fall back to console")

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailService:
    """Service for sending emails via Gmail API"""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Gmail API service with credentials"""
        if not GMAIL_AVAILABLE:
            logging.warning("Gmail API not available")
            return False
        
        try:
            # Check for credentials in environment variables
            credentials_json = os.getenv('GMAIL_CREDENTIALS_JSON')
            token_json = os.getenv('GMAIL_TOKEN_JSON')
            
            if credentials_json and token_json:
                # Load credentials from environment variables
                self._load_credentials_from_env(credentials_json, token_json)
            else:
                # Try to load from files (for development)
                self._load_credentials_from_files()
            
            if self.credentials and self.credentials.valid:
                self.service = build('gmail', 'v1', credentials=self.credentials)
                logging.info("Gmail API service initialized successfully")
                return True
            else:
                logging.warning("Gmail credentials not valid or not found")
                return False
                
        except Exception as e:
            logging.error(f"Failed to initialize Gmail service: {e}")
            return False
    
    def _load_credentials_from_env(self, credentials_json: str, token_json: str):
        """Load Gmail credentials from environment variables"""
        try:
            # Parse credentials JSON
            credentials_info = json.loads(credentials_json)
            token_info = json.loads(token_json)
            
            # Create credentials object
            self.credentials = Credentials(
                token=token_info.get('token'),
                refresh_token=token_info.get('refresh_token'),
                id_token=token_info.get('id_token'),
                token_uri=credentials_info.get('installed', {}).get('token_uri'),
                client_id=credentials_info.get('installed', {}).get('client_id'),
                client_secret=credentials_info.get('installed', {}).get('client_secret'),
                scopes=SCOPES
            )
            
            # Refresh token if expired
            if not self.credentials.valid and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                
        except Exception as e:
            logging.error(f"Failed to load credentials from environment: {e}")
            self.credentials = None
    
    def _load_credentials_from_files(self):
        """Load Gmail credentials from files (for development)"""
        try:
            # Look for token file
            token_path = 'gmail_token.json'
            credentials_path = 'gmail_credentials.json'
            
            creds = None
            
            # Load existing token
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # If no valid credentials, try to get them
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(credentials_path):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next time
                if creds:
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
            
            self.credentials = creds
            
        except Exception as e:
            logging.error(f"Failed to load credentials from files: {e}")
            self.credentials = None
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """
        Send an email via Gmail API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            text_body: Plain text content (optional)
            
        Returns:
            bool: True if email sent successfully
        """
        
        if not self.service:
            logging.warning("Gmail service not initialized")
            return False
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['From'] = os.getenv('GMAIL_FROM_EMAIL', 'noreply@campusmobility.app')
            message['Subject'] = subject
            
            # Add text part if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                message.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logging.info(f"Email sent successfully to {to_email}, Message ID: {send_result.get('id')}")
            return True
            
        except HttpError as error:
            logging.error(f"Gmail API error: {error}")
            
            # Handle specific Gmail API errors
            if error.resp.status == 403:
                logging.error("Gmail API access forbidden - check permissions")
            elif error.resp.status == 401:
                logging.error("Gmail API unauthorized - credentials may be expired")
            elif error.resp.status == 429:
                logging.error("Gmail API rate limit exceeded")
            
            return False
            
        except Exception as e:
            logging.error(f"Unexpected error sending email: {e}")
            return False
    
    def send_verification_email(self, email: str, code: str, college: str) -> bool:
        """Send verification email using Gmail API"""
        
        if not self.service:
            return False
        
        # Create HTML content (reusing the existing template)
        html_body = self._create_verification_email_html(code, college)
        
        # Create text content
        text_body = f"""
        Welcome to Campus Mobility!
        
        Thank you for joining our ride-sharing community for {college}.
        
        Your verification code is: {code}
        
        This code will expire in 1 hour.
        
        If you didn't request this verification, please ignore this email.
        
        Campus Mobility Team
        Connecting students across college communities
        """
        
        subject = "🚗 Campus Mobility - Verify Your Email"
        
        return self.send_email(email, subject, html_body, text_body.strip())
    
    def send_password_reset_email(self, email: str, reset_code: str, college: str) -> bool:
        """Send password reset email using Gmail API"""
        
        if not self.service:
            return False
        
        # Create HTML content
        html_body = self._create_password_reset_email_html(reset_code, college)
        
        # Create text content
        text_body = f"""
        Campus Mobility - Password Reset Request
        
        We received a request to reset the password for your Campus Mobility account.
        
        College: {college}
        Reset Code: {reset_code}
        
        This code will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        Campus Mobility Team
        """
        
        subject = "🔐 Campus Mobility - Password Reset Request"
        
        return self.send_email(email, subject, html_body, text_body.strip())
    
    def _create_verification_email_html(self, code: str, college: str) -> str:
        """Create HTML-formatted verification email"""
        return f"""
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
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 Campus Mobility</h1>
                    <p>Connecting College Communities</p>
                </div>
                
                <div class="content">
                    <h2>Welcome to Campus Mobility!</h2>
                    <p>Thank you for joining our ride-sharing community. Please verify your email address to complete your registration.</p>
                    
                    <div class="college-info">
                        <strong>📚 College:</strong> {college}
                    </div>
                    
                    <div class="verification-code">
                        {code}
                    </div>
                    
                    <div class="expiry-notice">
                        ⏰ This code will expire in 1 hour
                    </div>
                    
                    <p>If you didn't request this verification, please ignore this email.</p>
                </div>
                
                <div class="footer">
                    <p>Campus Mobility Team<br>
                    Connecting students across college communities</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_password_reset_email_html(self, code: str, college: str) -> str:
        """Create HTML-formatted password reset email"""
        return f"""
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
                .content {{
                    padding: 30px;
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
                    
                    <div class="reset-code">
                        {code}
                    </div>
                    
                    <p>⏰ This code will expire in 1 hour</p>
                    
                    <div class="security-notice">
                        <strong>⚠️ Security Notice:</strong><br>
                        If you didn't request this password reset, please ignore this email.
                    </div>
                </div>
                
                <div class="footer">
                    <p>Campus Mobility Team<br>
                    Connecting students across college communities</p>
                </div>
            </div>
        </body>
        </html>
        """

# Global Gmail service instance
gmail_service = GmailService()