import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin, TimestampMixin


class IntelligenceEvent(Base, TenantMixin, TimestampMixin):
    __tablename__ = "intelligence_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # price_change, low_margin, stock_warning, pricing_recommendation, order_risk, trend_insight
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="info")  # info, warning, critical
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
