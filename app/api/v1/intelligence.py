import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.intelligence import (
    AskRequest,
    IntelligenceEventOut,
    OrderParseRequest,
    ParsedOrderResult,
    PricingAdviceRequest,
    PricingAdviceResult,
)
from app.services import intelligence_service

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/parse-order-request", response_model=ParsedOrderResult)
def parse_order(
    payload: OrderParseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = intelligence_service.parse_order_request(db, user.tenant_id, payload)
    db.commit()
    return result


@router.post("/pricing-advice", response_model=PricingAdviceResult)
def pricing_advice(
    payload: PricingAdviceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return intelligence_service.get_pricing_advice(db, user.tenant_id, payload)


@router.get("/events", response_model=list[IntelligenceEventOut])
def list_events(
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return intelligence_service.list_events(db, user.tenant_id, unread_only=unread_only)


@router.post("/events/{event_id}/mark-read", response_model=IntelligenceEventOut)
def mark_read(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    event = intelligence_service.mark_event_read(db, user.tenant_id, event_id)
    db.commit()
    return event


@router.post("/generate-margin-alerts")
def generate_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    count = intelligence_service.generate_margin_alerts(db, user.tenant_id)
    db.commit()
    return {"created": count}


@router.post("/ask")
def ask(
    payload: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return intelligence_service.ask(db, user.tenant_id, payload)
