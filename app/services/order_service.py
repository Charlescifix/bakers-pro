import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, TenantIsolationError
from app.core.money import q_money
from app.models.order import Order, OrderItem
from app.models.product import ProductVariant
from app.models.quote import Quote, QuoteItem
from app.schemas.order import OrderCreate


def _next_order_number(db: Session, tenant_id: uuid.UUID, slug: str) -> str:
    count = db.query(Order).filter(Order.tenant_id == tenant_id).count()
    return f"{slug.upper()}-O-{count + 1:05d}"


def create_order(db: Session, tenant_id: uuid.UUID, tenant_slug: str, payload: OrderCreate) -> Order:
    order_number = _next_order_number(db, tenant_id, tenant_slug)
    order = Order(
        tenant_id=tenant_id,
        order_number=order_number,
        customer_id=payload.customer_id,
        sales_channel_id=payload.sales_channel_id,
        order_date=payload.order_date,
        due_date=payload.due_date,
        delivery_method=payload.delivery_method,
        notes=payload.notes,
    )
    total_revenue = q_money(sum((i.unit_price * i.quantity for i in payload.items), __import__("decimal").Decimal("0")))
    order.total_revenue = total_revenue
    order.balance_due = total_revenue

    for item_in in payload.items:
        pv = db.query(ProductVariant).filter(ProductVariant.id == item_in.product_variant_id).first()
        if not pv:
            raise NotFoundError(f"ProductVariant {item_in.product_variant_id} not found")
        order.items.append(
            OrderItem(
                product_variant_id=item_in.product_variant_id,
                quantity=item_in.quantity,
                unit_price=item_in.unit_price,
            )
        )

    db.add(order)
    db.flush()
    db.refresh(order)
    return order


def convert_quote_to_order(db: Session, tenant_id: uuid.UUID, tenant_slug: str, quote_id: uuid.UUID) -> Order:
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise NotFoundError(f"Quote {quote_id} not found")
    if quote.tenant_id != tenant_id:
        raise TenantIsolationError()

    order_number = _next_order_number(db, tenant_id, tenant_slug)
    order = Order(
        tenant_id=tenant_id,
        quote_id=quote_id,
        order_number=order_number,
        customer_id=quote.customer_id,
        sales_channel_id=quote.sales_channel_id,
        order_date=datetime.now(timezone.utc),
        delivery_method=quote.delivery_method or "pickup",
        total_revenue=quote.total_revenue,
        total_cost=quote.total_cost_excluding_labour + quote.total_labour_cost,
        net_profit=quote.net_profit,
        balance_due=quote.total_revenue,
    )

    quote_items: list[QuoteItem] = db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).all()
    for qi in quote_items:
        order.items.append(
            OrderItem(
                product_variant_id=qi.product_variant_id,
                quantity=qi.quantity,
                unit_price=qi.unit_price,
                actual_ingredient_cost=qi.line_ingredient_cost,
                actual_packaging_cost=qi.line_packaging_cost,
                actual_labour_cost=qi.line_labour_cost,
                actual_channel_fee=qi.line_channel_fee,
                actual_net_profit=qi.line_net_profit,
            )
        )

    quote.status = "converted"
    db.add(order)
    db.flush()
    db.refresh(order)
    return order


def list_orders(db: Session, tenant_id: uuid.UUID) -> list[Order]:
    return db.query(Order).filter(Order.tenant_id == tenant_id).order_by(Order.created_at.desc()).all()


def get_order(db: Session, tenant_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise NotFoundError(f"Order {order_id} not found")
    if order.tenant_id != tenant_id:
        raise TenantIsolationError()
    return order


def update_order_status(db: Session, tenant_id: uuid.UUID, order_id: uuid.UUID, status: str) -> Order:
    order = get_order(db, tenant_id, order_id)
    order.status = status
    db.flush()
    return order


def mark_paid(db: Session, tenant_id: uuid.UUID, order_id: uuid.UUID, amount: "Decimal") -> Order:
    from decimal import Decimal
    order = get_order(db, tenant_id, order_id)
    order.amount_paid = q_money(order.amount_paid + amount)
    order.balance_due = q_money(order.total_revenue - order.amount_paid)
    if order.balance_due <= Decimal("0"):
        order.payment_status = "paid"
    else:
        order.payment_status = "deposit_paid"
    db.flush()
    return order


def complete_order(db: Session, tenant_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order = get_order(db, tenant_id, order_id)
    order.status = "completed"
    order.delivery_date = datetime.now(timezone.utc)
    db.flush()
    return order
