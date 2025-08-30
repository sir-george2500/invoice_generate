from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from models.business import Business
from schemas.business_schemas import (
    BusinessCreate, 
    BusinessUpdate, 
    BusinessResponse, 
    BusinessSummary,
    BusinessCreateResponse
)
from services.business_service import BusinessService
from auth.dependencies import get_current_user

def require_super_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require super admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user

def require_business_context(current_user: User = Depends(get_current_user)):
    """Dependency to require business context"""
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business context required"
        )
    return current_user

class BusinessController:
    """Controller for business management endpoints"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1/businesses", tags=["Business Management"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all business routes"""
        
        # Admin only endpoints
        self.router.add_api_route(
            "", 
            self.create_business, 
            methods=["POST"], 
            response_model=BusinessCreateResponse,
            summary="Create Business",
            description="Create a new business with auto-generated admin credentials (Super Admin only)",
        )
        
        self.router.add_api_route(
            "", 
            self.list_businesses, 
            methods=["GET"], 
            response_model=List[BusinessSummary],
            summary="List All Businesses",
            description="Get list of all businesses with pagination (Super Admin only)",
        )
        
        self.router.add_api_route(
            "/search", 
            self.search_businesses, 
            methods=["GET"], 
            response_model=List[BusinessSummary],
            summary="Search Businesses",
            description="Search businesses by name, email, or TIN number (Super Admin only)",
        )
        
        self.router.add_api_route(
            "/{business_id}", 
            self.get_business, 
            methods=["GET"], 
            response_model=BusinessResponse,
            summary="Get Business Details",
            description="Get detailed information about a specific business",
        )
        
        self.router.add_api_route(
            "/{business_id}", 
            self.update_business, 
            methods=["PUT"], 
            response_model=BusinessResponse,
            summary="Update Business",
            description="Update business information",
        )
        
        self.router.add_api_route(
            "/{business_id}/deactivate", 
            self.deactivate_business, 
            methods=["PUT"],
            summary="Deactivate Business",
            description="Deactivate a business and all its users (Super Admin only)",
        )
        
        # Business user endpoints
        self.router.add_api_route(
            "/me", 
            self.get_my_business, 
            methods=["GET"], 
            response_model=BusinessResponse,
            summary="Get My Business",
            description="Get current user's business information",
        )
        

    

    
    async def create_business(
        self, 
        business_data: BusinessCreate, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
    ):
        """Create a new business with auto-generated admin credentials"""
        business_service = BusinessService(db)
        result = business_service.create_business(business_data)
        
        return BusinessCreateResponse(
            business=BusinessResponse.model_validate(result["business"]),
            admin_credentials=result["admin_credentials"]
        )
    
    async def list_businesses(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        active_only: bool = Query(True),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
    ):
        """List all businesses with pagination"""
        business_service = BusinessService(db)
        businesses = business_service.list_businesses(skip=skip, limit=limit, active_only=active_only)
        return [BusinessSummary.model_validate(business) for business in businesses]
    
    async def search_businesses(
        self,
        q: str = Query(..., min_length=1),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
    ):
        """Search businesses"""
        business_service = BusinessService(db)
        businesses = business_service.search_businesses(q, skip=skip, limit=limit)
        return [BusinessSummary.model_validate(business) for business in businesses]
    
    async def get_business(
        self,
        business_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Get business details - super admin can view any, business users can only view their own"""
        
        # Super admin can view any business
        if current_user.role == "admin":
            pass
        # Business users can only view their own business
        elif current_user.business_id == business_id:
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        business_service = BusinessService(db)
        business = business_service.get_business(business_id)
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        return BusinessResponse.model_validate(business)
    
    async def update_business(
        self,
        business_id: int,
        business_data: BusinessUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Update business information"""
        
        # Super admin can update any business, business admins can update their own
        if current_user.role == "admin":
            pass
        elif current_user.role == "business_admin" and current_user.business_id == business_id:
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        business_service = BusinessService(db)
        updated_business = business_service.update_business(business_id, business_data)
        
        if not updated_business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        return BusinessResponse.model_validate(updated_business)
    
    async def deactivate_business(
        self,
        business_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_super_admin)
    ):
        """Deactivate business"""
        business_service = BusinessService(db)
        success = business_service.deactivate_business(business_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        return {"message": "Business deactivated successfully"}
    
    async def get_my_business(
        self,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_business_context)
    ):
        """Get current user's business"""
        business_service = BusinessService(db)
        business = business_service.get_business(current_user.business_id)
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        return BusinessResponse.model_validate(business)
    
