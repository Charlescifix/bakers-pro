import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductionBatchCreate(BaseModel):
    recipe_id: uuid.UUID
    planned_yield_quantity: Decimal
    planned_start_at: datetime | None = None
    planned_end_at: datetime | None = None
    assigned_to_user_id: uuid.UUID | None = None
    notes: str | None = None


class ProductionBatchUpdate(BaseModel):
    status: str | None = None
    actual_yield_quantity: Decimal | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    assigned_to_user_id: uuid.UUID | None = None
    notes: str | None = None


class ProductionBatchItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_item_id: uuid.UUID
    quantity_allocated: int


class ProductionBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_number: str
    recipe_id: uuid.UUID
    planned_yield_quantity: Decimal
    actual_yield_quantity: Decimal | None
    planned_start_at: datetime | None
    planned_end_at: datetime | None
    actual_start_at: datetime | None
    actual_end_at: datetime | None
    status: str
    assigned_to_user_id: uuid.UUID | None
    notes: str | None
    created_at: datetime
    batch_items: list[ProductionBatchItemResponse] = []


class GenerateProductionPlanRequest(BaseModel):
    order_ids: list[uuid.UUID]


class ProductionChecklistItem(BaseModel):
    batch_number: str
    recipe_name: str
    batches_required: int
    planned_yield_quantity: Decimal
    prep_time_minutes: int | None
    bake_time_minutes: int | None
    cooling_time_minutes: int | None
    labour_minutes: int | None
    storage_instruction: str | None
    serving_tip: str | None


class ProductionPlanResponse(BaseModel):
    batches: list[ProductionBatchResponse]
    checklist: list[ProductionChecklistItem]
