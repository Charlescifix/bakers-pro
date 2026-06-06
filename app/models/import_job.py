import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin, TimestampMixin


class ImportJob(Base, TenantMixin, TimestampMixin):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    source_file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_file_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # xlsx, csv, pdf, image
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="uploaded"
    )  # uploaded, parsing, needs_review, imported, failed
    detected_sections_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    mapping_confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_entity_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
