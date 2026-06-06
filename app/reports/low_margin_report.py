"""Pure functions for low-margin detection — no DB dependency."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class LowMarginItem:
    variant_id: str
    product_name: str
    variant_name: str
    current_selling_price: Decimal
    net_margin_percent: Decimal
    desired_margin_percent: Decimal
    shortfall_percent: Decimal
    severity: str  # warning, critical


def find_low_margin_items(
    variant_summaries: list[dict],
) -> list[LowMarginItem]:
    """
    variant_summaries: list of dicts with keys:
        variant_id, product_name, variant_name,
        current_selling_price, net_margin_percent, desired_margin_percent
    Returns only items that are below their desired margin.
    """
    low: list[LowMarginItem] = []
    for v in variant_summaries:
        net_margin = Decimal(str(v.get("net_margin_percent", "0")))
        desired = Decimal(str(v.get("desired_margin_percent", "50")))
        if net_margin < desired:
            shortfall = desired - net_margin
            severity = "critical" if net_margin < Decimal("0") else "warning"
            low.append(
                LowMarginItem(
                    variant_id=str(v["variant_id"]),
                    product_name=v.get("product_name", ""),
                    variant_name=v.get("variant_name", ""),
                    current_selling_price=Decimal(str(v.get("current_selling_price", "0"))),
                    net_margin_percent=net_margin,
                    desired_margin_percent=desired,
                    shortfall_percent=shortfall,
                    severity=severity,
                )
            )
    return sorted(low, key=lambda x: x.net_margin_percent)
