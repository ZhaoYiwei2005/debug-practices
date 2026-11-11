from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


PRIORITY_RANK = {
    "low": 0,
    "normal": 1,
    "high": 2,
    "critical": 3,
}

EFFORT_MINUTES = {
    "low": 10,
    "normal": 20,
    "high": 30,
    "critical": 45,
}


@dataclass(frozen=True, slots=True)
class Ticket:
    id: str
    subject: str
    priority: str
    created_at: datetime
    language: str
    requested_skill: str


@dataclass(frozen=True, slots=True)
class Agent:
    id: str
    skills: frozenset[str]
    languages: frozenset[str]
    capacity_minutes: int
    active: bool = True


@dataclass(frozen=True, slots=True)
class Assignment:
    ticket_id: str
    agent_id: str
    effort_minutes: int


@dataclass(frozen=True, slots=True)
class RouteResult:
    assignments: tuple[Assignment, ...]
    unassigned: tuple[Ticket, ...]
