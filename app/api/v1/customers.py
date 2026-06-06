import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


def _err(exc: Exception) -> HTTPException:
    code = getattr(exc, "status_code", 400)
    return HTTPException(status_code=code, detail=exc.to_dict() if hasattr(exc, "to_dict") else str(exc))


@router.get("", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return customer_service.list_customers(db, user.tenant_id)


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return customer_service.create_customer(db, user.tenant_id, data)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return customer_service.get_customer(db, user.tenant_id, customer_id)
    except BakerProfitError as exc:
        raise _err(exc)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: uuid.UUID, data: CustomerUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return customer_service.update_customer(db, user.tenant_id, customer_id, data)
    except BakerProfitError as exc:
        raise _err(exc)
