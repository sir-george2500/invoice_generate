import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import EmailStr

from models.user import User, PasswordResetOTP
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.email_service import EmailService


class PasswordResetService:
    """Service for password reset functionality"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.email_service = EmailService()
        self.otp_validity_minutes = 15  # OTP valid for 15 minutes
    
    def _generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    async def send_reset_otp(self, email: EmailStr) -> bool:
        """Send OTP for password reset"""
        # Find user by email
        user = self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal that user doesn't exist for security reasons
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="If this email is registered, you will receive a reset code"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is deactivated"
            )
        
        # Invalidate any existing unused OTPs for this user
        self.db.query(PasswordResetOTP).filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.is_used == False
        ).update({PasswordResetOTP.is_used: True})
        
        # Generate new OTP
        otp_code = self._generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=self.otp_validity_minutes)
        
        # Store OTP in database
        otp_record = PasswordResetOTP(
            user_id=user.id,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False
        )
        
        self.db.add(otp_record)
        self.db.commit()
        
        # Send OTP via email
        success = await self.email_service.send_otp_email(email, otp_code, user.username)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset code. Please try again."
            )
        
        return True
    
    def verify_otp(self, email: EmailStr, otp_code: str) -> bool:
        """Verify OTP without resetting password"""
        user = self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid email or OTP"
            )
        
        # Find valid OTP
        otp_record = self.db.query(PasswordResetOTP).filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.otp_code == otp_code,
            PasswordResetOTP.is_used == False,
            PasswordResetOTP.expires_at > datetime.utcnow()
        ).first()
        
        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        return True
    
    async def reset_password(self, email: EmailStr, otp_code: str, new_password: str) -> bool:
        """Reset password using OTP"""
        user = self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid email or OTP"
            )
        
        # Find and validate OTP
        otp_record = self.db.query(PasswordResetOTP).filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.otp_code == otp_code,
            PasswordResetOTP.is_used == False,
            PasswordResetOTP.expires_at > datetime.utcnow()
        ).first()
        
        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Mark OTP as used
        otp_record.is_used = True
        
        # Update user password
        hashed_password = AuthService.hash_password(new_password)
        user.hashed_password = hashed_password
        
        self.db.commit()
        
        # Send confirmation email
        await self.email_service.send_password_changed_email(email, user.username)
        
        return True
    
    def cleanup_expired_otps(self):
        """Clean up expired OTP records"""
        self.db.query(PasswordResetOTP).filter(
            PasswordResetOTP.expires_at < datetime.utcnow()
        ).update({PasswordResetOTP.is_used: True})
        self.db.commit()