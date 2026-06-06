"""Pure functions for weekly/monthly profit report — no DB dependency."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.core.money import q_money


@dataclass
class ProductSummary:
    product_name: str
    total_revenue: Decimal
    total_net_profit: Decimal
    order_count: int


@dataclass
class WeeklyReportResult:
    period_label: str
    total_revenue: Decimal
    total_ingredient_cost: Decimal
    total_packaging_cost: Decimal
    total_labour_cost: Decimal
    total_channel_fees: Decimal
    net_profit: Decimal
    order_count: int
    best_product: str | None = None
    worst_margin_product: str | None = None
    product_breakdown: list[ProductSummary] = field(default_factory=list)


def compute_period_report(
    period_label: str,
    order_rows: list[dict],
    order_item_rows: list[dict],
) -> WeeklyReportResult:
    """
    order_rows: list of dicts with keys:
        total_revenue, net_profit
    order_item_rows: list of dicts with keys:
        product_name, unit_price, quantity,
        actual_ingredient_cost, actual_packaging_cost,
        actual_labour_cost, actual_channel_fee, actual_net_profit
    """
    total_revenue = q_money(sum((Decimal(str(r["total_revenue"])) for r in order_rows), Decimal("0")))
    net_profit = q_money(sum((Decimal(str(r["net_profit"])) for r in order_rows), Decimal("0")))

    total_ingredient = q_money(
        sum((Decimal(str(i["actual_ingredient_cost"])) * i["quantity"] for i in order_item_rows), Decimal("0"))
    )
    total_packaging = q_money(
        sum((Decimal(str(i["actual_packaging_cost"])) * i["quantity"] for i in order_item_rows), Decimal("0"))
    )
    total_labour = q_money(
        sum((Decimal(str(i["actual_labour_cost"])) * i["quantity"] for i in order_item_rows), Decimal("0"))
    )
    total_fees = q_money(
        sum((Decimal(str(i["actual_channel_fee"])) * i["quantity"] for i in order_item_rows), Decimal("0"))
    )

    # Aggregate per-product
    by_product: dict[str, ProductSummary] = {}
    for item in order_item_rows:
        name = item.get("product_name") or "Unknown"
        rev = Decimal(str(item["unit_price"])) * item["quantity"]
        profit = Decimal(str(item["actual_net_profit"])) * item["quantity"]
        if name not in by_product:
            by_product[name] = ProductSummary(name, Decimal("0"), Decimal("0"), 0)
        by_product[name].total_revenue += rev
        by_product[name].total_net_profit += profit
        by_product[name].order_count += 1

    product_list = list(by_product.values())

    best = max(product_list, key=lambda p: p.total_net_profit, default=None)
    worst = None
    if product_list:
        def _margin(p: ProductSummary) -> Decimal:
            return p.total_net_profit / p.total_revenue if p.total_revenue > 0 else Decimal("0")
        worst = min(product_list, key=_margin)

    return WeeklyReportResult(
        period_label=period_label,
        total_revenue=total_revenue,
        total_ingredient_cost=total_ingredient,
        total_packaging_cost=total_packaging,
        total_labour_cost=total_labour,
        total_channel_fees=total_fees,
        net_profit=net_profit,
        order_count=len(order_rows),
        best_product=best.product_name if best else None,
        worst_margin_product=worst.product_name if worst else None,
        product_breakdown=product_list,
    )
