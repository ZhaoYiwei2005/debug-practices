# Python Debugging Practices

This directory contains two self-contained Python debugging practices. Each
project has a small application, a behavioral specification, and tests that
currently fail.

## Practices

### 1. Ticket routing

A support-ticket router that normalizes incoming payloads, selects eligible
agents, respects shared capacity, and tracks active assignments.

```bash
cd 01-ticket-routing
python -m pytest -q
```

### 2. Metered billing

A layered billing service that handles usage ingestion, UTC billing periods,
progressive pricing tiers, discounts, tax, and final invoice totals.

```bash
cd 02-meter-billing
python -m pytest -q
```

Both projects include their own README and diagnosis template. Work through
the tests, identify the causes of the failures, and update application code
under `src/`.
