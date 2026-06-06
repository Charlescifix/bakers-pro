import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, ActiveMixin


class Product(Base, TenantMixin, TimestampMixin, ActiveMixin):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="custom")
    default_recipe_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=True
    )
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    variants: Mapped[list["ProductVariant"]] = relationship(
        "ProductVariant", back_populates="product", order_by="ProductVariant.name"
    )


class ProductVariant(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    recipe_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=True
    )
    # How many recipe items one unit of this variant represents.
    # e.g. 1 = one full item from the recipe yield
    #      8 = eight items (a "Box of 8" backed by a recipe that yields items)
    quantity_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False, default=Decimal("1")
    )
    minimum_order_quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    current_selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    desired_margin_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("60")
    )
    # JSON blob for per-channel price rules: {"tiktok": {"fee_pct": "12.2"}, ...}
    channel_default_price_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    product: Mapped["Product"] = relationship("Product", back_populates="variants")
