"""
Price engine tests covering the full pricing summary for product variants.
All values use Decimal; no database needed.
"""
from decimal import Decimal

import pytest

from app.calculators.price_engine import compute_variant_pricing


# ── helpers ────────────────────────────────────────────────────────────────────

def _price(
    ing: str,
    pkg: str = "0",
    lab: str = "0",
    multiplier: str = "1",
    selling: str = "0",
    desired_margin: str = "60",
):
    return compute_variant_pricing(
        ingredient_cost_per_item=Decimal(ing),
        packaging_cost_per_item=Decimal(pkg),
        labour_cost_per_item=Decimal(lab),
        quantity_multiplier=Decimal(multiplier),
        selling_price=Decimal(selling),
        desired_margin_pct=Decimal(desired_margin),
    )


# ── cost scaling by quantity_multiplier ───────────────────────────────────────

def test_costs_scale_with_multiplier():
    single = _price(ing="1.00", lab="0.50", multiplier="1")
    box_of_8 = _price(ing="1.00", lab="0.50", multiplier="8")
    assert box_of_8.ingredient_cost == Decimal("8.00")
    assert box_of_8.labour_cost == Decimal("4.00")


def test_multiplier_one_leaves_costs_unchanged():
    result = _price(ing="2.50", pkg="0.30", lab="1.00", multiplier="1")
    assert result.ingredient_cost == Decimal("2.50")
    assert result.packaging_cost == Decimal("0.30")
    assert result.labour_cost == Decimal("1.00")


# ── cost totals ────────────────────────────────────────────────────────────────

def test_total_cost_excl_labour_is_ingredients_plus_packaging():
    result = _price(ing="3.00", pkg="0.50", lab="2.00")
    assert result.total_cost_excluding_labour == Decimal("3.50")


def test_total_cost_incl_labour_adds_labour():
    result = _price(ing="3.00", pkg="0.50", lab="2.00")
    assert result.total_cost_including_labour == Decimal("5.50")


# ── recommended price ─────────────────────────────────────────────────────────

def test_recommended_price_60_margin():
    # cost=5.00, margin=60% → 5 / (1 - 0.60) = 12.50
    result = _price(ing="5.00", desired_margin="60")
    assert result.recommended_price == Decimal("12.50")


def test_recommended_price_at_desired_margin():
    result = _price(ing="7.00", desired_margin="65")
    expected = (Decimal("7.00") / Decimal("0.35")).quantize(Decimal("0.01"))
    assert result.recommended_price == expected


def test_recommended_prices_dict_has_all_margins():
    result = _price(ing="5.00")
    for m in [50, 55, 60, 65, 70]:
        assert f"{m}_pct" in result.recommended_prices
        assert result.recommended_prices[f"{m}_pct"] > Decimal("0")


def test_higher_margin_means_higher_recommended_price():
    result = _price(ing="5.00")
    assert result.recommended_prices["70_pct"] > result.recommended_prices["60_pct"]


# ── gross & net profit ────────────────────────────────────────────────────────

def test_gross_profit_at_recommended_price_is_positive():
    result = _price(ing="5.00", desired_margin="60", selling="12.50")
    # cost_excl_labour = 5.00, selling = 12.50 → gross_profit = 7.50
    assert result.gross_profit == Decimal("7.50")


def test_net_profit_deducts_labour():
    result = _price(ing="3.00", lab="2.00", selling="10.00")
    # cost_incl = 5.00, selling = 10.00 → net_profit = 5.00
    assert result.net_profit == Decimal("5.00")


def test_net_profit_negative_when_selling_below_cost():
    result = _price(ing="5.00", lab="3.00", selling="4.00")
    assert result.net_profit < Decimal("0")


# ── food cost percent ─────────────────────────────────────────────────────────

def test_food_cost_percent_correct():
    # ingredient_cost = 2.50, selling = 10.00 → 25%
    result = _price(ing="2.50", selling="10.00")
    assert result.food_cost_percent == Decimal("25.0000")


def test_food_cost_percent_zero_when_no_selling_price():
    result = _price(ing="2.50", selling="0")
    assert result.food_cost_percent == Decimal("0")


# ── margin percent ────────────────────────────────────────────────────────────

def test_net_margin_percent_correct():
    # net_profit=5, selling=10 → 50%
    result = _price(ing="3.00", lab="2.00", selling="10.00")
    assert result.net_margin_percent == Decimal("50.0000")


def test_gross_margin_percent_excludes_labour():
    # cost_excl=3.00, selling=10.00 → gross margin = 70%
    result = _price(ing="3.00", lab="2.00", selling="10.00")
    assert result.gross_margin_percent == Decimal("70.0000")


# ── margin status ─────────────────────────────────────────────────────────────

def test_status_loss_making_when_selling_below_true_cost():
    result = _price(ing="5.00", lab="3.00", selling="4.00")
    assert result.margin_status == "loss_making"


def test_status_excellent_when_above_desired_margin():
    # cost_incl=5.00, selling=20.00 → net_margin=75% > desired 60%
    result = _price(ing="5.00", selling="20.00", desired_margin="60")
    assert result.margin_status == "excellent"


def test_status_low_margin_under_20_percent():
    # food_cost must stay <=40% to avoid high_food_cost firing first
    # ing=0.80 (8%), lab=8.10, selling=10.00 → net_margin=11%, food_cost=8%
    result = _price(ing="0.80", lab="8.10", selling="10.00", desired_margin="60")
    assert result.margin_status == "low_margin"


def test_status_profitable_between_20_and_desired():
    # ing=2.00 (20% food cost), lab=4.50, selling=10.00 → net_margin=35%, desired=60%
    result = _price(ing="2.00", lab="4.50", selling="10.00", desired_margin="60")
    assert result.margin_status == "profitable"


# ── warnings ──────────────────────────────────────────────────────────────────

def test_loss_making_generates_warning():
    result = _price(ing="8.00", selling="5.00")
    assert len(result.warnings) > 0
    assert any("loss" in w.lower() for w in result.warnings)


def test_no_warnings_for_excellent_margin():
    result = _price(ing="2.00", selling="10.00", desired_margin="60")
    # net_margin = 80%, food_cost = 20%, all good
    assert result.margin_status == "excellent"


# ── packaging included in gross cost ─────────────────────────────────────────

def test_packaging_included_in_cost_excl_labour():
    result = _price(ing="3.00", pkg="1.00", lab="2.00", selling="10.00")
    assert result.total_cost_excluding_labour == Decimal("4.00")
    assert result.total_cost_including_labour == Decimal("6.00")
    assert result.net_profit == Decimal("4.00")


# ── Box of 8 minis end-to-end ─────────────────────────────────────────────────

def test_box_of_8_minis_pricing():
    """
    Recipe makes 8 mini loaves.
    Per-item costs: ingredient=1.20, packaging=0.15, labour=0.50
    Variant: Box of 8 → multiplier=8
    Selling price: £18.00
    """
    result = _price(
        ing="1.20", pkg="0.15", lab="0.50",
        multiplier="8", selling="18.00", desired_margin="60"
    )
    assert result.ingredient_cost == Decimal("9.60")
    assert result.packaging_cost == Decimal("1.20")
    assert result.labour_cost == Decimal("4.00")
    assert result.total_cost_including_labour == Decimal("14.80")
    assert result.net_profit == Decimal("3.20")
