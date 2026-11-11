from __future__ import annotations

from pulsequeue import RoutingService


def test_batch_prefers_oldest_high_priority_ticket(ticket_factory, agent_factory):
    service = RoutingService()
    tickets = [
        ticket_factory(
            id="T-new-high",
            priority="P1",
            created_at="2026-11-11T09:30:00Z",
        ),
        ticket_factory(
            id="T-old-high",
            priority="P1",
            created_at="2026-11-11T09:00:00Z",
        ),
        ticket_factory(
            id="T-normal",
            priority="P2",
            created_at="2026-11-11T08:00:00Z",
        ),
    ]

    result = service.route(tickets, [agent_factory(capacity_minutes=40)])

    assert [assignment.ticket_id for assignment in result.assignments] == [
        "T-old-high"
    ]
    assert [ticket.id for ticket in result.unassigned] == [
        "T-new-high",
        "T-normal",
    ]


def test_shared_capacity_is_consumed_across_tickets(ticket_factory, agent_factory):
    service = RoutingService()
    tickets = [
        ticket_factory(id="T-1", priority="P1"),
        ticket_factory(id="T-2", priority="P1"),
    ]

    result = service.route(tickets, [agent_factory(capacity_minutes=45)])

    assert len(result.assignments) == 1
    assert len(result.unassigned) == 1


def test_lowest_current_load_is_selected(ticket_factory, agent_factory):
    service = RoutingService()
    first = service.route(
        [ticket_factory(id="T-1", priority="P2")],
        [
            agent_factory("A-1", capacity_minutes=100),
            agent_factory("A-2", capacity_minutes=100),
        ],
    )
    second = service.route(
        [ticket_factory(id="T-2", priority="P2")],
        [
            agent_factory("A-1", capacity_minutes=100),
            agent_factory("A-2", capacity_minutes=100),
        ],
    )

    assert first.assignments[0].agent_id == "A-1"
    assert second.assignments[0].agent_id == "A-2"


def test_cancel_releases_capacity_and_is_idempotent(
    ticket_factory, agent_factory
):
    service = RoutingService()
    agents = [agent_factory(capacity_minutes=30)]
    first = service.route([ticket_factory(id="T-1", priority="P1")], agents)

    assert first.assignments
    assert service.cancel("T-1") is True
    assert service.cancel("T-1") is False

    replacement = service.route(
        [ticket_factory(id="T-2", priority="P1")],
        agents,
    )
    assert [assignment.ticket_id for assignment in replacement.assignments] == [
        "T-2"
    ]


def test_inactive_agent_is_never_selected(ticket_factory, agent_factory):
    service = RoutingService()
    result = service.route(
        [ticket_factory()],
        [
            agent_factory("A-inactive", active=False),
            agent_factory("A-active", active=True),
        ],
    )

    assert [assignment.agent_id for assignment in result.assignments] == ["A-active"]


def test_duplicate_active_ticket_is_not_reassigned(ticket_factory, agent_factory):
    service = RoutingService()
    agents = [agent_factory("A-1"), agent_factory("A-2")]
    ticket = ticket_factory(id="T-1", priority="P2")

    first = service.route([ticket], agents)
    second = service.route([ticket], agents)

    assert len(first.assignments) == 1
    assert second.assignments == ()
    assert [item.id for item in second.unassigned] == ["T-1"]
