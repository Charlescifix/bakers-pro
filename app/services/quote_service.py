import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.calculators.quote_calculator import (
    QuoteLineInput,
    QuoteResult,
    compute_quote,
    generate_customer_message,
)
from app.core.errors import NotFoundError, ValidationError, BakerProfitError
from app.models.ingredient import Ingredient
from app.models.packaging import PackagingItem
from app.models.product import Product, ProductVariant
from app.models.quote import Quote, QuoteItem
from app.models.recipe import Recipe, RecipeVersion
from app.models.sales_channel import SalesChannel
from app.models.tenant import Tenant
from app.schemas.quote import QuoteCreate, QuoteUpdate, GenerateMessageRequest


# ---------- helpers ----------

def _tenant_labour_rate(db: Session, tenant_id: uuid.UUID) -> Decimal:
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return t.default_labour_rate_per_hour if t else Decimal("10.00")


def _next_quote_number(db: Session, tenant_id: uuid.UUID) -> str:
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    slug = (t.slug[:4].upper() if t else "BKR")
    count = db.query(Quote).filter(Quote.tenant_id == tenant_id).count()
    return f"{slug}-Q-{(count + 1):05d}"


def _get_active_version(db: Session, recipe: Recipe) -> RecipeVersion | None:
    return (
        db.query(RecipeVersion)
        .filter(RecipeVersion.recipe_id == recipe.id, RecipeVersion.status == "active")
        .first()
    )


def _build_line_inputs(
    db: Session,
    tenant_id: uuid.UUID,
    items_data,
    hourly_rate: Decimal,
) -> list[QuoteLineInput]:
    inputs = []
    for item in items_data:
        variant = (
            db.query(ProductVariant)
            .join(Product, Product.id == ProductVariant.product_id)
            .filter(ProductVariant.id == item.product_variant_id, Product.tenant_id == tenant_id)
            .first()
        )
        if not variant:
            raise NotFoundError("ProductVariant", str(item.product_variant_id))

        product = db.query(Product).filter(Product.id == variant.product_id).first()
        recipe_id = variant.recipe_id or (product.default_recipe_id if product else None)

        recipe = None
        version = None
        ingredient_map = {}
        packaging_map = {}

        if recipe_id:
            recipe = db.query(Recipe).filter(
                Recipe.id == recipe_id, Recipe.tenant_id == tenant_id
            ).first()
            if recipe:
                version = _get_active_version(db, recipe)
                if version:
                    ing_ids = [i.ingredient_id for i in version.items]
                    pkg_ids = [r.packaging_item_id for r in recipe.packaging_rules]
                    ingredient_map = {
                        str(r.id): r
                        for r in db.query(Ingredient)
                        .filter(Ingredient.id.in_(ing_ids), Ingredient.tenant_id == tenant_id)
                        .all()
                    }
                    packaging_map = {
                        str(r.id): r
                        for r in db.query(PackagingItem)
                        .filter(PackagingItem.id.in_(pkg_ids), PackagingItem.tenant_id == tenant_id)
                        .all()
                    }

        inputs.append(QuoteLineInput(
            variant_id=str(variant.id),
            variant_name=variant.name,
            product_name=product.name if product else "Unknown",
            quantity=item.quantity,
            quantity_multiplier=variant.quantity_multiplier,
            desired_margin_percent=variant.desired_margin_percent,
            unit_price_override=item.unit_price_override,
            recipe=recipe,
            recipe_version=version,
            ingredient_map=ingredient_map,
            packaging_map=packaging_map,
            hourly_rate=hourly_rate,
        ))
    return inputs


def _apply_result_to_quote(quote: Quote, result: QuoteResult) -> None:
    quote.total_revenue = result.total_revenue
    quote.total_cost_excluding_labour = result.total_cost_excluding_labour
    quote.total_labour_cost = result.total_labour_cost
    quote.total_channel_fees = result.total_channel_fees
    quote.gross_profit = result.gross_profit
    quote.net_profit = result.net_profit
    quote.food_cost_percent = result.food_cost_percent
    quote.profit_margin_percent = result.profit_margin_percent
    quote.recommendation_status = result.recommendation_status


def _upsert_quote_items(db: Session, quote: Quote, lines) -> None:
    db.query(QuoteItem).filter(QuoteItem.quote_id == quote.id).delete()
    for line in lines:
        db.add(QuoteItem(
            quote_id=quote.id,
            product_variant_id=uuid.UUID(line.variant_id),
            quantity=line.quantity,
            unit_price=line.unit_price,
            recommended_unit_price=line.recommended_unit_price,
            manual_price_override=line.manual_price_override,
            line_revenue=line.line_revenue,
            line_ingredient_cost=line.line_ingredient_cost,
            line_packaging_cost=line.line_packaging_cost,
            line_labour_cost=line.line_labour_cost,
            line_channel_fee=line.line_channel_fee,
            line_net_profit=line.line_net_profit,
            line_margin_percent=line.line_margin_percent,
        ))


# ---------- CRUD ----------

