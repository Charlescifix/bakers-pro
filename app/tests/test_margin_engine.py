from decimal import Decimal

from app.calculators.margin_engine import classify_quote, margin_warnings


def test_loss_making():
    status = classify_quote(Decimal("-5"), Decimal("-10"), Decimal("50"), Decimal("60"))
    assert status == "loss_making"


def test_high_food_cost():
    status = classify_quote(Decimal("10"), Decimal("25"), Decimal("45"), Decimal("60"))
    assert status == "high_food_cost"


def test_low_margin():
    status = classify_quote(Decimal("5"), Decimal("15"), Decimal("30"), Decimal("60"))
    assert status == "low_margin"


def test_excellent():
    status = classify_quote(Decimal("40"), Decimal("65"), Decimal("25"), Decimal("60"))
    assert status == "excellent"


def test_profitable():
    status = classify_quote(Decimal("20"), Decimal("35"), Decimal("30"), Decimal("60"))
    assert status == "profitable"


def test_warnings_loss():
    warnings = margin_warnings(Decimal("-5"), Decimal("-10"), Decimal("30"), Decimal("60"))
    assert any("loss" in w.lower() for w in warnings)


def test_warnings_channel_fee():
    warnings = margin_warnings(
        Decimal("10"), Decimal("25"), Decimal("30"), Decimal("60"),
        channel_fees=Decimal("6.80"), channel_name="TikTok"
    )
    assert any("TikTok" in w for w in warnings)
