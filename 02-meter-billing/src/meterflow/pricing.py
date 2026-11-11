from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .models import Plan


class PricingError(ValueError):
    """Raised when a plan cannot price the supplied usage."""


_CENT = Decimal("1")
_BPS_DIVISOR = Decimal("10000")


def _round_cents(value: Decimal) -> int:
    return int(value.quantize(_CENT, rounding=ROUND_HALF_UP))


def usage_charge_cents(units: int, plan: Plan) -> int:
    if units < 0:
        raise PricingError("usage units cannot be negative")

    remaining = max(0, units - plan.included_units)
    charge = Decimal("0")

    for tier in plan.tiers:
        if remaining == 0:
            break

        if tier.up_to_units is None:
            billable_units = remaining
        else:
            billable_units = min(remaining, tier.up_to_units)

        charge += Decimal(billable_units) * tier.unit_price_cents
        remaining -= billable_units

    if remaining > 0:
        raise PricingError(
            "usage exceeds the plan's finite tiers and has no open-ended tier"
        )

    return _round_cents(charge)


def calculate_totals(units: int, plan: Plan) -> tuple[int, int, int, int, int]:
    usage_cents = usage_charge_cents(units, plan)

    discount_cents = 0
    if (
        plan.discount_threshold_units is not None
        and units > plan.discount_threshold_units
    ):
        discount_cents = _round_cents(
            Decimal(plan.base_fee_cents + usage_cents)
            * Decimal(plan.discount_bps)
            / _BPS_DIVISOR
        )

    taxable_subtotal = plan.base_fee_cents + usage_cents - discount_cents
    tax_cents = _round_cents(
        Decimal(taxable_subtotal) * Decimal(plan.tax_rate_bps) / _BPS_DIVISOR
    )
    total_cents = taxable_subtotal + tax_cents
    return (
        plan.base_fee_cents,
        usage_cents,
        discount_cents,
        tax_cents,
        total_cents,
    )
