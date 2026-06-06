import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderItemCreate(BaseModel):
    product_variant_id: uuid.UUID
    quantity: int
    unit_price: Decimal


class OrderCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    sales_channel_id: uuid.UUID | None = None
    order_date: datetime
    due_date: datetime | None = None
    delivery_method: str = "pickup"
    notes: str | None = None
    items: list[OrderItemCreate]


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_variant_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    actual_ingredient_cost: Decimal
    actual_packaging_cost: Decimal
    actual_labour_cost: Decimal
    actual_channel_fee: Decimal
    actual_net_profit: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_number: str
    quote_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    status: str
    sales_channel_id: uuid.UUID | None
    order_date: datetime
    due_date: datetime | None
    delivery_date: datetime | None
    delivery_method: str
    payment_status: str
    amount_paid: Decimal
    balance_due: Decimal
    total_revenue: Decimal
    total_cost: Decimal
    net_profit: Decimal
    notes: str | None
    created_at: datetime
    items: list[OrderItemResponse] = []


class OrderStatusUpdate(BaseModel):
    status: str


class OrderPaymentUpdate(BaseModel):
    amount: Decimal
