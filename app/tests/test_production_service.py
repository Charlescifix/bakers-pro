"""Tests for production plan generator and shopping list logic (pure calculations, no DB)."""
import math
from decimal import Decimal

import pytest


# ── helpers replicating service logic without DB ─────────────────────────────

def batches_required(order_quantity: int, base_yield: int) -> int:
    return math.ceil(order_quantity / base_yield) if base_yield > 0 else 1


def planned_yield(batches: int, base_yield: int) -> Decimal:
    return Decimal(str(batches * base_yield))


def aggregate_ingredients(recipe_items, batches_needed: int):
    """Aggregate ingredient quantities across batches."""
    totals = {}
    for ri in recipe_items:
        scaled = ri["quantity_used"] * Decimal(str(batches_needed))
        totals[ri["ingredient_id"]] = totals.get(ri["ingredient_id"], Decimal("0")) + scaled
    return totals


def aggregate_packaging(packaging_rules, batches_needed: int, total_items: Decimal):
    totals = {}
    for rule in packaging_rules:
        if rule["rule_type"] == "per_batch":
            qty = rule["quantity_per_batch"] * Decimal(str(batches_needed))
        elif rule["rule_type"] == "per_item":
            qty = rule["quantity_per_item"] * total_items
        else:  # per_order
            qty = rule.get("quantity_per_batch") or Decimal("1")
        totals[rule["packaging_item_id"]] = totals.get(rule["packaging_item_id"], Decimal("0")) + qty
    return totals


def quantity_to_buy(required: Decimal, stock: Decimal) -> Decimal:
    return max(Decimal("0"), required - stock)


# ── batches_required ──────────────────────────────────────────────────────────

class TestBatchesRequired:
    def test_exact_multiple(self):
        assert batches_required(12, 12) == 1

    def test_exact_multiple_two(self):
        assert batches_required(24, 12) == 2

    def test_rounds_up(self):
        assert batches_required(13, 12) == 2

    def test_one_item_batch_yield_6(self):
        assert batches_required(1, 6) == 1

    def test_seven_items_batch_yield_6(self):
        assert batches_required(7, 6) == 2

    def test_zero_yield_returns_one(self):
        assert batches_required(5, 0) == 1


# ── planned yield ─────────────────────────────────────────────────────────────

class TestPlannedYield:
    def test_single_batch(self):
        assert planned_yield(1, 12) == Decimal("12")

    def test_two_batches(self):
        assert planned_yield(2, 12) == Decimal("24")

    def test_fractional_yield(self):
        assert planned_yield(3, 6) == Decimal("18")


# ── aggregate ingredients ─────────────────────────────────────────────────────

class TestAggregateIngredients:
    def setup_method(self):
        self.recipe_items = [
            {"ingredient_id": "flour", "quantity_used": Decimal("500")},
            {"ingredient_id": "sugar", "quantity_used": Decimal("200")},
            {"ingredient_id": "flour", "quantity_used": Decimal("100")},  # second flour item
        ]

    def test_single_batch(self):
        totals = aggregate_ingredients(self.recipe_items, 1)
        assert totals["flour"] == Decimal("600")
        assert totals["sugar"] == Decimal("200")

    def test_two_batches(self):
        totals = aggregate_ingredients(self.recipe_items, 2)
        assert totals["flour"] == Decimal("1200")
        assert totals["sugar"] == Decimal("400")

    def test_empty_recipe(self):
        totals = aggregate_ingredients([], 2)
        assert totals == {}


# ── aggregate packaging ───────────────────────────────────────────────────────

class TestAggregatePackaging:
    def test_per_batch_rule(self):
        rules = [{"packaging_item_id": "box", "rule_type": "per_batch", "quantity_per_batch": Decimal("1"), "quantity_per_item": Decimal("0")}]
        totals = aggregate_packaging(rules, batches_needed=2, total_items=Decimal("24"))
        assert totals["box"] == Decimal("2")

    def test_per_item_rule(self):
        rules = [{"packaging_item_id": "wrap", "rule_type": "per_item", "quantity_per_batch": Decimal("0"), "quantity_per_item": Decimal("1")}]
        totals = aggregate_packaging(rules, batches_needed=2, total_items=Decimal("24"))
        assert totals["wrap"] == Decimal("24")

    def test_per_order_rule(self):
        rules = [{"packaging_item_id": "ribbon", "rule_type": "per_order", "quantity_per_batch": Decimal("1"), "quantity_per_item": Decimal("0")}]
        totals = aggregate_packaging(rules, batches_needed=2, total_items=Decimal("24"))
        assert totals["ribbon"] == Decimal("1")

    def test_multiple_rules(self):
        rules = [
            {"packaging_item_id": "box", "rule_type": "per_batch", "quantity_per_batch": Decimal("2"), "quantity_per_item": Decimal("0")},
            {"packaging_item_id": "wrap", "rule_type": "per_item", "quantity_per_batch": Decimal("0"), "quantity_per_item": Decimal("1")},
        ]
        totals = aggregate_packaging(rules, batches_needed=3, total_items=Decimal("18"))
        assert totals["box"] == Decimal("6")
        assert totals["wrap"] == Decimal("18")


# ── quantity to buy ───────────────────────────────────────────────────────────

class TestQuantityToBuy:
    def test_no_stock(self):
        assert quantity_to_buy(Decimal("500"), Decimal("0")) == Decimal("500")

    def test_sufficient_stock(self):
        assert quantity_to_buy(Decimal("500"), Decimal("600")) == Decimal("0")

    def test_partial_stock(self):
        assert quantity_to_buy(Decimal("500"), Decimal("300")) == Decimal("200")

    def test_exact_stock(self):
        assert quantity_to_buy(Decimal("500"), Decimal("500")) == Decimal("0")


# ── shopping list cost estimate ───────────────────────────────────────────────

class TestShoppingListCost:
    def test_estimated_cost(self):
        to_buy = Decimal("600")
        unit_cost = Decimal("0.003")  # £0.003 per gram
        from app.core.money import q_money
        assert q_money(to_buy * unit_cost) == Decimal("1.80")

    def test_zero_to_buy_zero_cost(self):
        from app.core.money import q_money
        assert q_money(Decimal("0") * Decimal("0.003")) == Decimal("0.00")

    def test_total_list_cost(self):
        from app.core.money import q_money
        costs = [Decimal("1.80"), Decimal("0.45"), Decimal("2.10")]
        total = q_money(sum(costs, Decimal("0")))
        assert total == Decimal("4.35")
