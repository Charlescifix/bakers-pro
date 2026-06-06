"""Compliance log service — batch records, fridge temps, cleaning logs."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, TenantIsolationError
from app.models.compliance_log import ComplianceLog
from app.schemas.compliance import (
    BatchRecordCreate,
    CleaningLog,
    ComplianceLogCreate,
    FridgeTemperatureLog,
)


def list_logs(
    db: Session,
    tenant_id: uuid.UUID,
    log_type: str | None = None,
    limit: int = 100,
) -> list[ComplianceLog]:
    q = db.query(ComplianceLog).filter(ComplianceLog.tenant_id == tenant_id)
    if log_type:
        q = q.filter(ComplianceLog.log_type == log_type)
    return q.order_by(ComplianceLog.recorded_at.desc()).limit(limit).all()


def create_log(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: ComplianceLogCreate,
) -> ComplianceLog:
    log = ComplianceLog(
        tenant_id=tenant_id,
        recorded_by_user_id=user_id,
        log_type=payload.log_type,
        recorded_at=payload.recorded_at,
        related_batch_id=payload.related_batch_id,
        data_json=json.dumps(payload.data_json) if payload.data_json else None,
        notes=payload.notes,
    )
    db.add(log)
    db.flush()
    return log


def log_fridge_temperature(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: FridgeTemperatureLog,
) -> ComplianceLog:
    data = {
        "location": payload.location,
        "temperature_celsius": payload.temperature_celsius,
    }
    log = ComplianceLog(
        tenant_id=tenant_id,
        recorded_by_user_id=user_id,
        log_type="fridge_temperature",
        recorded_at=payload.recorded_at,
        data_json=json.dumps(data),
        notes=payload.notes,
    )
    db.add(log)
    db.flush()
    return log


def log_cleaning(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: CleaningLog,
) -> ComplianceLog:
    data = {
        "area": payload.area,
        "cleaned_by": payload.cleaned_by,
        "cleaning_product": payload.cleaning_product,
    }
    log = ComplianceLog(
        tenant_id=tenant_id,
        recorded_by_user_id=user_id,
        log_type="cleaning",
        recorded_at=payload.recorded_at,
        data_json=json.dumps(data),
        notes=payload.notes,
    )
    db.add(log)
    db.flush()
    return log


def create_batch_record(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: BatchRecordCreate,
) -> ComplianceLog:
    data = {
        "batch_id": str(payload.batch_id),
        "yield_quantity": payload.yield_quantity,
        "yield_unit": payload.yield_unit,
    }
    log = ComplianceLog(
        tenant_id=tenant_id,
        recorded_by_user_id=user_id,
        log_type="batch_record",
        recorded_at=payload.recorded_at,
        related_batch_id=payload.batch_id,
        data_json=json.dumps(data),
        notes=payload.notes,
    )
    db.add(log)
    db.flush()
    return log


def list_batch_records(db: Session, tenant_id: uuid.UUID) -> list[ComplianceLog]:
    return list_logs(db, tenant_id, log_type="batch_record")
