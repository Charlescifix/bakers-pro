import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.calculators.cost_engine import unit_cost as calc_unit_cost
from app.core.errors import NotFoundError, TenantIsolationError
from app.core.units import convert_to_base
from app.models.ingredient import Ingredient, IngredientPriceHistory
from app.schemas.ingredient import IngredientCreate, IngredientUpdate, PriceUpdateRequest


def _compute_unit_cost_base(price: Decimal, qty: Decimal, unit_code: str) -> Decimal:
    qty_base = convert_to_base(qty, unit_code)
    return calc_unit_cost(price, qty_base)


def create_ingredient(db: Session, tenant_id: uuid.UUID, data: IngredientCreate) -> Ingredient:
    unit_cost_base = _compute_unit_cost_base(
        data.current_purchase_price,
        data.current_purchase_quantity,
        data.current_purchase_unit_code,
    )
    ingredient = Ingredient(
        tenant_id=tenant_id,
        name=data.name,
        category_id=data.category_id,
        default_unit_code=data.default_unit_code,
        density_g_per_ml=data.density_g_per_ml,
        is_perishable=data.is_perishable,
        shelf_life_days=data.shelf_life_days,
        storage_instruction=data.storage_instruction,
        allergen_notes=data.allergen_notes,
        supplier_id=data.supplier_id,
        current_purchase_price=data.current_purchase_price,
        current_purchase_quantity=data.current_purchase_quantity,
        current_purchase_unit_code=data.current_purchase_unit_code,
        current_unit_cost_base=unit_cost_base,
        waste_percent_default=data.waste_percent_default,
        reorder_level=data.reorder_level,
        notes=data.notes,
    )
    db.add(ingredient)
    # Record initial price history
    _add_price_history(db, ingredient, "manual")
    db.commit()
    db.refresh(ingredient)
    return ingredient


def get_ingredient(db: Session, tenant_id: uuid.UUID, ingredient_id: uuid.UUID) -> Ingredient:
    obj = db.query(Ingredient).filter(
        Ingredient.id == ingredient_id,
        Ingredient.tenant_id == tenant_id,
    ).first()
    if not obj:
        raise NotFoundError("Ingredient", str(ingredient_id))
    return obj


def list_ingredients(
    db: Session, tenant_id: uuid.UUID, active_only: bool = True
) -> list[Ingredient]:
    q = db.query(Ingredient).filter(Ingredient.tenant_id == tenant_id)
    if active_only:
        q = q.filter(Ingredient.is_active == True)
    return q.order_by(Ingredient.name).all()


def update_ingredient(
    db: Session, tenant_id: uuid.UUID, ingredient_id: uuid.UUID, data: IngredientUpdate
) -> Ingredient:
    obj = get_ingredient(db, tenant_id, ingredient_id)
    changed_price = False
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
        if field in ("current_purchase_price", "current_purchase_quantity", "current_purchase_unit_code"):
            changed_price = True
    if changed_price:
        obj.current_unit_cost_base = _compute_unit_cost_base(
            obj.current_purchase_price,
            obj.current_purchase_quantity,
            obj.current_purchase_unit_code,
        )
        _add_price_history(db, obj, "manual")
    db.commit()
    db.refresh(obj)
    return obj


def delete_ingredient(db: Session, tenant_id: uuid.UUID, ingredient_id: uuid.UUID) -> None:
    obj = get_ingredient(db, tenant_id, ingredient_id)
    obj.is_active = False
    db.commit()


def add_price(
    db: Session, tenant_id: uuid.UUID, ingredient_id: uuid.UUID, data: PriceUpdateRequest
) -> IngredientPriceHistory:
    obj = get_ingredient(db, tenant_id, ingredient_id)
    unit_cost_base = _compute_unit_cost_base(
        data.purchase_price, data.purchase_quantity, data.purchase_unit_code
    )
    # Update current price on ingredient
    obj.current_purchase_price = data.purchase_price
    obj.current_purchase_quantity = data.purchase_quantity
    obj.current_purchase_unit_code = data.purchase_unit_code
    obj.current_unit_cost_base = unit_cost_base
    # Record history
    history = IngredientPriceHistory(
        tenant_id=tenant_id,
        ingredient_id=ingredient_id,
        supplier_id=data.supplier_id,
        purchase_price=data.purchase_price,
        purchase_quantity=data.purchase_quantity,
        purchase_unit_code=data.purchase_unit_code,
        unit_cost_base=unit_cost_base,
        effective_date=data.effective_date or datetime.now(timezone.utc),
        source="manual",
        receipt_file_url=data.receipt_file_url,
        notes=data.notes,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_price_history(
    db: Session, tenant_id: uuid.UUID, ingredient_id: uuid.UUID
) -> list[IngredientPriceHistory]:
    get_ingredient(db, tenant_id, ingredient_id)
    return (
        db.query(IngredientPriceHistory)
        .filter(IngredientPriceHistory.ingredient_id == ingredient_id)
        .order_by(IngredientPriceHistory.effective_date.desc())
        .all()
    )


def list_low_stock(db: Session, tenant_id: uuid.UUID) -> list[Ingredient]:
    results = []
    for ing in list_ingredients(db, tenant_id):
        if ing.reorder_level is not None:
            # low stock based on reorder_level — inventory tracking will refine this later
            results.append(ing)
    return results


def _add_price_history(db: Session, ingredient: Ingredient, source: str) -> None:
    history = IngredientPriceHistory(
        tenant_id=ingredient.tenant_id,
        ingredient_id=ingredient.id,
        purchase_price=ingredient.current_purchase_price,
        purchase_quantity=ingredient.current_purchase_quantity,
        purchase_unit_code=ingredient.current_purchase_unit_code,
        unit_cost_base=ingredient.current_unit_cost_base,
        effective_date=datetime.now(timezone.utc),
        source=source,
    )
    db.add(history)
