from __future__ import annotations

from decimal import Decimal

import pytest

from meterflow import Plan, PricingError, Tier, calculate_totals, usage_charge_cents


def test_included_usage_has_no_usage_charge(standard_plan):
    assert usage_charge_cents(1000, standard_plan) == 0


def test_tiers_are_charged_using_cumulative_boundaries(standard_plan):
    assert usage_charge_cents(2000, standard_plan) == 650
    assert usage_charge_cents(3000, standard_plan) == 1050
    assert usage_charge_cents(5000, standard_plan) == 1650


def test_exact_tier_boundary_only_charges_units_in_that_block(standard_plan):
    assert usage_charge_cents(2500, standard_plan) == 900


def test_fractional_charge_rounds_half_up():
    plan = Plan(
        base_fee_cents=0,
        included_units=0,
        tiers=(Tier(None, Decimal("0.05")),),
    )
    assert usage_charge_cents(10, plan) == 1


def test_open_ended_tier_is_required_after_last_finite_tier():
    plan = Plan(
        base_fee_cents=0,
        included_units=0,
        tiers=(Tier(10, Decimal("1")),),
    )

    with pytest.raises(PricingError):
        usage_charge_cents(11, plan)


def test_discount_applies_at_exact_threshold(standard_plan):
    base, usage, discount, tax, total = calculate_totals(2000, standard_plan)

    assert base == 1200
    assert usage == 650
    assert discount == 65
    assert tax == 156
    assert total == 1941


def test_discount_never_applies_to_base_fee(standard_plan):
    base, usage, discount, tax, total = calculate_totals(3000, standard_plan)

    assert base == 1200
    assert usage == 1050
    assert discount == 105
    assert tax == 188
    assert total == 2333


def test_no_usage_still_returns_base_fee_and_tax(standard_plan):
    assert calculate_totals(0, standard_plan) == (1200, 0, 0, 105, 1305)
