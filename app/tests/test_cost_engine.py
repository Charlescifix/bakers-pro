"""Golden tests from founder workflow data as described in bakers-backend.md §11."""
from decimal import Decimal

import pytest

from app.calculators.cost_engine import (
    unit_cost,
    ingredient_line_cost,
    labour_cost,
    recommended_price,
    net_profit,
    food_cost_percent,
    margin_percent,
    channel_fee,
)
from app.core.units import convert_to_base


# --- Test type A: ingredient unit cost ---

def test_flour_unit_cost():
    """Flour at £0.78 / 1500g → £0.00052/g"""
    price = Decimal("0.78")
    qty_base = convert_to_base(Decimal("1500"), "g")
    cost = unit_cost(price, qty_base)
    assert cost == Decimal("0.000520")


def test_unit_cost_zero_quantity_raises():
    with pytest.raises(ValueError):
        unit_cost(Decimal("1.00"), Decimal("0"))


def test_unit_cost_kg():
    """1kg butter at £2.50 → £0.0025/g"""
    qty_base = convert_to_base(Decimal("1"), "kg")
    cost = unit_cost(Decimal("2.50"), qty_base)
    assert cost == Decimal("0.002500")


# --- Test type C: recommended selling price ---

def test_recommended_price_65_margin():
    """unit_cost=7.00, margin=65% → £20.00"""
    price = recommended_price(Decimal("7.00"), Decimal("65"))
    assert price == Decimal("20.00")


def test_recommended_price_60_margin():
    """unit_cost=5.00, margin=60% → £12.50"""
    price = recommended_price(Decimal("5.00"), Decimal("60"))
    assert price == Decimal("12.50")


def test_recommended_price_with_fee():
    """unit_cost=7.00, margin=55%, platform_fee=10% → check calculation"""
    price = recommended_price(Decimal("7.00"), Decimal("55"), fee_percent=Decimal("10"))
    denominator = Decimal("1") - Decimal("0.55") - Decimal("0.10")
    expected = (Decimal("7.00") / denominator).quantize(Decimal("0.01"))
    assert price == expected


def test_recommended_price_over_100_raises():
    with pytest.raises(ValueError):
        recommended_price(Decimal("5.00"), Decimal("100"))


# --- Test type D: platform commission ---

def test_net_profit_with_commission():
    """revenue=18.00, commission=2.20, other_costs=8.80 → net_profit=7.00"""
    profit = net_profit(Decimal("18.00"), Decimal("2.20") + Decimal("8.80"))
    assert profit == Decimal("7.00")


# --- Labour cost ---

def test_labour_cost_30_min():
    """£10/hour × 30 min = £5.00"""
    cost = labour_cost(Decimal("10.00"), Decimal("30"))
    assert cost == Decimal("5.00")


def test_labour_cost_45_min():
    """£12/hour × 45 min = £9.00"""
    cost = labour_cost(Decimal("12.00"), Decimal("45"))
    assert cost == Decimal("9.00")


# --- Food cost percentage ---

def test_food_cost_percent():
    """ingredient_cost=2.50, selling_price=10.00 → 25%"""
    pct = food_cost_percent(Decimal("2.50"), Decimal("10.00"))
    assert pct == Decimal("25.0000")


def test_food_cost_percent_zero_price():
    pct = food_cost_percent(Decimal("2.50"), Decimal("0"))
    assert pct == Decimal("0")


# --- Ingredient line cost with waste ---

def test_ingredient_line_cost_no_waste():
    cost = ingredient_line_cost(Decimal("280"), Decimal("0.000520"), Decimal("0"))
    assert cost == Decimal("0.145600")


def test_ingredient_line_cost_with_waste():
    cost = ingredient_line_cost(Decimal("100"), Decimal("0.01"), Decimal("10"))
    expected = (Decimal("100") * Decimal("0.01") * Decimal("1.10")).quantize(Decimal("0.000001"))
    assert cost == expected


# --- Channel fee ---

def test_channel_fee_percentage():
    fee = channel_fee(Decimal("50.00"), pct_fee=Decimal("12.2"))
    assert fee == Decimal("6.10")


# --- Margin percent ---

def test_margin_percent():
    pct = margin_percent(Decimal("30.00"), Decimal("100.00"))
    assert pct == Decimal("30.0000")


def test_margin_percent_zero_revenue():
    pct = margin_percent(Decimal("10.00"), Decimal("0"))
    assert pct == Decimal("0")
