import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin


class Quote(Base, TenantMixin, TimestampMixin):
    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft"
    )  # draft, sent, accepted, rejected, expired, converted_to_order
    sales_channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_channels.id"), nullable=True
    )
    requested_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_method: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pickup"
    )  # pickup, local_delivery, postal_delivery, courier, event_dropoff
    delivery_fee_charged: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    delivery_cost_estimate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    desired_margin_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("60"))
    # Computed totals — updated on every recalculate
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    total_cost_excluding_labour: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    total_labour_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    total_channel_fees: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    total_delivery_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    net_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    food_cost_percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=Decimal("0"))
    profit_margin_percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=Decimal("0"))
    recommendation_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft"
    )  # draft, profitable, low_margin, high_food_cost, loss_making, excellent
    customer_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["QuoteItem"]] = relationship(
        "QuoteItem", back_populates="quote", cascade="all, delete-orphan"
    )


class QuoteItem(Base, TimestampMixin):
    __tablename__ = "quote_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False, index=True
    )
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    recommended_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    manual_price_override: Mapped[bool] = mapped_column(default=False, nullable=False)
    line_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    line_ingredient_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    line_packaging_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    line_labour_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    line_overhead_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    line_channel_fee: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    line_net_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    line_margin_percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=Decimal("0"))

    quote: Mapped["Quote"] = relationship("Quote", back_populates="items")
