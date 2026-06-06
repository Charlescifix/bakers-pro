"""Intelligence service — order parsing, pricing advice, event management."""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, TenantIsolationError
from app.models.intelligence_event import IntelligenceEvent
from app.models.product import Product, ProductVariant
from app.schemas.intelligence import (
    AskRequest,
    OrderParseRequest,
    ParsedOrderResult,
    PricingAdviceRequest,
    PricingAdviceResult,
)
from app.services.ai_provider import get_ai_provider
from app.services.reporting_service import get_product_profitability


def parse_order_request(db: Session, tenant_id: uuid.UUID, payload: OrderParseRequest) -> ParsedOrderResult:
    provider = get_ai_provider()
    result = provider.parse_order_request(payload.message)

    # Store as an intelligence event for audit trail
    event = IntelligenceEvent(
        tenant_id=tenant_id,
        event_type="order_risk",
        severity="info",
        title="Order request parsed",
        message=f"Parsed {len(result.items)} item(s) from message. Confidence: {result.confidence:.0%}",
        data_json=json.dumps({"items": [i.model_dump() for i in result.items], "confidence": result.confidence}),
    )
    db.add(event)
    db.flush()
    return result


def get_pricing_advice(
    db: Session, tenant_id: uuid.UUID, payload: PricingAdviceRequest
) -> PricingAdviceResult:
    prof_rows = get_product_profitability(db, tenant_id)

    if payload.variant_ids:
        prof_rows = [r for r in prof_rows if r.variant_id in payload.variant_ids]

    variant_data = [
        {
            "variant_id": r.variant_id,
            "product_name": r.product_name,
            "variant_name": r.variant_name,
            "current_selling_price": float(r.current_selling_price),
            "recommended_price": float(r.recommended_price_50),
            "net_margin_percent": float(r.net_margin_percent),
            "desired_margin_percent": float(r.desired_margin_percent),
        }
        for r in prof_rows
    ]

    provider = get_ai_provider()
    advice_items = provider.generate_pricing_advice(variant_data)

    summary = (
        f"Reviewed {len(variant_data)} variant(s). "
        f"{sum(1 for a in advice_items if a.priority == 'high')} need immediate attention."
    )

    return PricingAdviceResult(items=advice_items, summary=summary)


def list_events(db: Session, tenant_id: uuid.UUID, unread_only: bool = False) -> list[IntelligenceEvent]:
    q = db.query(IntelligenceEvent).filter(IntelligenceEvent.tenant_id == tenant_id)
    if unread_only:
        q = q.filter(IntelligenceEvent.is_read.is_(False))
    return q.order_by(IntelligenceEvent.created_at.desc()).limit(100).all()


def mark_event_read(db: Session, tenant_id: uuid.UUID, event_id: uuid.UUID) -> IntelligenceEvent:
    event = db.query(IntelligenceEvent).filter(IntelligenceEvent.id == event_id).first()
    if not event:
        raise NotFoundError(f"IntelligenceEvent {event_id} not found")
    if event.tenant_id != tenant_id:
        raise TenantIsolationError()
    event.is_read = True
    db.flush()
    return event


def generate_margin_alerts(db: Session, tenant_id: uuid.UUID) -> int:
    """Scan all variants for low margin; create IntelligenceEvent rows. Returns count created."""
    prof_rows = get_product_profitability(db, tenant_id)
    count = 0
    for r in prof_rows:
        if r.net_margin_percent < r.desired_margin_percent:
            severity = "critical" if r.net_margin_percent < Decimal("0") else "warning"
            event = IntelligenceEvent(
                tenant_id=tenant_id,
                event_type="low_margin",
                severity=severity,
                title=f"Low margin: {r.product_name} {r.variant_name}".strip(),
                message=(
                    f"{r.product_name} {r.variant_name} has a margin of "
                    f"{float(r.net_margin_percent):.1f}%, below your target of "
                    f"{float(r.desired_margin_percent):.1f}%. "
                    f"Recommended price at 50% margin: £{float(r.recommended_price_50):.2f}."
                ),
                data_json=json.dumps(
                    {
                        "variant_id": str(r.variant_id),
                        "net_margin_percent": float(r.net_margin_percent),
                        "desired_margin_percent": float(r.desired_margin_percent),
                        "recommended_price": float(r.recommended_price_50),
                    }
                ),
            )
            db.add(event)
            count += 1
    db.flush()
    return count


def ask(db: Session, tenant_id: uuid.UUID, payload: AskRequest) -> dict:
    """Simple Q&A — interpret question and route to the right report."""
    q = payload.question.lower()
    if any(w in q for w in ("profit", "revenue", "earning", "made")):
        from app.services.reporting_service import get_weekly_report
        report = get_weekly_report(db, tenant_id)
        return {
            "answer": (
                f"This week's revenue: £{float(report.total_revenue):.2f}. "
                f"Net profit: £{float(report.net_profit):.2f}. "
                f"Best product: {report.best_product or 'N/A'}."
            )
        }
    if any(w in q for w in ("margin", "price", "cheap", "expensive", "low")):
        advice = get_pricing_advice(db, tenant_id, PricingAdviceRequest())
        urgent = [a for a in advice.items if a.priority == "high"]
        if urgent:
            return {"answer": urgent[0].advice}
        return {"answer": "All your products are currently within target margins."}
    return {"answer": "I can answer questions about profit, revenue, and product pricing. Try asking about this week's earnings or which products need a price review."}
