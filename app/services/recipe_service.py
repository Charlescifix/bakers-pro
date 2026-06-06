import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.calculators.recipe_calculator import compute_recipe_cost, scale_recipe_cost, RecipeCostResult
from app.core.errors import NotFoundError, ValidationError
from app.models.ingredient import Ingredient
from app.models.packaging import PackagingItem
from app.models.recipe import Recipe, RecipeVersion, RecipeItem, RecipePackagingRule
from app.models.tenant import Tenant
from app.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeVersionCreate, PackagingRuleCreate


# ---------- helpers ----------

def _get_active_version(db: Session, recipe: Recipe) -> RecipeVersion | None:
    return (
        db.query(RecipeVersion)
        .filter(RecipeVersion.recipe_id == recipe.id, RecipeVersion.status == "active")
        .first()
    )


def _build_ingredient_map(db: Session, tenant_id: uuid.UUID, ingredient_ids: list[uuid.UUID]) -> dict:
    rows = (
        db.query(Ingredient)
        .filter(Ingredient.id.in_(ingredient_ids), Ingredient.tenant_id == tenant_id)
        .all()
    )
    return {str(r.id): r for r in rows}


def _build_packaging_map(db: Session, tenant_id: uuid.UUID, packaging_ids: list[uuid.UUID]) -> dict:
    rows = (
        db.query(PackagingItem)
        .filter(PackagingItem.id.in_(packaging_ids), PackagingItem.tenant_id == tenant_id)
        .all()
    )
    return {str(r.id): r for r in rows}


def _tenant_labour_rate(db: Session, tenant_id: uuid.UUID) -> Decimal:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant:
        return tenant.default_labour_rate_per_hour
    return Decimal("10.00")


# ---------- CRUD ----------

def create_recipe(
    db: Session, tenant_id: uuid.UUID, user_id: uuid.UUID, data: RecipeCreate
) -> Recipe:
    recipe = Recipe(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        category=data.category,
        base_yield_quantity=data.base_yield_quantity,
        base_yield_unit=data.base_yield_unit,
        prep_time_minutes=data.prep_time_minutes,
        bake_time_minutes=data.bake_time_minutes,
        cooling_time_minutes=data.cooling_time_minutes,
        labour_minutes_default=data.labour_minutes_default,
        storage_instruction=data.storage_instruction,
        serving_tip=data.serving_tip,
        internal_notes=data.internal_notes,
    )
    db.add(recipe)
    db.flush()

    version = RecipeVersion(
        recipe_id=recipe.id,
        version_number=1,
        status="active",
        effective_from=datetime.now(timezone.utc),
        created_by_user_id=user_id,
    )
    db.add(version)
    db.flush()

    for item_data in data.items:
        db.add(RecipeItem(
            recipe_version_id=version.id,
            ingredient_id=item_data.ingredient_id,
            quantity_used=item_data.quantity_used,
            unit_code=item_data.unit_code,
            waste_percent_override=item_data.waste_percent_override,
            preparation_note=item_data.preparation_note,
            is_optional=item_data.is_optional,
            variant_group=item_data.variant_group,
        ))

    db.commit()
    db.refresh(recipe)
    return recipe


def get_recipe(db: Session, tenant_id: uuid.UUID, recipe_id: uuid.UUID) -> Recipe:
    obj = db.query(Recipe).filter(
        Recipe.id == recipe_id, Recipe.tenant_id == tenant_id
    ).first()
    if not obj:
        raise NotFoundError("Recipe", str(recipe_id))
    return obj


def list_recipes(db: Session, tenant_id: uuid.UUID, active_only: bool = True) -> list[Recipe]:
    q = db.query(Recipe).filter(Recipe.tenant_id == tenant_id)
    if active_only:
        q = q.filter(Recipe.is_active == True)
    return q.order_by(Recipe.name).all()


