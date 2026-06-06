import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.shopping_list import (
    GenerateShoppingListRequest,
    ShoppingListItemMarkPurchased,
    ShoppingListResponse,
)
from app.services import shopping_list_service

router = APIRouter(prefix="/shopping-lists", tags=["shopping_lists"])


@router.post("", response_model=ShoppingListResponse, status_code=201)
def generate(
    payload: GenerateShoppingListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager")),
):
    sl = shopping_list_service.generate_shopping_list(db, current_user.tenant_id, payload)
    db.commit()
    db.refresh(sl)
    return sl


@router.get("", response_model=list[ShoppingListResponse])
def list_shopping_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return shopping_list_service.list_shopping_lists(db, current_user.tenant_id)


@router.get("/{list_id}", response_model=ShoppingListResponse)
def get_shopping_list(
    list_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return shopping_list_service.get_shopping_list(db, current_user.tenant_id, list_id)


@router.post("/{list_id}/mark-purchased", response_model=ShoppingListResponse)
def mark_purchased(
    list_id: uuid.UUID,
    payload: ShoppingListItemMarkPurchased,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("owner", "manager")),
):
    sl = shopping_list_service.mark_purchased(db, current_user.tenant_id, list_id, payload.item_ids)
    db.commit()
    db.refresh(sl)
    return sl
