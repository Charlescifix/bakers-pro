import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CustomerCreate(BaseModel):
    full_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    address: Optional[str] = None
    postcode: Optional[str] = None
    customer_type: str = "individual"
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    address: Optional[str] = None
    postcode: Optional[str] = None
    customer_type: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    full_name: str
    company_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    instagram_handle: Optional[str]
    tiktok_handle: Optional[str]
    address: Optional[str]
    postcode: Optional[str]
    customer_type: str
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
