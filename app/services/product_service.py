import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.calculators.price_engine import compute_variant_pricing, VariantPricingResult
from app.calculators.recipe_calculator import compute_recipe_cost
from app.core.errors import NotFoundError, ValidationError
from app.models.ingredient import Ingredient
from app.models.packaging import PackagingItem
from app.models.product import Product, ProductVariant
from app.models.recipe import Recipe, RecipeVersion
from app.models.tenant import Tenant
from app.schemas.product import ProductCreate, ProductUpdate, VariantCreate, VariantUpdate


# ---------- helpers ----------

def _get_active_version(db: Session, recipe: Recipe) -> RecipeVersion | None:
    return (
        db.query(RecipeVersion)
        .filter(RecipeVersion.recipe_id == recipe.id, RecipeVersion.status == "active")
        .first()
    )


def _tenant_labour_rate(db: Session, tenant_id: uuid.UUID) -> Decimal:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant.default_labour_rate_per_hour if tenant else Decimal("10.00")


# ---------- Product CRUD ----------

def create_product(db: Session, tenant_id: uuid.UUID, data: ProductCreate) -> Product:
    product = Product(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        category=data.category,
        default_recipe_id=data.default_recipe_id,
        image_url=data.image_url,
    )
    db.add(product)
    db.flush()

    for v in data.variants:
        db.add(ProductVariant(
            product_id=product.id,
            name=v.name,
            recipe_id=v.recipe_id or data.default_recipe_id,
            quantity_multiplier=v.quantity_multiplier,
            minimum_order_quantity=v.minimum_order_quantity,
            current_selling_price=v.current_selling_price,
            desired_margin_percent=v.desired_margin_percent,
            channel_default_price_rules=v.channel_default_price_rules,
            sku=v.sku,
        ))

    db.commit()
    db.refresh(product)
    return product


def get_product(db: Session, tenant_id: uuid.UUID, product_id: uuid.UUID) -> Product:
    obj = db.query(Product).filter(
        Product.id == product_id, Product.tenant_id == tenant_id
    ).first()
    if not obj:
        raise NotFoundError("Product", str(product_id))
    return obj


def list_products(db: Session, tenant_id: uuid.UUID, active_only: bool = True) -> list[Product]:
    q = db.query(Product).filter(Product.tenant_id == tenant_id)
    if active_only:
        q = q.filter(Product.is_active == True)
    return q.order_by(Product.name).all()


