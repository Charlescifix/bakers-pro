import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.quote import (
    GenerateMessageRequest,
    QuoteCreate,
    QuoteDetailResponse,
    QuoteResponse,
    QuoteUpdate,
    ShoppingLineOut,
)
from app.services import quote_service

router = APIRouter(prefix="/quotes", tags=["quotes"])


def _err(exc: Exception) -> HTTPException:
    code = getattr(exc, "status_code", 400)
    return HTTPException(status_code=code, detail=exc.to_dict() if hasattr(exc, "to_dict") else str(exc))


def _detail(quote, result) -> QuoteDetailResponse:
    base = QuoteDetailResponse.model_validate(quote)
    base.recommended_total_price = result.recommended_total_price
    base.warnings = result.warnings
    base.shopping_list_preview = [
        ShoppingLineOut(
            ingredient_id=s.ingredient_id,
            ingredient_name=s.ingredient_name,
            required_quantity=s.required_quantity,
            unit_code=s.unit_code,
        )
        for s in result.shopping_list_preview
    ]
    return base


@router.get("", response_model=list[QuoteResponse])
def list_quotes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return quote_service.list_quotes(db, user.tenant_id)


@router.post("", response_model=QuoteDetailResponse, status_code=201)
def create_quote(data: QuoteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        quote, result = quote_service.create_quote(db, user.tenant_id, data)
        return _detail(quote, result)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return quote_service.get_quote(db, user.tenant_id, quote_id)
    except BakerProfitError as exc:
        raise _err(exc)


@router.patch("/{quote_id}", response_model=QuoteResponse)
def update_quote(quote_id: uuid.UUID, data: QuoteUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return quote_service.update_quote(db, user.tenant_id, quote_id, data)
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/{quote_id}/recalculate", response_model=QuoteDetailResponse)
def recalculate(quote_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        quote, result = quote_service.recalculate(db, user.tenant_id, quote_id)
        return _detail(quote, result)
    except (BakerProfitError, ValueError) as exc:
        raise _err(exc)


@router.post("/{quote_id}/accept", response_model=QuoteResponse)
def accept_quote(quote_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return quote_service.accept_quote(db, user.tenant_id, quote_id)
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/{quote_id}/generate-message")
def generate_message(quote_id: uuid.UUID, data: GenerateMessageRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        msg = quote_service.do_generate_message(db, user.tenant_id, quote_id, data)
        return {"customer_message": msg}
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/{quote_id}/convert-to-order")
def convert_to_order(quote_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.tenant import Tenant
    from app.services import order_service
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    try:
        order = order_service.convert_quote_to_order(db, user.tenant_id, tenant.slug, quote_id)
        db.commit()
        db.refresh(order)
        from app.schemas.order import OrderResponse
        return OrderResponse.model_validate(order)
    except BakerProfitError as exc:
        raise _err(exc)
