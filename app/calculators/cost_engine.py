from decimal import Decimal

from app.core.money import q_money, q_cost, q_percent, MONEY_PLACES
from app.core.units import convert_to_base


def unit_cost(purchase_price: Decimal, purchase_quantity_base: Decimal) -> Decimal:
    if purchase_quantity_base <= 0:
        raise ValueError("purchase_quantity must be greater than zero")
    return q_cost(purchase_price / purchase_quantity_base)


def ingredient_line_cost(
    quantity_used: Decimal,
    item_unit_cost: Decimal,
    waste_percent: Decimal = Decimal("0"),
) -> Decimal:
    waste_multiplier = Decimal("1") + (waste_percent / Decimal("100"))
    return q_cost(quantity_used * item_unit_cost * waste_multiplier)


def packaging_cost(items: list[tuple[Decimal, Decimal]]) -> Decimal:
    """items: list of (quantity_used, unit_cost)"""
    return q_money(sum(qty * cost for qty, cost in items))


def labour_cost(hourly_rate: Decimal, minutes: Decimal) -> Decimal:
    return q_money(hourly_rate * (minutes / Decimal("60")))


def overhead_cost(
    energy: Decimal = Decimal("0"),
    water: Decimal = Decimal("0"),
    transport: Decimal = Decimal("0"),
    shipping: Decimal = Decimal("0"),
    rent_allocation: Decimal = Decimal("0"),
    misc: Decimal = Decimal("0"),
) -> Decimal:
    return q_money(energy + water + transport + shipping + rent_allocation + misc)


def product_cost_excluding_labour(
    ingredient_cost: Decimal,
    pack_cost: Decimal,
    direct_overhead: Decimal,
) -> Decimal:
    return q_money(ingredient_cost + pack_cost + direct_overhead)


def true_cost(
    ingredient_cost: Decimal,
    pack_cost: Decimal,
    overhead: Decimal,
    lab_cost: Decimal,
    channel_fees: Decimal,
    delivery_cost: Decimal = Decimal("0"),
) -> Decimal:
    return q_money(ingredient_cost + pack_cost + overhead + lab_cost + channel_fees + delivery_cost)


def cost_per_item(total_cost: Decimal, quantity: Decimal) -> Decimal:
    if quantity <= 0:
        raise ValueError("quantity must be greater than zero")
    return q_cost(total_cost / quantity)


def revenue(selling_price: Decimal, quantity: Decimal) -> Decimal:
    return q_money(selling_price * quantity)


def gross_profit(rev: Decimal, cost_excl_labour: Decimal) -> Decimal:
    return q_money(rev - cost_excl_labour)


def net_profit(rev: Decimal, total_cost: Decimal) -> Decimal:
    return q_money(rev - total_cost)


def food_cost_percent(ingredient_cost_per_item: Decimal, selling_price: Decimal) -> Decimal:
    if selling_price <= 0:
        return Decimal("0")
    return q_percent((ingredient_cost_per_item / selling_price) * Decimal("100"))


def margin_percent(profit: Decimal, rev: Decimal) -> Decimal:
    if rev <= 0:
        return Decimal("0")
    return q_percent((profit / rev) * Decimal("100"))


def recommended_price(
    unit_cost_val: Decimal,
    desired_margin_percent: Decimal,
    fee_percent: Decimal = Decimal("0"),
    fixed_fee: Decimal = Decimal("0"),
) -> Decimal:
    margin = desired_margin_percent / Decimal("100")
    fee = fee_percent / Decimal("100")
    denominator = Decimal("1") - margin - fee
    if denominator <= 0:
        raise ValueError("desired margin plus fee percent must be less than 100%")
    return q_money((unit_cost_val + fixed_fee) / denominator)


def channel_fee(
    rev: Decimal,
    pct_fee: Decimal = Decimal("0"),
    fixed_per_order: Decimal = Decimal("0"),
    fixed_per_item: Decimal = Decimal("0"),
    quantity: Decimal = Decimal("1"),
    payment_pct: Decimal = Decimal("0"),
    payment_fixed: Decimal = Decimal("0"),
) -> Decimal:
    total = (
        rev * (pct_fee / Decimal("100"))
        + fixed_per_order
        + fixed_per_item * quantity
        + rev * (payment_pct / Decimal("100"))
        + payment_fixed
    )
    return q_money(total)
