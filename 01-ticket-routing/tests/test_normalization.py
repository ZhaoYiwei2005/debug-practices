from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pulsequeue import InvalidPayload, normalize_agent, normalize_ticket


@pytest.mark.parametrize(
    ("raw_priority", "expected"),
    [
        ("P0", "critical"),
        ("urgent", "critical"),
        (" P1 ", "high"),
        ("HIGH", "high"),
        ("p2", "normal"),
        (" low ", "low"),
    ],
)
def test_priority_aliases_are_canonicalized(ticket_factory, raw_priority, expected):
    ticket = normalize_ticket(ticket_factory(priority=raw_priority))
    assert ticket.priority == expected


@pytest.mark.parametrize("timestamp", [1794387600, 1794387600000])
def test_numeric_timestamps_are_supported(ticket_factory, timestamp):
    ticket = normalize_ticket(ticket_factory(created_at=timestamp))
    assert ticket.created_at == datetime(2026, 11, 11, 9, 0, tzinfo=UTC)


def test_iso_timestamp_with_z_is_converted_to_utc(ticket_factory):
    ticket = normalize_ticket(
        ticket_factory(created_at="2026-11-11T11:30:00+02:30")
    )
    assert ticket.created_at == datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
    assert ticket.created_at.tzinfo is UTC


def test_agent_skills_and_languages_are_normalized(ticket_factory, agent_factory):
    agent = normalize_agent(
        agent_factory(
            skills=(" Payments ", "security", "PAYMENTS"),
            languages=(" EN ", "de"),
        )
    )
    assert agent.skills == frozenset({"payments", "security"})
    assert agent.languages == frozenset({"en", "de"})


def test_missing_required_ticket_field_has_useful_error(ticket_factory):
    raw = ticket_factory()
    del raw["requested_skill"]
    with pytest.raises(InvalidPayload, match="ticket.requested_skill"):
        normalize_ticket(raw)


def test_unknown_priority_is_rejected(ticket_factory):
    with pytest.raises(InvalidPayload, match="unsupported ticket priority"):
        normalize_ticket(ticket_factory(priority="P9"))
