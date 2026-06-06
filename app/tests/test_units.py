from decimal import Decimal

import pytest

from app.core.units import convert_to_base, get_unit_type, units_compatible, UnitType


def test_grams_to_base():
    assert convert_to_base(Decimal("500"), "g") == Decimal("500")


def test_kg_to_base():
    assert convert_to_base(Decimal("1"), "kg") == Decimal("1000")


def test_oz_to_base():
    result = convert_to_base(Decimal("1"), "oz")
    assert abs(result - Decimal("28.349523")) < Decimal("0.000001")


def test_ml_to_base():
    assert convert_to_base(Decimal("250"), "ml") == Decimal("250")


def test_litre_to_base():
    assert convert_to_base(Decimal("1"), "l") == Decimal("1000")


def test_tsp_to_base():
    result = convert_to_base(Decimal("1"), "tsp")
    assert abs(result - Decimal("4.92892")) < Decimal("0.00001")


def test_piece_to_base():
    assert convert_to_base(Decimal("6"), "piece") == Decimal("6")


def test_unit_type_weight():
    assert get_unit_type("kg") == UnitType.weight


def test_unit_type_volume():
    assert get_unit_type("ml") == UnitType.volume


def test_unit_type_count():
    assert get_unit_type("piece") == UnitType.count


def test_units_compatible_same_type():
    assert units_compatible("g", "kg") is True


def test_units_compatible_different_type():
    assert units_compatible("g", "ml") is False


def test_unknown_unit_raises():
    with pytest.raises(ValueError):
        convert_to_base(Decimal("1"), "zap")
