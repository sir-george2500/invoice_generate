from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List
from models.business import Business
from models.user import User

class BusinessRepository:
    """Repository for Business data access operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, business: Business) -> Business:
        """Create a new business"""
        self.db.add(business)
        self.db.commit()
        self.db.refresh(business)
        return business
    
    def get_by_id(self, business_id: int) -> Optional[Business]:
        """Get business by ID"""
        return self.db.query(Business).filter(Business.id == business_id).first()
    
    def get_by_tin(self, tin_number: str) -> Optional[Business]:
        """Get business by TIN number"""
        return self.db.query(Business).filter(Business.tin_number == tin_number).first()
    
    def get_by_email(self, email: str) -> Optional[Business]:
        """Get business by email"""
        return self.db.query(Business).filter(Business.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Business]:
        """Get all businesses with pagination"""
        query = self.db.query(Business)
        if active_only:
            query = query.filter(Business.is_active == True)
        return query.order_by(desc(Business.created_at)).offset(skip).limit(limit).all()
    
    def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Business]:
        """Search businesses by name, email, or TIN"""
        search_pattern = f"%{search_term}%"
        return self.db.query(Business).filter(
            or_(
                Business.business_name.ilike(search_pattern),
                Business.email.ilike(search_pattern),
                Business.tin_number.ilike(search_pattern)
            )
        ).order_by(desc(Business.created_at)).offset(skip).limit(limit).all()
    
    def update(self, business_id: int, **updates) -> Optional[Business]:
        """Update business by ID"""
        business = self.get_by_id(business_id)
        if not business:
            return None
        
        for key, value in updates.items():
            if hasattr(business, key):
                setattr(business, key, value)
        
        self.db.commit()
        self.db.refresh(business)
        return business
    
    def delete(self, business_id: int) -> bool:
        """Soft delete business (set is_active to False)"""
        business = self.get_by_id(business_id)
        if not business:
            return False
        
        business.is_active = False
        self.db.commit()
        return True
    
    def exists_by_tin(self, tin_number: str, exclude_id: Optional[int] = None) -> bool:
        """Check if business exists by TIN number"""
        query = self.db.query(Business).filter(Business.tin_number == tin_number)
        if exclude_id:
            query = query.filter(Business.id != exclude_id)
        return query.first() is not None
    
    def exists_by_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if business exists by email"""
        query = self.db.query(Business).filter(Business.email == email)
        if exclude_id:
            query = query.filter(Business.id != exclude_id)
        return query.first() is not None
    
    def get_business_users(self, business_id: int) -> List[User]:
        """Get all users belonging to a business"""
        return self.db.query(User).filter(User.business_id == business_id).all()
    
    def count_total(self, active_only: bool = True) -> int:
        """Count total businesses"""
        query = self.db.query(Business)
        if active_only:
            query = query.filter(Business.is_active == True)
        return query.count()
    
    def get_by_zoho_org_id(self, zoho_org_id: str) -> Optional[Business]:
        """Get business by Zoho organization ID"""
        return self.db.query(Business).filter(Business.zoho_organization_id == zoho_org_id).first()
    
    def exists_by_zoho_org_id(self, zoho_org_id: str, exclude_id: Optional[int] = None) -> bool:
        """Check if business exists by Zoho organization ID"""
        query = self.db.query(Business).filter(Business.zoho_organization_id == zoho_org_id)
        if exclude_id:
            query = query.filter(Business.id != exclude_id)
        return query.first() is not None