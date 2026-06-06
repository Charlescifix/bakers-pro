from decimal import Decimal


def classify_quote(
    net_profit: Decimal,
    net_margin_pct: Decimal,
    food_cost_pct: Decimal,
    desired_margin_pct: Decimal,
) -> str:
    if net_profit < 0:
        return "loss_making"
    if food_cost_pct > Decimal("40"):
        return "high_food_cost"
    if net_margin_pct < Decimal("20"):
        return "low_margin"
    if net_margin_pct >= desired_margin_pct:
        return "excellent"
    return "profitable"


def margin_warnings(
    net_profit: Decimal,
    net_margin_pct: Decimal,
    food_cost_pct: Decimal,
    desired_margin_pct: Decimal,
    channel_fees: Decimal = Decimal("0"),
    channel_name: str | None = None,
) -> list[str]:
    warnings = []
    if net_profit < 0:
        warnings.append("This order is loss-making. Review your pricing.")
    elif net_margin_pct < Decimal("20"):
        warnings.append(f"Net margin is {net_margin_pct:.1f}% — below the recommended 20%.")
    if food_cost_pct > Decimal("40"):
        warnings.append(f"Food cost is {food_cost_pct:.1f}% — above the 40% target.")
    if net_margin_pct < desired_margin_pct and net_profit >= 0:
        warnings.append(
            f"Margin is {net_margin_pct:.1f}%, below your desired {desired_margin_pct:.1f}%."
        )
    if channel_fees > 0 and channel_name:
        warnings.append(f"{channel_name} fees reduce profit by £{channel_fees:.2f}.")
    return warnings
