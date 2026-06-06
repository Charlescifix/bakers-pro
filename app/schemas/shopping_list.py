import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class GenerateShoppingListRequest(BaseModel):
    name: str
    order_ids: list[uuid.UUID]
    start_date: datetime | None = None
    end_date: datetime | None = None


class ShoppingListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ingredient_id: uuid.UUID | None
    packaging_item_id: uuid.UUID | None
    item_name: str
    item_type: str
    required_quantity: Decimal
    unit_code: str
    current_stock_quantity: Decimal
    quantity_to_buy: Decimal
    estimated_cost: Decimal
    supplier_id: uuid.UUID | None


class ShoppingListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    start_date: datetime | None
    end_date: datetime | None
    status: str
    total_estimated_cost: Decimal
    created_at: datetime
    list_items: list[ShoppingListItemResponse] = []


class ShoppingListItemMarkPurchased(BaseModel):
    item_ids: list[uuid.UUID]
