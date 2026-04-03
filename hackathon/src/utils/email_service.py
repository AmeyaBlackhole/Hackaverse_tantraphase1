import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

def send_invitation_email(invitee_email: str, team_name: str, hackathon_name: str, token: str):
    """
    Send team invitation email with secure token link
    
    Args:
        invitee_email: Email of the person being invited
        team_name: Name of the team
        hackathon_name: Name of the hackathon
        token: Secure token for accepting invitation
    """
    try:
        # Email configuration
        sender_email = os.getenv("EMAIL_USER", "noreply@hackaverse.com")
        sender_password = os.getenv("EMAIL_PASSWORD", "")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        # If no email credentials, log and skip
        if not sender_email or not sender_password:
            logger.warning(f"Email credentials not configured. Skipping email to {invitee_email}")
            return True
        
        # Create invitation link
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        invitation_link = f"{frontend_url}/accept-invitation?token={token}"
        
        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"You're invited to join {team_name} in {hackathon_name}!"
        message["From"] = sender_email
        message["To"] = invitee_email
        
        # HTML email body
        html = f"""\
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
              <h2 style="color: #333; margin-bottom: 20px;">🎉 You're Invited!</h2>
              
              <p style="color: #666; font-size: 16px; line-height: 1.6;">
                You've been invited to join <strong>{team_name}</strong> in the <strong>{hackathon_name}</strong> hackathon!
              </p>
              
              <p style="color: #666; font-size: 16px; line-height: 1.6;">
                Click the button below to accept the invitation and join the team.
              </p>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="{invitation_link}" style="background-color: #00d9ff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                  Accept Invitation
                </a>
              </div>
              
              <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                This invitation will expire in 7 days. If you didn't expect this invitation, you can safely ignore this email.
              </p>
              
              <p style="color: #999; font-size: 12px;">
                Or copy and paste this link in your browser:<br>
                <code style="background-color: #f5f5f5; padding: 5px 10px; border-radius: 3px;">{invitation_link}</code>
              </p>
            </div>
          </body>
        </html>
        """
        
        # Plain text version
        text = f"""\
        You're Invited!
        
        You've been invited to join {team_name} in the {hackathon_name} hackathon!
        
        Click the link below to accept the invitation:
        {invitation_link}
        
        This invitation will expire in 7 days.
        """
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, invitee_email, message.as_string())
        
        logger.info(f"Invitation email sent to {invitee_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send invitation email to {invitee_email}: {str(e)}")
        # Don't raise exception - email is optional
        return False
