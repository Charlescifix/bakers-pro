from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParsedOrderItem(BaseModel):
    product_name: str
    quantity: int


class ParsedOrderResult(BaseModel):
    items: list[ParsedOrderItem]
    requested_date: str | None
    delivery_method: str
    confidence: float
    raw_message: str


class OrderParseRequest(BaseModel):
    message: str


class PricingAdviceRequest(BaseModel):
    variant_ids: list[uuid.UUID] | None = None


class PricingAdviceItem(BaseModel):
    variant_id: uuid.UUID
    product_name: str
    variant_name: str
    advice: str
    current_price: float
    suggested_price: float | None
    priority: str  # low, medium, high


class PricingAdviceResult(BaseModel):
    items: list[PricingAdviceItem]
    summary: str


class IntelligenceEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    severity: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


class AskRequest(BaseModel):
    question: str
