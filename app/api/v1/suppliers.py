import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services import supplier_service

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return supplier_service.list_suppliers(db, user.tenant_id)


@router.post("", response_model=SupplierResponse, status_code=201)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return supplier_service.create_supplier(db, user.tenant_id, data)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return supplier_service.get_supplier(db, user.tenant_id, supplier_id)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: uuid.UUID,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return supplier_service.update_supplier(db, user.tenant_id, supplier_id, data)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        supplier_service.delete_supplier(db, user.tenant_id, supplier_id)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())
