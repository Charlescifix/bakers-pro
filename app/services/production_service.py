import math
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, TenantIsolationError
from app.models.order import Order, OrderItem
from app.models.production import ProductionBatch, ProductionBatchItem
from app.models.product import ProductVariant
from app.models.recipe import Recipe, RecipeVersion
from app.schemas.production import (
    GenerateProductionPlanRequest,
    ProductionBatchUpdate,
    ProductionChecklistItem,
    ProductionPlanResponse,
)


def _next_batch_number(db: Session, tenant_id: uuid.UUID) -> str:
    count = db.query(ProductionBatch).filter(ProductionBatch.tenant_id == tenant_id).count()
    return f"BATCH-{count + 1:05d}"


def generate_production_plan(
    db: Session, tenant_id: uuid.UUID, payload: GenerateProductionPlanRequest
) -> ProductionPlanResponse:
    # Gather all order items for specified orders
    # Group by recipe_id, accumulate quantities
    recipe_groups: dict[uuid.UUID, list[tuple[OrderItem, int]]] = {}

    for order_id in payload.order_ids:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise NotFoundError(f"Order {order_id} not found")
        if order.tenant_id != tenant_id:
            raise TenantIsolationError()

        for oi in order.items:
            pv = db.query(ProductVariant).filter(ProductVariant.id == oi.product_variant_id).first()
            if not pv or not pv.recipe_id:
                continue
            recipe_id = pv.recipe_id
            if recipe_id not in recipe_groups:
                recipe_groups[recipe_id] = []
            recipe_groups[recipe_id].append((oi, oi.quantity))

    batches = []
    checklist = []

    for recipe_id, items_and_qtys in recipe_groups.items():
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            continue

        active_version = (
            db.query(RecipeVersion)
            .filter(
                RecipeVersion.recipe_id == recipe_id,
                RecipeVersion.status == "active",
            )
            .first()
        )

        total_items = sum(qty for _, qty in items_and_qtys)
        base_yield = int(recipe.base_yield_quantity)
        batches_needed = math.ceil(total_items / base_yield) if base_yield > 0 else 1
        planned_yield = Decimal(str(batches_needed * base_yield))

        batch_number = _next_batch_number(db, tenant_id)
        batch = ProductionBatch(
            tenant_id=tenant_id,
            batch_number=batch_number,
            recipe_id=recipe_id,
            planned_yield_quantity=planned_yield,
        )

        for oi, qty in items_and_qtys:
            batch.batch_items.append(
                ProductionBatchItem(
                    order_item_id=oi.id,
                    quantity_allocated=qty,
                )
            )

        db.add(batch)
        db.flush()
        db.refresh(batch)
        batches.append(batch)

        checklist.append(
            ProductionChecklistItem(
                batch_number=batch_number,
                recipe_name=recipe.name,
                batches_required=batches_needed,
                planned_yield_quantity=planned_yield,
                prep_time_minutes=recipe.prep_time_minutes,
                bake_time_minutes=recipe.bake_time_minutes,
                cooling_time_minutes=recipe.cooling_time_minutes,
                labour_minutes=recipe.labour_minutes_default,
                storage_instruction=recipe.storage_instruction,
                serving_tip=recipe.serving_tip,
            )
        )

    return ProductionPlanResponse(batches=batches, checklist=checklist)


def list_batches(db: Session, tenant_id: uuid.UUID) -> list[ProductionBatch]:
    return (
        db.query(ProductionBatch)
        .filter(ProductionBatch.tenant_id == tenant_id)
        .order_by(ProductionBatch.created_at.desc())
        .all()
    )


def get_batch(db: Session, tenant_id: uuid.UUID, batch_id: uuid.UUID) -> ProductionBatch:
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise NotFoundError(f"ProductionBatch {batch_id} not found")
    if batch.tenant_id != tenant_id:
        raise TenantIsolationError()
    return batch


def update_batch(
    db: Session, tenant_id: uuid.UUID, batch_id: uuid.UUID, payload: ProductionBatchUpdate
) -> ProductionBatch:
    batch = get_batch(db, tenant_id, batch_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(batch, field, value)
    db.flush()
    return batch


def get_checklist(db: Session, tenant_id: uuid.UUID) -> list[ProductionChecklistItem]:
    batches = (
        db.query(ProductionBatch)
        .filter(ProductionBatch.tenant_id == tenant_id, ProductionBatch.status.in_(["planned", "in_progress"]))
        .all()
    )
    checklist = []
    for batch in batches:
        recipe = db.query(Recipe).filter(Recipe.id == batch.recipe_id).first()
        if not recipe:
            continue
        base_yield = int(recipe.base_yield_quantity) if recipe.base_yield_quantity else 1
        batches_required = math.ceil(float(batch.planned_yield_quantity) / base_yield) if base_yield > 0 else 1
        checklist.append(
            ProductionChecklistItem(
                batch_number=batch.batch_number,
                recipe_name=recipe.name,
                batches_required=batches_required,
                planned_yield_quantity=batch.planned_yield_quantity,
                prep_time_minutes=recipe.prep_time_minutes,
                bake_time_minutes=recipe.bake_time_minutes,
                cooling_time_minutes=recipe.cooling_time_minutes,
                labour_minutes=recipe.labour_minutes_default,
                storage_instruction=recipe.storage_instruction,
                serving_tip=recipe.serving_tip,
            )
        )
    return checklist
