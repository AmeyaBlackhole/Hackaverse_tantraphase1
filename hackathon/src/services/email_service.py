import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def send_invitation_email(invitee_email: str, team_name: str, hackathon_name: str, token: str):
    """Send team invitation email with confirmation link"""
    
    logger.info(f"Attempting to send invitation email to {invitee_email}")
    
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.error("Email credentials not configured. EMAIL_USER or EMAIL_PASSWORD missing.")
        logger.error(f"EMAIL_USER: {'SET' if EMAIL_USER else 'NOT SET'}")
        logger.error(f"EMAIL_PASSWORD: {'SET' if EMAIL_PASSWORD else 'NOT SET'}")
        return False
    
    logger.info(f"Email configuration - SMTP_SERVER: {SMTP_SERVER}, SMTP_PORT: {SMTP_PORT}")
    
    try:
        # Create confirmation link
        confirm_link = f"{FRONTEND_URL}/invite/accept?token={token}"
        logger.info(f"Generated confirmation link: {confirm_link}")
        
        # Create email content
        subject = f"You're invited to join team '{team_name}' - HackaVerse"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 HackaVerse Team Invitation</h1>
                </div>
                <div class="content">
                    <h2>You've been invited to join a hackathon team!</h2>
                    
                    <p><strong>Team:</strong> {team_name}</p>
                    <p><strong>Hackathon:</strong> {hackathon_name}</p>
                    
                    <p>You have been invited to join this amazing team for the upcoming hackathon. Click the button below to accept the invitation and start collaborating!</p>
                    
                    <div style="text-align: center;">
                        <a href="{confirm_link}" class="button">Accept Invitation</a>
                    </div>
                    
                    <p><small>This invitation will expire in 7 days. If you can't click the button, copy and paste this link into your browser:</small></p>
                    <p><small>{confirm_link}</small></p>
                </div>
                <div class="footer">
                    <p>© 2024 HackaVerse - Hackathon Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        logger.info("Creating email message...")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = invitee_email
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        logger.info(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}...")
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=5) as server:
            logger.info("Starting TLS...")
            server.starttls()
            
            logger.info(f"Logging in with user: {EMAIL_USER}")
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            
            logger.info("Sending email...")
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {invitee_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        logger.error("Please check EMAIL_USER and EMAIL_PASSWORD credentials")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send invitation email to {invitee_email}: {str(e)}")
        return False


def send_judge_invitation_email(invitee_email: str, hackathon_name: str, token: str):
    """Send judge invitation email with confirmation link"""
    logger.info(f"Attempting to send judge invitation email to {invitee_email}")

    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.error("Email credentials not configured. EMAIL_USER or EMAIL_PASSWORD missing.")
        return False

    try:
        confirm_link = f"{FRONTEND_URL}/judge/accept?token={token}"
        logger.info(f"Generated judge invitation link: {confirm_link}")

        subject = f"You're invited as a judge for {hackathon_name} - HackaVerse"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; background: #f9f9f9; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Judge Invitation</h2>
                <p>You've been invited to judge <strong>{hackathon_name}</strong> on HackaVerse.</p>
                <p>Click the button below to accept:</p>
                <p><a class="button" href="{confirm_link}">Accept Judge Invitation</a></p>
                <p>If the button does not work, copy and paste this URL:</p>
                <p>{confirm_link}</p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = invitee_email
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=5) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Judge invitation email sent successfully to {invitee_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send judge invitation email to {invitee_email}: {str(e)}")
        return False