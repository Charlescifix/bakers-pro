import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GenerateLabelRequest(BaseModel):
    product_variant_id: uuid.UUID
    label_type: str = "allergen"
    batch_number: str | None = None
    best_before_date: str | None = None


class LabelDataOut(BaseModel):
    product_name: str
    variant_name: str
    label_type: str
    ingredients: list[str]
    allergens_contains: list[str]
    allergens_may_contain: list[str]
    storage_instruction: str | None
    reheating_instruction: str | None
    shelf_life_days: int | None
    batch_number: str | None
    best_before_date: str | None
    bakery_name: str
    fsa_rating: str | None
    template_html: str


class LabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    product_variant_id: uuid.UUID
    label_type: str
    template_html: str | None
    last_generated_at: datetime | None
    created_at: datetime
