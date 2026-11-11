from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from .models import Agent, Ticket


class InvalidPayload(ValueError):
    """Raised when an inbound payload cannot be normalized."""


PRIORITY_ALIASES = {
    "p0": "critical",
    "urgent": "critical",
    "critical": "critical",
    "p1": "high",
    "high": "high",
    "p2": "normal",
    "normal": "normal",
    "p3": "low",
    "low": "low",
}


def _required_text(raw: Mapping[str, Any], key: str, location: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvalidPayload(f"{location}.{key} must be a non-empty string")
    return value.strip()


def _normalize_priority(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidPayload("ticket.priority must be a non-empty string")
    normalized = PRIORITY_ALIASES.get(value.lower())
    if normalized is None:
        raise InvalidPayload(f"unsupported ticket priority: {value!r}")
    return normalized


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, bool):
        raise InvalidPayload("ticket.created_at must be a timestamp or ISO-8601 string")

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value) / 1_000, tz=UTC)

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise InvalidPayload("ticket.created_at must not be empty")

        try:
            if stripped.isdigit():
                return datetime.fromtimestamp(float(stripped) / 1_000, tz=UTC)
            parsed = datetime.fromisoformat(stripped.replace("Z", "+00:00"))
        except (ValueError, OverflowError) as exc:
            raise InvalidPayload(f"invalid ticket.created_at: {value!r}") from exc

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    raise InvalidPayload("ticket.created_at must be a timestamp or ISO-8601 string")


def _normalized_string_list(
    value: Any,
    field_name: str,
    *,
    allow_empty: bool = True,
) -> frozenset[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise InvalidPayload(f"{field_name} must be a list of strings")
    normalized = {item.strip().lower() for item in value if item.strip()}
    if not normalized and not allow_empty:
        raise InvalidPayload(f"{field_name} must contain at least one value")
    return frozenset(normalized)


def normalize_ticket(raw: Mapping[str, Any]) -> Ticket:
    if not isinstance(raw, Mapping):
        raise InvalidPayload("ticket payload must be an object")

    requester = raw.get("requester")
    if not isinstance(requester, Mapping):
        raise InvalidPayload("ticket.requester must be an object")

    return Ticket(
        id=_required_text(raw, "id", "ticket"),
        subject=_required_text(raw, "subject", "ticket"),
        priority=_normalize_priority(raw.get("priority")),
        created_at=_parse_timestamp(raw.get("created_at")),
        language=_required_text(requester, "language", "ticket.requester").lower(),
        requested_skill=_required_text(
            raw, "requested_skill", "ticket"
        ).lower(),
    )


def normalize_agent(raw: Mapping[str, Any]) -> Agent:
    if not isinstance(raw, Mapping):
        raise InvalidPayload("agent payload must be an object")

    capacity = raw.get("capacity_minutes")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise InvalidPayload("agent.capacity_minutes must be a positive integer")

    active = raw.get("active", True)
    if not isinstance(active, bool):
        raise InvalidPayload("agent.active must be a boolean")

    return Agent(
        id=_required_text(raw, "id", "agent"),
        skills=_normalized_string_list(
            raw.get("skills"), "agent.skills", allow_empty=False
        ),
        languages=_normalized_string_list(
            raw.get("languages"), "agent.languages", allow_empty=False
        ),
        capacity_minutes=capacity,
        active=active,
    )
