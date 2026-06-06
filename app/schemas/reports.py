from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel


class ProductSummaryOut(BaseModel):
    product_name: str
    total_revenue: Decimal
    total_net_profit: Decimal
    order_count: int


class WeeklyReportOut(BaseModel):
    period_label: str
    total_revenue: Decimal
    total_ingredient_cost: Decimal
    total_packaging_cost: Decimal
    total_labour_cost: Decimal
    total_channel_fees: Decimal
    net_profit: Decimal
    order_count: int
    best_product: str | None
    worst_margin_product: str | None
    product_breakdown: list[ProductSummaryOut]


class ProductProfitabilityRow(BaseModel):
    variant_id: uuid.UUID
    product_name: str
    variant_name: str
    current_selling_price: Decimal
    ingredient_cost_per_item: Decimal
    packaging_cost_per_item: Decimal
    labour_cost_per_item: Decimal
    true_cost_per_item: Decimal
    gross_profit: Decimal
    net_margin_percent: Decimal
    food_cost_percent: Decimal
    recommended_price_50: Decimal
    desired_margin_percent: Decimal
    margin_status: str


class ChannelProfitabilityRow(BaseModel):
    channel_id: uuid.UUID
    channel_name: str
    total_revenue: Decimal
    total_fees: Decimal
    net_profit: Decimal
    order_count: int
    average_order_value: Decimal


class DashboardOut(BaseModel):
    orders_today: int
    open_quotes: int
    week_revenue: Decimal
    week_net_profit: Decimal
    upcoming_deliveries: list[dict]
    low_margin_products: list[dict]
    most_profitable_product: str | None
    low_stock_ingredients: list[dict]
