import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SupplierCreate(BaseModel):
    name: str
    type: str = "mixed"
    website: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    website: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    type: str
    website: Optional[str]
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
