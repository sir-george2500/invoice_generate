from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
import time
import json

from models.webhook_activity import WebhookActivity, WebhookStatus, WebhookType
from repositories.webhook_activity_repository import WebhookActivityRepository

class WebhookActivityService:
    """Service for managing webhook activity tracking and logging"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = WebhookActivityRepository(db)
    
    def create_webhook_activity(
        self,
        webhook_type: WebhookType,
        business_tin: Optional[str] = None,
        business_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        zoho_payload: Optional[Dict[str, Any]] = None
    ) -> WebhookActivity:
        """Create a new webhook activity entry"""
        
        activity_data = {
            "webhook_type": webhook_type,
            "status": WebhookStatus.PENDING,
            "business_tin": business_tin,
            "business_name": business_name,
            "invoice_number": invoice_number,
            "zoho_payload": zoho_payload,
            "created_at": datetime.utcnow()
        }
        
        return self.repository.create(activity_data)
    
    def update_webhook_success(
        self,
        activity_id: int,
        vsdc_payload: Dict[str, Any],
        vsdc_response: Dict[str, Any],
        processing_time_ms: int,
        pdf_filename: Optional[str] = None
    ) -> Optional[WebhookActivity]:
        """Update webhook activity with success details"""
        
        # Extract receipt number from VSDC response
        vsdc_receipt_number = None
        if isinstance(vsdc_response, dict):
            data_section = vsdc_response.get("data", {})
            if isinstance(data_section, dict):
                vsdc_receipt_number = data_section.get("rcptNo")
        
        update_data = {
            "status": WebhookStatus.SUCCESS,
            "vsdc_payload": vsdc_payload,
            "vsdc_response": vsdc_response,
            "vsdc_receipt_number": vsdc_receipt_number,
            "processing_time_ms": processing_time_ms,
            "pdf_generated": pdf_filename is not None,
            "pdf_filename": pdf_filename,
            "processed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return self.repository.update(activity_id, update_data)
    
    def update_webhook_failure(
        self,
        activity_id: int,
        error_code: Optional[str],
        error_message: str,
        error_type: str,
        processing_time_ms: int,
        vsdc_payload: Optional[Dict[str, Any]] = None,
        vsdc_response: Optional[Dict[str, Any]] = None
    ) -> Optional[WebhookActivity]:
        """Update webhook activity with failure details"""
        
        update_data = {
            "status": WebhookStatus.FAILED,
            "error_code": error_code,
            "error_message": error_message,
            "error_type": error_type,
            "processing_time_ms": processing_time_ms,
            "processed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if vsdc_payload:
            update_data["vsdc_payload"] = vsdc_payload
        
        if vsdc_response:
            update_data["vsdc_response"] = vsdc_response
            # Try to extract receipt number even from failed responses
            if isinstance(vsdc_response, dict):
                data_section = vsdc_response.get("data", {})
                if isinstance(data_section, dict):
                    receipt_number = data_section.get("rcptNo")
                    if receipt_number:
                        update_data["vsdc_receipt_number"] = receipt_number
        
        return self.repository.update(activity_id, update_data)
    
    def increment_retry_count(self, activity_id: int) -> Optional[WebhookActivity]:
        """Increment the retry count for a webhook activity"""
        activity = self.repository.get_by_id(activity_id)
        if activity:
            update_data = {
                "retry_count": activity.retry_count + 1,
                "status": WebhookStatus.RETRY,
                "updated_at": datetime.utcnow()
            }
            return self.repository.update(activity_id, update_data)
        return None
    
    def get_webhook_activities(
        self,
        business_tin: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        webhook_type: Optional[WebhookType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WebhookActivity]:
        """Get webhook activities with optional filtering"""
        
        return self.repository.get_filtered_activities(
            business_tin=business_tin,
            status=status,
            webhook_type=webhook_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
    
    def get_failed_webhook_activities(
        self,
        hours_back: int = 24,
        limit: int = 50
    ) -> List[WebhookActivity]:
        """Get recent failed webhook activities for troubleshooting"""
        
        start_date = datetime.utcnow() - timedelta(hours=hours_back)
        
        return self.repository.get_filtered_activities(
            status=WebhookStatus.FAILED,
            start_date=start_date,
            limit=limit,
            offset=0
        )
    
    def get_webhook_stats(
        self,
        business_tin: Optional[str] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Get webhook activity statistics"""
        
        start_date = datetime.utcnow() - timedelta(days=days_back)
        
        activities = self.repository.get_filtered_activities(
            business_tin=business_tin,
            start_date=start_date,
            limit=1000,  # Get more for stats
            offset=0
        )
        
        stats = {
            "total_webhooks": len(activities),
            "successful": len([a for a in activities if a.status == WebhookStatus.SUCCESS]),
            "failed": len([a for a in activities if a.status == WebhookStatus.FAILED]),
            "pending": len([a for a in activities if a.status == WebhookStatus.PENDING]),
            "by_type": {
                "invoices": len([a for a in activities if a.webhook_type == WebhookType.INVOICE]),
                "credit_notes": len([a for a in activities if a.webhook_type == WebhookType.CREDIT_NOTE])
            },
            "avg_processing_time_ms": 0,
            "success_rate": 0.0
        }
        
        # Calculate average processing time
        completed_activities = [a for a in activities if a.processing_time_ms is not None]
        if completed_activities:
            stats["avg_processing_time_ms"] = sum(a.processing_time_ms for a in completed_activities) / len(completed_activities)
        
        # Calculate success rate
        if stats["total_webhooks"] > 0:
            stats["success_rate"] = (stats["successful"] / stats["total_webhooks"]) * 100
        
        return stats
    
    def extract_business_info_from_payload(
        self, 
        zoho_payload: Dict[str, Any], 
        webhook_type: WebhookType
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract business TIN, name, and invoice number from Zoho payload"""
        
        try:
            if webhook_type == WebhookType.INVOICE:
                invoice_data = zoho_payload.get("invoice", {})
            else:  # CREDIT_NOTE
                invoice_data = zoho_payload.get("creditnote", {})
            
            if not invoice_data:
                return None, None, None
            
            # Extract TIN from custom fields
            custom_fields = invoice_data.get("custom_field_hash", {})
            business_tin = custom_fields.get("cf_tin")
            
            # Extract invoice/credit note number
            invoice_number = invoice_data.get("invoice_number") or invoice_data.get("creditnote_number")
            
            # Extract business name (might be in different places)
            business_name = (
                invoice_data.get("company_name") or 
                invoice_data.get("organization_name") or
                custom_fields.get("cf_company_name")
            )
            
            return business_tin, business_name, invoice_number
            
        except Exception as e:
            # Log error but don't fail the webhook
            print(f"Error extracting business info from payload: {str(e)}")
            return None, None, None