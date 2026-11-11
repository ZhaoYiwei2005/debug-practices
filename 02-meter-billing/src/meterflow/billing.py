from __future__ import annotations

from .ledger import UsageLedger
from .models import Invoice, Plan
from .periods import parse_period
from .pricing import calculate_totals


class BillingService:
    def __init__(self, ledger: UsageLedger) -> None:
        self.ledger = ledger

    def create_invoice(
        self,
        customer_id: str,
        period: str,
        plan: Plan,
    ) -> Invoice:
        parse_period(period)
        events = self.ledger.events_for_period(customer_id, period)
        usage_units = sum(event.quantity for event in events)
        base, usage, discount, tax, total = calculate_totals(usage_units, plan)

        return Invoice(
            customer_id=customer_id.strip().lower(),
            period=period,
            usage_units=usage_units,
            base_fee_cents=base,
            usage_cents=usage,
            discount_cents=discount,
            tax_cents=tax,
            total_cents=total,
            event_ids=tuple(event.id for event in events),
        )