def create_quote(db: Session, tenant_id: uuid.UUID, data: QuoteCreate) -> tuple[Quote, QuoteResult]:
    hourly_rate = _tenant_labour_rate(db, tenant_id)
    channel = None
    if data.sales_channel_id:
        channel = db.query(SalesChannel).filter(
            SalesChannel.id == data.sales_channel_id, SalesChannel.tenant_id == tenant_id
        ).first()

    line_inputs = _build_line_inputs(db, tenant_id, data.items, hourly_rate)
    result = compute_quote(
        line_inputs,
        channel=channel,
        desired_margin_percent=data.desired_margin_percent,
        delivery_fee_charged=data.delivery_fee_charged,
        delivery_cost_estimate=data.delivery_cost_estimate,
        discount_amount=data.discount_amount,
    )

    quote = Quote(
        tenant_id=tenant_id,
        quote_number=_next_quote_number(db, tenant_id),
        customer_id=data.customer_id,
        sales_channel_id=data.sales_channel_id,
        requested_delivery_date=data.requested_delivery_date,
        delivery_method=data.delivery_method,
        delivery_fee_charged=data.delivery_fee_charged,
        delivery_cost_estimate=data.delivery_cost_estimate,
        discount_amount=data.discount_amount,
        discount_percent=data.discount_percent,
        desired_margin_percent=data.desired_margin_percent,
        internal_notes=data.internal_notes,
    )
    _apply_result_to_quote(quote, result)
    db.add(quote)
    db.flush()
    _upsert_quote_items(db, quote, result.lines)
    db.commit()
    db.refresh(quote)
    return quote, result


def get_quote(db: Session, tenant_id: uuid.UUID, quote_id: uuid.UUID) -> Quote:
    obj = db.query(Quote).filter(
        Quote.id == quote_id, Quote.tenant_id == tenant_id
    ).first()
    if not obj:
        raise NotFoundError("Quote", str(quote_id))
    return obj


def list_quotes(db: Session, tenant_id: uuid.UUID) -> list[Quote]:
    return (
        db.query(Quote)
        .filter(Quote.tenant_id == tenant_id)
        .order_by(Quote.created_at.desc())
        .all()
    )


def update_quote(
    db: Session, tenant_id: uuid.UUID, quote_id: uuid.UUID, data: QuoteUpdate
) -> Quote:
    obj = get_quote(db, tenant_id, quote_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def recalculate(db: Session, tenant_id: uuid.UUID, quote_id: uuid.UUID) -> tuple[Quote, QuoteResult]:
    quote = get_quote(db, tenant_id, quote_id)
    hourly_rate = _tenant_labour_rate(db, tenant_id)

    channel = None
    if quote.sales_channel_id:
        channel = db.query(SalesChannel).filter(SalesChannel.id == quote.sales_channel_id).first()

    # Re-read existing items with their current prices
    existing = db.query(QuoteItem).filter(QuoteItem.quote_id == quote.id).all()

    class _FakeItem:
        def __init__(self, qi: QuoteItem):
            self.product_variant_id = qi.product_variant_id
            self.quantity = qi.quantity
            self.unit_price_override = qi.unit_price if qi.manual_price_override else None

    line_inputs = _build_line_inputs(db, tenant_id, [_FakeItem(qi) for qi in existing], hourly_rate)
    result = compute_quote(
        line_inputs,
        channel=channel,
        desired_margin_percent=quote.desired_margin_percent,
        delivery_fee_charged=quote.delivery_fee_charged,
        delivery_cost_estimate=quote.delivery_cost_estimate,
        discount_amount=quote.discount_amount,
    )

    _apply_result_to_quote(quote, result)
    _upsert_quote_items(db, quote, result.lines)
    db.commit()
    db.refresh(quote)
    return quote, result


def accept_quote(db: Session, tenant_id: uuid.UUID, quote_id: uuid.UUID) -> Quote:
    quote = get_quote(db, tenant_id, quote_id)
    if quote.status not in ("draft", "sent"):
        raise BakerProfitError("INVALID_STATUS", f"Cannot accept a quote with status '{quote.status}'.", status_code=422)
    quote.status = "accepted"
    db.commit()
    db.refresh(quote)
    return quote


def do_generate_message(
    db: Session, tenant_id: uuid.UUID, quote_id: uuid.UUID, data: GenerateMessageRequest
) -> str:
    quote = get_quote(db, tenant_id, quote_id)
    items = db.query(QuoteItem).filter(QuoteItem.quote_id == quote.id).all()

    # Build minimal line stubs for message formatting
    variant_names = []
    for qi in items:
        v = db.query(ProductVariant).filter(ProductVariant.id == qi.product_variant_id).first()
        class _L:
            quantity = qi.quantity
            variant_name = v.name if v else "item"
        variant_names.append(_L())

    msg = generate_customer_message(
        lines=variant_names,
        total_price=quote.total_revenue,
        delivery_method=quote.delivery_method,
        customer_name=data.customer_name,
    )
    quote.customer_message = msg
    db.commit()
    return msg
