"""Tests for label HTML generation and allergen matrix logic — pure functions, no DB."""
import pytest

from app.services.label_service import _worst_status, _render_label_html


# ── allergen status priority ──────────────────────────────────────────────────

class TestWorstStatus:
    def test_empty_returns_free(self):
        assert _worst_status([]) == "free"

    def test_single_contains(self):
        assert _worst_status(["contains"]) == "contains"

    def test_contains_beats_may_contain(self):
        assert _worst_status(["may_contain", "contains"]) == "contains"

    def test_may_contain_beats_free(self):
        assert _worst_status(["free", "may_contain"]) == "may_contain"

    def test_unknown_beats_free(self):
        assert _worst_status(["free", "unknown"]) == "unknown"

    def test_contains_beats_all(self):
        assert _worst_status(["free", "unknown", "may_contain", "contains"]) == "contains"

    def test_all_free(self):
        assert _worst_status(["free", "free", "free"]) == "free"


# ── label HTML rendering ──────────────────────────────────────────────────────

class TestRenderLabelHtml:
    def _render(self, **kwargs):
        defaults = dict(
            product_name="Banana Bread",
            variant_name="Regular Loaf",
            label_type="allergen",
            ingredient_names=["Plain Flour", "Eggs", "Butter", "Sugar"],
            allergens_contains=["Eggs", "Milk", "Cereals containing gluten"],
            allergens_may_contain=["Nuts (tree nuts)"],
            storage_instruction="Store in a cool, dry place. Consume within 3 days.",
            batch_number=None,
            best_before_date=None,
            bakery_name="Bold Munch",
            fsa_rating="5",
        )
        defaults.update(kwargs)
        return _render_label_html(**defaults)

    def test_returns_html_string(self):
        html = self._render()
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_product_name_in_output(self):
        html = self._render()
        assert "Banana Bread" in html

    def test_ingredients_listed(self):
        html = self._render()
        assert "Plain Flour" in html
        assert "Eggs" in html

    def test_allergens_bold(self):
        html = self._render()
        assert "<strong>Eggs</strong>" in html or "Eggs" in html
        assert "Milk" in html

    def test_may_contain_section(self):
        html = self._render()
        assert "May contain" in html
        assert "Nuts" in html

    def test_no_allergens_shows_none_declared(self):
        html = self._render(allergens_contains=[], allergens_may_contain=[])
        assert "No declared allergens" in html

    def test_storage_instruction_included(self):
        html = self._render()
        assert "cool, dry place" in html

    def test_bakery_name_included(self):
        html = self._render()
        assert "Bold Munch" in html

    def test_fsa_rating_included(self):
        html = self._render()
        assert "FSA" in html
        assert "5" in html

    def test_no_fsa_when_none(self):
        html = self._render(fsa_rating=None)
        assert "FSA" not in html

    def test_batch_number_included_when_set(self):
        html = self._render(batch_number="BATCH-00042")
        assert "BATCH-00042" in html

    def test_best_before_included_when_set(self):
        html = self._render(best_before_date="12 Jun 2026")
        assert "12 Jun 2026" in html

    def test_xss_escaped(self):
        html = self._render(product_name="<script>alert(1)</script>")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_ingredient_label_type(self):
        html = self._render(label_type="ingredient")
        assert isinstance(html, str)

    def test_empty_ingredients_no_error(self):
        html = self._render(ingredient_names=[])
        assert isinstance(html, str)


# ── allergen seed list ─────────────────────────────────────────────────────────

class TestAllergenSeedList:
    def test_fourteen_uk_allergens(self):
        from app.models.allergen import UK_ALLERGENS
        assert len(UK_ALLERGENS) == 14

    def test_all_have_name_and_description(self):
        from app.models.allergen import UK_ALLERGENS
        for name, desc in UK_ALLERGENS:
            assert name and isinstance(name, str)
            assert desc and isinstance(desc, str)

    def test_includes_gluten(self):
        from app.models.allergen import UK_ALLERGENS
        names = [a[0] for a in UK_ALLERGENS]
        assert any("gluten" in n.lower() for n in names)

    def test_includes_milk(self):
        from app.models.allergen import UK_ALLERGENS
        names = [a[0] for a in UK_ALLERGENS]
        assert "Milk" in names

    def test_includes_eggs(self):
        from app.models.allergen import UK_ALLERGENS
        names = [a[0] for a in UK_ALLERGENS]
        assert "Eggs" in names

    def test_includes_sesame(self):
        from app.models.allergen import UK_ALLERGENS
        names = [a[0] for a in UK_ALLERGENS]
        assert "Sesame" in names
