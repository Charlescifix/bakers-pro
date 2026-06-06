"""
Quote calculator tests using Bold Munch reference data (spec §13.3).
Pure unit tests — no database, no HTTP.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

import pytest

from app.calculators.cost_engine import unit_cost
from app.calculators.quote_calculator import (
    QuoteLineInput,
    compute_quote,
    generate_customer_message,
)
from app.core.units import convert_to_base


# ── Fakes (mirror the recipe_calculator test pattern) ─────────────────────────

@dataclass
class FakeIngredient:
    id: str
    name: str
    current_unit_cost_base: Decimal
    waste_percent_default: Decimal = Decimal("0")


@dataclass
class FakeRecipeItem:
    ingredient_id: str
    quantity_used: Decimal
    unit_code: str
    waste_percent_override: Optional[Decimal] = None
    is_optional: bool = False
    variant_group: Optional[str] = None
    preparation_note: Optional[str] = None


@dataclass
class FakeVersion:
    id: str
    version_number: int = 1
    items: list = field(default_factory=list)


@dataclass
class FakeRecipe:
    id: str
    name: str
    base_yield_quantity: Decimal
    base_yield_unit: str
    labour_minutes_default: int
    packaging_rules: list = field(default_factory=list)


@dataclass
class FakeChannel:
    name: str
    percentage_fee: Decimal = Decimal("0")
    fixed_fee_per_order: Decimal = Decimal("0")
    fixed_fee_per_item: Decimal = Decimal("0")
    payment_processing_percent: Decimal = Decimal("0")
    payment_processing_fixed: Decimal = Decimal("0")


# ── Pre-computed ingredient costs ─────────────────────────────────────────────

FLOUR_UC = unit_cost(Decimal("0.78"), convert_to_base(Decimal("1500"), "g"))
SUGAR_UC = unit_cost(Decimal("0.99"), convert_to_base(Decimal("1000"), "g"))
YEAST_UC = unit_cost(Decimal("1.20"), convert_to_base(Decimal("7"), "g"))
MEAT_UC  = unit_cost(Decimal("5.00"), convert_to_base(Decimal("500"), "g"))
BUTTER_UC= unit_cost(Decimal("2.50"), convert_to_base(Decimal("1000"), "g"))
BANANA_UC= unit_cost(Decimal("1.00"), convert_to_base(Decimal("4"), "piece"))


# ── Recipe factories ───────────────────────────────────────────────────────────

def _puff_puff():
    ings = {
        "flour": FakeIngredient("flour", "Flour", FLOUR_UC),
        "sugar": FakeIngredient("sugar", "White Sugar", SUGAR_UC),
        "yeast": FakeIngredient("yeast", "Yeast", YEAST_UC),
    }
    items = [
        FakeRecipeItem("flour", Decimal("430"), "g"),
        FakeRecipeItem("sugar", Decimal("175"), "g"),
        FakeRecipeItem("yeast", Decimal("7"),   "g"),
    ]
    version = FakeVersion("ver-pp", items=items)
    recipe  = FakeRecipe("r-pp", "Puff Puff", Decimal("30"), "item", 30)
    return recipe, version, ings


def _meat_pie():
    ings = {
        "flour": FakeIngredient("flour", "Flour", FLOUR_UC),
        "meat":  FakeIngredient("meat",  "Minced Meat", MEAT_UC),
        "butter":FakeIngredient("butter","Butter", BUTTER_UC),
    }
    items = [
        FakeRecipeItem("flour",  Decimal("300"), "g"),
        FakeRecipeItem("meat",   Decimal("400"), "g"),
        FakeRecipeItem("butter", Decimal("100"), "g"),
    ]
    version = FakeVersion("ver-mp", items=items)
    recipe  = FakeRecipe("r-mp", "Small Meat Pie", Decimal("20"), "item", 45)
    return recipe, version, ings


def _mini_banana_bread():
    ings = {
        "flour":  FakeIngredient("flour",  "Flour",   FLOUR_UC),
        "butter": FakeIngredient("butter", "Butter",  BUTTER_UC),
        "banana": FakeIngredient("banana", "Bananas", BANANA_UC),
    }
    items = [
        FakeRecipeItem("flour",  Decimal("280"), "g"),
        FakeRecipeItem("butter", Decimal("120"), "g"),
        FakeRecipeItem("banana", Decimal("4"),   "piece"),
    ]
    version = FakeVersion("ver-mb", items=items)
    recipe  = FakeRecipe("r-mb", "Mini Banana Bread", Decimal("8"), "item", 40)
    return recipe, version, ings


def _make_input(recipe, version, ings, variant_id, variant_name, product_name,
                quantity, multiplier="1", desired_margin="55",
                price_override=None, hourly_rate="10"):
    return QuoteLineInput(
        variant_id=variant_id,
        variant_name=variant_name,
        product_name=product_name,
        quantity=quantity,
        quantity_multiplier=Decimal(multiplier),
        desired_margin_percent=Decimal(desired_margin),
        unit_price_override=Decimal(price_override) if price_override else None,
        recipe=recipe,
        recipe_version=version,
        ingredient_map=ings,
        packaging_map={},
        hourly_rate=Decimal(hourly_rate),
    )


# ── Single-line quote tests ────────────────────────────────────────────────────

def test_single_line_recommended_price_covers_cost():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30)
    result = compute_quote([inp])
    assert result.total_revenue > Decimal("0")
    assert result.net_profit >= Decimal("0")


def test_recommended_price_respects_desired_margin():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, desired_margin="60")
    result = compute_quote([inp])
    # At recommended price, net margin should be close to 60%
    assert result.profit_margin_percent >= Decimal("55")   # allow small rounding


def test_unit_price_override_is_respected():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=10, price_override="0.50")
    result = compute_quote([inp])
    assert result.lines[0].unit_price == Decimal("0.50")
    assert result.lines[0].manual_price_override is True


def test_total_revenue_is_unit_price_times_quantity():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, price_override="1.00")
    result = compute_quote([inp])
    assert result.total_revenue == Decimal("30.00")


# ── Multi-line quote (spec §13.3 scenario) ───────────────────────────────────

def test_multi_line_quote_three_products():
    r_mp, v_mp, i_mp = _meat_pie()
    r_mb, v_mb, i_mb = _mini_banana_bread()
    r_pp, v_pp, i_pp = _puff_puff()

    inputs = [
        _make_input(r_mp, v_mp, i_mp, "v-mp", "Small Meat Pie",     "Meat Pie",         quantity=50),
        _make_input(r_mb, v_mb, i_mb, "v-mb", "Mini Banana Bread",  "Mini Banana Bread",quantity=12),
        _make_input(r_pp, v_pp, i_pp, "v-pp", "Puff Puff",          "Puff Puff",        quantity=30),
    ]
    result = compute_quote(inputs, desired_margin_percent=Decimal("55"))

    assert len(result.lines) == 3
    assert result.total_revenue > Decimal("0")
    assert result.recommended_total_price > Decimal("0")
    assert result.total_cost_excluding_labour > Decimal("0")


def test_multi_line_totals_sum_of_lines():
    r_mp, v_mp, i_mp = _meat_pie()
    r_pp, v_pp, i_pp = _puff_puff()

    inputs = [
        _make_input(r_mp, v_mp, i_mp, "v1", "Meat Pie",   "Meat Pie",   quantity=20, price_override="2.50"),
        _make_input(r_pp, v_pp, i_pp, "v2", "Puff Puff",  "Puff Puff",  quantity=30, price_override="0.80"),
    ]
    result = compute_quote(inputs)

    expected_rev = Decimal("20") * Decimal("2.50") + Decimal("30") * Decimal("0.80")
    assert result.total_revenue == expected_rev


def test_ingredient_totals_aggregate_across_lines():
    r_pp, v_pp, i_pp = _puff_puff()
    r_mp, v_mp, i_mp = _meat_pie()
    # Both use flour — shopping list should combine
    inputs = [
        _make_input(r_pp, v_pp, i_pp, "v1", "Puff Puff", "Puff Puff", quantity=30),
        _make_input(r_mp, v_mp, i_mp, "v2", "Meat Pie",  "Meat Pie",  quantity=20),
    ]
    result = compute_quote(inputs)
    flour_lines = [s for s in result.shopping_list_preview if s.ingredient_name == "Flour"]
    assert len(flour_lines) == 1
    assert flour_lines[0].required_quantity > Decimal("0")


# ── Channel fee tests ──────────────────────────────────────────────────────────

def test_tiktok_fee_reduces_net_profit():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, price_override="1.50")

    no_channel = compute_quote([inp])
    tiktok = FakeChannel("TikTok Shop", percentage_fee=Decimal("12.2"))
    with_tiktok = compute_quote([inp], channel=tiktok)

    assert with_tiktok.net_profit < no_channel.net_profit
    assert with_tiktok.total_channel_fees > Decimal("0")


def test_channel_fee_in_recommended_price_preserves_margin():
    r, v, i = _puff_puff()
    channel = FakeChannel("TikTok Shop", percentage_fee=Decimal("12.2"))
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, desired_margin="55")
    result = compute_quote([inp], channel=channel, desired_margin_percent=Decimal("55"))
    # When using recommended price, margin should still be meaningful
    assert result.profit_margin_percent > Decimal("20")


def test_channel_warning_in_results():
    r, v, i = _puff_puff()
    channel = FakeChannel("TikTok Shop", percentage_fee=Decimal("12.2"))
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, price_override="1.00")
    result = compute_quote([inp], channel=channel)
    assert any("TikTok" in w for w in result.warnings)


# ── Delivery fee and discount ──────────────────────────────────────────────────

def test_delivery_fee_added_to_revenue():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, price_override="1.00")
    base = compute_quote([inp])
    with_delivery = compute_quote([inp], delivery_fee_charged=Decimal("5.00"))
    assert with_delivery.total_revenue == base.total_revenue + Decimal("5.00")


def test_discount_reduces_revenue():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, price_override="1.00")
    base = compute_quote([inp])
    discounted = compute_quote([inp], discount_amount=Decimal("3.00"))
    assert discounted.total_revenue == base.total_revenue - Decimal("3.00")


# ── Batch scaling in shopping list ────────────────────────────────────────────

def test_batches_required_in_line_result():
    r, v, i = _puff_puff()
    # 90 puff puff, recipe yields 30 → 3 batches
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=90)
    result = compute_quote([inp])
    assert result.lines[0].batches_required == 3


def test_shopping_list_scales_with_batches():
    r, v, i = _puff_puff()
    one_batch = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30)
    three_batches = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=90)

    r1 = compute_quote([one_batch])
    r3 = compute_quote([three_batches])

    flour_1 = next(s for s in r1.shopping_list_preview if "Flour" in s.ingredient_name)
    flour_3 = next(s for s in r3.shopping_list_preview if "Flour" in s.ingredient_name)
    assert flour_3.required_quantity == flour_1.required_quantity * 3


# ── Loss-making detection ──────────────────────────────────────────────────────

def test_loss_making_quote_detected():
    r, v, i = _puff_puff()
    # Price of 0.01 per puff puff will be below cost
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, price_override="0.01")
    result = compute_quote([inp])
    assert result.recommendation_status == "loss_making"
    assert result.net_profit < Decimal("0")
    assert any("loss" in w.lower() for w in result.warnings)


# ── Customer message generator ────────────────────────────────────────────────

def test_message_contains_item_names():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=30, price_override="1.00")
    result = compute_quote([inp])
    msg = generate_customer_message(result.lines, result.total_revenue, "local_delivery", "Sarah")
    assert "Sarah" in msg
    assert "Puff Puff" in msg
    assert "30" in msg
    assert "£" in msg


def test_message_pickup_vs_delivery_wording():
    r, v, i = _puff_puff()
    inp = _make_input(r, v, i, "v1", "Puff Puff", "Puff Puff", quantity=10, price_override="1.00")
    result = compute_quote([inp])
    pickup_msg   = generate_customer_message(result.lines, result.total_revenue, "pickup")
    delivery_msg = generate_customer_message(result.lines, result.total_revenue, "local_delivery")
    assert "collected" in pickup_msg
    assert "delivered" in delivery_msg


def test_message_multi_item_format():
    r_pp, v_pp, i_pp = _puff_puff()
    r_mp, v_mp, i_mp = _meat_pie()
    inputs = [
        _make_input(r_pp, v_pp, i_pp, "v1", "Puff Puff", "Puff Puff", quantity=30, price_override="1.00"),
        _make_input(r_mp, v_mp, i_mp, "v2", "Small Meat Pie", "Meat Pie", quantity=20, price_override="2.00"),
    ]
    result = compute_quote(inputs)
    msg = generate_customer_message(result.lines, result.total_revenue, "pickup")
    assert "Puff Puff" in msg
    assert "Small Meat Pie" in msg
