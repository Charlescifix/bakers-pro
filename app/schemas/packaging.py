import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class PackagingCreate(BaseModel):
    name: str
    supplier_id: Optional[uuid.UUID] = None
    purchase_price: Decimal
    purchase_quantity: Decimal
    purchase_unit_code: str = "piece"
    reorder_level: Optional[Decimal] = None
    notes: Optional[str] = None

    @field_validator("purchase_price")
    @classmethod
    def price_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("purchase_price must be >= 0")
        return v

    @field_validator("purchase_quantity")
    @classmethod
    def quantity_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("purchase_quantity must be > 0")
        return v


class PackagingUpdate(BaseModel):
    name: Optional[str] = None
    supplier_id: Optional[uuid.UUID] = None
    purchase_price: Optional[Decimal] = None
    purchase_quantity: Optional[Decimal] = None
    purchase_unit_code: Optional[str] = None
    current_stock_quantity: Optional[Decimal] = None
    reorder_level: Optional[Decimal] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class PackagingResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    supplier_id: Optional[uuid.UUID]
    purchase_price: Decimal
    purchase_quantity: Decimal
    purchase_unit_code: str
    unit_cost: Decimal
    current_stock_quantity: Decimal
    reorder_level: Optional[Decimal]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
