from __future__ import annotations

import pytest

from meterflow import LedgerConflict, UsageLedger


def test_ingest_reports_new_events(event_factory):
    ledger = UsageLedger()
    result = ledger.ingest(
        [event_factory(id="evt-1"), event_factory(id="evt-2")]
    )

    assert [event.id for event in result.accepted] == ["evt-1", "evt-2"]
    assert result.duplicates == ()


def test_identical_reingestion_is_idempotent(event_factory):
    ledger = UsageLedger()
    payload = event_factory(id="evt-1")
    ledger.ingest([payload])

    result = ledger.ingest([payload])

    assert result.accepted == ()
    assert [event.id for event in result.duplicates] == ["evt-1"]
    assert len(ledger.events) == 1


def test_conflicting_event_id_raises(event_factory):
    ledger = UsageLedger()
    ledger.ingest([event_factory(id="evt-1", quantity=10)])

    with pytest.raises(LedgerConflict, match="evt-1"):
        ledger.ingest([event_factory(id="evt-1", quantity=11)])


def test_conflicting_batch_is_atomic(event_factory):
    ledger = UsageLedger()
    batch = [
        event_factory(id="evt-1", quantity=10),
        event_factory(id="evt-1", quantity=99),
    ]

    with pytest.raises(LedgerConflict):
        ledger.ingest(batch)

    assert ledger.events == ()


def test_period_query_is_customer_scoped_and_half_open(event_factory):
    ledger = UsageLedger()
    ledger.ingest(
        [
            event_factory(
                id="before",
                occurred_at="2026-10-31T23:59:59Z",
            ),
            event_factory(
                id="start",
                occurred_at="2026-11-01T00:00:00Z",
            ),
            event_factory(
                id="end",
                occurred_at="2026-12-01T00:00:00Z",
            ),
            event_factory(
                id="other-customer",
                customer_id="globex",
                occurred_at="2026-11-15T12:00:00Z",
            ),
            event_factory(
                id="inside",
                occurred_at="2026-11-30T23:59:59Z",
            ),
        ]
    )

    events = ledger.events_for_period("ACME", "2026-11")

    assert [event.id for event in events] == ["start", "inside"]


def test_period_query_is_chronological_then_id(event_factory):
    ledger = UsageLedger()
    ledger.ingest(
        [
            event_factory(id="evt-b", occurred_at="2026-11-15T12:00:00Z"),
            event_factory(id="evt-c", occurred_at="2026-11-20T12:00:00Z"),
            event_factory(id="evt-a", occurred_at="2026-11-15T12:00:00Z"),
        ]
    )

    events = ledger.events_for_period("acme", "2026-11")

    assert [event.id for event in events] == ["evt-a", "evt-b", "evt-c"]
