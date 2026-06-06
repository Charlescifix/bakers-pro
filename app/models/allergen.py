import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Allergen(Base):
    """Global (non-tenant) allergen reference table. Seeded with UK 14 major allergens."""
    __tablename__ = "allergens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngredientAllergen(Base, TimestampMixin):
    """Tenant-specific mapping of ingredients to allergens with contains status."""
    __tablename__ = "ingredient_allergens"
    __table_args__ = (UniqueConstraint("ingredient_id", "allergen_id", name="uq_ingredient_allergen"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False, index=True
    )
    allergen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("allergens.id"), nullable=False
    )
    contains_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="contains"
    )  # contains, may_contain, free, unknown
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    allergen: Mapped["Allergen"] = relationship("Allergen")


# ── UK 14 major allergens seed list ──────────────────────────────────────────

UK_ALLERGENS = [
    ("Celery", "Including celeriac. Found in salads, soups, celery salt."),
    ("Cereals containing gluten", "Wheat, rye, barley, oats, spelt, kamut."),
    ("Crustaceans", "Crabs, lobsters, prawns, shrimp."),
    ("Eggs", "Found in cakes, some pasta, quiche, mayonnaise."),
    ("Fish", "Found in sauces, pizza, relishes, dressings."),
    ("Lupin", "Found in flour and seeds. Related to peanuts."),
    ("Milk", "Includes butter, cheese, cream, lactose."),
    ("Molluscs", "Clams, mussels, oysters, squid, snails."),
    ("Mustard", "Found in salads, marinades, curries."),
    ("Nuts (tree nuts)", "Almonds, hazelnuts, walnuts, cashews, pecans, pistachios, macadamia, Brazil nuts."),
    ("Peanuts", "Found in groundnut oil, some curries, satay sauce."),
    ("Sesame", "Found in bread, breadsticks, tahini, hummus."),
    ("Soya", "Found in beancurd, edamame, miso, tofu, soya milk."),
    ("Sulphur dioxide / sulphites", "Found in wine, beer, dried fruit, vinegar."),
]
