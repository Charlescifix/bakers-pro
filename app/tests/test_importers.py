"""Tests for the import pipeline — pure logic, no DB required."""
import csv
import io
from decimal import Decimal

import openpyxl
import pytest

from app.imports.mapping_detector import (
    detect_column_mapping,
    detect_section_type,
    is_sample_content,
    score_row,
    _parse_decimal,
)
from app.imports.import_validator import validate_ingredient_row, validate_packaging_row
from app.imports.spreadsheet_importer import parse_csv, parse_xlsx


# ── mapping_detector ──────────────────────────────────────────────────────────

class TestDetectColumnMapping:
    def test_all_four_columns_high_confidence(self):
        headers = ["Ingredient Name", "Purchase Price", "Purchase Quantity", "Unit"]
        cm = detect_column_mapping(headers)
        assert cm.name_col is not None
        assert cm.price_col is not None
        assert cm.qty_col is not None
        assert cm.unit_col is not None
        assert cm.confidence == 0.92

    def test_three_columns(self):
        headers = ["Item", "Cost", "Quantity"]
        cm = detect_column_mapping(headers)
        assert cm.confidence == 0.78

    def test_two_columns(self):
        headers = ["Product", "Price"]
        cm = detect_column_mapping(headers)
        assert cm.confidence == 0.55

    def test_one_column(self):
        headers = ["Name"]
        cm = detect_column_mapping(headers)
        assert cm.confidence == 0.35

    def test_no_matching_columns(self):
        headers = ["Date", "Reference", "Notes"]
        cm = detect_column_mapping(headers)
        assert cm.confidence == 0.10

    def test_waste_column_detected(self):
        headers = ["Ingredient", "Price", "Qty", "Unit", "Waste %"]
        cm = detect_column_mapping(headers)
        assert cm.waste_col is not None

    def test_used_qty_before_qty(self):
        headers = ["Ingredient", "Price", "Quantity Used", "Pack Qty", "Unit"]
        cm = detect_column_mapping(headers)
        assert cm.used_qty_col is not None
        assert cm.qty_col is not None


class TestDetectSectionType:
    def test_detects_packaging(self):
        assert detect_section_type(["Packaging Item", "Cost"], []) == "packaging"

    def test_detects_ingredients(self):
        assert detect_section_type(["Ingredient", "Price", "Qty"], []) == "ingredients"

    def test_detects_selling_price(self):
        assert detect_section_type(["Selling Price", "Margin"], []) == "selling_price"

    def test_detects_overhead(self):
        assert detect_section_type(["Labour", "Energy", "Overhead"], []) == "overhead"

    def test_unknown_falls_back(self):
        assert detect_section_type(["Date", "Ref"], []) == "unknown"


class TestIsSampleContent:
    def test_detects_sample_by_name(self):
        is_sample, reason = is_sample_content(None, ["salmon", "potato"])
        assert is_sample is True
        assert reason == "sample_recipe"

    def test_detects_template_trigger(self):
        is_sample, reason = is_sample_content("template", [])
        assert is_sample is True

    def test_real_bakery_ingredient(self):
        is_sample, reason = is_sample_content("Banana Bread", ["flour", "eggs", "butter"])
        assert is_sample is False

    def test_sheet_named_demo(self):
        is_sample, _ = is_sample_content("demo version", [])
        assert is_sample is True


class TestParseDecimal:
    def test_plain_number(self):
        assert _parse_decimal("1.50") == "1.50"

    def test_currency_symbol(self):
        assert _parse_decimal("£2.99") == "2.99"

    def test_comma_thousands(self):
        assert _parse_decimal("1,500") == "1500"

    def test_dash_returns_none(self):
        assert _parse_decimal("-") is None

    def test_empty_returns_none(self):
        assert _parse_decimal("") is None

    def test_text_returns_none(self):
        assert _parse_decimal("N/A") is None


class TestScoreRow:
    def setup_method(self):
        from app.imports.mapping_detector import ColumnMapping
        self.col_map = ColumnMapping(
            name_col="Ingredient",
            price_col="Price",
            qty_col="Qty",
            unit_col="Unit",
        )

    def test_full_row(self):
        row = {"Ingredient": "Flour", "Price": "1.50", "Qty": "1000", "Unit": "g"}
        mapped, conf, flags = score_row(row, self.col_map)
        assert mapped["name"] == "Flour"
        assert mapped["purchase_price"] == "1.50"
        assert mapped["purchase_quantity"] == "1000"
        assert mapped["unit_code"] == "g"
        assert conf == 1.0
        assert flags == []

    def test_missing_price(self):
        row = {"Ingredient": "Sugar", "Price": "", "Qty": "500", "Unit": "g"}
        mapped, conf, flags = score_row(row, self.col_map)
        assert "missing_price" in flags
        assert conf < 1.0

    def test_missing_name(self):
        row = {"Ingredient": "", "Price": "2.00", "Qty": "500", "Unit": "g"}
        mapped, conf, flags = score_row(row, self.col_map)
        assert "missing_name" in flags


# ── import_validator ──────────────────────────────────────────────────────────

