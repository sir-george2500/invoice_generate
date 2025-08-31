from sqlalchemy import Integer, String, DateTime, Boolean, Text, JSON, Enum
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
import enum

class WebhookStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success" 
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRY = "retry"

class WebhookType(str, enum.Enum):
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"

class WebhookActivity(Base):
    __tablename__ = "webhook_activities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Basic webhook info
    webhook_type: Mapped[WebhookType] = mapped_column(Enum(WebhookType), nullable=False)
    status: Mapped[WebhookStatus] = mapped_column(Enum(WebhookStatus), default=WebhookStatus.PENDING)
    
    # Business identification (for easier troubleshooting)
    business_tin: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    business_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    vsdc_receipt_number: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    
    # Request/Response details
    zoho_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    vsdc_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    vsdc_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Error information
    error_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Processing details
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    pdf_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    pdf_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)