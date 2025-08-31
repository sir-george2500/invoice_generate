from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta

from models.webhook_activity import WebhookActivity, WebhookStatus, WebhookType

class WebhookActivityRepository:
    """Repository for webhook activity data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, activity_data: Dict[str, Any]) -> WebhookActivity:
        """Create a new webhook activity record"""
        activity = WebhookActivity(**activity_data)
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity
    
    def get_by_id(self, activity_id: int) -> Optional[WebhookActivity]:
        """Get webhook activity by ID"""
        return self.db.query(WebhookActivity).filter(WebhookActivity.id == activity_id).first()
    
    def update(self, activity_id: int, update_data: Dict[str, Any]) -> Optional[WebhookActivity]:
        """Update webhook activity record"""
        activity = self.get_by_id(activity_id)
        if activity:
            for key, value in update_data.items():
                setattr(activity, key, value)
            self.db.commit()
            self.db.refresh(activity)
        return activity
    
    def get_filtered_activities(
        self,
        business_tin: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        webhook_type: Optional[WebhookType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        invoice_number: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WebhookActivity]:
        """Get filtered webhook activities"""
        
        query = self.db.query(WebhookActivity)
        
        # Apply filters
        if business_tin:
            query = query.filter(WebhookActivity.business_tin == business_tin)
        
        if status:
            query = query.filter(WebhookActivity.status == status)
        
        if webhook_type:
            query = query.filter(WebhookActivity.webhook_type == webhook_type)
        
        if invoice_number:
            query = query.filter(WebhookActivity.invoice_number.ilike(f"%{invoice_number}%"))
        
        if start_date:
            query = query.filter(WebhookActivity.created_at >= start_date)
        
        if end_date:
            query = query.filter(WebhookActivity.created_at <= end_date)
        
        # Order by most recent first
        query = query.order_by(desc(WebhookActivity.created_at))
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        return query.all()
    
    def get_recent_failures(self, hours_back: int = 24) -> List[WebhookActivity]:
        """Get recent webhook failures"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        return self.db.query(WebhookActivity).filter(
            and_(
                WebhookActivity.status == WebhookStatus.FAILED,
                WebhookActivity.created_at >= cutoff_time
            )
        ).order_by(desc(WebhookActivity.created_at)).all()
    
    def delete(self, activity_id: int) -> bool:
        """Delete webhook activity record"""
        activity = self.get_by_id(activity_id)
        if activity:
            self.db.delete(activity)
            self.db.commit()
            return True
        return False
    
    def get_activities_by_business(self, business_tin: str, limit: int = 50) -> List[WebhookActivity]:
        """Get all activities for a specific business"""
        return self.db.query(WebhookActivity).filter(
            WebhookActivity.business_tin == business_tin
        ).order_by(desc(WebhookActivity.created_at)).limit(limit).all()