"""Reporting service — loads data from DB and delegates to pure report functions."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.calculators.price_engine import compute_variant_pricing
from app.calculators.recipe_calculator import compute_recipe_cost
from app.core.config import settings
from app.models.ingredient import Ingredient
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductVariant
from app.models.quote import Quote
from app.models.recipe import Recipe, RecipeItem, RecipeVersion, RecipePackagingRule
from app.models.packaging import PackagingItem
from app.models.sales_channel import SalesChannel
from app.reports.low_margin_report import find_low_margin_items
from app.reports.weekly_profit_report import WeeklyReportResult, compute_period_report
from app.schemas.reports import (
    ChannelProfitabilityRow,
    DashboardOut,
    ProductProfitabilityRow,
    WeeklyReportOut,
    ProductSummaryOut,
)


def _week_bounds(ref: datetime) -> tuple[datetime, datetime]:
    start = ref - timedelta(days=ref.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start, end


def _month_bounds(ref: datetime) -> tuple[datetime, datetime]:
    start = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def _orders_in_range(db: Session, tenant_id: uuid.UUID, start: datetime, end: datetime) -> list[Order]:
    return (
        db.query(Order)
        .filter(
            Order.tenant_id == tenant_id,
            Order.order_date >= start,
            Order.order_date < end,
            Order.status != "cancelled",
        )
        .all()
    )


def _build_order_rows(orders: list[Order]) -> list[dict]:
    return [{"total_revenue": o.total_revenue, "net_profit": o.net_profit} for o in orders]


def _build_item_rows(db: Session, orders: list[Order]) -> list[dict]:
    rows: list[dict] = []
    for order in orders:
        for oi in order.items:
            pv = db.query(ProductVariant).filter(ProductVariant.id == oi.product_variant_id).first()
            product_name = "Unknown"
            variant_name = ""
            if pv:
                p = db.query(Product).filter(Product.id == pv.product_id).first()
                product_name = p.name if p else "Unknown"
                variant_name = pv.name or ""
            rows.append(
                {
                    "product_name": product_name,
                    "variant_name": variant_name,
                    "unit_price": oi.unit_price,
                    "quantity": oi.quantity,
                    "actual_ingredient_cost": oi.actual_ingredient_cost,
                    "actual_packaging_cost": oi.actual_packaging_cost,
                    "actual_labour_cost": oi.actual_labour_cost,
                    "actual_channel_fee": oi.actual_channel_fee,
                    "actual_net_profit": oi.actual_net_profit,
                }
            )
    return rows


def _report_to_schema(result: WeeklyReportResult) -> WeeklyReportOut:
    return WeeklyReportOut(
        period_label=result.period_label,
        total_revenue=result.total_revenue,
        total_ingredient_cost=result.total_ingredient_cost,
        total_packaging_cost=result.total_packaging_cost,
        total_labour_cost=result.total_labour_cost,
        total_channel_fees=result.total_channel_fees,
        net_profit=result.net_profit,
        order_count=result.order_count,
        best_product=result.best_product,
        worst_margin_product=result.worst_margin_product,
        product_breakdown=[
            ProductSummaryOut(
                product_name=p.product_name,
                total_revenue=p.total_revenue,
                total_net_profit=p.total_net_profit,
                order_count=p.order_count,
            )
            for p in result.product_breakdown
        ],
    )


def get_weekly_report(db: Session, tenant_id: uuid.UUID) -> WeeklyReportOut:
    now = datetime.now(timezone.utc)
    start, end = _week_bounds(now)
    orders = _orders_in_range(db, tenant_id, start, end)
    result = compute_period_report(
        f"Week of {start.strftime('%d %b %Y')}",
        _build_order_rows(orders),
        _build_item_rows(db, orders),
    )
    return _report_to_schema(result)


def get_monthly_report(db: Session, tenant_id: uuid.UUID) -> WeeklyReportOut:
    now = datetime.now(timezone.utc)
    start, end = _month_bounds(now)
    orders = _orders_in_range(db, tenant_id, start, end)
    result = compute_period_report(
        now.strftime("%B %Y"),
        _build_order_rows(orders),
        _build_item_rows(db, orders),
    )
    return _report_to_schema(result)


def get_product_profitability(db: Session, tenant_id: uuid.UUID) -> list[ProductProfitabilityRow]:
    variants = (
        db.query(ProductVariant)
        .join(Product, Product.id == ProductVariant.product_id)
        .filter(Product.tenant_id == tenant_id)
        .all()
    )

    rows: list[ProductProfitabilityRow] = []
    for pv in variants:
        recipe_id = pv.recipe_id or (pv.product.default_recipe_id if pv.product else None)
        if not recipe_id:
            continue

        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            continue

        active_version = (
            db.query(RecipeVersion)
            .filter(RecipeVersion.recipe_id == recipe_id, RecipeVersion.status == "active")
            .first()
        )
        if not active_version:
            continue

        recipe_items = db.query(RecipeItem).filter(RecipeItem.recipe_version_id == active_version.id).all()
        ingredient_map: dict = {}
        for ri in recipe_items:
            if ri.ingredient_id:
                ing = db.query(Ingredient).filter(Ingredient.id == ri.ingredient_id).first()
                if ing:
                    ingredient_map[ri.ingredient_id] = ing

        packaging_rules = (
            db.query(RecipePackagingRule)
            .filter(RecipePackagingRule.recipe_id == recipe_id, RecipePackagingRule.tenant_id == tenant_id)
            .all()
        )
        packaging_map: dict = {}
        for rule in packaging_rules:
            pkg = db.query(PackagingItem).filter(PackagingItem.id == rule.packaging_item_id).first()
            if pkg:
                packaging_map[rule.packaging_item_id] = pkg

        hourly_rate = Decimal(str(settings.default_labour_rate_per_hour))
        try:
            cost_result = compute_recipe_cost(recipe, active_version, ingredient_map, packaging_map, hourly_rate)
        except Exception:
            continue

        selling_price = pv.current_selling_price or Decimal("0")
        desired_margin = pv.desired_margin_percent or Decimal(str(settings.default_desired_margin_percent))
        multiplier = pv.quantity_multiplier or Decimal("1")

        try:
            pricing = compute_variant_pricing(
                ingredient_cost_per_item=cost_result.ingredient_cost_per_item,
                packaging_cost_per_item=cost_result.packaging_cost_per_item,
                labour_cost_per_item=cost_result.labour_cost_per_item,
                quantity_multiplier=multiplier,
                selling_price=selling_price,
                desired_margin_pct=desired_margin,
            )
        except Exception:
            continue

        product = db.query(Product).filter(Product.id == pv.product_id).first()
        rows.append(
            ProductProfitabilityRow(
                variant_id=pv.id,
                product_name=product.name if product else "Unknown",
                variant_name=pv.name or "",
                current_selling_price=selling_price,
                ingredient_cost_per_item=pricing.ingredient_cost_per_item,
                packaging_cost_per_item=pricing.packaging_cost_per_item,
                labour_cost_per_item=pricing.labour_cost_per_item,
                true_cost_per_item=pricing.total_cost_per_item,
                gross_profit=pricing.gross_profit,
                net_margin_percent=pricing.net_margin_percent,
                food_cost_percent=pricing.food_cost_percent,
                recommended_price_50=pricing.recommended_prices.get("50", Decimal("0")),
                desired_margin_percent=desired_margin,
                margin_status=pricing.margin_status,
            )
        )
    return rows


def get_channel_profitability(db: Session, tenant_id: uuid.UUID) -> list[ChannelProfitabilityRow]:
    channels = db.query(SalesChannel).filter(SalesChannel.tenant_id == tenant_id).all()
    rows: list[ChannelProfitabilityRow] = []
    for ch in channels:
        orders = (
            db.query(Order)
            .filter(Order.sales_channel_id == ch.id, Order.status != "cancelled")
            .all()
        )
        if not orders:
            continue
        total_rev = sum((o.total_revenue for o in orders), Decimal("0"))
        total_profit = sum((o.net_profit for o in orders), Decimal("0"))
        # Fees: approximate from order items
        all_items = [oi for o in orders for oi in o.items]
        total_fees = sum((oi.actual_channel_fee for oi in all_items), Decimal("0"))
        avg_order_value = total_rev / len(orders) if orders else Decimal("0")
        rows.append(
            ChannelProfitabilityRow(
                channel_id=ch.id,
                channel_name=ch.name,
                total_revenue=total_rev,
                total_fees=total_fees,
                net_profit=total_profit,
                order_count=len(orders),
                average_order_value=avg_order_value,
            )
        )
    return rows


def get_dashboard(db: Session, tenant_id: uuid.UUID) -> DashboardOut:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_start, week_end = _week_bounds(now)
    next_week = now + timedelta(days=7)

    orders_today = (
        db.query(Order)
        .filter(
            Order.tenant_id == tenant_id,
            Order.order_date >= today_start,
            Order.order_date < today_end,
            Order.status != "cancelled",
        )
        .count()
    )

    open_quotes = (
        db.query(Quote)
        .filter(
            Quote.tenant_id == tenant_id,
            Quote.status.in_(["draft", "sent", "pending"]),
        )
        .count()
    )

    week_orders = _orders_in_range(db, tenant_id, week_start, week_end)
    week_revenue = sum((o.total_revenue for o in week_orders), Decimal("0"))
    week_profit = sum((o.net_profit for o in week_orders), Decimal("0"))

    upcoming = (
        db.query(Order)
        .filter(
            Order.tenant_id == tenant_id,
            Order.due_date >= now,
            Order.due_date <= next_week,
            Order.status.notin_(["cancelled", "completed"]),
        )
        .order_by(Order.due_date)
        .limit(10)
        .all()
    )
    upcoming_list = [
        {"order_id": str(o.id), "order_number": o.order_number, "due_date": str(o.due_date)}
        for o in upcoming
    ]

    low_stock = (
        db.query(Ingredient)
        .filter(
            Ingredient.tenant_id == tenant_id,
            Ingredient.reorder_level.isnot(None),
        )
        .all()
    )

    # Get profitability to identify low-margin products
    prof_rows = get_product_profitability(db, tenant_id)
    low_margin_summaries = [
        {
            "variant_id": str(r.variant_id),
            "product_name": r.product_name,
            "variant_name": r.variant_name,
            "net_margin_percent": float(r.net_margin_percent),
            "desired_margin_percent": float(r.desired_margin_percent),
        }
        for r in prof_rows
    ]
    low_margin = find_low_margin_items(low_margin_summaries)
    low_margin_list = [
        {
            "variant_id": item.variant_id,
            "product_name": item.product_name,
            "variant_name": item.variant_name,
            "net_margin_percent": float(item.net_margin_percent),
            "severity": item.severity,
        }
        for item in low_margin
    ]

    best_product = None
    if prof_rows:
        best = max(prof_rows, key=lambda r: r.gross_profit, default=None)
        if best:
            best_product = f"{best.product_name} {best.variant_name}".strip()

    return DashboardOut(
        orders_today=orders_today,
        open_quotes=open_quotes,
        week_revenue=week_revenue,
        week_net_profit=week_profit,
        upcoming_deliveries=upcoming_list,
        low_margin_products=low_margin_list,
        most_profitable_product=best_product,
        low_stock_ingredients=[],
    )
