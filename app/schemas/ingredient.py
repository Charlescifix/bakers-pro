import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class IngredientCreate(BaseModel):
    name: str
    category_id: Optional[uuid.UUID] = None
    default_unit_code: str = "g"
    density_g_per_ml: Optional[Decimal] = None
    is_perishable: bool = False
    shelf_life_days: Optional[int] = None
    storage_instruction: Optional[str] = None
    allergen_notes: Optional[str] = None
    supplier_id: Optional[uuid.UUID] = None
    current_purchase_price: Decimal
    current_purchase_quantity: Decimal
    current_purchase_unit_code: str = "g"
    waste_percent_default: Decimal = Decimal("0")
    reorder_level: Optional[Decimal] = None
    notes: Optional[str] = None

    @field_validator("current_purchase_price")
    @classmethod
    def price_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("purchase_price must be >= 0")
        return v

    @field_validator("current_purchase_quantity")
    @classmethod
    def quantity_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("purchase_quantity must be > 0")
        return v


class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    default_unit_code: Optional[str] = None
    density_g_per_ml: Optional[Decimal] = None
    is_perishable: Optional[bool] = None
    shelf_life_days: Optional[int] = None
    storage_instruction: Optional[str] = None
    allergen_notes: Optional[str] = None
    supplier_id: Optional[uuid.UUID] = None
    current_purchase_price: Optional[Decimal] = None
    current_purchase_quantity: Optional[Decimal] = None
    current_purchase_unit_code: Optional[str] = None
    waste_percent_default: Optional[Decimal] = None
    reorder_level: Optional[Decimal] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class IngredientResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    category_id: Optional[uuid.UUID]
    default_unit_code: str
    density_g_per_ml: Optional[Decimal]
    is_perishable: bool
    shelf_life_days: Optional[int]
    storage_instruction: Optional[str]
    allergen_notes: Optional[str]
    supplier_id: Optional[uuid.UUID]
    current_purchase_price: Decimal
    current_purchase_quantity: Decimal
    current_purchase_unit_code: str
    current_unit_cost_base: Decimal
    waste_percent_default: Decimal
    reorder_level: Optional[Decimal]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PriceUpdateRequest(BaseModel):
    purchase_price: Decimal
    purchase_quantity: Decimal
    purchase_unit_code: str
    effective_date: Optional[datetime] = None
    supplier_id: Optional[uuid.UUID] = None
    receipt_file_url: Optional[str] = None
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


class PriceHistoryResponse(BaseModel):
    id: uuid.UUID
    ingredient_id: uuid.UUID
    supplier_id: Optional[uuid.UUID]
    purchase_price: Decimal
    purchase_quantity: Decimal
    purchase_unit_code: str
    unit_cost_base: Decimal
    effective_date: datetime
    source: str
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
