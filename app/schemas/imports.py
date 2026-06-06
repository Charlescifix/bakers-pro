import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DetectedRow(BaseModel):
    row_index: int
    raw: dict
    mapped: dict
    confidence: float
    flags: list[str] = []


class DetectedSection(BaseModel):
    section_type: str  # ingredients, recipe, packaging, overhead, selling_price, unknown
    sheet_name: str | None = None
    rows: list[DetectedRow]
    confidence: float
    is_sample: bool = False
    sample_reason: str | None = None


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    source_file_type: str
    source_file_url: str
    mapping_confidence_score: float | None
    error_message: str | None
    detected_sections: list[DetectedSection] | None = None
    created_at: datetime
    completed_at: datetime | None


class ReviewMappingRequest(BaseModel):
    column_overrides: dict[str, str] = {}
    exclude_section_indices: list[int] = []


class ConfirmImportResponse(BaseModel):
    imported_ingredients: int = 0
    imported_recipes: int = 0
    imported_packaging: int = 0
    skipped_rows: int = 0
    warnings: list[str] = []


class RollbackResponse(BaseModel):
    deleted_ingredients: int = 0
    deleted_recipes: int = 0
    deleted_packaging: int = 0
