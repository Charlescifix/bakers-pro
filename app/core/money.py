from decimal import Decimal, ROUND_HALF_UP

MONEY_PLACES = Decimal("0.01")
COST_PLACES = Decimal("0.000001")
PERCENT_PLACES = Decimal("0.0001")


def q_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def q_cost(value: Decimal) -> Decimal:
    return value.quantize(COST_PLACES, rounding=ROUND_HALF_UP)


def q_percent(value: Decimal) -> Decimal:
    return value.quantize(PERCENT_PLACES, rounding=ROUND_HALF_UP)


def to_decimal(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
