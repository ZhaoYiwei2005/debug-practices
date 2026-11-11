from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from .models import UsageEvent


class InvalidUsageEvent(ValueError):
    """Raised when a metered usage payload cannot be normalized."""


def _required_text(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvalidUsageEvent(f"event.{key} must be a non-empty string")
    return value.strip()


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, bool):
        raise InvalidUsageEvent("event.occurred_at must not be a boolean")

    if isinstance(value, (int, float)):
        seconds = float(value)
        if abs(seconds) >= 100_000_000_000:
            seconds /= 1_000
        return datetime.fromtimestamp(seconds, tz=UTC)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise InvalidUsageEvent("event.occurred_at must not be empty")
        try:
            if text.isdigit():
                numeric = float(text)
                if abs(numeric) >= 100_000_000_000:
                    numeric /= 1_000
                return datetime.fromtimestamp(numeric, tz=UTC)
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except (ValueError, OverflowError) as exc:
            raise InvalidUsageEvent(
                f"invalid event.occurred_at: {value!r}"
            ) from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    raise InvalidUsageEvent("event.occurred_at must be a timestamp or ISO-8601 string")


def normalize_usage_event(raw: Mapping[str, Any]) -> UsageEvent:
    if not isinstance(raw, Mapping):
        raise InvalidUsageEvent("usage event must be an object")

    quantity = raw.get("quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise InvalidUsageEvent("event.quantity must be a positive integer")

    return UsageEvent(
        id=_required_text(raw, "id"),
        customer_id=_required_text(raw, "customer_id").lower(),
        metric=_required_text(raw, "metric").lower(),
        quantity=quantity,
        occurred_at=_parse_timestamp(raw.get("occurred_at")),
    )
