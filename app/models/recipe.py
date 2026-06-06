import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, ActiveMixin


class Recipe(Base, TenantMixin, TimestampMixin, ActiveMixin):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="custom"
    )  # banana_bread, meat_pie, puff_puff, cake, cookie, custom
    base_yield_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    base_yield_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="item")
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bake_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cooling_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    labour_minutes_default: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    storage_instruction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    serving_tip: Mapped[str | None] = mapped_column(String(500), nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    versions: Mapped[list["RecipeVersion"]] = relationship(
        "RecipeVersion", back_populates="recipe", order_by="RecipeVersion.version_number"
    )
    packaging_rules: Mapped[list["RecipePackagingRule"]] = relationship(
        "RecipePackagingRule", back_populates="recipe"
    )


class RecipeVersion(Base, TimestampMixin):
    __tablename__ = "recipe_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft, active, archived
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="versions")
    items: Mapped[list["RecipeItem"]] = relationship(
        "RecipeItem", back_populates="version", cascade="all, delete-orphan"
    )


class RecipeItem(Base, TimestampMixin):
    __tablename__ = "recipe_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipe_versions.id"), nullable=False, index=True
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False
    )
    quantity_used: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(20), nullable=False)
    waste_percent_override: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    preparation_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    variant_group: Mapped[str | None] = mapped_column(String(100), nullable=True)

    version: Mapped["RecipeVersion"] = relationship("RecipeVersion", back_populates="items")


class RecipePackagingRule(Base, TenantMixin, TimestampMixin):
    __tablename__ = "recipe_packaging_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False, index=True
    )
    packaging_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("packaging_items.id"), nullable=False
    )
    quantity_per_batch: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    quantity_per_item: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    rule_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="per_item"
    )  # per_item, per_batch, per_order
    notes: Mapped[str | None] = mapped_column(String(300), nullable=True)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="packaging_rules")
