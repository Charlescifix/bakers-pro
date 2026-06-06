"""Validates mapped rows before they are committed to the database."""
from __future__ import annotations

from dataclasses import dataclass


VALID_UNITS = {
    "g", "kg", "ml", "l", "litre", "liter", "oz", "lb", "lbs",
    "tsp", "tbsp", "cup", "piece", "pcs", "pack", "bag", "box",
    "bunch", "clove", "pinch", "slice", "sheet",
}


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_ingredient_row(mapped: dict) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    name = mapped.get("name")
    if not name:
        errors.append("ingredient name is required")
    elif len(name) > 200:
        errors.append("ingredient name too long (max 200 chars)")

    price = mapped.get("purchase_price")
    if price is None:
        warnings.append("purchase_price missing — will default to 0")
    else:
        try:
            from decimal import Decimal
            p = Decimal(price)
            if p < 0:
                errors.append("purchase_price must be >= 0")
        except Exception:
            errors.append(f"purchase_price '{price}' is not a valid number")

    qty = mapped.get("purchase_quantity")
    if qty is None:
        warnings.append("purchase_quantity missing — will default to 1")
    else:
        try:
            from decimal import Decimal
            q = Decimal(qty)
            if q <= 0:
                errors.append("purchase_quantity must be > 0")
        except Exception:
            errors.append(f"purchase_quantity '{qty}' is not a valid number")

    unit = mapped.get("unit_code")
    if not unit:
        warnings.append("unit_code missing — will default to 'g'")
    elif unit.lower() not in VALID_UNITS:
        warnings.append(f"unit_code '{unit}' not recognised — will store as-is")

    waste = mapped.get("waste_percent")
    if waste is not None:
        try:
            from decimal import Decimal
            w = Decimal(waste)
            if not (0 <= w <= 100):
                errors.append("waste_percent must be between 0 and 100")
        except Exception:
            errors.append(f"waste_percent '{waste}' is not a valid number")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_packaging_row(mapped: dict) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not mapped.get("name"):
        errors.append("packaging item name is required")

    price = mapped.get("purchase_price")
    if price is None:
        warnings.append("purchase_price missing — will default to 0")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
