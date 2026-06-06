"""Tests for report calculation functions — pure logic, no DB."""
from decimal import Decimal

import pytest

from app.reports.weekly_profit_report import compute_period_report, WeeklyReportResult
from app.reports.low_margin_report import find_low_margin_items, LowMarginItem


# ── weekly profit report ──────────────────────────────────────────────────────

def _order(rev, profit):
    return {"total_revenue": rev, "net_profit": profit}


def _item(name, price, qty, ing, pkg, lab, fee, profit):
    return {
        "product_name": name,
        "variant_name": "",
        "unit_price": price,
        "quantity": qty,
        "actual_ingredient_cost": ing,
        "actual_packaging_cost": pkg,
        "actual_labour_cost": lab,
        "actual_channel_fee": fee,
        "actual_net_profit": profit,
    }


class TestWeeklyReport:
    def test_empty_period(self):
        result = compute_period_report("Test Week", [], [])
        assert result.total_revenue == Decimal("0.00")
        assert result.net_profit == Decimal("0.00")
        assert result.order_count == 0
        assert result.best_product is None

    def test_single_order(self):
        orders = [_order("100.00", "40.00")]
        items = [_item("Banana Bread", "10.00", 10, "2.00", "0.50", "1.00", "0.25", "4.00")]
        result = compute_period_report("Week 1", orders, items)
        assert result.total_revenue == Decimal("100.00")
        assert result.net_profit == Decimal("40.00")
        assert result.order_count == 1
        assert result.best_product == "Banana Bread"

    def test_multiple_orders_aggregate(self):
        orders = [_order("100.00", "40.00"), _order("80.00", "30.00")]
        items = [
            _item("Banana Bread", "10.00", 10, "2.00", "0.50", "1.00", "0.25", "4.00"),
            _item("Puff Puff", "8.00", 10, "1.50", "0.20", "0.80", "0.10", "3.00"),
        ]
        result = compute_period_report("Week 1", orders, items)
        assert result.total_revenue == Decimal("180.00")
        assert result.net_profit == Decimal("70.00")
        assert result.order_count == 2

    def test_best_product_by_profit(self):
        orders = [_order("200.00", "70.00")]
        items = [
            _item("Banana Bread", "10.00", 10, "2.00", "0.50", "1.00", "0.00", "5.00"),
            _item("Meat Pie", "8.00", 10, "3.00", "0.80", "2.00", "0.00", "1.00"),
        ]
        result = compute_period_report("Week 1", orders, items)
        assert result.best_product == "Banana Bread"

    def test_worst_margin_product(self):
        orders = [_order("200.00", "20.00")]
        items = [
            _item("Banana Bread", "10.00", 5, "2.00", "0.50", "1.00", "0.00", "5.00"),
            _item("Puff Puff", "5.00", 20, "4.00", "0.50", "1.50", "0.00", "0.10"),
        ]
        result = compute_period_report("Week 1", orders, items)
        # Puff Puff has terrible margin
        assert result.worst_margin_product == "Puff Puff"

    def test_ingredient_cost_aggregated(self):
        orders = [_order("100.00", "50.00")]
        items = [_item("Banana Bread", "10.00", 10, "2.00", "0.50", "1.00", "0.25", "5.00")]
        result = compute_period_report("Week", orders, items)
        # 10 items × £2.00 ingredient = £20.00
        assert result.total_ingredient_cost == Decimal("20.00")
        assert result.total_packaging_cost == Decimal("5.00")
        assert result.total_labour_cost == Decimal("10.00")
        assert result.total_channel_fees == Decimal("2.50")

    def test_product_breakdown_populated(self):
        orders = [_order("100.00", "40.00")]
        items = [
            _item("Banana Bread", "10.00", 5, "2.00", "0.50", "1.00", "0.00", "4.00"),
            _item("Puff Puff", "5.00", 10, "1.00", "0.20", "0.80", "0.00", "2.00"),
        ]
        result = compute_period_report("Week", orders, items)
        assert len(result.product_breakdown) == 2
        names = {p.product_name for p in result.product_breakdown}
        assert "Banana Bread" in names and "Puff Puff" in names


# ── low margin report ─────────────────────────────────────────────────────────

def _variant(vid, pname, vname, price, margin, desired):
    return {
        "variant_id": vid,
        "product_name": pname,
        "variant_name": vname,
        "current_selling_price": price,
        "net_margin_percent": margin,
        "desired_margin_percent": desired,
    }


class TestLowMarginReport:
    def test_all_above_target_returns_empty(self):
        variants = [
            _variant("v1", "Banana Bread", "Regular", "10.00", "60.0", "50.0"),
            _variant("v2", "Puff Puff", "Box 20", "8.00", "55.0", "50.0"),
        ]
        result = find_low_margin_items(variants)
        assert result == []

    def test_one_below_target(self):
        variants = [
            _variant("v1", "Banana Bread", "Regular", "10.00", "40.0", "50.0"),
            _variant("v2", "Puff Puff", "Box 20", "8.00", "55.0", "50.0"),
        ]
        result = find_low_margin_items(variants)
        assert len(result) == 1
        assert result[0].product_name == "Banana Bread"
        assert result[0].shortfall_percent == Decimal("10.0")
        assert result[0].severity == "warning"

    def test_loss_making_is_critical(self):
        variants = [_variant("v1", "Meat Pie", "Regular", "5.00", "-5.0", "50.0")]
        result = find_low_margin_items(variants)
        assert result[0].severity == "critical"

    def test_sorted_worst_first(self):
        variants = [
            _variant("v1", "Product A", "", "10.00", "30.0", "50.0"),
            _variant("v2", "Product B", "", "8.00", "10.0", "50.0"),
            _variant("v3", "Product C", "", "12.00", "45.0", "50.0"),
        ]
        result = find_low_margin_items(variants)
        assert result[0].product_name == "Product B"
        assert result[-1].product_name == "Product C"

    def test_exact_target_not_flagged(self):
        variants = [_variant("v1", "Cookie", "Box 12", "6.00", "50.0", "50.0")]
        result = find_low_margin_items(variants)
        assert result == []
