import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SalesChannelCreate(BaseModel):
    name: str
    percentage_fee: Decimal = Decimal("0")
    fixed_fee_per_order: Decimal = Decimal("0")
    fixed_fee_per_item: Decimal = Decimal("0")
    payment_processing_percent: Decimal = Decimal("0")
    payment_processing_fixed: Decimal = Decimal("0")
    commission_notes: Optional[str] = None


class SalesChannelUpdate(BaseModel):
    name: Optional[str] = None
    percentage_fee: Optional[Decimal] = None
    fixed_fee_per_order: Optional[Decimal] = None
    fixed_fee_per_item: Optional[Decimal] = None
    payment_processing_percent: Optional[Decimal] = None
    payment_processing_fixed: Optional[Decimal] = None
    commission_notes: Optional[str] = None
    is_active: Optional[bool] = None


class SalesChannelResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    percentage_fee: Decimal
    fixed_fee_per_order: Decimal
    fixed_fee_per_item: Decimal
    payment_processing_percent: Decimal
    payment_processing_fixed: Decimal
    commission_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
