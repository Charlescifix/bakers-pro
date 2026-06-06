import uuid

from pydantic import BaseModel, ConfigDict


class AllergenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None


class IngredientAllergenCreate(BaseModel):
    allergen_id: uuid.UUID
    contains_status: str = "contains"
    notes: str | None = None


class IngredientAllergenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    ingredient_id: uuid.UUID
    allergen_id: uuid.UUID
    contains_status: str
    notes: str | None
    allergen: AllergenOut


class AllergenMatrixCell(BaseModel):
    allergen_id: uuid.UUID
    allergen_name: str
    status: str  # contains, may_contain, free, unknown


class AllergenMatrixRow(BaseModel):
    variant_id: uuid.UUID
    product_name: str
    variant_name: str
    allergens: list[AllergenMatrixCell]


class AllergenMatrixOut(BaseModel):
    allergen_names: list[str]
    rows: list[AllergenMatrixRow]
