# MeterFlow Advanced Debugging Practical

MeterFlow turns metered usage events into monthly customer invoices. The
service has four layers:

```text
raw usage JSON
      |
      v
normalization.py ----> UTC UsageEvent objects
      |
      v
ledger.py -----------> idempotent event storage and period queries
      |
      v
pricing.py ----------> marginal tiers, discounts, and tax
      |
      v
billing.py ----------> complete invoices
```

Several tests are failing. Your job is to restore the behavior specified below.
Change application code under `src/`; do not change the tests.

## Run it

```bash
python -m pytest -q
```

Focused commands:

```bash
python -m pytest tests/test_periods.py tests/test_normalization.py -q
python -m pytest tests/test_ledger.py -q
python -m pytest tests/test_pricing.py -q
python -m pytest tests/test_billing.py -q
```

Generate the sample invoice:

```bash
PYTHONPATH=src python -m meterflow data/sample_invoice.json
```

## Behavioral contract

### Usage events

- Every event has an `id`, `customer_id`, `metric`, positive integer
  `quantity`, and `occurred_at`.
- IDs, customers, and metrics are trimmed. Customer IDs and metrics are
  lowercase.
- `occurred_at` accepts ISO-8601, Unix seconds, or Unix milliseconds. It is
  always returned as a timezone-aware datetime in UTC.
- Booleans are not valid quantities or timestamps.

### Billing periods

- A period is a string in `YYYY-MM` form.
- Its billing window is `[first instant of the month, first instant of the
  following month)` in UTC. The start is included; the end is excluded.
- December correctly rolls over into January of the following year.
- Invalid malformed periods or month numbers raise `InvalidPeriod`.

### Usage ledger

- An event ID represents one logical event across the whole ledger.
- Re-ingesting an identical event is idempotent and is reported as a
  duplicate.
- Reusing an event ID with a different normalized payload raises
  `LedgerConflict`.
- Batch ingestion is atomic. If any event in a batch conflicts, no event from
  that batch is added.
- Period queries include only the requested customer and the half-open UTC
  window. Results are ordered by `occurred_at`, then event ID.

### Pricing

- The subscription base fee is charged every month, including months with no
  usage.
- `included_units` are free. Tier boundaries apply to usage **above the
  included allowance**, not to total usage.
- Tiers are marginal/progressive. The first block is charged at the first
  rate, the next block at the second rate, and so on.
- A tier's `up_to_units` is a cumulative overage-unit boundary. `None` marks
  the final open-ended tier.
- All money is represented in integer cents at API boundaries, but
  intermediate rate calculations use `Decimal` and round once to the nearest
  cent using `ROUND_HALF_UP`.
- If usage exceeds the last finite tier and there is no open-ended tier,
  raise `PricingError`.

Volume discounts:

- When `discount_threshold_units` is set, the discount applies when total
  monthly usage is greater than **or equal to** that threshold.
- The discount percentage applies only to the metered usage charge, never to
  the base fee.
- Tax applies to the base fee plus metered usage, minus the discount.
- The discount and tax are each rounded to whole cents with `ROUND_HALF_UP`.

### Invoice fields

`BillingService.create_invoice()` returns:

- `customer_id` and `period`;
- `usage_units`;
- `base_fee_cents`;
- `usage_cents`;
- `discount_cents`;
- `tax_cents`;
- `total_cents`;
- the included event IDs.

## Example standard plan

The tests use this plan shape frequently:

- base fee: 1,200 cents;
- included usage: 1,000 units;
- overage tiers:
  - first 500 overage units at 0.80 cents/unit;
  - next 1,000 overage units at 0.50 cents/unit;
  - remaining overage units at 0.30 cents/unit;
- volume discount: 10% at 2,000 total units;
- tax: 8.75%.

For 2,500 total units:

```text
overage             = 1,500
usage charge        = 500 × 0.80 + 1,000 × 0.50 = 900 cents
volume discount     = 10% × 900 = 90 cents
taxable subtotal    = 1,200 + 900 - 90 = 2,010 cents
tax, half-up        = 175.875 -> 176 cents
total               = 2,186 cents
```

## Suggested workflow

1. Read the contract and identify each module's responsibility.
2. Run all tests and group failures by behavior rather than by file.
3. Work inside-out: normalization and periods, then ledger, pricing, and
   finally integration.
4. After each fix, rerun the focused test and the full suite to detect
   regressions.
5. Fill in `diagnosis-template.md` with a reproduction, root cause, and fix
   for each defect.

A strong debugging note should make the failing input, expected result, actual
result, faulty branch, and verification command explicit.
