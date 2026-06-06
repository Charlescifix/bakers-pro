"""
Quote calculator — pure, deterministic, no database.
Receives pre-loaded data objects and returns a QuoteResult.
All money in Decimal. AI never touches these numbers.
"""
from dataclasses import dataclass, field
from decimal import Decimal

from app.calculators.batch_scaler import batches_required
from app.calculators.cost_engine import (
    channel_fee as calc_channel_fee,
    gross_profit,
    margin_percent,
    net_profit,
    food_cost_percent,
    recommended_price,
)
from app.calculators.margin_engine import classify_quote, margin_warnings
from app.calculators.recipe_calculator import compute_recipe_cost
from app.core.money import q_money, q_cost, q_percent


@dataclass
class QuoteLineInput:
    variant_id: str
    variant_name: str
    product_name: str
    quantity: int
    quantity_multiplier: Decimal       # items per recipe yield unit this variant represents
    desired_margin_percent: Decimal
    unit_price_override: Decimal | None  # None = use recommended
    recipe: object | None              # Recipe ORM / fake
    recipe_version: object | None      # RecipeVersion ORM / fake
    ingredient_map: dict               # {id_str: ingredient_obj}
    packaging_map: dict                # {id_str: packaging_obj}
    hourly_rate: Decimal


@dataclass
class QuoteLineResult:
    variant_id: str
    variant_name: str
    product_name: str
    quantity: int
    recommended_unit_price: Decimal
    unit_price: Decimal
    manual_price_override: bool
    line_revenue: Decimal
    line_ingredient_cost: Decimal
    line_packaging_cost: Decimal
    line_labour_cost: Decimal
    line_channel_fee: Decimal
    line_overhead_cost: Decimal = Decimal("0")
    line_net_profit: Decimal = Decimal("0")
    line_margin_percent: Decimal = Decimal("0")
    # For shopping list
    batches_required: int = 0
    base_yield_quantity: Decimal = Decimal("1")


@dataclass
class ShoppingLinePreview:
    ingredient_id: str
    ingredient_name: str
    required_quantity: Decimal
    unit_code: str


@dataclass
class QuoteResult:
    lines: list[QuoteLineResult]
    total_revenue: Decimal
    total_cost_excluding_labour: Decimal
    total_labour_cost: Decimal
    total_channel_fees: Decimal
    total_ingredient_cost: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    food_cost_percent: Decimal
    profit_margin_percent: Decimal
    recommended_total_price: Decimal
    recommendation_status: str
    warnings: list[str]
    shopping_list_preview: list[ShoppingLinePreview]


