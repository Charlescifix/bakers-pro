import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.packaging import PackagingCreate, PackagingResponse, PackagingUpdate
from app.services import packaging_service

router = APIRouter(prefix="/packaging-items", tags=["packaging"])


@router.get("", response_model=list[PackagingResponse])
def list_packaging(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return packaging_service.list_packaging(db, user.tenant_id)


@router.post("", response_model=PackagingResponse, status_code=201)
def create_packaging(
    data: PackagingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return packaging_service.create_packaging(db, user.tenant_id, data)
    except (BakerProfitError, ValueError) as exc:
        code = getattr(exc, "status_code", 400)
        raise HTTPException(status_code=code, detail=str(exc))


@router.patch("/{item_id}", response_model=PackagingResponse)
def update_packaging(
    item_id: uuid.UUID,
    data: PackagingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return packaging_service.update_packaging(db, user.tenant_id, item_id, data)
    except (BakerProfitError, ValueError) as exc:
        code = getattr(exc, "status_code", 400)
        raise HTTPException(status_code=code, detail=str(exc))


@router.delete("/{item_id}", status_code=204)
def delete_packaging(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        packaging_service.delete_packaging(db, user.tenant_id, item_id)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())
