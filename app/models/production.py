import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin


class ProductionBatch(Base, TenantMixin, TimestampMixin):
    __tablename__ = "production_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False
    )
    planned_yield_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    actual_yield_quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    planned_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="planned"
    )  # planned, in_progress, completed, failed
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    batch_items: Mapped[list["ProductionBatchItem"]] = relationship(
        "ProductionBatchItem", back_populates="batch", cascade="all, delete-orphan"
    )


class ProductionBatchItem(Base, TimestampMixin):
    __tablename__ = "production_batch_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("production_batches.id"), nullable=False, index=True
    )
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_items.id"), nullable=False
    )
    quantity_allocated: Mapped[int] = mapped_column(Integer, nullable=False)

    batch: Mapped["ProductionBatch"] = relationship("ProductionBatch", back_populates="batch_items")
