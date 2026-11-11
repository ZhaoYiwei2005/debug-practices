from __future__ import annotations

import json
import sys
from pathlib import Path

from .service import RoutingService


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m pulsequeue <batch.json>")

    path = Path(sys.argv[1])
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = RoutingService().route(payload["tickets"], payload["agents"])

    print(f"Assigned {len(result.assignments)} ticket(s)")
    for assignment in result.assignments:
        print(
            f"  {assignment.ticket_id} -> {assignment.agent_id} "
            f"({assignment.effort_minutes} min)"
        )
    print(f"Unassigned {len(result.unassigned)} ticket(s)")
    for ticket in result.unassigned:
        print(f"  {ticket.id}: {ticket.priority}")


if __name__ == "__main__":
    main()
