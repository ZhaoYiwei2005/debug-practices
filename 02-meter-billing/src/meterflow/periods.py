from __future__ import annotations

import re
from datetime import UTC, datetime


class InvalidPeriod(ValueError):
    """Raised when a billing period is malformed."""


_PERIOD_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")


def parse_period(period: str) -> tuple[int, int]:
    match = _PERIOD_PATTERN.fullmatch(period)
    if match is None:
        raise InvalidPeriod(f"period must use YYYY-MM format: {period!r}")

    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        raise InvalidPeriod(f"period has an invalid month: {period!r}")
    return year, month


def billing_window(period: str) -> tuple[datetime, datetime]:
    year, month = parse_period(period)
    start = datetime(year, month, 1, tzinfo=UTC)
    end = datetime(year, month + 1, 1, tzinfo=UTC)
    return start, end


def period_for_timestamp(timestamp: datetime) -> str:
    if timestamp.tzinfo is None:
        raise InvalidPeriod("period timestamps must be timezone-aware")
    utc = timestamp.astimezone(UTC)
    return f"{utc.year:04d}-{utc.month:02d}"