def update_recipe(
    db: Session, tenant_id: uuid.UUID, recipe_id: uuid.UUID, data: RecipeUpdate
) -> Recipe:
    obj = get_recipe(db, tenant_id, recipe_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_recipe(db: Session, tenant_id: uuid.UUID, recipe_id: uuid.UUID) -> None:
    obj = get_recipe(db, tenant_id, recipe_id)
    obj.is_active = False
    db.commit()


# ---------- Versions ----------

def create_version(
    db: Session,
    tenant_id: uuid.UUID,
    recipe_id: uuid.UUID,
    user_id: uuid.UUID,
    data: RecipeVersionCreate,
) -> RecipeVersion:
    recipe = get_recipe(db, tenant_id, recipe_id)

    # Get next version number
    last = (
        db.query(RecipeVersion)
        .filter(RecipeVersion.recipe_id == recipe.id)
        .order_by(RecipeVersion.version_number.desc())
        .first()
    )
    next_num = (last.version_number + 1) if last else 1

    version = RecipeVersion(
        recipe_id=recipe.id,
        version_number=next_num,
        status="draft",
        created_by_user_id=user_id,
        notes=data.notes,
    )
    db.add(version)
    db.flush()

    for item_data in data.items:
        db.add(RecipeItem(
            recipe_version_id=version.id,
            ingredient_id=item_data.ingredient_id,
            quantity_used=item_data.quantity_used,
            unit_code=item_data.unit_code,
            waste_percent_override=item_data.waste_percent_override,
            preparation_note=item_data.preparation_note,
            is_optional=item_data.is_optional,
            variant_group=item_data.variant_group,
        ))

    db.commit()
    db.refresh(version)
    return version


def activate_version(
    db: Session, tenant_id: uuid.UUID, recipe_id: uuid.UUID, version_id: uuid.UUID
) -> RecipeVersion:
    recipe = get_recipe(db, tenant_id, recipe_id)
    version = db.query(RecipeVersion).filter(
        RecipeVersion.id == version_id, RecipeVersion.recipe_id == recipe.id
    ).first()
    if not version:
        raise NotFoundError("RecipeVersion", str(version_id))

    # Archive current active
    db.query(RecipeVersion).filter(
        RecipeVersion.recipe_id == recipe.id, RecipeVersion.status == "active"
    ).update({"status": "archived"})

    version.status = "active"
    version.effective_from = datetime.now(timezone.utc)
    db.commit()
    db.refresh(version)
    return version


# ---------- Cost Preview ----------

def cost_preview(
    db: Session, tenant_id: uuid.UUID, recipe_id: uuid.UUID
) -> RecipeCostResult:
    recipe = get_recipe(db, tenant_id, recipe_id)
    version = _get_active_version(db, recipe)
    if not version:
        raise ValidationError("Recipe has no active version. Create and activate a version first.")

    ingredient_ids = [item.ingredient_id for item in version.items]
    packaging_ids = [r.packaging_item_id for r in recipe.packaging_rules]

    ingredient_map = _build_ingredient_map(db, tenant_id, ingredient_ids)
    packaging_map = _build_packaging_map(db, tenant_id, packaging_ids)
    hourly_rate = _tenant_labour_rate(db, tenant_id)

    return compute_recipe_cost(recipe, version, ingredient_map, packaging_map, hourly_rate)


# ---------- Scale ----------

def scale(
    db: Session, tenant_id: uuid.UUID, recipe_id: uuid.UUID, order_quantity: Decimal
) -> dict:
    recipe = get_recipe(db, tenant_id, recipe_id)
    version = _get_active_version(db, recipe)
    if not version:
        raise ValidationError("Recipe has no active version.")

    ingredient_ids = [item.ingredient_id for item in version.items]
    packaging_ids = [r.packaging_item_id for r in recipe.packaging_rules]

    ingredient_map = _build_ingredient_map(db, tenant_id, ingredient_ids)
    packaging_map = _build_packaging_map(db, tenant_id, packaging_ids)
    hourly_rate = _tenant_labour_rate(db, tenant_id)

    return scale_recipe_cost(recipe, version, ingredient_map, packaging_map, hourly_rate, order_quantity)


# ---------- Packaging rules ----------

def add_packaging_rule(
    db: Session, tenant_id: uuid.UUID, recipe_id: uuid.UUID, data: PackagingRuleCreate
) -> RecipePackagingRule:
    recipe = get_recipe(db, tenant_id, recipe_id)
    rule = RecipePackagingRule(
        tenant_id=tenant_id,
        recipe_id=recipe.id,
        packaging_item_id=data.packaging_item_id,
        rule_type=data.rule_type,
        quantity_per_item=data.quantity_per_item,
        quantity_per_batch=data.quantity_per_batch,
        notes=data.notes,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
