from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database.connection import get_db
from models.user import User
from models.webhook_activity import WebhookActivity, WebhookStatus, WebhookType
from services.webhook_activity_service import WebhookActivityService
from middleware.dependencies import get_current_user

def require_admin_access(current_user: User = Depends(get_current_user)):
    """Dependency to require admin access for webhook activity"""
    if current_user.role not in ["admin", "business_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

class WebhookActivityController:
    """Controller for webhook activity management endpoints"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1/webhook-activities", tags=["Webhook Activity"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all webhook activity routes"""
        
        self.router.add_api_route(
            "", 
            self.list_webhook_activities, 
            methods=["GET"],
            summary="List Webhook Activities",
            description="Get list of webhook activities with filtering options",
        )
        
        self.router.add_api_route(
            "/failures", 
            self.list_failed_webhooks, 
            methods=["GET"],
            summary="List Failed Webhooks",
            description="Get recent failed webhook activities for troubleshooting",
        )
        
        self.router.add_api_route(
            "/stats", 
            self.get_webhook_stats, 
            methods=["GET"],
            summary="Get Webhook Statistics",
            description="Get webhook activity statistics and performance metrics",
        )
        
        self.router.add_api_route(
            "/{activity_id}", 
            self.get_webhook_activity, 
            methods=["GET"],
            summary="Get Webhook Activity Details",
            description="Get detailed information about a specific webhook activity",
        )
    
    async def list_webhook_activities(
        self,
        business_tin: Optional[str] = Query(None, description="Filter by business TIN"),
        status: Optional[str] = Query(None, description="Filter by status (pending, success, failed, timeout, retry)"),
        webhook_type: Optional[str] = Query(None, description="Filter by type (invoice, credit_note)"),
        invoice_number: Optional[str] = Query(None, description="Filter by invoice number"),
        hours_back: int = Query(24, description="Hours to look back", ge=1, le=168),  # Max 1 week
        limit: int = Query(50, description="Number of records to return", ge=1, le=200),
        offset: int = Query(0, description="Number of records to skip", ge=0),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin_access)
    ):
        """List webhook activities with filtering"""
        
        webhook_service = WebhookActivityService(db)
        
        # Convert string parameters to enums
        status_enum = None
        if status:
            try:
                status_enum = WebhookStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {[s.value for s in WebhookStatus]}"
                )
        
        webhook_type_enum = None
        if webhook_type:
            try:
                webhook_type_enum = WebhookType(webhook_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid webhook type. Must be one of: {[t.value for t in WebhookType]}"
                )
        
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(hours=hours_back)
        
        # If user is business_admin, only show their business data
        if current_user.role == "business_admin" and current_user.business_id:
            # Get business TIN from business_id - we'd need to join with business table
            # For now, let's assume business_tin filter is provided by frontend
            pass
        
        activities = webhook_service.get_webhook_activities(
            business_tin=business_tin,
            status=status_enum,
            webhook_type=webhook_type_enum,
            start_date=start_date,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        response_activities = []
        for activity in activities:
            response_activities.append({
                "id": activity.id,
                "webhook_type": activity.webhook_type.value,
                "status": activity.status.value,
                "business_tin": activity.business_tin,
                "business_name": activity.business_name,
                "invoice_number": activity.invoice_number,
                "vsdc_receipt_number": activity.vsdc_receipt_number,
                "error_code": activity.error_code,
                "error_message": activity.error_message,
                "error_type": activity.error_type,
                "processing_time_ms": activity.processing_time_ms,
                "retry_count": activity.retry_count,
                "pdf_generated": activity.pdf_generated,
                "pdf_filename": activity.pdf_filename,
                "created_at": activity.created_at.isoformat() if activity.created_at else None,
                "processed_at": activity.processed_at.isoformat() if activity.processed_at else None,
            })
        
        return {
            "activities": response_activities,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(response_activities)
            },
            "filters": {
                "business_tin": business_tin,
                "status": status,
                "webhook_type": webhook_type,
                "invoice_number": invoice_number,
                "hours_back": hours_back
            }
        }
    
    async def list_failed_webhooks(
        self,
        hours_back: int = Query(24, description="Hours to look back for failures", ge=1, le=168),
        limit: int = Query(50, description="Number of records to return", ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin_access)
    ):
        """List recent failed webhooks for troubleshooting"""
        
        webhook_service = WebhookActivityService(db)
        
        failed_activities = webhook_service.get_failed_webhook_activities(
            hours_back=hours_back,
            limit=limit
        )
        
        # Group by common failure patterns for easier troubleshooting
        failures_by_business = {}
        failures_by_error_type = {}
        
        response_failures = []
        for activity in failed_activities:
            failure_info = {
                "id": activity.id,
                "webhook_type": activity.webhook_type.value,
                "business_tin": activity.business_tin,
                "business_name": activity.business_name,
                "invoice_number": activity.invoice_number,
                "error_code": activity.error_code,
                "error_message": activity.error_message,
                "error_type": activity.error_type,
                "retry_count": activity.retry_count,
                "created_at": activity.created_at.isoformat() if activity.created_at else None,
                "processing_time_ms": activity.processing_time_ms
            }
            response_failures.append(failure_info)
            
            # Group for analysis
            business_key = f"{activity.business_tin} ({activity.business_name})"
            if business_key not in failures_by_business:
                failures_by_business[business_key] = 0
            failures_by_business[business_key] += 1
            
            if activity.error_type:
                if activity.error_type not in failures_by_error_type:
                    failures_by_error_type[activity.error_type] = 0
                failures_by_error_type[activity.error_type] += 1
        
        return {
            "failed_webhooks": response_failures,
            "summary": {
                "total_failures": len(response_failures),
                "failures_by_business": failures_by_business,
                "failures_by_error_type": failures_by_error_type,
                "time_period_hours": hours_back
            }
        }
    
    async def get_webhook_stats(
        self,
        business_tin: Optional[str] = Query(None, description="Get stats for specific business"),
        days_back: int = Query(7, description="Days to look back for stats", ge=1, le=30),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin_access)
    ):
        """Get webhook activity statistics"""
        
        webhook_service = WebhookActivityService(db)
        
        stats = webhook_service.get_webhook_stats(
            business_tin=business_tin,
            days_back=days_back
        )
        
        return {
            "statistics": stats,
            "period": {
                "days_back": days_back,
                "business_tin": business_tin
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def get_webhook_activity(
        self,
        activity_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin_access)
    ):
        """Get detailed webhook activity information"""
        
        webhook_service = WebhookActivityService(db)
        activity = webhook_service.repository.get_by_id(activity_id)
        
        if not activity:
            raise HTTPException(
                status_code=404,
                detail="Webhook activity not found"
            )
        
        return {
            "id": activity.id,
            "webhook_type": activity.webhook_type.value,
            "status": activity.status.value,
            "business_tin": activity.business_tin,
            "business_name": activity.business_name,
            "invoice_number": activity.invoice_number,
            "vsdc_receipt_number": activity.vsdc_receipt_number,
            "error_code": activity.error_code,
            "error_message": activity.error_message,
            "error_type": activity.error_type,
            "processing_time_ms": activity.processing_time_ms,
            "retry_count": activity.retry_count,
            "pdf_generated": activity.pdf_generated,
            "pdf_filename": activity.pdf_filename,
            "created_at": activity.created_at.isoformat() if activity.created_at else None,
            "updated_at": activity.updated_at.isoformat() if activity.updated_at else None,
            "processed_at": activity.processed_at.isoformat() if activity.processed_at else None,
            "payloads": {
                "zoho_payload": activity.zoho_payload,
                "vsdc_payload": activity.vsdc_payload,
                "vsdc_response": activity.vsdc_response
            }
        }