from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.compliance import (
    BatchRecordCreate,
    CleaningLog,
    ComplianceLogCreate,
    ComplianceLogOut,
    FridgeTemperatureLog,
)
from app.services import compliance_service

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/logs", response_model=list[ComplianceLogOut])
def list_logs(
    log_type: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return compliance_service.list_logs(db, user.tenant_id, log_type=log_type)


@router.post("/logs", response_model=ComplianceLogOut, status_code=201)
def create_log(
    payload: ComplianceLogCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager", "staff")),
):
    log = compliance_service.create_log(db, user.tenant_id, user.id, payload)
    db.commit()
    db.refresh(log)
    return log


@router.get("/batch-records", response_model=list[ComplianceLogOut])
def list_batch_records(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return compliance_service.list_batch_records(db, user.tenant_id)


@router.post("/batch-records", response_model=ComplianceLogOut, status_code=201)
def create_batch_record(
    payload: BatchRecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager", "staff")),
):
    log = compliance_service.create_batch_record(db, user.tenant_id, user.id, payload)
    db.commit()
    db.refresh(log)
    return log


@router.post("/fridge-temperature", response_model=ComplianceLogOut, status_code=201)
def log_fridge_temp(
    payload: FridgeTemperatureLog,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager", "staff")),
):
    log = compliance_service.log_fridge_temperature(db, user.tenant_id, user.id, payload)
    db.commit()
    db.refresh(log)
    return log


@router.post("/cleaning-log", response_model=ComplianceLogOut, status_code=201)
def log_cleaning(
    payload: CleaningLog,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager", "staff")),
):
    log = compliance_service.log_cleaning(db, user.tenant_id, user.id, payload)
    db.commit()
    db.refresh(log)
    return log
