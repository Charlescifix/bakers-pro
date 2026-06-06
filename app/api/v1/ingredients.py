import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.ingredient import (
    IngredientCreate,
    IngredientResponse,
    IngredientUpdate,
    PriceHistoryResponse,
    PriceUpdateRequest,
)
from app.services import ingredient_service

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientResponse])
def list_ingredients(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ingredient_service.list_ingredients(db, user.tenant_id)


@router.post("", response_model=IngredientResponse, status_code=201)
def create_ingredient(
    data: IngredientCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return ingredient_service.create_ingredient(db, user.tenant_id, data)
    except (BakerProfitError, ValueError) as exc:
        code = getattr(exc, "status_code", 400)
        raise HTTPException(status_code=code, detail=str(exc))


@router.get("/low-stock", response_model=list[IngredientResponse])
def low_stock(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ingredient_service.list_low_stock(db, user.tenant_id)


@router.get("/{ingredient_id}", response_model=IngredientResponse)
def get_ingredient(
    ingredient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return ingredient_service.get_ingredient(db, user.tenant_id, ingredient_id)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.patch("/{ingredient_id}", response_model=IngredientResponse)
def update_ingredient(
    ingredient_id: uuid.UUID,
    data: IngredientUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return ingredient_service.update_ingredient(db, user.tenant_id, ingredient_id, data)
    except (BakerProfitError, ValueError) as exc:
        code = getattr(exc, "status_code", 400)
        raise HTTPException(status_code=code, detail=str(exc))


@router.delete("/{ingredient_id}", status_code=204)
def delete_ingredient(
    ingredient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        ingredient_service.delete_ingredient(db, user.tenant_id, ingredient_id)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())


@router.post("/{ingredient_id}/prices", response_model=PriceHistoryResponse, status_code=201)
def add_price(
    ingredient_id: uuid.UUID,
    data: PriceUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return ingredient_service.add_price(db, user.tenant_id, ingredient_id, data)
    except (BakerProfitError, ValueError) as exc:
        code = getattr(exc, "status_code", 400)
        raise HTTPException(status_code=code, detail=str(exc))


@router.get("/{ingredient_id}/price-history", response_model=list[PriceHistoryResponse])
def price_history(
    ingredient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return ingredient_service.get_price_history(db, user.tenant_id, ingredient_id)
    except BakerProfitError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_dict())
