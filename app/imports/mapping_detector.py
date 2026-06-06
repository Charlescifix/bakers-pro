"""Column and section detection heuristics for imported spreadsheet/CSV/PDF data."""
from __future__ import annotations

from dataclasses import dataclass, field

# ── keyword banks ─────────────────────────────────────────────────────────────

_NAME_KW = {"ingredient", "item", "product", "description", "name", "material"}
_PRICE_KW = {"price", "cost", "rate", "£", "$", "purchase price", "unit price", "buy price"}
_QTY_KW = {"quantity", "qty", "amount", "weight", "measure", "pack size", "pack qty"}
_UNIT_KW = {"unit", "uom", "measure", "measurement", "unit code"}
_WASTE_KW = {"waste", "loss", "shrink", "waste %", "yield loss"}
_USED_QTY_KW = {"quantity used", "used", "qty used", "amount used", "recipe qty", "use"}
_RECIPE_KW = {"recipe", "method", "instructions", "how to", "procedure"}
_PACKAGING_KW = {"packaging", "box", "bag", "wrapper", "container", "label", "wrap", "case"}
_OVERHEAD_KW = {"overhead", "energy", "gas", "electricity", "transport", "labour", "fixed cost"}
_SELLING_KW = {"selling price", "sale price", "price to customer", "retail price", "sell"}

# Generic demo-data names that indicate a sample/template sheet
_SAMPLE_NAMES = {
    "salmon", "potato", "tartar sauce", "chicken breast", "beef mince", "pasta",
    "rice", "example", "sample", "demo", "test", "item 1", "item 2", "product a",
    "ingredient a", "ingredient b",
}

_TEMPLATE_TRIGGERS = {"copyright", "template", "demo version", "sample data", "do not distribute"}


@dataclass
class ColumnMapping:
    name_col: str | None = None
    price_col: str | None = None
    qty_col: str | None = None
    unit_col: str | None = None
    waste_col: str | None = None
    used_qty_col: str | None = None
    confidence: float = 0.0


def _kw_match(header: str, bank: set[str]) -> bool:
    h = header.lower().strip()
    return any(kw in h for kw in bank)


def detect_column_mapping(headers: list[str]) -> ColumnMapping:
    """Given a list of column headers, detect which columns map to which fields."""
    m = ColumnMapping()
    for h in headers:
        if not m.name_col and _kw_match(h, _NAME_KW):
            m.name_col = h
        elif not m.price_col and _kw_match(h, _PRICE_KW):
            m.price_col = h
        elif not m.used_qty_col and _kw_match(h, _USED_QTY_KW):
            m.used_qty_col = h
        elif not m.qty_col and _kw_match(h, _QTY_KW):
            m.qty_col = h
        elif not m.unit_col and _kw_match(h, _UNIT_KW):
            m.unit_col = h
        elif not m.waste_col and _kw_match(h, _WASTE_KW):
            m.waste_col = h

    found = sum(
        1 for v in [m.name_col, m.price_col, m.qty_col, m.unit_col] if v is not None
    )
    m.confidence = {4: 0.92, 3: 0.78, 2: 0.55, 1: 0.35, 0: 0.10}[found]
    return m


def detect_section_type(headers: list[str], first_cell_values: list[str]) -> str:
    """Classify a table as ingredients, recipe, packaging, overhead, selling_price, or unknown."""
    all_text = " ".join(h.lower() for h in headers + first_cell_values)
    if any(kw in all_text for kw in _PACKAGING_KW):
        return "packaging"
    if any(kw in all_text for kw in _OVERHEAD_KW):
        return "overhead"
    if any(kw in all_text for kw in _SELLING_KW):
        return "selling_price"
    if any(kw in all_text for kw in _RECIPE_KW):
        return "recipe"
    if any(kw in all_text for kw in _NAME_KW | _PRICE_KW | _QTY_KW):
        return "ingredients"
    return "unknown"


def is_sample_content(sheet_name: str | None, row_values: list[str]) -> tuple[bool, str | None]:
    """Return (is_sample, reason) based on sheet name and cell content."""
    text = " ".join((sheet_name or "").lower().split() + [v.lower() for v in row_values])
    for trigger in _TEMPLATE_TRIGGERS:
        if trigger in text:
            return True, "possible_template_content"
    for name in _SAMPLE_NAMES:
        if name in text:
            return True, "sample_recipe"
    return False, None


def score_row(row: dict, col_map: ColumnMapping) -> tuple[dict, float, list[str]]:
    """Extract mapped fields from a raw row dict; return mapped dict, row confidence, flags."""
    mapped: dict = {}
    flags: list[str] = []

    name_val = row.get(col_map.name_col, "") if col_map.name_col else ""
    price_val = row.get(col_map.price_col, "") if col_map.price_col else ""
    qty_val = row.get(col_map.qty_col, "") if col_map.qty_col else ""
    unit_val = row.get(col_map.unit_col, "") if col_map.unit_col else ""
    waste_val = row.get(col_map.waste_col, "") if col_map.waste_col else ""
    used_val = row.get(col_map.used_qty_col, "") if col_map.used_qty_col else ""

    mapped["name"] = str(name_val).strip() if name_val else None
    mapped["purchase_price"] = _parse_decimal(price_val)
    mapped["purchase_quantity"] = _parse_decimal(qty_val)
    mapped["unit_code"] = str(unit_val).strip().lower() if unit_val else None
    mapped["waste_percent"] = _parse_decimal(waste_val)
    mapped["quantity_used"] = _parse_decimal(used_val)

    if not mapped["name"]:
        flags.append("missing_name")
    if mapped["purchase_price"] is None:
        flags.append("missing_price")
    if mapped["purchase_quantity"] is None:
        flags.append("missing_purchase_qty")

    missing_count = len([f for f in flags])
    row_conf = max(0.0, 1.0 - 0.25 * missing_count)
    return mapped, row_conf, flags


def _parse_decimal(value) -> "str | None":
    """Attempt to coerce a cell value to a decimal string; return None if not parseable."""
    if value is None or str(value).strip() in ("", "-", "N/A", "n/a"):
        return None
    cleaned = str(value).replace("£", "").replace("$", "").replace(",", "").strip()
    try:
        from decimal import Decimal, InvalidOperation
        Decimal(cleaned)
        return cleaned
    except (InvalidOperation, ValueError):
        return None