def compute_quote(
    line_inputs: list[QuoteLineInput],
    channel=None,         # SalesChannel ORM / fake (optional)
    desired_margin_percent: Decimal = Decimal("60"),
    delivery_fee_charged: Decimal = Decimal("0"),
    delivery_cost_estimate: Decimal = Decimal("0"),
    discount_amount: Decimal = Decimal("0"),
) -> QuoteResult:

    lines: list[QuoteLineResult] = []
    ingredient_totals: dict[str, dict] = {}  # id_str -> {name, qty, unit}

    for inp in line_inputs:
        if inp.recipe is None or inp.recipe_version is None:
            # No recipe — use override price only, zero costs
            unit_price = inp.unit_price_override or Decimal("0")
            rev = q_money(unit_price * inp.quantity)
            lines.append(QuoteLineResult(
                variant_id=inp.variant_id,
                variant_name=inp.variant_name,
                product_name=inp.product_name,
                quantity=inp.quantity,
                recommended_unit_price=Decimal("0"),
                unit_price=unit_price,
                manual_price_override=True,
                line_revenue=rev,
                line_ingredient_cost=Decimal("0"),
                line_packaging_cost=Decimal("0"),
                line_labour_cost=Decimal("0"),
                line_channel_fee=Decimal("0"),
            ))
            continue

        recipe_cost = compute_recipe_cost(
            inp.recipe, inp.recipe_version,
            inp.ingredient_map, inp.packaging_map,
            inp.hourly_rate,
        )
        yield_qty = inp.recipe.base_yield_quantity

        # Per-variant-unit costs (one sellable unit)
        mul = inp.quantity_multiplier
        ing_per_unit  = q_cost(recipe_cost.total_ingredient_cost / yield_qty * mul)
        pkg_per_unit  = q_cost(recipe_cost.total_packaging_cost  / yield_qty * mul)
        lab_per_unit  = q_cost(recipe_cost.total_labour_cost     / yield_qty * mul)
        cost_per_unit = q_money(ing_per_unit + pkg_per_unit + lab_per_unit)

        # Recommended price before channel fees (fees applied to final price below)
        rec_price_base = _safe_rec_price(cost_per_unit, inp.desired_margin_percent)

        # Channel fee on one unit at recommended price
        unit_channel_fee = _unit_channel_fee(channel, rec_price_base, Decimal("1"))
        # Absorb fee into recommended price so margin holds after fees
        rec_price_with_fee = _safe_rec_price(
            cost_per_unit,
            inp.desired_margin_percent,
            fee_pct=(channel.percentage_fee + channel.payment_processing_percent) if channel else Decimal("0"),
            fixed_fee=((channel.fixed_fee_per_item or Decimal("0")) + (channel.payment_processing_fixed or Decimal("0"))) if channel else Decimal("0"),
        )

        unit_price = inp.unit_price_override if inp.unit_price_override is not None else rec_price_with_fee
        is_override = inp.unit_price_override is not None

        qty = Decimal(str(inp.quantity))

        # Line-level channel fee based on actual unit price
        line_ch_fee = _unit_channel_fee(channel, unit_price, qty)

        line_rev  = q_money(unit_price * qty)
        line_ing  = q_money(ing_per_unit * qty)
        line_pkg  = q_money(pkg_per_unit * qty)
        line_lab  = q_money(lab_per_unit * qty)
        line_cost = q_money(line_ing + line_pkg + line_lab + line_ch_fee)
        line_np   = q_money(line_rev - line_cost)
        line_mp   = margin_percent(line_np, line_rev)

        n_batches = batches_required(qty * mul, yield_qty)

        # Accumulate shopping list
        for item in inp.recipe_version.items:
            iid = str(item.ingredient_id)
            ing = inp.ingredient_map.get(iid)
            if ing is None:
                continue
            required = item.quantity_used * Decimal(str(n_batches))
            if iid in ingredient_totals:
                ingredient_totals[iid]["quantity"] += required
            else:
                ingredient_totals[iid] = {
                    "name": ing.name,
                    "quantity": required,
                    "unit_code": item.unit_code,
                }

        lines.append(QuoteLineResult(
            variant_id=inp.variant_id,
            variant_name=inp.variant_name,
            product_name=inp.product_name,
            quantity=inp.quantity,
            recommended_unit_price=rec_price_with_fee,
            unit_price=unit_price,
            manual_price_override=is_override,
            line_revenue=line_rev,
            line_ingredient_cost=line_ing,
            line_packaging_cost=line_pkg,
            line_labour_cost=line_lab,
            line_channel_fee=line_ch_fee,
            line_net_profit=line_np,
            line_margin_percent=line_mp,
            batches_required=n_batches,
            base_yield_quantity=yield_qty,
        ))

    # Quote totals
    total_rev     = q_money(sum((l.line_revenue          for l in lines), Decimal("0")) + delivery_fee_charged - discount_amount)
    total_ing     = q_money(sum((l.line_ingredient_cost  for l in lines), Decimal("0")))
    total_pkg     = q_money(sum((l.line_packaging_cost   for l in lines), Decimal("0")))
    total_lab     = q_money(sum((l.line_labour_cost      for l in lines), Decimal("0")))
    total_ch_fees = q_money(sum((l.line_channel_fee      for l in lines), Decimal("0")))
    total_cost_excl = q_money(total_ing + total_pkg)
    true_cost    = q_money(total_cost_excl + total_lab + total_ch_fees + delivery_cost_estimate)

    gp = gross_profit(total_rev, total_cost_excl)
    np = net_profit(total_rev, true_cost)
    fcp = food_cost_percent(total_ing, total_rev) if total_rev > 0 else Decimal("0")
    mp  = margin_percent(np, total_rev)

    recommended_total = q_money(sum((l.recommended_unit_price * l.quantity for l in lines), Decimal("0")) + delivery_fee_charged)

    status = classify_quote(np, mp, fcp, desired_margin_percent)
    warns  = margin_warnings(np, mp, fcp, desired_margin_percent,
                             channel_fees=total_ch_fees,
                             channel_name=channel.name if channel else None)

    shopping = [
        ShoppingLinePreview(
            ingredient_id=iid,
            ingredient_name=v["name"],
            required_quantity=v["quantity"],
            unit_code=v["unit_code"],
        )
        for iid, v in ingredient_totals.items()
    ]

    return QuoteResult(
        lines=lines,
        total_revenue=total_rev,
        total_cost_excluding_labour=total_cost_excl,
        total_labour_cost=total_lab,
        total_channel_fees=total_ch_fees,
        total_ingredient_cost=total_ing,
        gross_profit=gp,
        net_profit=np,
        food_cost_percent=fcp,
        profit_margin_percent=mp,
        recommended_total_price=recommended_total,
        recommendation_status=status,
        warnings=warns,
        shopping_list_preview=shopping,
    )


def generate_customer_message(lines: list[QuoteLineResult], total_price: Decimal, delivery_method: str, customer_name: str | None = None) -> str:
    greeting = f"Hi {customer_name}! " if customer_name else "Hi! "
    items_str = _format_items(lines)
    delivery_note = "collected" if delivery_method == "pickup" else "delivered"
    return (
        f"{greeting}Thanks for your enquiry. "
        f"For {items_str}, the quote is £{total_price:.2f}. "
        f"This includes fresh preparation, packaging, and everything ready to be {delivery_note}. "
        f"Please confirm to secure your order. Looking forward to baking for you! 🎉"
    )


def _format_items(lines: list[QuoteLineResult]) -> str:
    parts = [f"{l.quantity} {l.variant_name}" for l in lines]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _safe_rec_price(cost: Decimal, margin_pct: Decimal, fee_pct: Decimal = Decimal("0"), fixed_fee: Decimal = Decimal("0")) -> Decimal:
    try:
        return recommended_price(cost, margin_pct, fee_percent=fee_pct, fixed_fee=fixed_fee)
    except ValueError:
        return cost  # fallback: at least cover costs


def _unit_channel_fee(channel, unit_price: Decimal, quantity: Decimal) -> Decimal:
    if channel is None:
        return Decimal("0")
    rev = unit_price * quantity
    return calc_channel_fee(
        rev,
        pct_fee=channel.percentage_fee,
        fixed_per_order=channel.fixed_fee_per_order if quantity > 0 else Decimal("0"),
        fixed_per_item=channel.fixed_fee_per_item,
        quantity=quantity,
        payment_pct=channel.payment_processing_percent,
        payment_fixed=channel.payment_processing_fixed,
    )
