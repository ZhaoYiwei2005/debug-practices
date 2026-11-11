from __future__ import annotations

from datetime import UTC, datetime

import pytest

from meterflow.periods import InvalidPeriod, billing_window, parse_period, period_for_timestamp


def test_parse_period_returns_year_and_month():
    assert parse_period("2026-11") == (2026, 11)


@pytest.mark.parametrize("period", ["2026-1", "2026-13", "November 2026", ""])
def test_invalid_periods_are_rejected(period):
    with pytest.raises(InvalidPeriod):
        parse_period(period)


def test_november_billing_window_is_half_open():
    start, end = billing_window("2026-11")

    assert start == datetime(2026, 11, 1, tzinfo=UTC)
    assert end == datetime(2026, 12, 1, tzinfo=UTC)


def test_december_billing_window_rolls_into_next_year():
    start, end = billing_window("2026-12")

    assert start == datetime(2026, 12, 1, tzinfo=UTC)
    assert end == datetime(2027, 1, 1, tzinfo=UTC)


def test_period_for_timestamp_converts_non_utc_timezone():
    timestamp = datetime(2026, 11, 30, 23, 45, tzinfo=UTC).astimezone(
        datetime.now().astimezone().tzinfo
    )
    assert period_for_timestamp(timestamp) == "2026-11"


def test_period_for_naive_timestamp_is_rejected():
    with pytest.raises(InvalidPeriod):
        period_for_timestamp(datetime(2026, 11, 1))
