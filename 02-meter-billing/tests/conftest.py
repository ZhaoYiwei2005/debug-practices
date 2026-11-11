from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

import pytest

from meterflow.models import Plan, Tier


@pytest.fixture
def event_factory():
    base = {
        "id": "evt-1",
        "customer_id": "acme",
        "metric": "api requests",
        "quantity": 100,
        "occurred_at": "2026-11-15T12:00:00Z",
    }

    def make(**overrides):
        event = deepcopy(base)
        event.update(overrides)
        return event

    return make


@pytest.fixture
def standard_plan() -> Plan:
    return Plan(
        base_fee_cents=1200,
        included_units=1000,
        tiers=(
            Tier(up_to_units=500, unit_price_cents=Decimal("0.80")),
            Tier(up_to_units=1500, unit_price_cents=Decimal("0.50")),
            Tier(up_to_units=None, unit_price_cents=Decimal("0.30")),
        ),
        tax_rate_bps=875,
        discount_threshold_units=2000,
        discount_bps=1000,
    )
