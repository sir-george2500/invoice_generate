from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets
import string

from models.business import Business
from models.user import User
from repositories.business_repository import BusinessRepository
from repositories.user_repository import UserRepository
from schemas.business_schemas import BusinessCreate, BusinessUpdate
from services.auth_service import AuthService

class BusinessService:
    """Service for business management operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.business_repo = BusinessRepository(db)
        self.user_repo = UserRepository(db)
    
    def _generate_unique_username(self, business_name: str, tin_number: str) -> str:
        """Generate a unique username for the business admin"""
        # Create base username from business name and TIN
        business_clean = ''.join(c for c in business_name.lower() if c.isalnum())[:8]
        tin_suffix = tin_number[-4:]  # Last 4 digits of TIN
        
        base_username = f"{business_clean}_{tin_suffix}"
        
        # Ensure uniqueness
        username = base_username
        counter = 1
        while self.user_repo.exists_by_username(username):
            username = f"{base_username}_{counter:02d}"
            counter += 1
        
        return username
    
    def _generate_secure_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        # Include uppercase, lowercase, digits, and some safe symbols
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        
        # Ensure at least one character from each category
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        
        # Fill the rest randomly
        for _ in range(length - 4):
            password.append(secrets.choice(characters))
        
        # Shuffle the password list
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    def create_business(self, business_data: BusinessCreate) -> dict:
        """Create a new business with auto-generated admin user"""
        
        # Check if TIN number already exists
        if self.business_repo.exists_by_tin(business_data.tin_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TIN number already exists"
            )
        
        # Check if business email already exists
        if self.business_repo.exists_by_email(business_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business email already exists"
            )
        
        # Check if admin email already exists (if provided)
        if business_data.admin_email and self.user_repo.exists_by_email(business_data.admin_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin email already exists"
            )
        
        # Generate unique username and secure password
        admin_username = self._generate_unique_username(
            business_data.business_name, 
            business_data.tin_number
        )
        admin_password = self._generate_secure_password()
        
        # Create business
        new_business = Business(
            business_name=business_data.business_name,
            email=business_data.email,
            location=business_data.location,
            tin_number=business_data.tin_number,
            phone_number=business_data.phone_number,
            is_active=True
        )
        
        created_business = self.business_repo.create(new_business)
        
        # Create business admin user
        hashed_password = AuthService.hash_password(admin_password)
        admin_user = User(
            username=admin_username,
            email=business_data.admin_email,
            hashed_password=hashed_password,
            role="business_admin",
            business_id=created_business.id,
            is_active=True
        )
        
        self.user_repo.create(admin_user)
        
        # Return business with generated credentials
        return {
            "business": created_business,
            "admin_credentials": {
                "username": admin_username,
                "password": admin_password,
                "email": business_data.admin_email
            }
        }
    
    def update_business(self, business_id: int, business_data: BusinessUpdate) -> Optional[Business]:
        """Update business information"""
        
        # Check if business exists
        existing_business = self.business_repo.get_by_id(business_id)
        if not existing_business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        update_data = business_data.model_dump(exclude_unset=True)
        
        # Validate unique constraints if being updated
        if 'tin_number' in update_data:
            if self.business_repo.exists_by_tin(update_data['tin_number'], exclude_id=business_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TIN number already exists"
                )
        
        if 'email' in update_data:
            if self.business_repo.exists_by_email(update_data['email'], exclude_id=business_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        return self.business_repo.update(business_id, **update_data)
    
    def get_business(self, business_id: int) -> Optional[Business]:
        """Get business by ID"""
        return self.business_repo.get_by_id(business_id)
    
    def get_business_by_tin(self, tin_number: str) -> Optional[Business]:
        """Get business by TIN number"""
        return self.business_repo.get_by_tin(tin_number)
    
    def list_businesses(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> list[Business]:
        """List all businesses with pagination"""
        return self.business_repo.get_all(skip=skip, limit=limit, active_only=active_only)
    
    def search_businesses(self, search_term: str, skip: int = 0, limit: int = 100) -> list[Business]:
        """Search businesses"""
        return self.business_repo.search(search_term, skip=skip, limit=limit)
    
    def deactivate_business(self, business_id: int) -> bool:
        """Deactivate a business and all its users"""
        
        business = self.business_repo.get_by_id(business_id)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        # Deactivate business
        success = self.business_repo.delete(business_id)
        
        if success:
            # Deactivate all business users
            business_users = self.user_repo.get_by_business_id(business_id)
            for user in business_users:
                user.is_active = False
                self.user_repo.update(user)
        
        return success
    

