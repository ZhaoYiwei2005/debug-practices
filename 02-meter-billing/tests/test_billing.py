from __future__ import annotations

from meterflow import BillingService, UsageLedger


def test_complete_invoice_for_mixed_event_inputs(
    event_factory,
    standard_plan,
):
    ledger = UsageLedger()
    ledger.ingest(
        [
            event_factory(
                id="evt-1",
                customer_id=" ACME ",
                quantity=1000,
                occurred_at="2026-11-01T00:00:00Z",
            ),
            event_factory(
                id="evt-2",
                customer_id="acme",
                quantity=800,
                occurred_at=1794825600,
            ),
            event_factory(
                id="evt-3",
                customer_id="AcMe",
                quantity=700,
                occurred_at="2026-11-20T15:00:00+03:00",
            ),
        ]
    )

    invoice = BillingService(ledger).create_invoice(
        " ACME ",
        "2026-11",
        standard_plan,
    )

    assert invoice.customer_id == "acme"
    assert invoice.period == "2026-11"
    assert invoice.usage_units == 2500
    assert invoice.base_fee_cents == 1200
    assert invoice.usage_cents == 900
    assert invoice.discount_cents == 90
    assert invoice.tax_cents == 176
    assert invoice.total_cents == 2186
    assert invoice.event_ids == ("evt-1", "evt-2", "evt-3")


def test_invoice_excludes_usage_from_other_customers_and_months(
    event_factory,
    standard_plan,
):
    ledger = UsageLedger()
    ledger.ingest(
        [
            event_factory(
                id="included",
                quantity=1200,
                occurred_at="2026-11-15T12:00:00Z",
            ),
            event_factory(
                id="other-customer",
                customer_id="globex",
                quantity=5000,
                occurred_at="2026-11-15T12:00:00Z",
            ),
            event_factory(
                id="decimal-boundary",
                quantity=5000,
                occurred_at="2026-12-01T00:00:00Z",
            ),
        ]
    )

    invoice = BillingService(ledger).create_invoice("acme", "2026-11", standard_plan)

    assert invoice.usage_units == 1200
    assert invoice.event_ids == ("included",)


def test_month_with_no_usage_still_produces_base_invoice(
    standard_plan,
):
    invoice = BillingService(UsageLedger()).create_invoice(
        "acme",
        "2026-11",
        standard_plan,
    )

    assert invoice.usage_units == 0
    assert invoice.usage_cents == 0
    assert invoice.total_cents == 1305
