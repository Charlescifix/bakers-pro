"""Label data assembly and HTML generation — pure data layer, no PDF rendering."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from html import escape

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, TenantIsolationError
from app.models.allergen import Allergen, IngredientAllergen
from app.models.ingredient import Ingredient
from app.models.label import Label
from app.models.product import Product, ProductVariant
from app.models.recipe import Recipe, RecipeItem, RecipeVersion
from app.models.tenant import Tenant
from app.schemas.allergen import AllergenMatrixCell, AllergenMatrixOut, AllergenMatrixRow
from app.schemas.label import GenerateLabelRequest, LabelDataOut


# ── allergen matrix ────────────────────────────────────────────────────────────

def get_allergen_matrix(db: Session, tenant_id: uuid.UUID) -> AllergenMatrixOut:
    all_allergens = db.query(Allergen).order_by(Allergen.name).all()
    variants = (
        db.query(ProductVariant)
        .join(Product, Product.id == ProductVariant.product_id)
        .filter(Product.tenant_id == tenant_id)
        .all()
    )

    rows: list[AllergenMatrixRow] = []
    for pv in variants:
        recipe_id = pv.recipe_id
        if not recipe_id:
            continue
        active_version = (
            db.query(RecipeVersion)
            .filter(RecipeVersion.recipe_id == recipe_id, RecipeVersion.status == "active")
            .first()
        )
        if not active_version:
            continue

        recipe_items = db.query(RecipeItem).filter(RecipeItem.recipe_version_id == active_version.id).all()
        ingredient_ids = [ri.ingredient_id for ri in recipe_items if ri.ingredient_id]

        # Build allergen status per allergen for this variant
        cells: list[AllergenMatrixCell] = []
        for allergen in all_allergens:
            # Find worst status across all ingredients in recipe
            links = (
                db.query(IngredientAllergen)
                .filter(
                    IngredientAllergen.ingredient_id.in_(ingredient_ids),
                    IngredientAllergen.allergen_id == allergen.id,
                )
                .all()
            )
            status = _worst_status([lnk.contains_status for lnk in links])
            cells.append(AllergenMatrixCell(
                allergen_id=allergen.id,
                allergen_name=allergen.name,
                status=status,
            ))

        product = db.query(Product).filter(Product.id == pv.product_id).first()
        rows.append(AllergenMatrixRow(
            variant_id=pv.id,
            product_name=product.name if product else "Unknown",
            variant_name=pv.name or "",
            allergens=cells,
        ))

    return AllergenMatrixOut(
        allergen_names=[a.name for a in all_allergens],
        rows=rows,
    )


def _worst_status(statuses: list[str]) -> str:
    """Return the most severe allergen status from a list."""
    priority = {"contains": 0, "may_contain": 1, "unknown": 2, "free": 3}
    if not statuses:
        return "free"
    return min(statuses, key=lambda s: priority.get(s, 2))


# ── label generation ──────────────────────────────────────────────────────────

def generate_label(
    db: Session, tenant_id: uuid.UUID, payload: GenerateLabelRequest
) -> LabelDataOut:
    pv = db.query(ProductVariant).filter(ProductVariant.id == payload.product_variant_id).first()
    if not pv:
        raise NotFoundError(f"ProductVariant {payload.product_variant_id} not found")

    product = db.query(Product).filter(Product.id == pv.product_id).first()
    if not product or product.tenant_id != tenant_id:
        raise TenantIsolationError()

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    recipe_id = pv.recipe_id or (product.default_recipe_id if product else None)
    recipe: Recipe | None = db.query(Recipe).filter(Recipe.id == recipe_id).first() if recipe_id else None

    ingredient_names: list[str] = []
    allergens_contains: list[str] = []
    allergens_may_contain: list[str] = []

    if recipe:
        active_version = (
            db.query(RecipeVersion)
            .filter(RecipeVersion.recipe_id == recipe_id, RecipeVersion.status == "active")
            .first()
        )
        if active_version:
            recipe_items = db.query(RecipeItem).filter(RecipeItem.recipe_version_id == active_version.id).all()
            seen_allergens: set[str] = set()
            for ri in recipe_items:
                if ri.ingredient_id:
                    ing = db.query(Ingredient).filter(Ingredient.id == ri.ingredient_id).first()
                    if ing:
                        ingredient_names.append(ing.name)
                        links = (
                            db.query(IngredientAllergen)
                            .filter(IngredientAllergen.ingredient_id == ing.id)
                            .all()
                        )
                        for lnk in links:
                            allergen = db.query(Allergen).filter(Allergen.id == lnk.allergen_id).first()
                            if allergen and allergen.name not in seen_allergens:
                                seen_allergens.add(allergen.name)
                                if lnk.contains_status == "contains":
                                    allergens_contains.append(allergen.name)
                                elif lnk.contains_status == "may_contain":
                                    allergens_may_contain.append(allergen.name)

    label_data = LabelDataOut(
        product_name=product.name,
        variant_name=pv.name or "",
        label_type=payload.label_type,
        ingredients=ingredient_names,
        allergens_contains=allergens_contains,
        allergens_may_contain=allergens_may_contain,
        storage_instruction=recipe.storage_instruction if recipe else None,
        reheating_instruction=None,
        shelf_life_days=None,
        batch_number=payload.batch_number,
        best_before_date=payload.best_before_date,
        bakery_name=tenant.name if tenant else "",
        fsa_rating=tenant.fsa_rating_value if tenant else None,
        template_html=_render_label_html(
            product_name=product.name,
            variant_name=pv.name or "",
            label_type=payload.label_type,
            ingredient_names=ingredient_names,
            allergens_contains=allergens_contains,
            allergens_may_contain=allergens_may_contain,
            storage_instruction=recipe.storage_instruction if recipe else None,
            batch_number=payload.batch_number,
            best_before_date=payload.best_before_date,
            bakery_name=tenant.name if tenant else "",
            fsa_rating=tenant.fsa_rating_value if tenant else None,
        ),
    )

    # Persist generated label
    existing = (
        db.query(Label)
        .filter(
            Label.product_variant_id == payload.product_variant_id,
            Label.tenant_id == tenant_id,
            Label.label_type == payload.label_type,
        )
        .first()
    )
    if existing:
        existing.template_html = label_data.template_html
        existing.last_generated_at = datetime.now(timezone.utc)
    else:
        lbl = Label(
            tenant_id=tenant_id,
            product_variant_id=payload.product_variant_id,
            label_type=payload.label_type,
            template_html=label_data.template_html,
            last_generated_at=datetime.now(timezone.utc),
        )
        db.add(lbl)
    db.flush()
    return label_data


def _render_label_html(
    product_name: str,
    variant_name: str,
    label_type: str,
    ingredient_names: list[str],
    allergens_contains: list[str],
    allergens_may_contain: list[str],
    storage_instruction: str | None,
    batch_number: str | None,
    best_before_date: str | None,
    bakery_name: str,
    fsa_rating: str | None,
) -> str:
    """Build a minimal print-ready HTML label string."""
    title = escape(f"{product_name} {variant_name}".strip())

    ingredients_html = ""
    if ingredient_names:
        items_str = escape(", ".join(ingredient_names))
        ingredients_html = f"<p><strong>Ingredients:</strong> {items_str}</p>"

    allergen_html = ""
    if allergens_contains:
        bold_names = ", ".join(f"<strong>{escape(a)}</strong>" for a in allergens_contains)
        allergen_html += f"<p><strong>Contains:</strong> {bold_names}</p>"
    if allergens_may_contain:
        names = escape(", ".join(allergens_may_contain))
        allergen_html += f"<p><em>May contain: {names}</em></p>"
    if not allergens_contains and not allergens_may_contain:
        allergen_html = "<p>No declared allergens.</p>"

    storage_html = f"<p><strong>Storage:</strong> {escape(storage_instruction)}</p>" if storage_instruction else ""
    batch_html = f"<p><strong>Batch:</strong> {escape(batch_number)}</p>" if batch_number else ""
    bb_html = f"<p><strong>Best before:</strong> {escape(best_before_date)}</p>" if best_before_date else ""
    fsa_html = f"<p><small>FSA Hygiene Rating: {escape(fsa_rating)}</small></p>" if fsa_rating else ""
    bakery_html = f"<p><strong>{escape(bakery_name)}</strong></p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<style>
body{{font-family:Arial,sans-serif;font-size:11px;max-width:8cm;padding:4mm;}}
strong{{font-weight:bold;}}
p{{margin:2px 0;}}
</style>
</head>
<body>
<h2 style="font-size:13px;margin:0 0 4px">{title}</h2>
{ingredients_html}
{allergen_html}
{storage_html}
{batch_html}
{bb_html}
{bakery_html}
{fsa_html}
</body>
</html>"""


# ── seed allergens ─────────────────────────────────────────────────────────────

def seed_allergens(db: Session) -> int:
    from app.models.allergen import Allergen, UK_ALLERGENS
    count = 0
    for name, description in UK_ALLERGENS:
        exists = db.query(Allergen).filter(Allergen.name == name).first()
        if not exists:
            db.add(Allergen(name=name, description=description))
            count += 1
    db.flush()
    return count
