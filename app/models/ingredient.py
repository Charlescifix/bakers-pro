import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, ActiveMixin


class IngredientCategory(Base, TenantMixin, TimestampMixin):
    __tablename__ = "ingredient_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Ingredient(Base, TenantMixin, TimestampMixin, ActiveMixin):
    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingredient_categories.id"), nullable=True
    )
    default_unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="g")
    density_g_per_ml: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_instruction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    allergen_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    # Current pricing snapshot — canonical values
    current_purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0")
    )
    current_purchase_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("1")
    )
    current_purchase_unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="g")
    # Pre-computed unit cost in base unit (e.g. per gram)
    current_unit_cost_base: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), nullable=False, default=Decimal("0")
    )
    waste_percent_default: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    reorder_level: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngredientPriceHistory(Base, TenantMixin, TimestampMixin):
    __tablename__ = "ingredient_price_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False, index=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    purchase_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    purchase_unit_code: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_cost_base: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    receipt_file_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
