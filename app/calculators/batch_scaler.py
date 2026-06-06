import math
from decimal import Decimal


def batches_required(order_quantity: Decimal, base_yield: Decimal) -> int:
    if base_yield <= 0:
        raise ValueError("base_yield must be greater than zero")
    return math.ceil(float(order_quantity / base_yield))


def scale_ingredient(
    base_quantity: Decimal,
    base_yield: Decimal,
    order_quantity: Decimal,
) -> Decimal:
    batches = Decimal(str(batches_required(order_quantity, base_yield)))
    return base_quantity * batches


def scale_recipe(
    items: list[dict],
    base_yield: Decimal,
    order_quantity: Decimal,
) -> list[dict]:
    """
    items: list of {"ingredient_id": ..., "quantity": Decimal, "unit_code": str, ...}
    Returns scaled items with 'scaled_quantity' added.
    """
    batches = Decimal(str(batches_required(order_quantity, base_yield)))
    scaled = []
    for item in items:
        scaled_item = dict(item)
        scaled_item["scaled_quantity"] = item["quantity"] * batches
        scaled_item["batches"] = int(batches)
        scaled.append(scaled_item)
    return scaled
