import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.production import (
    GenerateProductionPlanRequest,
    ProductionBatchResponse,
    ProductionBatchUpdate,
    ProductionChecklistItem,
    ProductionPlanResponse,
)
from app.services import production_service

router = APIRouter(prefix="/production", tags=["production"])


@router.post("/generate-plan", response_model=ProductionPlanResponse, status_code=201)
def generate_plan(
    payload: GenerateProductionPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager")),
):
    result = production_service.generate_production_plan(db, current_user.tenant_id, payload)
    db.commit()
    return result


@router.get("/batches", response_model=list[ProductionBatchResponse])
def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return production_service.list_batches(db, current_user.tenant_id)


@router.get("/batches/{batch_id}", response_model=ProductionBatchResponse)
def get_batch(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return production_service.get_batch(db, current_user.tenant_id, batch_id)


@router.patch("/batches/{batch_id}", response_model=ProductionBatchResponse)
def update_batch(
    batch_id: uuid.UUID,
    payload: ProductionBatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager")),
):
    batch = production_service.update_batch(db, current_user.tenant_id, batch_id, payload)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/checklist", response_model=list[ProductionChecklistItem])
def get_checklist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return production_service.get_checklist(db, current_user.tenant_id)
