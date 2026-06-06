"""
Computes the full cost breakdown for a recipe version.
All money values use Decimal — never float.
"""
from dataclasses import dataclass, field
from decimal import Decimal

from app.calculators.batch_scaler import batches_required, scale_recipe
from app.calculators.cost_engine import (
    ingredient_line_cost,
    labour_cost,
    recommended_price,
    cost_per_item,
    packaging_cost as calc_packaging_cost,
)
from app.core.money import q_money, q_cost
from app.core.units import convert_to_base


@dataclass
class IngredientLineResult:
    ingredient_id: str
    ingredient_name: str
    quantity_used: Decimal
    unit_code: Decimal
    quantity_in_base: Decimal
    unit_cost_base: Decimal
    waste_percent: Decimal
    line_cost: Decimal


@dataclass
class PackagingLineResult:
    packaging_item_id: str
    packaging_item_name: str
    rule_type: str
    quantity: Decimal
    unit_cost: Decimal
    line_cost: Decimal


@dataclass
class RecipeCostResult:
    recipe_id: str
    recipe_name: str
    version_id: str
    version_number: int
    base_yield_quantity: Decimal
    base_yield_unit: str
    ingredient_lines: list[IngredientLineResult]
    packaging_lines: list[PackagingLineResult]
    total_ingredient_cost: Decimal
    total_packaging_cost: Decimal
    labour_minutes: int
    hourly_rate: Decimal
    total_labour_cost: Decimal
    total_cost_excluding_labour: Decimal
    total_cost_including_labour: Decimal
    cost_per_item_excl_labour: Decimal
    cost_per_item_incl_labour: Decimal
    recommended_prices: dict[str, Decimal] = field(default_factory=dict)


def compute_recipe_cost(
    recipe,
    version,
    ingredient_map: dict,     # ingredient_id -> Ingredient ORM obj
    packaging_map: dict,      # packaging_item_id -> PackagingItem ORM obj
    hourly_rate: Decimal,
    labour_minutes_override: int | None = None,
) -> RecipeCostResult:
    """
    ingredient_map: {uuid_str: ingredient_obj}
    packaging_map: {uuid_str: packaging_item_obj}
    """
    ingredient_lines: list[IngredientLineResult] = []
    for item in version.items:
        ing = ingredient_map.get(str(item.ingredient_id))
        if ing is None:
            continue
        waste_pct = (
            item.waste_percent_override
            if item.waste_percent_override is not None
            else ing.waste_percent_default
        )
        qty_base = convert_to_base(item.quantity_used, item.unit_code)
        line = ingredient_line_cost(qty_base, ing.current_unit_cost_base, waste_pct)
        ingredient_lines.append(
            IngredientLineResult(
                ingredient_id=str(item.ingredient_id),
                ingredient_name=ing.name,
                quantity_used=item.quantity_used,
                unit_code=item.unit_code,
                quantity_in_base=q_cost(qty_base),
                unit_cost_base=ing.current_unit_cost_base,
                waste_percent=waste_pct,
                line_cost=line,
            )
        )

    total_ingredient_cost = q_money(sum((l.line_cost for l in ingredient_lines), Decimal("0")))

    # Packaging cost — per_item rules × yield; per_batch × 1
    packaging_lines: list[PackagingLineResult] = []
    yield_qty = recipe.base_yield_quantity
    for rule in recipe.packaging_rules:
        pkg = packaging_map.get(str(rule.packaging_item_id))
        if pkg is None:
            continue
        if rule.rule_type == "per_item":
            qty = (rule.quantity_per_item or Decimal("1")) * yield_qty
        elif rule.rule_type == "per_batch":
            qty = rule.quantity_per_batch or Decimal("1")
        else:  # per_order — treat as per_batch for recipe costing
            qty = rule.quantity_per_batch or Decimal("1")
        line_cost = q_money(qty * pkg.unit_cost)
        packaging_lines.append(
            PackagingLineResult(
                packaging_item_id=str(rule.packaging_item_id),
                packaging_item_name=pkg.name,
                rule_type=rule.rule_type,
                quantity=qty,
                unit_cost=pkg.unit_cost,
                line_cost=line_cost,
            )
        )

    total_packaging_cost = q_money(sum((l.line_cost for l in packaging_lines), Decimal("0")))

    labour_mins = labour_minutes_override if labour_minutes_override is not None else recipe.labour_minutes_default
    lab_cost = labour_cost(hourly_rate, Decimal(str(labour_mins)))

    total_excl = q_money(total_ingredient_cost + total_packaging_cost)
    total_incl = q_money(total_excl + lab_cost)

    yield_qty_d = recipe.base_yield_quantity
    cpi_excl = cost_per_item(total_excl, yield_qty_d) if yield_qty_d > 0 else Decimal("0")
    cpi_incl = cost_per_item(total_incl, yield_qty_d) if yield_qty_d > 0 else Decimal("0")

    rec_prices = {}
    for margin in [50, 55, 60, 65, 70]:
        try:
            rec_prices[f"{margin}_pct"] = recommended_price(cpi_incl, Decimal(str(margin)))
        except ValueError:
            pass

    return RecipeCostResult(
        recipe_id=str(recipe.id),
        recipe_name=recipe.name,
        version_id=str(version.id),
        version_number=version.version_number,
        base_yield_quantity=yield_qty_d,
        base_yield_unit=recipe.base_yield_unit,
        ingredient_lines=ingredient_lines,
        packaging_lines=packaging_lines,
        total_ingredient_cost=total_ingredient_cost,
        total_packaging_cost=total_packaging_cost,
        labour_minutes=labour_mins,
        hourly_rate=hourly_rate,
        total_labour_cost=lab_cost,
        total_cost_excluding_labour=total_excl,
        total_cost_including_labour=total_incl,
        cost_per_item_excl_labour=cpi_excl,
        cost_per_item_incl_labour=cpi_incl,
        recommended_prices=rec_prices,
    )


def scale_recipe_cost(
    recipe,
    version,
    ingredient_map: dict,
    packaging_map: dict,
    hourly_rate: Decimal,
    order_quantity: Decimal,
) -> dict:
    """Returns scaled ingredients, batch count, and scaled costs."""
    base_yield = recipe.base_yield_quantity
    n_batches = batches_required(order_quantity, base_yield)

    raw_items = [
        {
            "ingredient_id": str(item.ingredient_id),
            "ingredient_name": ingredient_map.get(str(item.ingredient_id), None),
            "quantity": item.quantity_used,
            "unit_code": item.unit_code,
        }
        for item in version.items
    ]
    scaled = scale_recipe(raw_items, base_yield, order_quantity)

    # Resolve ingredient names
    for s in scaled:
        ing = ingredient_map.get(s["ingredient_id"])
        s["ingredient_name"] = ing.name if ing else "Unknown"
        del s["ingredient_id"]

    base_cost = compute_recipe_cost(recipe, version, ingredient_map, packaging_map, hourly_rate)
    total_cost_excl = q_money(base_cost.total_cost_excluding_labour * Decimal(str(n_batches)))
    total_cost_incl = q_money(base_cost.total_cost_including_labour * Decimal(str(n_batches)))

    return {
        "order_quantity": order_quantity,
        "base_yield_quantity": base_yield,
        "batches_required": n_batches,
        "scaled_ingredients": scaled,
        "total_cost_excluding_labour": total_cost_excl,
        "total_cost_including_labour": total_cost_incl,
        "cost_per_item_excl_labour": cost_per_item(total_cost_excl, order_quantity),
        "cost_per_item_incl_labour": cost_per_item(total_cost_incl, order_quantity),
    }
