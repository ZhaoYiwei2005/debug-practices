# PulseQueue Debugging Practical

PulseQueue assigns incoming support tickets to on-call support agents. The
project is deliberately small, but a ticket passes through several layers:

```text
JSON payload
    |
    v
normalization.py  ->  Ticket / Agent models
    |
    v
routing.py        ->  eligibility and ordering
    |
    v
service.py        ->  assignment state and capacity accounting
```

The implementation is not passing its test suite. Your task is to restore the
behavior described below. You may change application code under `src/`. For
this practice, do not change the tests.

## Run the tests

```bash
python -m pytest -q
```

For a shorter feedback loop:

```bash
python -m pytest tests/test_normalization.py -q
python -m pytest tests/test_routing.py -q
python -m pytest tests/test_service.py -q
```

You can also run the sample input:

```bash
PYTHONPATH=src python -m pulsequeue data/sample_batch.json
```

## Required behavior

### Input normalization

- Ticket priorities are case-insensitive and may have surrounding whitespace.
- Priority aliases are:

  | Accepted values | Canonical value |
  | --- | --- |
  | `P0`, `urgent`, `critical` | `critical` |
  | `P1`, `high` | `high` |
  | `P2`, `normal` | `normal` |
  | `P3`, `low` | `low` |

- `created_at` may be an ISO-8601 string, Unix seconds, or Unix milliseconds.
  Every returned timestamp must be timezone-aware and expressed in UTC.
- Skills and languages are case-insensitive. Agent skills and languages are
  deduplicated.
- Missing required fields or an invalid known field should raise
  `InvalidPayload`.

### Routing

- An agent is eligible only when all of these are true:
  - the agent is active;
  - the agent has the ticket's exact requested skill;
  - the agent speaks the requester's language;
  - the agent has at least enough unused minutes for the ticket.
- Estimated effort is 45 minutes for `critical`, 30 for `high`, 20 for
  `normal`, and 10 for `low` tickets.
- A batch is considered in this order:
  1. priority (`critical` first, then `high`, `normal`, `low`);
  2. submission time (oldest first);
  3. ticket ID (lexicographically).
- When several agents are eligible, choose the agent with the fewest active
  tickets. If loads tie, choose the agent with the larger total capacity, then
  the lexicographically smaller agent ID.
- Tickets with no eligible agent are returned as unassigned rather than
  causing the entire batch to fail.

### Assignment state

- Accepted assignments consume their estimated minutes from the agent's
  capacity. Capacity is shared across all tickets in the batch.
- Cancelling an active assignment releases its minutes immediately.
- Cancelling an unknown or already-cancelled ticket is a harmless no-op.
- A duplicate ticket ID in an active server is not reassigned.

## Suggested 60-minute workflow

1. Spend 5 minutes reading the README, directory layout, and tests.
2. Run the full suite and group failures by the layer where behavior diverges.
3. Reproduce one failure at a time with the smallest useful input.
4. Fix the root cause, then rerun both the focused test and the full suite.
5. Record a concise explanation using `diagnosis-template.md`.

A strong debugging note connects each failing assertion to a specific code
path, describes why the implementation differs from the contract, and states
how the fix was verified.
