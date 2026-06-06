import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, ActiveMixin


class Tenant(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, default="GB")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Europe/London")
    default_labour_rate_per_hour: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("10.00")
    )
    default_desired_margin_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("60.00")
    )
    default_food_cost_target_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("35.00")
    )
    fsa_rating_value: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fsa_rating_authority: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fsa_rating_last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fsa_rating_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    brand_primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    brand_secondary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
