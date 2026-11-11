from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .models import Agent, Assignment, EFFORT_MINUTES, RouteResult, Ticket
from .normalization import normalize_agent, normalize_ticket
from .routing import choose_agent, order_tickets


class RoutingService:
    """Tracks active assignments and routes batches of tickets."""

    def __init__(self) -> None:
        self._active: dict[str, Assignment] = {}

    @property
    def assignments(self) -> tuple[Assignment, ...]:
        return tuple(self._active.values())

    def _ticket_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for assignment in self._active.values():
            counts[assignment.agent_id] = counts.get(assignment.agent_id, 0) + 1
        return counts

    def _used_minutes(self) -> dict[str, int]:
        used: dict[str, int] = {}
        for assignment in self._active.values():
            used[assignment.agent_id] = (
                used.get(assignment.agent_id, 0) + assignment.effort_minutes
            )
        return used

    def route(
        self,
        ticket_payloads: Sequence[Mapping[str, Any]],
        agent_payloads: Sequence[Mapping[str, Any]],
    ) -> RouteResult:
        tickets = [normalize_ticket(raw) for raw in ticket_payloads]
        agents = [normalize_agent(raw) for raw in agent_payloads]
        return self._route_normalized(tickets, agents)

    def _route_normalized(
        self,
        tickets: Sequence[Ticket],
        agents: Sequence[Agent],
    ) -> RouteResult:
        new_assignments: list[Assignment] = []
        unassigned: list[Ticket] = []

        for ticket in order_tickets(tickets):
            if ticket.id in self._active:
                unassigned.append(ticket)
                continue

            counts = self._ticket_counts()
            used = self._used_minutes()
            agent = choose_agent(ticket, agents, counts, used)
            if agent is None:
                unassigned.append(ticket)
                continue

            assignment = Assignment(
                ticket_id=ticket.id,
                agent_id=agent.id,
                effort_minutes=EFFORT_MINUTES[ticket.priority],
            )
            self._active[ticket.id] = assignment
            new_assignments.append(assignment)

        return RouteResult(
            assignments=tuple(new_assignments),
            unassigned=tuple(unassigned),
        )

    def cancel(self, ticket_id: str) -> bool:
        assignment = self._active.pop(ticket_id)
        return assignment is not None
