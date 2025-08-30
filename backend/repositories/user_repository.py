from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.user import User

class UserRepository:
    """Repository for user data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_business_id(self, business_id: int) -> List[User]:
        """Get all users belonging to a specific business"""
        return self.db.query(User).filter(User.business_id == business_id).all()
    
    def get_business_admin(self, business_id: int) -> Optional[User]:
        """Get the business admin user for a specific business"""
        return self.db.query(User).filter(
            and_(User.business_id == business_id, User.role == "business_admin")
        ).first()
    
    def create(self, user: User) -> User:
        """Create a new user"""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user: User) -> User:
        """Update existing user"""
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user: User) -> None:
        """Delete user"""
        self.db.delete(user)
        self.db.commit()
    
    def exists_by_username(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if user exists by username"""
        query = self.db.query(User).filter(User.username == username)
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None
    
    def exists_by_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if user exists by email"""
        query = self.db.query(User).filter(User.email == email)
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None
    
    def exists_by_username_in_business(self, username: str, business_id: int, exclude_id: Optional[int] = None) -> bool:
        """Check if username exists within a specific business"""
        query = self.db.query(User).filter(
            and_(User.username == username, User.business_id == business_id)
        )
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None