def update_product(
    db: Session, tenant_id: uuid.UUID, product_id: uuid.UUID, data: ProductUpdate
) -> Product:
    obj = get_product(db, tenant_id, product_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


# ---------- Variant CRUD ----------

def add_variant(
    db: Session, tenant_id: uuid.UUID, product_id: uuid.UUID, data: VariantCreate
) -> ProductVariant:
    product = get_product(db, tenant_id, product_id)
    variant = ProductVariant(
        product_id=product.id,
        name=data.name,
        recipe_id=data.recipe_id or product.default_recipe_id,
        quantity_multiplier=data.quantity_multiplier,
        minimum_order_quantity=data.minimum_order_quantity,
        current_selling_price=data.current_selling_price,
        desired_margin_percent=data.desired_margin_percent,
        channel_default_price_rules=data.channel_default_price_rules,
        sku=data.sku,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def get_variant(db: Session, tenant_id: uuid.UUID, variant_id: uuid.UUID) -> ProductVariant:
    variant = (
        db.query(ProductVariant)
        .join(Product, Product.id == ProductVariant.product_id)
        .filter(ProductVariant.id == variant_id, Product.tenant_id == tenant_id)
        .first()
    )
    if not variant:
        raise NotFoundError("ProductVariant", str(variant_id))
    return variant


def update_variant(
    db: Session, tenant_id: uuid.UUID, variant_id: uuid.UUID, data: VariantUpdate
) -> ProductVariant:
    variant = get_variant(db, tenant_id, variant_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(variant, field, value)
    db.commit()
    db.refresh(variant)
    return variant


# ---------- Pricing Summary ----------

def pricing_summary(
    db: Session, tenant_id: uuid.UUID, variant_id: uuid.UUID
) -> dict:
    variant = get_variant(db, tenant_id, variant_id)
    product = db.query(Product).filter(Product.id == variant.product_id).first()

    recipe_id = variant.recipe_id or (product.default_recipe_id if product else None)
    if not recipe_id:
        raise ValidationError("Variant has no recipe assigned.")

    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id, Recipe.tenant_id == tenant_id
    ).first()
    if not recipe:
        raise NotFoundError("Recipe", str(recipe_id))

    version = _get_active_version(db, recipe)
    if not version:
        raise ValidationError("Recipe has no active version.")

    # Build maps
    ingredient_ids = [item.ingredient_id for item in version.items]
    packaging_ids = [r.packaging_item_id for r in recipe.packaging_rules]

    ingredient_map = {
        str(r.id): r
        for r in db.query(Ingredient)
        .filter(Ingredient.id.in_(ingredient_ids), Ingredient.tenant_id == tenant_id)
        .all()
    }
    packaging_map = {
        str(r.id): r
        for r in db.query(PackagingItem)
        .filter(PackagingItem.id.in_(packaging_ids), PackagingItem.tenant_id == tenant_id)
        .all()
    }

    hourly_rate = _tenant_labour_rate(db, tenant_id)
    recipe_cost = compute_recipe_cost(recipe, version, ingredient_map, packaging_map, hourly_rate)

    # Per-item costs from recipe (already per yield unit)
    ing_per_item = recipe_cost.cost_per_item_excl_labour - (
        recipe_cost.total_packaging_cost / recipe.base_yield_quantity
        if recipe.base_yield_quantity > 0 else Decimal("0")
    )
    # More precise: derive from the individual totals
    ing_cost_per_item = (
        recipe_cost.total_ingredient_cost / recipe.base_yield_quantity
        if recipe.base_yield_quantity > 0 else Decimal("0")
    )
    pkg_cost_per_item = (
        recipe_cost.total_packaging_cost / recipe.base_yield_quantity
        if recipe.base_yield_quantity > 0 else Decimal("0")
    )
    lab_cost_per_item = (
        recipe_cost.total_labour_cost / recipe.base_yield_quantity
        if recipe.base_yield_quantity > 0 else Decimal("0")
    )

    pricing = compute_variant_pricing(
        ingredient_cost_per_item=ing_cost_per_item,
        packaging_cost_per_item=pkg_cost_per_item,
        labour_cost_per_item=lab_cost_per_item,
        quantity_multiplier=variant.quantity_multiplier,
        selling_price=variant.current_selling_price,
        desired_margin_pct=variant.desired_margin_percent,
    )

    return {
        "variant_id": str(variant.id),
        "variant_name": variant.name,
        "product_id": str(product.id),
        "product_name": product.name,
        "recipe_id": str(recipe.id),
        "recipe_name": recipe.name,
        "quantity_multiplier": variant.quantity_multiplier,
        "current_selling_price": variant.current_selling_price,
        "desired_margin_percent": variant.desired_margin_percent,
        "minimum_order_quantity": variant.minimum_order_quantity,
        "ingredient_cost": pricing.ingredient_cost,
        "packaging_cost": pricing.packaging_cost,
        "labour_cost": pricing.labour_cost,
        "total_cost_excluding_labour": pricing.total_cost_excluding_labour,
        "total_cost_including_labour": pricing.total_cost_including_labour,
        "gross_profit": pricing.gross_profit,
        "net_profit": pricing.net_profit,
        "food_cost_percent": pricing.food_cost_percent,
        "gross_margin_percent": pricing.gross_margin_percent,
        "net_margin_percent": pricing.net_margin_percent,
        "recommended_price": pricing.recommended_price,
        "recommended_prices": pricing.recommended_prices,
        "margin_status": pricing.margin_status,
        "warnings": pricing.warnings,
    }
