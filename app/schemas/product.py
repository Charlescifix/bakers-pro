import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------- Product Variant ----------

class VariantCreate(BaseModel):
    name: str
    recipe_id: Optional[uuid.UUID] = None
    quantity_multiplier: Decimal = Decimal("1")
    minimum_order_quantity: int = 1
    current_selling_price: Decimal = Decimal("0")
    desired_margin_percent: Decimal = Decimal("60")
    channel_default_price_rules: Optional[dict] = None
    sku: Optional[str] = None

    @field_validator("quantity_multiplier")
    @classmethod
    def multiplier_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("quantity_multiplier must be > 0")
        return v

    @field_validator("minimum_order_quantity")
    @classmethod
    def moq_at_least_one(cls, v: int) -> int:
        if v < 1:
            raise ValueError("minimum_order_quantity must be >= 1")
        return v

    @field_validator("current_selling_price")
    @classmethod
    def price_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("current_selling_price must be >= 0")
        return v


class VariantUpdate(BaseModel):
    name: Optional[str] = None
    recipe_id: Optional[uuid.UUID] = None
    quantity_multiplier: Optional[Decimal] = None
    minimum_order_quantity: Optional[int] = None
    current_selling_price: Optional[Decimal] = None
    desired_margin_percent: Optional[Decimal] = None
    channel_default_price_rules: Optional[dict] = None
    sku: Optional[str] = None
    is_active: Optional[bool] = None


class VariantResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    name: str
    recipe_id: Optional[uuid.UUID]
    quantity_multiplier: Decimal
    minimum_order_quantity: int
    current_selling_price: Decimal
    desired_margin_percent: Decimal
    channel_default_price_rules: Optional[dict]
    sku: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Product ----------

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "custom"
    default_recipe_id: Optional[uuid.UUID] = None
    image_url: Optional[str] = None
    variants: list[VariantCreate] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    default_recipe_id: Optional[uuid.UUID] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    category: str
    default_recipe_id: Optional[uuid.UUID]
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    variants: list[VariantResponse] = []

    model_config = {"from_attributes": True}


# ---------- Pricing Summary ----------

class PricingSummaryResponse(BaseModel):
    variant_id: str
    variant_name: str
    product_id: str
    product_name: str
    recipe_id: Optional[str]
    recipe_name: Optional[str]
    quantity_multiplier: Decimal

    current_selling_price: Decimal
    desired_margin_percent: Decimal
    minimum_order_quantity: int

    # Per-variant costs
    ingredient_cost: Decimal
    packaging_cost: Decimal
    labour_cost: Decimal
    total_cost_excluding_labour: Decimal
    total_cost_including_labour: Decimal

    # At current selling price
    gross_profit: Decimal
    net_profit: Decimal
    food_cost_percent: Decimal
    gross_margin_percent: Decimal
    net_margin_percent: Decimal

    # Recommended prices
    recommended_price: Decimal          # at desired_margin_percent
    recommended_prices: dict[str, Decimal]  # at 50/55/60/65/70%

    # Margin health
    margin_status: str
    warnings: list[str]
