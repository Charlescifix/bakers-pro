import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------- Recipe Item ----------

class RecipeItemCreate(BaseModel):
    ingredient_id: uuid.UUID
    quantity_used: Decimal
    unit_code: str
    waste_percent_override: Optional[Decimal] = None
    preparation_note: Optional[str] = None
    is_optional: bool = False
    variant_group: Optional[str] = None

    @field_validator("quantity_used")
    @classmethod
    def quantity_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("quantity_used must be > 0")
        return v


class RecipeItemResponse(BaseModel):
    id: uuid.UUID
    recipe_version_id: uuid.UUID
    ingredient_id: uuid.UUID
    quantity_used: Decimal
    unit_code: str
    waste_percent_override: Optional[Decimal]
    preparation_note: Optional[str]
    is_optional: bool
    variant_group: Optional[str]

    model_config = {"from_attributes": True}


# ---------- Recipe Packaging Rule ----------

class PackagingRuleCreate(BaseModel):
    packaging_item_id: uuid.UUID
    rule_type: str = "per_item"  # per_item, per_batch, per_order
    quantity_per_item: Optional[Decimal] = None
    quantity_per_batch: Optional[Decimal] = None
    notes: Optional[str] = None


class PackagingRuleResponse(BaseModel):
    id: uuid.UUID
    recipe_id: uuid.UUID
    packaging_item_id: uuid.UUID
    rule_type: str
    quantity_per_item: Optional[Decimal]
    quantity_per_batch: Optional[Decimal]
    notes: Optional[str]

    model_config = {"from_attributes": True}


# ---------- Recipe Version ----------

class RecipeVersionCreate(BaseModel):
    items: list[RecipeItemCreate]
    notes: Optional[str] = None


class RecipeVersionResponse(BaseModel):
    id: uuid.UUID
    recipe_id: uuid.UUID
    version_number: int
    status: str
    effective_from: Optional[datetime]
    created_by_user_id: Optional[uuid.UUID]
    notes: Optional[str]
    items: list[RecipeItemResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Recipe ----------

class RecipeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "custom"
    base_yield_quantity: Decimal
    base_yield_unit: str = "item"
    prep_time_minutes: Optional[int] = None
    bake_time_minutes: Optional[int] = None
    cooling_time_minutes: Optional[int] = None
    labour_minutes_default: int = 60
    storage_instruction: Optional[str] = None
    serving_tip: Optional[str] = None
    internal_notes: Optional[str] = None
    items: list[RecipeItemCreate]

    @field_validator("base_yield_quantity")
    @classmethod
    def yield_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("base_yield_quantity must be > 0")
        return v

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Recipe must have at least one item")
        return v


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    base_yield_quantity: Optional[Decimal] = None
    base_yield_unit: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    bake_time_minutes: Optional[int] = None
    cooling_time_minutes: Optional[int] = None
    labour_minutes_default: Optional[int] = None
    storage_instruction: Optional[str] = None
    serving_tip: Optional[str] = None
    internal_notes: Optional[str] = None
    is_active: Optional[bool] = None


class RecipeResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    category: str
    base_yield_quantity: Decimal
    base_yield_unit: str
    prep_time_minutes: Optional[int]
    bake_time_minutes: Optional[int]
    cooling_time_minutes: Optional[int]
    labour_minutes_default: int
    storage_instruction: Optional[str]
    serving_tip: Optional[str]
    internal_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    packaging_rules: list[PackagingRuleResponse] = []

    model_config = {"from_attributes": True}


class RecipeWithVersionResponse(RecipeResponse):
    active_version: Optional[RecipeVersionResponse] = None


# ---------- Cost Preview ----------

class IngredientLineOut(BaseModel):
    ingredient_id: str
    ingredient_name: str
    quantity_used: Decimal
    unit_code: str
    quantity_in_base: Decimal
    unit_cost_base: Decimal
    waste_percent: Decimal
    line_cost: Decimal


class PackagingLineOut(BaseModel):
    packaging_item_id: str
    packaging_item_name: str
    rule_type: str
    quantity: Decimal
    unit_cost: Decimal
    line_cost: Decimal


class CostPreviewResponse(BaseModel):
    recipe_id: str
    recipe_name: str
    version_id: str
    version_number: int
    base_yield_quantity: Decimal
    base_yield_unit: str
    ingredient_lines: list[IngredientLineOut]
    packaging_lines: list[PackagingLineOut]
    total_ingredient_cost: Decimal
    total_packaging_cost: Decimal
    labour_minutes: int
    hourly_rate: Decimal
    total_labour_cost: Decimal
    total_cost_excluding_labour: Decimal
    total_cost_including_labour: Decimal
    cost_per_item_excl_labour: Decimal
    cost_per_item_incl_labour: Decimal
    recommended_prices: dict[str, Decimal]


# ---------- Scale Request ----------

class ScaleRequest(BaseModel):
    order_quantity: Decimal

    @field_validator("order_quantity")
    @classmethod
    def qty_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("order_quantity must be > 0")
        return v
