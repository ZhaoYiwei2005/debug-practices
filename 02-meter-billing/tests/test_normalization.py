from __future__ import annotations

from datetime import UTC, datetime

import pytest

from meterflow import InvalidUsageEvent, normalize_usage_event


def test_event_text_fields_are_trimmed_and_lowercased(event_factory):
    event = normalize_usage_event(
        event_factory(
            id="  evt-42 ",
            customer_id="  AcMe-42 ",
            metric="  API Requests ",
        )
    )

    assert event.id == "evt-42"
    assert event.customer_id == "acme-42"
    assert event.metric == "api requests"


def test_iso_timestamp_is_converted_to_utc(event_factory):
    event = normalize_usage_event(
        event_factory(occurred_at="2026-11-15T12:30:00+03:30")
    )
    assert event.occurred_at == datetime(2026, 11, 15, 9, 0, tzinfo=UTC)


@pytest.mark.parametrize("timestamp", [1794830400, 1794830400000])
def test_numeric_timestamps_are_supported(event_factory, timestamp):
    event = normalize_usage_event(event_factory(occurred_at=timestamp))
    assert event.occurred_at == datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


def test_naive_iso_timestamp_is_interpreted_as_utc(event_factory):
    event = normalize_usage_event(
        event_factory(occurred_at="2026-11-15T12:00:00")
    )
    assert event.occurred_at == datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
    assert event.occurred_at.tzinfo is UTC


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True, "10"])
def test_invalid_quantities_are_rejected(event_factory, quantity):
    with pytest.raises(InvalidUsageEvent, match="quantity"):
        normalize_usage_event(event_factory(quantity=quantity))


@pytest.mark.parametrize("field", ["id", "customer_id", "metric"])
def test_missing_text_fields_are_rejected(event_factory, field):
    raw = event_factory()
    raw[field] = " "
    with pytest.raises(InvalidUsageEvent, match=field):
        normalize_usage_event(raw)
