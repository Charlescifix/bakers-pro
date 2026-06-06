"""
Recipe cost calculator tests using Bold Munch reference data from bakers-backend.md §11.
All values use Decimal to match production behaviour.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from unittest.mock import MagicMock

import pytest

from app.calculators.recipe_calculator import compute_recipe_cost, scale_recipe_cost
from app.calculators.cost_engine import unit_cost
from app.core.units import convert_to_base


# ── Minimal fakes ──────────────────────────────────────────────────────────────

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
    id: str = "ver-001"
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


# ── Pre-computed ingredient costs matching founder spreadsheet data ────────────
# Flour: £0.78 / 1500g
FLOUR_UNIT_COST = unit_cost(Decimal("0.78"), convert_to_base(Decimal("1500"), "g"))
# Sugar: £0.99 / 1000g
SUGAR_UNIT_COST = unit_cost(Decimal("0.99"), convert_to_base(Decimal("1000"), "g"))
# Yeast: £1.20 / 7g (one sachet counts as a piece here, but let's use grams for cost)
YEAST_UNIT_COST = unit_cost(Decimal("1.20"), convert_to_base(Decimal("7"), "g"))
# Butter: £2.50 / 1000g
BUTTER_UNIT_COST = unit_cost(Decimal("2.50"), convert_to_base(Decimal("1000"), "g"))
# Eggs: £2.00 / 6 pieces
EGG_UNIT_COST = unit_cost(Decimal("2.00"), convert_to_base(Decimal("6"), "piece"))
# Bananas: £1.00 / 4 pieces (approx)
BANANA_UNIT_COST = unit_cost(Decimal("1.00"), convert_to_base(Decimal("4"), "piece"))


# ── Test: Puff Puff recipe total ───────────────────────────────────────────────

def _puff_puff_recipe():
    ing_flour = FakeIngredient("flour", "Flour", FLOUR_UNIT_COST)
    ing_sugar = FakeIngredient("sugar", "White Sugar", SUGAR_UNIT_COST)
    ing_yeast = FakeIngredient("yeast", "Yeast", YEAST_UNIT_COST)

    items = [
        FakeRecipeItem("flour", Decimal("430"), "g"),
        FakeRecipeItem("sugar", Decimal("175"), "g"),
        FakeRecipeItem("yeast", Decimal("7"), "g"),
    ]
    version = FakeVersion(items=items)
    recipe = FakeRecipe("r-puff", "Puff Puff", Decimal("30"), "item", 30)
    ingredient_map = {"flour": ing_flour, "sugar": ing_sugar, "yeast": ing_yeast}
    return recipe, version, ingredient_map


def test_puff_puff_ingredient_cost():
    recipe, version, ingredient_map = _puff_puff_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))

    # Flour: 430g * 0.000520/g = 0.2236
    expected_flour = Decimal("430") * FLOUR_UNIT_COST
    # Sugar: 175g * SUGAR_UNIT_COST
    expected_sugar = Decimal("175") * SUGAR_UNIT_COST
    # Yeast: 7g * YEAST_UNIT_COST
    expected_yeast = Decimal("7") * YEAST_UNIT_COST
    expected_total = (expected_flour + expected_sugar + expected_yeast).quantize(Decimal("0.01"))

    assert abs(result.total_ingredient_cost - expected_total) < Decimal("0.01")


def test_puff_puff_labour_cost():
    recipe, version, ingredient_map = _puff_puff_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    # 30 minutes at £10/hour = £5.00
    assert result.total_labour_cost == Decimal("5.00")


def test_puff_puff_cost_per_item():
    recipe, version, ingredient_map = _puff_puff_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    expected = result.total_cost_including_labour / Decimal("30")
    assert abs(result.cost_per_item_incl_labour - expected.quantize(Decimal("0.000001"))) < Decimal("0.000001")


def test_puff_puff_recommended_price_60():
    recipe, version, ingredient_map = _puff_puff_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    cpi = result.cost_per_item_incl_labour
    expected = (cpi / (Decimal("1") - Decimal("0.60"))).quantize(Decimal("0.01"))
    assert result.recommended_prices["60_pct"] == expected


# ── Test: Banana Bread (classic maxi) ─────────────────────────────────────────

def _banana_bread_recipe():
    ing_flour = FakeIngredient("flour", "Flour", FLOUR_UNIT_COST)
    ing_butter = FakeIngredient("butter", "Butter", BUTTER_UNIT_COST)
    ing_sugar = FakeIngredient("sugar", "White Sugar", SUGAR_UNIT_COST)
    ing_egg = FakeIngredient("egg", "Eggs", EGG_UNIT_COST)
    ing_banana = FakeIngredient("banana", "Bananas", BANANA_UNIT_COST)

    items = [
        FakeRecipeItem("flour", Decimal("280"), "g"),
        FakeRecipeItem("butter", Decimal("150"), "g"),
        FakeRecipeItem("sugar", Decimal("200"), "g"),
        FakeRecipeItem("egg", Decimal("3"), "piece"),
        FakeRecipeItem("banana", Decimal("4"), "piece"),
    ]
    version = FakeVersion(items=items)
    recipe = FakeRecipe("r-bb", "Classic Banana Bread", Decimal("1"), "loaf", 45)
    ingredient_map = {
        "flour": ing_flour, "butter": ing_butter, "sugar": ing_sugar,
        "egg": ing_egg, "banana": ing_banana,
    }
    return recipe, version, ingredient_map


def test_banana_bread_has_five_ingredient_lines():
    recipe, version, ingredient_map = _banana_bread_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    assert len(result.ingredient_lines) == 5


def test_banana_bread_labour_45min():
    recipe, version, ingredient_map = _banana_bread_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    # 45 min at £10/hour = £7.50
    assert result.total_labour_cost == Decimal("7.50")


def test_banana_bread_total_cost_structure():
    recipe, version, ingredient_map = _banana_bread_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    assert result.total_cost_including_labour == result.total_cost_excluding_labour + result.total_labour_cost


def test_banana_bread_cost_excl_labour_equals_ingredients_plus_packaging():
    recipe, version, ingredient_map = _banana_bread_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    assert result.total_cost_excluding_labour == result.total_ingredient_cost + result.total_packaging_cost


# ── Test: waste percent ────────────────────────────────────────────────────────

def test_waste_percent_increases_cost():
    ing = FakeIngredient("flour", "Flour", FLOUR_UNIT_COST, waste_percent_default=Decimal("10"))
    items = [FakeRecipeItem("flour", Decimal("430"), "g")]
    version = FakeVersion(items=items)
    recipe = FakeRecipe("r-w", "Test", Decimal("30"), "item", 0)
    result_with_waste = compute_recipe_cost(recipe, version, {"flour": ing}, {}, Decimal("0"))

    ing_no_waste = FakeIngredient("flour", "Flour", FLOUR_UNIT_COST, waste_percent_default=Decimal("0"))
    result_no_waste = compute_recipe_cost(recipe, FakeVersion(items=items), {"flour": ing_no_waste}, {}, Decimal("0"))

    assert result_with_waste.total_ingredient_cost > result_no_waste.total_ingredient_cost


def test_waste_override_takes_priority():
    ing = FakeIngredient("flour", "Flour", FLOUR_UNIT_COST, waste_percent_default=Decimal("20"))
    items = [FakeRecipeItem("flour", Decimal("430"), "g", waste_percent_override=Decimal("5"))]
    version = FakeVersion(items=items)
    recipe = FakeRecipe("r-wo", "Test", Decimal("30"), "item", 0)

    result = compute_recipe_cost(recipe, version, {"flour": ing}, {}, Decimal("0"))
    assert result.ingredient_lines[0].waste_percent == Decimal("5")


# ── Test: Scale ────────────────────────────────────────────────────────────────

def test_scale_puff_puff_3_batches():
    recipe, version, ingredient_map = _puff_puff_recipe()
    result = scale_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"), Decimal("90"))

    assert result["batches_required"] == 3
    assert result["order_quantity"] == Decimal("90")


def test_scale_cost_is_batches_times_single_batch():
    recipe, version, ingredient_map = _puff_puff_recipe()
    single = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    scaled = scale_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"), Decimal("90"))

    expected_excl = (single.total_cost_excluding_labour * 3).quantize(Decimal("0.01"))
    assert scaled["total_cost_excluding_labour"] == expected_excl


def test_scale_rounding_up():
    recipe, version, ingredient_map = _puff_puff_recipe()
    # 31 puff puff needs 2 batches (base yield 30)
    result = scale_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"), Decimal("31"))
    assert result["batches_required"] == 2


# ── Test: zero-labour rate ─────────────────────────────────────────────────────

def test_zero_labour_rate():
    recipe, version, ingredient_map = _puff_puff_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("0.00"))
    assert result.total_labour_cost == Decimal("0.00")
    assert result.total_cost_including_labour == result.total_cost_excluding_labour


# ── Test: recommended prices present ──────────────────────────────────────────

def test_recommended_prices_all_margins_present():
    recipe, version, ingredient_map = _puff_puff_recipe()
    result = compute_recipe_cost(recipe, version, ingredient_map, {}, Decimal("10.00"))
    for margin in [50, 55, 60, 65, 70]:
        assert f"{margin}_pct" in result.recommended_prices
        assert result.recommended_prices[f"{margin}_pct"] > Decimal("0")
