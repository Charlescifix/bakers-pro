from decimal import Decimal

import pytest

from app.calculators.batch_scaler import batches_required, scale_ingredient, scale_recipe


def test_exact_multiple():
    assert batches_required(Decimal("90"), Decimal("30")) == 3


def test_rounds_up():
    assert batches_required(Decimal("31"), Decimal("30")) == 2


def test_single_batch():
    assert batches_required(Decimal("20"), Decimal("30")) == 1


def test_zero_yield_raises():
    with pytest.raises(ValueError):
        batches_required(Decimal("30"), Decimal("0"))


def test_scale_ingredient_3x():
    result = scale_ingredient(Decimal("430"), Decimal("30"), Decimal("90"))
    assert result == Decimal("1290")


def test_scale_recipe():
    items = [
        {"ingredient_id": "abc", "quantity": Decimal("430"), "unit_code": "g"},
        {"ingredient_id": "def", "quantity": Decimal("175"), "unit_code": "g"},
    ]
    scaled = scale_recipe(items, Decimal("30"), Decimal("90"))
    assert scaled[0]["scaled_quantity"] == Decimal("1290")
    assert scaled[0]["batches"] == 3
    assert scaled[1]["scaled_quantity"] == Decimal("525")
