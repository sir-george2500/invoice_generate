from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class BusinessBase(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    location: Optional[str] = Field(None, max_length=500)
    tin_number: str = Field(..., min_length=6, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)

class BusinessCreate(BusinessBase):
    admin_email: Optional[EmailStr] = None

class BusinessUpdate(BaseModel):
    business_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    location: Optional[str] = Field(None, max_length=500)
    tin_number: Optional[str] = Field(None, min_length=6, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None



class BusinessResponse(BusinessBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

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
