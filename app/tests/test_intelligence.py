"""Tests for AI provider logic — pure, no DB, no external API calls."""
import uuid

import pytest

from app.services.ai_provider import MockAIProvider, _parse_items, _detect_delivery_method, _detect_date
from app.schemas.intelligence import ParsedOrderResult

_V1 = uuid.uuid4()
_V2 = uuid.uuid4()
_V3 = uuid.uuid4()


provider = MockAIProvider()


# ── order parser ──────────────────────────────────────────────────────────────

class TestParseItems:
    def test_simple_order(self):
        items = _parse_items("60 puff puff, 20 meat pies")
        assert len(items) == 2
        quantities = {i.product_name: i.quantity for i in items}
        assert quantities.get("Puff Puff") == 60
        assert quantities.get("Meat Pies") == 20

    def test_order_with_and(self):
        items = _parse_items("60 puff puff, 20 meat pies and 10 mini banana breads")
        names = {i.product_name for i in items}
        assert any("Puff" in n for n in names)
        assert any("Meat" in n for n in names)

    def test_single_item(self):
        items = _parse_items("12 cupcakes")
        assert len(items) == 1
        assert items[0].quantity == 12

    def test_no_items_returns_empty(self):
        items = _parse_items("Hello, when are you open?")
        assert items == []

    def test_title_case_normalisation(self):
        items = _parse_items("30 banana bread")
        assert items[0].product_name == "Banana Bread"


class TestDetectDeliveryMethod:
    def test_delivery_keyword(self):
        assert _detect_delivery_method("please deliver to my house") == "delivery"

    def test_pickup_keyword(self):
        assert _detect_delivery_method("I will collect on Saturday") == "pickup"

    def test_shipped_keyword(self):
        assert _detect_delivery_method("Can it be shipped?") == "delivery"

    def test_default_pickup(self):
        assert _detect_delivery_method("I want 10 cupcakes") == "pickup"


class TestDetectDate:
    def test_saturday(self):
        date = _detect_date("ready for Saturday please")
        assert date is not None
        assert "saturday" in date.lower()

    def test_next_friday(self):
        date = _detect_date("deliver next friday")
        assert "friday" in date.lower()

    def test_tomorrow(self):
        date = _detect_date("I need this for tomorrow")
        assert date is not None

    def test_no_date_returns_none(self):
        assert _detect_date("60 puff puff please") is None


class TestMockAIProviderParseOrder:
    def test_full_order_message(self):
        msg = "Can I get 60 puff puff, 20 meat pies and 10 mini banana breads for Saturday delivery?"
        result = provider.parse_order_request(msg)
        assert isinstance(result, ParsedOrderResult)
        assert len(result.items) >= 2
        assert result.delivery_method == "delivery"
        assert result.requested_date is not None
        assert result.confidence >= 0.80

    def test_low_confidence_empty_message(self):
        result = provider.parse_order_request("Hello!")
        assert result.confidence < 0.65
        assert result.items == []

    def test_confidence_increases_with_items(self):
        few = provider.parse_order_request("12 cupcakes")
        many = provider.parse_order_request("12 cupcakes, 6 muffins, 4 pies, 10 brownies")
        assert many.confidence >= few.confidence

    def test_raw_message_preserved(self):
        msg = "20 meat pies for Sunday"
        result = provider.parse_order_request(msg)
        assert result.raw_message == msg


# ── pricing advice ────────────────────────────────────────────────────────────

class TestPricingAdvice:
    def _variant(self, vid, name, current, recommended, margin, desired):
        return {
            "variant_id": vid,
            "product_name": name,
            "variant_name": "",
            "current_selling_price": current,
            "recommended_price": recommended,
            "net_margin_percent": margin,
            "desired_margin_percent": desired,
        }

    def test_loss_making_high_priority(self):
        data = [self._variant(_V1, "Meat Pie", "3.00", "6.00", "-10.0", "50.0")]
        advice = provider.generate_pricing_advice(data)
        assert len(advice) == 1
        assert advice[0].priority == "high"
        assert "loss" in advice[0].advice.lower()

    def test_below_margin_medium_priority(self):
        data = [self._variant(_V1, "Banana Bread", "8.00", "10.00", "45.0", "50.0")]
        advice = provider.generate_pricing_advice(data)
        assert advice[0].priority == "medium"

    def test_well_above_margin_low_priority(self):
        data = [self._variant(_V1, "Cookie", "5.00", "3.50", "72.0", "50.0")]
        advice = provider.generate_pricing_advice(data)
        assert len(advice) == 1
        assert advice[0].priority == "low"

    def test_on_target_no_advice(self):
        data = [self._variant(_V1, "Brownie", "6.00", "5.80", "52.0", "50.0")]
        advice = provider.generate_pricing_advice(data)
        assert advice == []

    def test_suggested_price_for_loss(self):
        data = [self._variant(_V1, "Puff Puff", "2.00", "5.00", "-5.0", "50.0")]
        advice = provider.generate_pricing_advice(data)
        assert advice[0].suggested_price == 5.0

    def test_no_suggested_price_for_strong_margin(self):
        data = [self._variant(_V1, "Mini Loaf", "8.00", "6.00", "70.0", "50.0")]
        advice = provider.generate_pricing_advice(data)
        assert len(advice) == 1
        assert advice[0].suggested_price is None


# ── explain margin warning ─────────────────────────────────────────────────────

class TestExplainMarginWarning:
    def test_returns_string(self):
        explanation = provider.explain_margin_warning(
            {"net_margin_percent": 35.0, "product_name": "Puff Puff Box", "labour_cost": 1.20}
        )
        assert isinstance(explanation, str)
        assert "Puff Puff Box" in explanation
        assert "35.0%" in explanation
