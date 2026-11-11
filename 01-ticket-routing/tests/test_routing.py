from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pulsequeue.models import Agent, Ticket
from pulsequeue.routing import choose_agent, order_tickets


def make_ticket(
    ticket_id: str,
    priority: str,
    created_at: datetime,
    *,
    skill: str = "payments",
    language: str = "en",
) -> Ticket:
    return Ticket(
        id=ticket_id,
        subject=ticket_id,
        priority=priority,
        created_at=created_at,
        language=language,
        requested_skill=skill,
    )


def test_batch_order_is_priority_then_oldest_submission():
    base = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
    tickets = [
        make_ticket("T-low", "low", base),
        make_ticket("T-high-new", "high", base + timedelta(minutes=10)),
        make_ticket("T-critical", "critical", base + timedelta(minutes=5)),
        make_ticket("T-high-old", "high", base),
    ]

    ordered = order_tickets(tickets)

    assert [ticket.id for ticket in ordered] == [
        "T-critical",
        "T-high-old",
        "T-high-new",
        "T-low",
    ]


def test_agent_must_match_both_skill_and_language():
    ticket = make_ticket(
        "T-1",
        "high",
        datetime(2026, 11, 11, 9, 0, tzinfo=UTC),
        skill="payments",
        language="de",
    )
    skill_only = Agent(
        id="A-skill-only",
        skills=frozenset({"payments"}),
        languages=frozenset({"en"}),
        capacity_minutes=120,
    )
    language_only = Agent(
        id="A-language-only",
        skills=frozenset({"analytics"}),
        languages=frozenset({"de"}),
        capacity_minutes=60,
    )
    correct = Agent(
        id="A-correct",
        skills=frozenset({"payments"}),
        languages=frozenset({"de"}),
        capacity_minutes=60,
    )

    chosen = choose_agent(ticket, [skill_only, language_only, correct], {}, {})

    assert chosen == correct


def test_agent_with_exactly_enough_capacity_is_eligible():
    ticket = make_ticket(
        "T-1",
        "high",
        datetime(2026, 11, 11, 9, 0, tzinfo=UTC),
    )
    agent = Agent(
        id="A-1",
        skills=frozenset({"payments"}),
        languages=frozenset({"en"}),
        capacity_minutes=30,
    )

    assert choose_agent(ticket, [agent], {}, {}) == agent
