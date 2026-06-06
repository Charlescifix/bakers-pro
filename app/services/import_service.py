"""Import job lifecycle: upload → parse → review → confirm → rollback."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, TenantIsolationError, ValidationError
from app.core.money import q_cost
from app.core.units import convert_to_base, get_unit_type
from app.imports.import_validator import validate_ingredient_row, validate_packaging_row
from app.imports.mapping_detector import ColumnMapping
from app.models.import_job import ImportJob
from app.models.ingredient import Ingredient
from app.models.packaging import PackagingItem
from app.schemas.imports import (
    ConfirmImportResponse,
    DetectedSection,
    ReviewMappingRequest,
    RollbackResponse,
)

UPLOAD_DIR = Path("uploads")


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)


def _detect_file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {"xlsx": "xlsx", "xls": "xlsx", "csv": "csv", "pdf": "pdf"}.get(ext, "unknown")


def _parse_file(file_type: str, file_bytes: bytes) -> list[DetectedSection]:
    if file_type == "xlsx":
        from app.imports.spreadsheet_importer import parse_xlsx
        return parse_xlsx(file_bytes)
    if file_type == "csv":
        from app.imports.spreadsheet_importer import parse_csv
        return parse_csv(file_bytes)
    if file_type == "pdf":
        from app.imports.pdf_importer import parse_pdf
        return parse_pdf(file_bytes)
    return []


def upload_and_parse(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    file_bytes: bytes,
) -> ImportJob:
    _ensure_upload_dir()
    file_type = _detect_file_type(filename)
    stored_name = f"{uuid.uuid4().hex}_{filename}"
    stored_path = UPLOAD_DIR / stored_name
    stored_path.write_bytes(file_bytes)

    job = ImportJob(
        tenant_id=tenant_id,
        uploaded_by_user_id=user_id,
        source_file_url=str(stored_path),
        source_file_type=file_type,
        status="parsing",
    )
    db.add(job)
    db.flush()

    try:
        sections = _parse_file(file_type, file_bytes)
        if not sections:
            job.status = "failed"
            job.error_message = "No parseable tables found in the file."
            db.flush()
            return job

        avg_conf = sum(s.confidence for s in sections) / len(sections)
        job.mapping_confidence_score = round(avg_conf, 3)
        job.detected_sections_json = json.dumps([s.model_dump() for s in sections])

        if avg_conf >= 0.90:
            job.status = "uploaded"
        else:
            job.status = "needs_review"

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)

    db.flush()
    return job


def get_job(db: Session, tenant_id: uuid.UUID, job_id: uuid.UUID) -> ImportJob:
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if not job:
        raise NotFoundError(f"ImportJob {job_id} not found")
    if job.tenant_id != tenant_id:
        raise TenantIsolationError()
    return job


def review_mapping(
    db: Session, tenant_id: uuid.UUID, job_id: uuid.UUID, payload: ReviewMappingRequest
) -> ImportJob:
    job = get_job(db, tenant_id, job_id)
    if not job.detected_sections_json:
        raise ValidationError("No parsed data to review")

    sections_raw = json.loads(job.detected_sections_json)

    if payload.exclude_section_indices:
        sections_raw = [
            s for i, s in enumerate(sections_raw)
            if i not in payload.exclude_section_indices
        ]

    if payload.column_overrides:
        for section in sections_raw:
            for row in section.get("rows", []):
                for override_from, override_to in payload.column_overrides.items():
                    if override_from in row.get("mapped", {}):
                        row["mapped"][override_to] = row["mapped"].pop(override_from)

    job.detected_sections_json = json.dumps(sections_raw)
    job.status = "uploaded"
    db.flush()
    return job


def confirm_import(
    db: Session, tenant_id: uuid.UUID, job_id: uuid.UUID
) -> tuple[ImportJob, ConfirmImportResponse]:
    job = get_job(db, tenant_id, job_id)
    if not job.detected_sections_json:
        raise ValidationError("No parsed data to import")
    if job.status == "imported":
        raise ValidationError("This job has already been imported")

    sections_raw = json.loads(job.detected_sections_json)
    response = ConfirmImportResponse()
    created_ids: dict[str, list[str]] = {"ingredients": [], "packaging": []}

    for section in sections_raw:
        section_type = section.get("section_type", "unknown")
        is_sample = section.get("is_sample", False)
        rows = section.get("rows", [])

        for row_data in rows:
            mapped = row_data.get("mapped", {})
            row_conf = row_data.get("confidence", 0.0)

            if section_type in ("ingredients", "recipe", "unknown") and not is_sample:
                result = validate_ingredient_row(mapped)
                if not result.is_valid:
                    response.skipped_rows += 1
                    response.warnings.extend(result.errors)
                    continue

                response.warnings.extend(result.warnings)
                ingredient = _build_ingredient(mapped, tenant_id)
                db.add(ingredient)
                db.flush()
                created_ids["ingredients"].append(str(ingredient.id))
                response.imported_ingredients += 1

            elif section_type == "packaging" and not is_sample:
                result = validate_packaging_row(mapped)
                if not result.is_valid:
                    response.skipped_rows += 1
                    response.warnings.extend(result.errors)
                    continue

                response.warnings.extend(result.warnings)
                pkg = _build_packaging(mapped, tenant_id)
                db.add(pkg)
                db.flush()
                created_ids["packaging"].append(str(pkg.id))
                response.imported_packaging += 1

            elif is_sample:
                response.skipped_rows += 1

    job.created_entity_ids_json = json.dumps(created_ids)
    job.status = "imported"
    job.completed_at = datetime.now(timezone.utc)
    db.flush()
    return job, response


def rollback_import(
    db: Session, tenant_id: uuid.UUID, job_id: uuid.UUID
) -> tuple[ImportJob, RollbackResponse]:
    job = get_job(db, tenant_id, job_id)
    if job.status != "imported":
        raise ValidationError("Can only rollback a job with status 'imported'")
    if not job.created_entity_ids_json:
        raise ValidationError("No entity IDs recorded for rollback")

    created_ids = json.loads(job.created_entity_ids_json)
    response = RollbackResponse()

    for id_str in created_ids.get("ingredients", []):
        obj = db.query(Ingredient).filter(
            Ingredient.id == uuid.UUID(id_str), Ingredient.tenant_id == tenant_id
        ).first()
        if obj:
            db.delete(obj)
            response.deleted_ingredients += 1

    for id_str in created_ids.get("packaging", []):
        obj = db.query(PackagingItem).filter(
            PackagingItem.id == uuid.UUID(id_str), PackagingItem.tenant_id == tenant_id
        ).first()
        if obj:
            db.delete(obj)
            response.deleted_packaging += 1

    job.status = "uploaded"
    job.created_entity_ids_json = None
    db.flush()
    return job, response


# ── builders ──────────────────────────────────────────────────────────────────

def _d(val, default="0") -> Decimal:
    try:
        return Decimal(str(val)) if val is not None else Decimal(default)
    except (InvalidOperation, TypeError):
        return Decimal(default)


def _build_ingredient(mapped: dict, tenant_id: uuid.UUID) -> Ingredient:
    price = _d(mapped.get("purchase_price"), "0")
    qty_raw = _d(mapped.get("purchase_quantity"), "1")
    unit = (mapped.get("unit_code") or "g").strip().lower()

    try:
        qty_base = convert_to_base(qty_raw, unit)
    except Exception:
        qty_base = qty_raw

    unit_cost = q_cost(price / qty_base) if qty_base > 0 else Decimal("0")

    return Ingredient(
        tenant_id=tenant_id,
        name=mapped["name"].strip(),
        default_unit_code=unit,
        current_purchase_price=price,
        current_purchase_quantity=qty_raw,
        current_purchase_unit_code=unit,
        current_unit_cost_base=unit_cost,
        waste_percent_default=_d(mapped.get("waste_percent"), "0"),
    )


def _build_packaging(mapped: dict, tenant_id: uuid.UUID) -> PackagingItem:
    price = _d(mapped.get("purchase_price"), "0")
    qty = _d(mapped.get("purchase_quantity"), "1")
    unit_cost = q_cost(price / qty) if qty > 0 else Decimal("0")

    return PackagingItem(
        tenant_id=tenant_id,
        name=mapped["name"].strip(),
        purchase_price=price,
        purchase_quantity=qty,
        purchase_unit_code=(mapped.get("unit_code") or "piece").strip().lower(),
        unit_cost=unit_cost,
    )
