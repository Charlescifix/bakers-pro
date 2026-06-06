import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin, TimestampMixin, ActiveMixin


class Customer(Base, TenantMixin, TimestampMixin, ActiveMixin):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    instagram_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tiktok_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    customer_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="individual"
    )  # individual, corporate, wholesale, event
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
