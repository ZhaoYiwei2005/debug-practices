from __future__ import annotations

from copy import deepcopy

import pytest


@pytest.fixture
def ticket_factory():
    base = {
        "id": "T-1",
        "subject": "Cannot complete checkout",
        "priority": "P1",
        "created_at": "2026-11-11T09:00:00Z",
        "requester": {"language": "en"},
        "requested_skill": "payments",
    }

    def make(**overrides):
        ticket = deepcopy(base)
        requester_overrides = overrides.pop("requester", {})
        ticket.update(overrides)
        ticket["requester"].update(requester_overrides)
        return ticket

    return make


@pytest.fixture
def agent_factory():
    def make(
        agent_id="A-1",
        *,
        skills=("payments",),
        languages=("en",),
        capacity_minutes=60,
        active=True,
    ):
        return {
            "id": agent_id,
            "skills": list(skills),
            "languages": list(languages),
            "capacity_minutes": capacity_minutes,
            "active": active,
        }

    return make
