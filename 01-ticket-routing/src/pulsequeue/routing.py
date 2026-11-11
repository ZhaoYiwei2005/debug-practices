from __future__ import annotations

from collections.abc import Mapping, Sequence

from .models import PRIORITY_RANK, Agent, EFFORT_MINUTES, Ticket


def order_tickets(tickets: Sequence[Ticket]) -> list[Ticket]:
    return sorted(
        tickets,
        key=lambda ticket: (
            PRIORITY_RANK[ticket.priority],
            ticket.created_at,
            ticket.id,
        ),
        reverse=True,
    )


def remaining_capacity(
    agent: Agent,
    used_minutes: Mapping[str, int],
) -> int:
    return agent.capacity_minutes - used_minutes.get(agent.id, 0)


def eligible_agents(
    ticket: Ticket,
    agents: Sequence[Agent],
    used_minutes: Mapping[str, int],
) -> list[Agent]:
    candidates: list[Agent] = []
    effort = EFFORT_MINUTES[ticket.priority]

    for agent in agents:
        if not agent.active:
            continue
        if (
            ticket.requested_skill not in agent.skills
            and ticket.language not in agent.languages
        ):
            continue
        if remaining_capacity(agent, used_minutes) <= effort:
            continue
        candidates.append(agent)

    return candidates


def choose_agent(
    ticket: Ticket,
    agents: Sequence[Agent],
    active_ticket_counts: Mapping[str, int],
    used_minutes: Mapping[str, int],
) -> Agent | None:
    candidates = eligible_agents(ticket, agents, used_minutes)
    if not candidates:
        return None

    return min(
        candidates,
        key=lambda agent: (
            active_ticket_counts.get(agent.id, 0),
            -agent.capacity_minutes,
            agent.id,
        ),
    )
