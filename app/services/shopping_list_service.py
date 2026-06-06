import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, TenantIsolationError
from app.core.money import q_money
from app.core.units import convert_to_base
from app.models.ingredient import Ingredient
from app.models.order import Order, OrderItem
from app.models.packaging import PackagingItem
from app.models.product import ProductVariant
from app.models.recipe import Recipe, RecipeItem, RecipePackagingRule, RecipeVersion
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.schemas.shopping_list import GenerateShoppingListRequest


def generate_shopping_list(
    db: Session, tenant_id: uuid.UUID, payload: GenerateShoppingListRequest
) -> ShoppingList:
    # Aggregate ingredient and packaging needs across all orders
    ingredient_totals: dict[uuid.UUID, Decimal] = {}
    packaging_totals: dict[uuid.UUID, Decimal] = {}

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

            recipe = db.query(Recipe).filter(Recipe.id == pv.recipe_id).first()
            if not recipe:
                continue

            active_version = (
                db.query(RecipeVersion)
                .filter(
                    RecipeVersion.recipe_id == pv.recipe_id,
                    RecipeVersion.status == "active",
                )
                .first()
            )
            if not active_version:
                continue

            base_yield = recipe.base_yield_quantity
            multiplier = pv.quantity_multiplier or Decimal("1")
            total_items = Decimal(str(oi.quantity)) * multiplier

            import math
            batches_needed = math.ceil(float(total_items) / float(base_yield)) if base_yield else 1

            recipe_items = (
                db.query(RecipeItem)
                .filter(RecipeItem.recipe_version_id == active_version.id)
                .all()
            )
            for ri in recipe_items:
                scaled = ri.quantity_used * Decimal(str(batches_needed))
                base_qty = convert_to_base(scaled, ri.unit_code)
                if ri.ingredient_id:
                    ingredient_totals[ri.ingredient_id] = (
                        ingredient_totals.get(ri.ingredient_id, Decimal("0")) + base_qty
                    )

            packaging_rules = (
                db.query(RecipePackagingRule)
                .filter(
                    RecipePackagingRule.recipe_id == pv.recipe_id,
                    RecipePackagingRule.tenant_id == tenant_id,
                )
                .all()
            )
            for rule in packaging_rules:
                if rule.rule_type == "per_batch":
                    qty = rule.quantity_per_batch * Decimal(str(batches_needed))
                elif rule.rule_type == "per_item":
                    qty = rule.quantity_per_item * total_items
                else:  # per_order
                    qty = rule.quantity_per_batch or Decimal("1")
                packaging_totals[rule.packaging_item_id] = (
                    packaging_totals.get(rule.packaging_item_id, Decimal("0")) + qty
                )

    shopping_list = ShoppingList(
        tenant_id=tenant_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    total_cost = Decimal("0")

    for ingredient_id, required_qty_base in ingredient_totals.items():
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            continue
        stock = ingredient.reorder_level or Decimal("0")
        to_buy = max(Decimal("0"), required_qty_base - stock)
        unit_cost_base = ingredient.current_unit_cost_base or Decimal("0")
        estimated = q_money(to_buy * unit_cost_base)
        total_cost += estimated

        shopping_list.list_items.append(
            ShoppingListItem(
                ingredient_id=ingredient_id,
                item_name=ingredient.name,
                item_type="ingredient",
                required_quantity=required_qty_base,
                unit_code="g" if ingredient.default_unit_code in ("g", "kg") else ingredient.default_unit_code,
                current_stock_quantity=stock,
                quantity_to_buy=to_buy,
                estimated_cost=estimated,
                supplier_id=ingredient.supplier_id,
            )
        )

    for packaging_id, required_qty in packaging_totals.items():
        pkg = db.query(PackagingItem).filter(PackagingItem.id == packaging_id).first()
        if not pkg:
            continue
        stock = pkg.current_stock_quantity or Decimal("0")
        to_buy = max(Decimal("0"), required_qty - stock)
        unit_cost = pkg.unit_cost or Decimal("0")
        estimated = q_money(to_buy * unit_cost)
        total_cost += estimated

        shopping_list.list_items.append(
            ShoppingListItem(
                packaging_item_id=packaging_id,
                item_name=pkg.name,
                item_type="packaging",
                required_quantity=required_qty,
                unit_code=pkg.purchase_unit_code or "piece",
                current_stock_quantity=stock,
                quantity_to_buy=to_buy,
                estimated_cost=estimated,
                supplier_id=pkg.supplier_id,
            )
        )

    shopping_list.total_estimated_cost = q_money(total_cost)
    db.add(shopping_list)
    db.flush()
    db.refresh(shopping_list)
    return shopping_list


def list_shopping_lists(db: Session, tenant_id: uuid.UUID) -> list[ShoppingList]:
    return (
        db.query(ShoppingList)
        .filter(ShoppingList.tenant_id == tenant_id)
        .order_by(ShoppingList.created_at.desc())
        .all()
    )


def get_shopping_list(db: Session, tenant_id: uuid.UUID, list_id: uuid.UUID) -> ShoppingList:
    sl = db.query(ShoppingList).filter(ShoppingList.id == list_id).first()
    if not sl:
        raise NotFoundError(f"ShoppingList {list_id} not found")
    if sl.tenant_id != tenant_id:
        raise TenantIsolationError()
    return sl


def mark_purchased(
    db: Session, tenant_id: uuid.UUID, list_id: uuid.UUID, item_ids: list[uuid.UUID]
) -> ShoppingList:
    sl = get_shopping_list(db, tenant_id, list_id)
    remaining = [item for item in sl.list_items if item.id not in item_ids]
    if not remaining:
        sl.status = "purchased"
    db.flush()
    return sl
