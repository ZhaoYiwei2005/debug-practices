from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .models import UsageEvent
from .normalization import normalize_usage_event
from .periods import billing_window


class LedgerConflict(ValueError):
    """Raised when an event ID is reused with a different payload."""


@dataclass(frozen=True, slots=True)
class IngestResult:
    accepted: tuple[UsageEvent, ...]
    duplicates: tuple[UsageEvent, ...]


class UsageLedger:
    def __init__(self) -> None:
        self._events: dict[str, UsageEvent] = {}

    @property
    def events(self) -> tuple[UsageEvent, ...]:
        return tuple(
            sorted(
                self._events.values(),
                key=lambda event: (event.occurred_at, event.id),
            )
        )

    def ingest(self, payloads: Sequence[Mapping[str, Any]]) -> IngestResult:
        normalized = [normalize_usage_event(payload) for payload in payloads]
        accepted: list[UsageEvent] = []
        duplicates: list[UsageEvent] = []

        for event in normalized:
            existing = self._events.get(event.id)
            if existing is not None:
                if existing != event:
                    raise LedgerConflict(
                        f"event {event.id!r} already exists with different data"
                    )
                duplicates.append(event)
                continue

            self._events[event.id] = event
            accepted.append(event)

        return IngestResult(tuple(accepted), tuple(duplicates))

    def events_for_period(
        self,
        customer_id: str,
        period: str,
    ) -> tuple[UsageEvent, ...]:
        start, end = billing_window(period)
        customer = customer_id.strip().lower()
        matching = [
            event
            for event in self._events.values()
            if event.customer_id == customer
            and start <= event.occurred_at <= end
        ]
        return tuple(
            sorted(
                matching,
                key=lambda event: event.occurred_at,
                reverse=True,
            )
        )
