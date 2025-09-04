from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime

class BusinessBase(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    location: Optional[str] = Field(None, max_length=500)
    tin_number: str = Field(..., min_length=6, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=1000)

class ZohoBusinessProfile(BaseModel):
    """Schema for creating business profile from Zoho plugin"""
    business_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    location: str = Field(..., min_length=5, max_length=500, description="Company address for EBM receipts")
    tin_number: str = Field(..., min_length=6, max_length=50, pattern=r"^\d{9}$", description="9-digit TIN number")
    phone_number: Optional[str] = Field(None, max_length=20)
    zoho_organization_id: str = Field(..., min_length=1, max_length=100)
    default_currency: Optional[str] = Field("RWF", max_length=10)
    ebm_service_url: Optional[str] = Field(None, max_length=500)

class BusinessCreate(BusinessBase):
    admin_email: Optional[EmailStr] = None

class BusinessUpdate(BaseModel):
    business_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    location: Optional[str] = Field(None, max_length=500)
    tin_number: Optional[str] = Field(None, min_length=6, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None



class BusinessResponse(BusinessBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    zoho_organization_id: Optional[str]
    default_currency: Optional[str]
    setup_completed_at: Optional[datetime]
    webhook_config: Optional[Dict[str, Any]]
    ebm_service_url: Optional[str]

    class Config:
        from_attributes = True

class ZohoBusinessProfileResponse(BaseModel):
    """Response for Zoho business profile operations"""
    id: int
    business_name: str
    email: str
    tin_number: str
    location: str
    zoho_organization_id: str
    default_currency: str
    setup_completed_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True

class BusinessSummary(BaseModel):
    id: int
    business_name: str
    email: str
    tin_number: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AdminCredentials(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class BusinessCreateResponse(BaseModel):
    business: BusinessResponse
    admin_credentials: AdminCredentials
