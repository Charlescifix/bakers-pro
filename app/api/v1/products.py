import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import (
    PricingSummaryResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    VariantCreate,
    VariantResponse,
    VariantUpdate,
)
from app.services import product_service

router = APIRouter(tags=["products"])


def _err(exc: Exception) -> HTTPException:
    code = getattr(exc, "status_code", 400)
    detail = exc.to_dict() if hasattr(exc, "to_dict") else str(exc)
    return HTTPException(status_code=code, detail=detail)


# ---------- Products ----------

@router.get("/products", response_model=list[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return product_service.list_products(db, user.tenant_id)


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return product_service.create_product(db, user.tenant_id, data)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return product_service.get_product(db, user.tenant_id, product_id)
    except BakerProfitError as exc:
        raise _err(exc)


@router.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return product_service.update_product(db, user.tenant_id, product_id, data)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.post("/products/{product_id}/variants", response_model=VariantResponse, status_code=201)
def add_variant(
    product_id: uuid.UUID,
    data: VariantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return product_service.add_variant(db, user.tenant_id, product_id, data)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


# ---------- Variants ----------

@router.patch("/product-variants/{variant_id}", response_model=VariantResponse)
def update_variant(
    variant_id: uuid.UUID,
    data: VariantUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return product_service.update_variant(db, user.tenant_id, variant_id, data)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.get("/product-variants/{variant_id}/pricing-summary", response_model=PricingSummaryResponse)
def pricing_summary(
    variant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return product_service.pricing_summary(db, user.tenant_id, variant_id)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)
