"""
Computes a full pricing summary for a single product variant unit.
Depends on recipe_calculator for cost data; applies selling price on top.
"""
from dataclasses import dataclass
from decimal import Decimal

from app.calculators.cost_engine import (
    gross_profit,
    net_profit,
    food_cost_percent,
    margin_percent,
    recommended_price,
)
from app.calculators.margin_engine import classify_quote, margin_warnings
from app.core.money import q_money, q_cost


@dataclass
class VariantPricingResult:
    ingredient_cost: Decimal
    packaging_cost: Decimal
    labour_cost: Decimal
    total_cost_excluding_labour: Decimal
    total_cost_including_labour: Decimal
    current_selling_price: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    food_cost_percent: Decimal
    gross_margin_percent: Decimal
    net_margin_percent: Decimal
    recommended_price: Decimal
    recommended_prices: dict[str, Decimal]
    margin_status: str
    warnings: list[str]


def compute_variant_pricing(
    ingredient_cost_per_item: Decimal,
    packaging_cost_per_item: Decimal,
    labour_cost_per_item: Decimal,
    quantity_multiplier: Decimal,
    selling_price: Decimal,
    desired_margin_pct: Decimal,
) -> VariantPricingResult:
    """
    ingredient_cost_per_item / packaging_cost_per_item / labour_cost_per_item:
        costs for a single yield unit from the recipe
    quantity_multiplier:
        how many yield units make one sellable variant unit
    selling_price:
        what the baker charges for one variant unit
    """
    # Scale per-item costs to per-variant costs
    ing_cost = q_money(ingredient_cost_per_item * quantity_multiplier)
    pkg_cost = q_money(packaging_cost_per_item * quantity_multiplier)
    lab_cost = q_money(labour_cost_per_item * quantity_multiplier)

    cost_excl = q_money(ing_cost + pkg_cost)
    cost_incl = q_money(cost_excl + lab_cost)

    gp = gross_profit(selling_price, cost_excl)
    np = net_profit(selling_price, cost_incl)
    fcp = food_cost_percent(ing_cost, selling_price)
    gmp = margin_percent(gp, selling_price)
    nmp = margin_percent(np, selling_price)

    rec_price = _safe_recommended_price(cost_incl, desired_margin_pct)

    rec_prices = {}
    for m in [50, 55, 60, 65, 70]:
        rec_prices[f"{m}_pct"] = _safe_recommended_price(cost_incl, Decimal(str(m)))

    status = classify_quote(np, nmp, fcp, desired_margin_pct)
    warns = margin_warnings(np, nmp, fcp, desired_margin_pct)

    return VariantPricingResult(
        ingredient_cost=ing_cost,
        packaging_cost=pkg_cost,
        labour_cost=lab_cost,
        total_cost_excluding_labour=cost_excl,
        total_cost_including_labour=cost_incl,
        current_selling_price=selling_price,
        gross_profit=gp,
        net_profit=np,
        food_cost_percent=fcp,
        gross_margin_percent=gmp,
        net_margin_percent=nmp,
        recommended_price=rec_price,
        recommended_prices=rec_prices,
        margin_status=status,
        warnings=warns,
    )


def _safe_recommended_price(cost: Decimal, margin_pct: Decimal) -> Decimal:
    try:
        return recommended_price(cost, margin_pct)
    except ValueError:
        return Decimal("0")
