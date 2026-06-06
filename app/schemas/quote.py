import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------- Quote Item ----------

class QuoteItemInput(BaseModel):
    product_variant_id: uuid.UUID
    quantity: int
    unit_price_override: Optional[Decimal] = None  # None = use recommended

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("quantity must be >= 1")
        return v


class QuoteItemResponse(BaseModel):
    id: uuid.UUID
    quote_id: uuid.UUID
    product_variant_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    recommended_unit_price: Decimal
    manual_price_override: bool
    line_revenue: Decimal
    line_ingredient_cost: Decimal
    line_packaging_cost: Decimal
    line_labour_cost: Decimal
    line_channel_fee: Decimal
    line_net_profit: Decimal
    line_margin_percent: Decimal

    model_config = {"from_attributes": True}


# ---------- Quote Create / Update ----------

class QuoteCreate(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    sales_channel_id: Optional[uuid.UUID] = None
    requested_delivery_date: Optional[datetime] = None
    delivery_method: str = "pickup"
    delivery_fee_charged: Decimal = Decimal("0")
    delivery_cost_estimate: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    discount_percent: Decimal = Decimal("0")
    desired_margin_percent: Decimal = Decimal("60")
    internal_notes: Optional[str] = None
    items: list[QuoteItemInput]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Quote must have at least one item")
        return v


class QuoteUpdate(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    sales_channel_id: Optional[uuid.UUID] = None
    requested_delivery_date: Optional[datetime] = None
    delivery_method: Optional[str] = None
    delivery_fee_charged: Optional[Decimal] = None
    delivery_cost_estimate: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    desired_margin_percent: Optional[Decimal] = None
    internal_notes: Optional[str] = None
    status: Optional[str] = None


# ---------- Shopping List Preview ----------

class ShoppingLineOut(BaseModel):
    ingredient_id: str
    ingredient_name: str
    required_quantity: Decimal
    unit_code: str


# ---------- Quote Response ----------

class QuoteResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    quote_number: str
    customer_id: Optional[uuid.UUID]
    status: str
    sales_channel_id: Optional[uuid.UUID]
    requested_delivery_date: Optional[datetime]
    delivery_method: str
    delivery_fee_charged: Decimal
    delivery_cost_estimate: Decimal
    discount_amount: Decimal
    discount_percent: Decimal
    desired_margin_percent: Decimal
    total_revenue: Decimal
    total_cost_excluding_labour: Decimal
    total_labour_cost: Decimal
    total_channel_fees: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    food_cost_percent: Decimal
    profit_margin_percent: Decimal
    recommendation_status: str
    customer_message: Optional[str]
    internal_notes: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    items: list[QuoteItemResponse] = []

    model_config = {"from_attributes": True}


class QuoteDetailResponse(QuoteResponse):
    recommended_total_price: Decimal = Decimal("0")
    warnings: list[str] = []
    shopping_list_preview: list[ShoppingLineOut] = []


# ---------- Message Request ----------

class GenerateMessageRequest(BaseModel):
    customer_name: Optional[str] = None
