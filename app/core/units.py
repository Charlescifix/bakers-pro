from decimal import Decimal
from enum import Enum


class UnitType(str, Enum):
    weight = "weight"
    volume = "volume"
    count = "count"
    batch = "batch"
    time = "time"


# Conversion factors to base unit (g for weight, ml for volume, piece for count, minute for time)
UNIT_CONVERSIONS: dict[str, dict] = {
    # Weight — base: g
    "g":   {"type": UnitType.weight, "base": "g",  "to_base": Decimal("1")},
    "kg":  {"type": UnitType.weight, "base": "g",  "to_base": Decimal("1000")},
    "oz":  {"type": UnitType.weight, "base": "g",  "to_base": Decimal("28.349523")},
    "lb":  {"type": UnitType.weight, "base": "g",  "to_base": Decimal("453.59237")},
    # Volume — base: ml
    "ml":   {"type": UnitType.volume, "base": "ml", "to_base": Decimal("1")},
    "l":    {"type": UnitType.volume, "base": "ml", "to_base": Decimal("1000")},
    "tsp":  {"type": UnitType.volume, "base": "ml", "to_base": Decimal("4.92892")},
    "tbsp": {"type": UnitType.volume, "base": "ml", "to_base": Decimal("14.78676")},
    "cup":  {"type": UnitType.volume, "base": "ml", "to_base": Decimal("236.588")},
    # Count — base: piece
    "piece":  {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "unit":   {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "pack":   {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "bag":    {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "carton": {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "sheet":  {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "label":  {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "item":   {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "loaf":   {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "pie":    {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "box":    {"type": UnitType.count, "base": "piece", "to_base": Decimal("1")},
    "batch":  {"type": UnitType.batch, "base": "batch", "to_base": Decimal("1")},
    # Time — base: minute
    "minute": {"type": UnitType.time, "base": "minute", "to_base": Decimal("1")},
    "hour":   {"type": UnitType.time, "base": "minute", "to_base": Decimal("60")},
}


def convert_to_base(quantity: Decimal, unit_code: str) -> Decimal:
    unit = UNIT_CONVERSIONS.get(unit_code)
    if unit is None:
        raise ValueError(f"Unknown unit code: {unit_code}")
    return quantity * unit["to_base"]


def get_unit_type(unit_code: str) -> UnitType:
    unit = UNIT_CONVERSIONS.get(unit_code)
    if unit is None:
        raise ValueError(f"Unknown unit code: {unit_code}")
    return unit["type"]


def units_compatible(unit_a: str, unit_b: str) -> bool:
    try:
        return get_unit_type(unit_a) == get_unit_type(unit_b)
    except ValueError:
        return False
