import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderPaymentUpdate, OrderResponse, OrderStatusUpdate
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager")),
):
    from app.models.tenant import Tenant
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    order = order_service.create_order(db, current_user.tenant_id, tenant.slug, payload)
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.list_orders(db, current_user.tenant_id)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.get_order(db, current_user.tenant_id, order_id)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager")),
):
    order = order_service.update_order_status(db, current_user.tenant_id, order_id, payload.status)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/mark-paid", response_model=OrderResponse)
def mark_paid(
    order_id: uuid.UUID,
    payload: OrderPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager", "accountant")),
):
    order = order_service.mark_paid(db, current_user.tenant_id, order_id, payload.amount)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/complete", response_model=OrderResponse)
def complete_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager")),
):
    order = order_service.complete_order(db, current_user.tenant_id, order_id)
    db.commit()
    db.refresh(order)
    return order
