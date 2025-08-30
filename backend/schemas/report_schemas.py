from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class TransactionCreate(BaseModel):
    business_tin: str = Field(..., description="Business TIN number")
    invoice_number: str = Field(..., description="Invoice number")
    transaction_type: str = Field(..., description="SALE, VOID, REFUND")
    total_amount: float = Field(..., ge=0, description="Total amount including tax")
    tax_amount: float = Field(0, ge=0, description="Tax amount")
    net_amount: float = Field(..., ge=0, description="Net amount excluding tax")
    payment_method: str = Field(..., description="Payment method")
    currency: str = Field("RWF", description="Currency code")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_tin: Optional[str] = Field(None, description="Customer TIN")
    receipt_number: Optional[str] = Field(None, description="Receipt number")

class TransactionResponse(BaseModel):
    id: int
    business_id: int
    invoice_number: str
    transaction_type: str
    total_amount: float
    tax_amount: float
    net_amount: float
    payment_method: str
    currency: str
    customer_name: Optional[str]
    customer_tin: Optional[str]
    receipt_number: Optional[str]
    is_voided: bool
    transaction_date: datetime
    vsdc_receipt_id: Optional[str]
    
    class Config:
        from_attributes = True

class PaymentMethodBreakdown(BaseModel):
    cash_amount: float = Field(default=0, description="Cash payments total")
    card_amount: float = Field(default=0, description="Card payments total")
    mobile_amount: float = Field(default=0, description="Mobile payments total")
    other_amount: float = Field(default=0, description="Other payments total")

class DailyReportSummary(BaseModel):
    # Report metadata
    report_type: str = Field(..., description="X or Z")
    report_number: int = Field(..., description="Sequential report number")
    report_date: datetime = Field(..., description="Report generation date")
    business_tin: str = Field(..., description="Business TIN")
    business_name: str = Field(..., description="Business name")
    
    # Period information
    period_start: datetime = Field(..., description="Report period start")
    period_end: datetime = Field(..., description="Report period end")
    
    # Sales totals
    total_sales_amount: float = Field(..., description="Total sales amount")
    total_tax_amount: float = Field(..., description="Total tax amount")
    total_net_amount: float = Field(..., description="Total net amount")
    
    # Transaction counts
    total_transactions: int = Field(..., description="Total number of transactions")
    voided_transactions: int = Field(default=0, description="Number of voided transactions")
    refunded_transactions: int = Field(default=0, description="Number of refunded transactions")
    
    # Payment breakdown
    payment_methods: PaymentMethodBreakdown = Field(..., description="Payment method breakdown")
    
    # Report status
    is_finalized: bool = Field(..., description="Whether report is finalized (Z report)")
    generated_by: str = Field(..., description="User who generated the report")

class XReportRequest(BaseModel):
    business_tin: str = Field(..., description="Business TIN number")

class ZReportRequest(BaseModel):
    business_tin: str = Field(..., description="Business TIN number")
    confirm_finalize: bool = Field(True, description="Confirm finalization of day")

class ReportFilters(BaseModel):
    business_tin: str = Field(..., description="Business TIN number")
    start_date: Optional[datetime] = Field(None, description="Filter from date")
    end_date: Optional[datetime] = Field(None, description="Filter to date")
    report_type: Optional[str] = Field(None, description="X or Z")

class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")