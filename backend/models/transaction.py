from sqlalchemy import Integer, String, DateTime, Boolean, Numeric, ForeignKey, Text
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # SALE, VOID, REFUND
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    net_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)  # CASH, CARD, MOBILE, etc.
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RWF")
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_tin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    receipt_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional VSDC specific fields
    vsdc_receipt_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vsdc_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    business = relationship("Business", backref="transactions")

class DailyReport(Base):
    __tablename__ = "daily_reports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(10), nullable=False)  # X or Z
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    report_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Sequential number per business
    
    # Sales totals
    total_sales_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_tax_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_net_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    
    # Transaction counts
    total_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    voided_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    refunded_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Payment method breakdown (JSON or separate fields)
    cash_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    card_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    mobile_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    other_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    
    # Period information
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Report metadata
    generated_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # True for Z reports
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    business = relationship("Business", backref="daily_reports")
    generated_by_user = relationship("User", backref="generated_reports")