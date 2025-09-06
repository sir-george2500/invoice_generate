"""
Custom Field Setup Controller
Handles endpoints for Zoho custom field setup and management
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from database.connection import get_db
from models.user import User
from models.business import Business
from services.zoho_custom_field_service import ZohoCustomFieldService
from services.business_service import BusinessService
from middleware.dependencies import get_current_user

logger = logging.getLogger(__name__)

class CustomFieldSetupController:
    """Controller for custom field setup endpoints"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1/custom-fields", tags=["Custom Field Setup"])
        self.custom_field_service = ZohoCustomFieldService()
        self._register_routes()
    
    def _register_routes(self):
        """Register all custom field setup routes"""
        
        self.router.add_api_route(
            "/setup/{zoho_org_id}", 
            self.setup_custom_fields, 
            methods=["POST"],
            summary="Setup Custom Fields for Zoho Organization",
            description="Creates all required custom fields in Zoho Books for EBM integration",
        )
        
        self.router.add_api_route(
            "/status/{zoho_org_id}", 
            self.get_setup_status, 
            methods=["GET"],
            summary="Get Custom Field Setup Status",
            description="Check the current status of custom field setup for a Zoho organization",
        )
        
        self.router.add_api_route(
            "/required-fields", 
            self.get_required_fields, 
            methods=["GET"],
            summary="Get Required Custom Fields",
            description="Get list of all custom fields required for EBM integration",
        )
        
        self.router.add_api_route(
            "/business/setup-status", 
            self.get_business_setup_status, 
            methods=["GET"],
            summary="Get Setup Status for Authenticated Business",
            description="Get custom field setup status for the current authenticated business",
        )
    
    async def setup_custom_fields(
        self,
        zoho_org_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Setup all required custom fields for a Zoho organization"""
        
        logger.info(f"Custom field setup requested for Zoho org: {zoho_org_id} by user: {current_user.username}")
        
        try:
            # Get business associated with the Zoho org
            business_service = BusinessService(db)
            business = business_service.get_business_by_zoho_org(zoho_org_id)
            
            if not business:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No business found for this Zoho organization"
                )
            
            # Check if user has access to this business
            if current_user.role != "admin" and current_user.business_id != business.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this business"
                )
            
            # Perform custom field setup
            setup_result = await self.custom_field_service.setup_all_custom_fields(zoho_org_id)
            
            # Update business with setup results
            update_data = {
                "custom_fields_setup_status": setup_result["overall_status"],
                "custom_fields_setup_result": setup_result
            }
            
            if setup_result["overall_status"] in ["success", "partial_success"]:
                from datetime import datetime
                update_data["custom_fields_setup_at"] = datetime.utcnow()
            
            business_service.update_custom_field_setup_status(business.id, update_data)
            
            logger.info(f"Custom field setup completed for business {business.id} with status: {setup_result['overall_status']}")
            
            return {
                "message": "Custom field setup completed",
                "business_id": business.id,
                "business_name": business.business_name,
                "zoho_organization_id": zoho_org_id,
                "setup_result": setup_result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Custom field setup failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Custom field setup failed: {str(e)}"
            )
    
    async def get_setup_status(
        self,
        zoho_org_id: str,
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Get custom field setup status for a Zoho organization"""
        
        try:
            # Get current status from Zoho
            status_result = await self.custom_field_service.check_setup_status(zoho_org_id)
            
            # Get business setup history if available
            business_service = BusinessService(db)
            business = business_service.get_business_by_zoho_org(zoho_org_id)
            
            if business:
                status_result["business_setup_history"] = {
                    "business_id": business.id,
                    "business_name": business.business_name,
                    "last_setup_status": business.custom_fields_setup_status,
                    "last_setup_at": business.custom_fields_setup_at.isoformat() if business.custom_fields_setup_at else None,
                    "last_setup_result": business.custom_fields_setup_result
                }
            
            return status_result
            
        except Exception as e:
            logger.error(f"Failed to get setup status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get setup status: {str(e)}"
            )
    
    async def get_required_fields(self) -> Dict[str, Any]:
        """Get list of all required custom fields"""
        
        try:
            return {
                "message": "Required custom fields for EBM integration",
                "fields": self.custom_field_service.get_required_fields_summary()
            }
            
        except Exception as e:
            logger.error(f"Failed to get required fields: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get required fields: {str(e)}"
            )
    
    async def get_business_setup_status(
        self,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get custom field setup status for the current authenticated business"""
        
        if not current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be associated with a business"
            )
        
        try:
            business_service = BusinessService(db)
            business = business_service.get_business(current_user.business_id)
            
            if not business:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business not found"
                )
            
            if not business.zoho_organization_id:
                return {
                    "message": "Business not linked to Zoho organization",
                    "business_id": business.id,
                    "business_name": business.business_name,
                    "setup_required": True,
                    "setup_status": "zoho_not_linked",
                    "next_action": "link_business_to_zoho_first"
                }
            
            # Get current status from Zoho
            status_result = await self.custom_field_service.check_setup_status(business.zoho_organization_id)
            
            return {
                "message": "Custom field setup status for your business",
                "business_id": business.id,
                "business_name": business.business_name,
                "zoho_organization_id": business.zoho_organization_id,
                "last_setup_status": business.custom_fields_setup_status,
                "last_setup_at": business.custom_fields_setup_at.isoformat() if business.custom_fields_setup_at else None,
                "current_status": status_result,
                "setup_available": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get business setup status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get business setup status: {str(e)}"
            )