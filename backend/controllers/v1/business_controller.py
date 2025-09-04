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
    BusinessCreateResponse,
    ZohoBusinessProfile,
    ZohoBusinessProfileResponse
)
from services.business_service import BusinessService
from middleware.dependencies import get_current_user

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
        
        # Zoho Plugin Integration endpoints
        self.router.add_api_route(
            "/zoho/link", 
            self.link_business_to_zoho, 
            methods=["POST"],
            summary="Link Business to Zoho Organization",
            description="Link authenticated business to Zoho organization ID",
        )
        
        self.router.add_api_route(
            "/zoho/lookup/{zoho_org_id}", 
            self.lookup_business_by_zoho_org, 
            methods=["GET"],
            summary="Lookup Business by Zoho Org ID",
            description="Retrieve business profile for auto-population in Zoho plugin",
        )
        
        self.router.add_api_route(
            "/zoho/fields/{zoho_org_id}", 
            self.get_business_fields_for_invoice, 
            methods=["GET"],
            summary="Get Business Fields for Auto-Population",
            description="Get only business fields that should be auto-populated in invoices",
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
    
    async def link_business_to_zoho(
        self,
        request: dict,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """Link authenticated business to Zoho organization ID"""
        if not current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be associated with a business"
            )
        
        zoho_org_id = request.get("zoho_organization_id")
        if not zoho_org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="zoho_organization_id is required"
            )
        
        business_service = BusinessService(db)
        
        # Check if this Zoho org is already linked to another business
        existing_business = business_service.get_business_by_zoho_org(zoho_org_id)
        if existing_business and existing_business.id != current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Zoho organization is already linked to another business"
            )
        
        # Link the business to Zoho org
        updated_business = business_service.link_business_to_zoho_org(
            current_user.business_id, zoho_org_id
        )
        
        if not updated_business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        return {
            "message": "Business successfully linked to Zoho organization",
            "business_id": updated_business.id,
            "business_name": updated_business.business_name,
            "zoho_organization_id": updated_business.zoho_organization_id,
            "setup_completed": True
        }
    
    async def lookup_business_by_zoho_org(
        self,
        zoho_org_id: str,
        db: Session = Depends(get_db)
    ):
        """Lookup business profile by Zoho organization ID"""
        business_service = BusinessService(db)
        business = business_service.get_business_by_zoho_org(zoho_org_id)
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No business profile found for this Zoho organization. Please contact support."
            )
        
        return {
            "business_id": business.id,
            "business_name": business.business_name,
            "tin_number": business.tin_number,
            "email": business.email,
            "location": business.location,
            "phone_number": business.phone_number,
            "is_active": business.is_active,
            "setup_completed_at": business.setup_completed_at
        }
    
    async def get_business_fields_for_invoice(
        self,
        zoho_org_id: str,
        db: Session = Depends(get_db)
    ):
        """Get only business fields that should be auto-populated in invoices"""
        business_service = BusinessService(db)
        business = business_service.get_business_by_zoho_org(zoho_org_id)
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found"
            )
        
        # Return ONLY business fields - customer fields must be entered by user
        # Return ONLY business fields - customer and purchase code are manual
        return {
            "business_fields": {
                "cf_tin": business.tin_number,
                "cf_seller_company_address": business.location, 
                "cf_seller_company_email": business.email,
                "cf_organizationname": business.business_name
            },
            "manual_fields_note": "Customer TIN and Purchase Code must be entered manually by user",
            "purchase_code_note": "Purchase Code is like OTP - get from RRA website for each invoice",
            "default_currency": business.default_currency or "RWF",
            "business_name": business.business_name
        }
    
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
    
