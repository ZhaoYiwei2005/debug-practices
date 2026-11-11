from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

from .billing import BillingService
from .ledger import UsageLedger
from .models import Plan, Tier


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m meterflow <invoice.json>")

    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    plan_data = payload["plan"]
    plan = Plan(
        base_fee_cents=plan_data["base_fee_cents"],
        included_units=plan_data["included_units"],
        tiers=tuple(
            Tier(
                up_to_units=tier["up_to_units"],
                unit_price_cents=Decimal(tier["unit_price_cents"]),
            )
            for tier in plan_data["tiers"]
        ),
        tax_rate_bps=plan_data.get("tax_rate_bps", 0),
        discount_threshold_units=plan_data.get("discount_threshold_units"),
        discount_bps=plan_data.get("discount_bps", 0),
    )

    ledger = UsageLedger()
    ledger.ingest(payload["events"])
    invoice = BillingService(ledger).create_invoice(
        payload["customer_id"],
        payload["period"],
        plan,
    )

    print(f"Invoice for {invoice.customer_id}, {invoice.period}")
    print(f"  Usage:    {invoice.usage_units} units")
    print(f"  Base:     {invoice.base_fee_cents} cents")
    print(f"  Usage:    {invoice.usage_cents} cents")
    print(f"  Discount: {invoice.discount_cents} cents")
    print(f"  Tax:      {invoice.tax_cents} cents")
    print(f"  Total:    {invoice.total_cents} cents")


if __name__ == "__main__":
    main()
