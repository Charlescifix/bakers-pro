import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ComplianceLogCreate(BaseModel):
    log_type: str
    recorded_at: datetime
    related_batch_id: uuid.UUID | None = None
    data_json: dict[str, Any] | None = None
    notes: str | None = None


class FridgeTemperatureLog(BaseModel):
    location: str
    temperature_celsius: float
    recorded_at: datetime
    notes: str | None = None


class CleaningLog(BaseModel):
    area: str
    cleaned_by: str | None = None
    cleaning_product: str | None = None
    recorded_at: datetime
    notes: str | None = None


class BatchRecordCreate(BaseModel):
    batch_id: uuid.UUID
    yield_quantity: float
    yield_unit: str = "pieces"
    recorded_at: datetime
    notes: str | None = None


class ComplianceLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    log_type: str
    recorded_at: datetime
    recorded_by_user_id: uuid.UUID
    related_batch_id: uuid.UUID | None
    data_json: str | None
    notes: str | None
    created_at: datetime