class TestValidateIngredientRow:
    def test_valid_row(self):
        row = {"name": "Plain Flour", "purchase_price": "1.50", "purchase_quantity": "1000", "unit_code": "g"}
        result = validate_ingredient_row(row)
        assert result.is_valid is True
        assert result.errors == []

    def test_missing_name_fails(self):
        row = {"name": None, "purchase_price": "1.50", "purchase_quantity": "1000", "unit_code": "g"}
        result = validate_ingredient_row(row)
        assert result.is_valid is False
        assert any("name" in e for e in result.errors)

    def test_negative_price_fails(self):
        row = {"name": "Butter", "purchase_price": "-1.00", "purchase_quantity": "500", "unit_code": "g"}
        result = validate_ingredient_row(row)
        assert result.is_valid is False

    def test_zero_quantity_fails(self):
        row = {"name": "Eggs", "purchase_price": "3.00", "purchase_quantity": "0", "unit_code": "piece"}
        result = validate_ingredient_row(row)
        assert result.is_valid is False

    def test_missing_price_warns(self):
        row = {"name": "Salt", "purchase_price": None, "purchase_quantity": "500", "unit_code": "g"}
        result = validate_ingredient_row(row)
        assert result.is_valid is True
        assert result.warnings

    def test_unrecognised_unit_warns(self):
        row = {"name": "Vanilla", "purchase_price": "5.00", "purchase_quantity": "100", "unit_code": "splash"}
        result = validate_ingredient_row(row)
        assert result.is_valid is True
        assert any("unit" in w.lower() for w in result.warnings)

    def test_waste_out_of_range(self):
        row = {"name": "Nut", "purchase_price": "2.00", "purchase_quantity": "200", "unit_code": "g", "waste_percent": "150"}
        result = validate_ingredient_row(row)
        assert result.is_valid is False


class TestValidatePackagingRow:
    def test_valid_packaging(self):
        row = {"name": "Cake Box", "purchase_price": "0.50", "purchase_quantity": "50", "unit_code": "piece"}
        result = validate_packaging_row(row)
        assert result.is_valid is True

    def test_missing_name_fails(self):
        row = {"name": None, "purchase_price": "0.50"}
        result = validate_packaging_row(row)
        assert result.is_valid is False


# ── spreadsheet_importer ──────────────────────────────────────────────────────

def _make_xlsx(sheets: dict[str, list[list]]) -> bytes:
    wb = openpyxl.Workbook()
    for i, (name, rows) in enumerate(sheets.items()):
        ws = wb.active if i == 0 else wb.create_sheet(name)
        if i == 0:
            ws.title = name
        for row in rows:
            ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_csv(rows: list[list]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


class TestParseXlsx:
    def test_basic_ingredient_sheet(self):
        data = _make_xlsx({
            "Ingredients": [
                ["Ingredient Name", "Purchase Price", "Purchase Quantity", "Unit"],
                ["Plain Flour", 1.50, 1000, "g"],
                ["Caster Sugar", 1.20, 1000, "g"],
                ["Butter", 2.50, 500, "g"],
            ]
        })
        sections = parse_xlsx(data)
        assert len(sections) == 1
        assert sections[0].section_type == "ingredients"
        assert len(sections[0].rows) == 3
        assert sections[0].rows[0].mapped["name"] == "Plain Flour"

    def test_high_confidence_all_columns(self):
        data = _make_xlsx({
            "Sheet1": [
                ["Ingredient Name", "Purchase Price", "Purchase Quantity", "Unit"],
                ["Eggs", 3.00, 6, "piece"],
            ]
        })
        sections = parse_xlsx(data)
        assert sections[0].confidence >= 0.90

    def test_sample_sheet_flagged(self):
        data = _make_xlsx({
            "Template": [
                ["Ingredient", "Price", "Qty", "Unit"],
                ["Salmon", 5.00, 200, "g"],
            ]
        })
        sections = parse_xlsx(data)
        assert sections[0].is_sample is True

    def test_empty_rows_skipped(self):
        data = _make_xlsx({
            "Ingredients": [
                ["Ingredient Name", "Purchase Price", "Qty", "Unit"],
                ["Flour", 1.50, 1000, "g"],
                ["", "", "", ""],
                ["Sugar", 1.20, 500, "g"],
            ]
        })
        sections = parse_xlsx(data)
        assert len(sections[0].rows) == 2

    def test_multi_sheet(self):
        data = _make_xlsx({
            "Ingredients": [
                ["Ingredient Name", "Purchase Price", "Qty", "Unit"],
                ["Flour", 1.50, 1000, "g"],
            ],
            "Packaging": [
                ["Packaging Item", "Cost", "Quantity", "Unit"],
                ["Cake Box", 0.50, 1, "piece"],
            ],
        })
        sections = parse_xlsx(data)
        assert len(sections) == 2


class TestParseCsv:
    def test_basic_csv(self):
        data = _make_csv([
            ["Ingredient Name", "Purchase Price", "Purchase Quantity", "Unit"],
            ["Plain Flour", "1.50", "1000", "g"],
            ["Caster Sugar", "1.20", "1000", "g"],
        ])
        sections = parse_csv(data)
        assert len(sections) == 1
        assert len(sections[0].rows) == 2
        assert sections[0].rows[0].mapped["name"] == "Plain Flour"

    def test_currency_in_price(self):
        data = _make_csv([
            ["Ingredient", "Price", "Qty", "Unit"],
            ["Butter", "£2.50", "500", "g"],
        ])
        sections = parse_csv(data)
        assert sections[0].rows[0].mapped["purchase_price"] == "2.50"

    def test_empty_csv_returns_no_sections(self):
        data = b""
        sections = parse_csv(data)
        assert sections == []
