"""Provider-agnostic AI interface. Swap MockAIProvider for a real LLM backend without changing callers."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.schemas.intelligence import ParsedOrderItem, ParsedOrderResult, PricingAdviceItem


class AIProvider(ABC):
    @abstractmethod
    def parse_order_request(self, message: str) -> ParsedOrderResult: ...

    @abstractmethod
    def generate_pricing_advice(self, variant_data: list[dict]) -> list[PricingAdviceItem]: ...

    @abstractmethod
    def explain_margin_warning(self, data: dict) -> str: ...


# ── Regex / heuristic implementation (no external API required) ───────────────

_DELIVERY_WORDS = {"delivery", "deliver", "shipped", "ship", "post", "send"}
_PICKUP_WORDS = {"pickup", "pick up", "collect", "collection", "take away", "takeaway"}

_DAY_PATTERN = re.compile(
    r"\b(next\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today)\b",
    re.IGNORECASE,
)
_DATE_PATTERN = re.compile(
    r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*)\b",
    re.IGNORECASE,
)
# Matches "60 puff puff" or "twenty meat pies"
_ITEM_PATTERN = re.compile(
    r"\b(\d+)\s+((?:[a-z][a-z\s\-\']*?)(?=\s*(?:,|and\s+\d|\n|$|for\b|please\b|on\b)))",
    re.IGNORECASE,
)
_ITEM_PATTERN_LOOSE = re.compile(
    r"(\d+)\s+([a-zA-Z][a-zA-Z\s\-\']{2,30}?)(?=\s*[,\n]|\s+and\b|\s+for\b|$)",
    re.IGNORECASE,
)


def _detect_delivery_method(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in _DELIVERY_WORDS):
        return "delivery"
    if any(w in lower for w in _PICKUP_WORDS):
        return "pickup"
    return "pickup"


def _detect_date(text: str) -> str | None:
    m = _DAY_PATTERN.search(text)
    if m:
        return m.group(0).strip()
    m = _DATE_PATTERN.search(text)
    if m:
        return m.group(0).strip()
    return None


def _parse_items(text: str) -> list[ParsedOrderItem]:
    # Normalise "and" separators so "20 meat pies and 10 mini" becomes "20 meat pies, 10 mini"
    normalised = re.sub(r"\band\b(?=\s+\d)", ",", text, flags=re.IGNORECASE)
    items: list[ParsedOrderItem] = []
    seen: set[str] = set()
    for m in _ITEM_PATTERN_LOOSE.finditer(normalised):
        qty_str, name = m.group(1), m.group(2).strip().rstrip(",").strip()
        # Skip very short noise words
        if len(name) < 3:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(ParsedOrderItem(product_name=name.title(), quantity=int(qty_str)))
    return items


class MockAIProvider(AIProvider):
    """Regex-based provider. Produces deterministic results; no API calls or cost."""

    def parse_order_request(self, message: str) -> ParsedOrderResult:
        items = _parse_items(message)
        requested_date = _detect_date(message)
        delivery_method = _detect_delivery_method(message)

        confidence = 0.50
        if items:
            confidence += 0.30
        if requested_date:
            confidence += 0.10
        confidence += min(0.09, len(items) * 0.03)
        confidence = round(min(0.99, confidence), 2)

        return ParsedOrderResult(
            items=items,
            requested_date=requested_date,
            delivery_method=delivery_method,
            confidence=confidence,
            raw_message=message,
        )

    def generate_pricing_advice(self, variant_data: list[dict]) -> list[PricingAdviceItem]:
        from decimal import Decimal
        advice_items: list[PricingAdviceItem] = []
        for v in variant_data:
            current = Decimal(str(v.get("current_selling_price", "0")))
            recommended = Decimal(str(v.get("recommended_price", "0")))
            net_margin = Decimal(str(v.get("net_margin_percent", "0")))
            desired = Decimal(str(v.get("desired_margin_percent", "50")))
            name = v.get("product_name", "Product")
            variant = v.get("variant_name", "")
            vid = v["variant_id"]

            if net_margin < Decimal("0"):
                advice = f"You are making a loss on {name} {variant}. Raise your price immediately."
                priority = "high"
                suggested = float(recommended)
            elif net_margin < desired:
                gap = desired - net_margin
                advice = (
                    f"{name} {variant} is {float(gap):.1f}% below your target margin. "
                    f"Consider raising the price from £{float(current):.2f} to £{float(recommended):.2f}."
                )
                priority = "high" if gap > Decimal("10") else "medium"
                suggested = float(recommended)
            elif net_margin >= desired + Decimal("15"):
                advice = (
                    f"{name} {variant} has a strong margin ({float(net_margin):.1f}%). "
                    "You have room to run a promotion or absorb a cost increase."
                )
                priority = "low"
                suggested = None
            else:
                continue

            advice_items.append(
                PricingAdviceItem(
                    variant_id=vid,
                    product_name=name,
                    variant_name=variant,
                    advice=advice,
                    current_price=float(current),
                    suggested_price=suggested,
                    priority=priority,
                )
            )
        return advice_items

    def explain_margin_warning(self, data: dict) -> str:
        net = data.get("net_margin_percent", 0)
        product = data.get("product_name", "this product")
        labour = data.get("labour_cost", 0)
        return (
            f"{product} has a net margin of {net:.1f}%. "
            f"Labour cost is £{labour:.2f} per item. "
            "If you pay yourself a market rate, this margin may fall further. "
            "Review your selling price or reduce recipe complexity."
        )


def get_ai_provider() -> AIProvider:
    """Factory — swap to ClaudeAIProvider or OpenAIProvider when ready."""
    return MockAIProvider()
