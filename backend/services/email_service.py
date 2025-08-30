import logging
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from pydantic import EmailStr
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_HOST,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER="templates"
        )
        self.fast_mail = FastMail(self.conf)
        
        # Setup Jinja2 template environment
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_dir))
    
    async def send_otp_email(self, email: EmailStr, otp_code: str, username: str) -> bool:
        """Send OTP email for password reset"""
        try:
            # Load and render the template
            template = self.jinja_env.get_template('password_reset_otp_email.html')
            html_content = template.render(
                username=username,
                otp_code=otp_code,
                email=email
            )
            
            message = MessageSchema(
                subject="🔐 Password Reset OTP - VSDC Integration System",
                recipients=[email],
                body=html_content,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            logger.info(f"OTP email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            return False
    
    async def send_password_changed_email(self, email: EmailStr, username: str) -> bool:
        """Send confirmation email after password reset"""
        try:
            # Load and render the template
            template = self.jinja_env.get_template('password_reset_confirmation_email.html')
            html_content = template.render(
                username=username,
                email=email
            )
            
            message = MessageSchema(
                subject="✅ Password Successfully Reset - VSDC Integration System",
                recipients=[email],
                body=html_content,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            logger.info(f"Password changed confirmation email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password changed email to {email}: {str(e)}")
            return False