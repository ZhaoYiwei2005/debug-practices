from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class UsageEvent:
    id: str
    customer_id: str
    metric: str
    quantity: int
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class Tier:
    up_to_units: int | None
    unit_price_cents: Decimal


@dataclass(frozen=True, slots=True)
class Plan:
    base_fee_cents: int
    included_units: int
    tiers: tuple[Tier, ...]
    tax_rate_bps: int = 0
    discount_threshold_units: int | None = None
    discount_bps: int = 0


@dataclass(frozen=True, slots=True)
class Invoice:
    customer_id: str
    period: str
    usage_units: int
    base_fee_cents: int
    usage_cents: int
    discount_cents: int
    tax_cents: int
    total_cents: int
    event_ids: tuple[str, ...]
