"""The engine against the hand-verified dev examples, plus the edge cases they don't cover."""

from dataclasses import replace
from decimal import Decimal

import pytest

from clause.engine import EngineError, adjudicate
from clause.io import load_claim, load_expected
from clause.models import Facts, Rule, RuleSet

from .conftest import DATA

DEV = sorted((DATA / "claims" / "dev").glob("*.json"))


@pytest.mark.parametrize("path", DEV, ids=lambda p: p.stem)
def test_engine_matches_hand_calculation(path, ruleset):
    """With gold facts, the engine must reproduce every hand-computed outcome exactly."""
    claim = load_claim(path)
    expected = load_expected(DATA / "expected" / "dev" / path.name)
    dec = adjudicate(claim, expected.facts, ruleset)
    assert dec.status == expected.status
    if expected.total_payable is not None:
        assert dec.total_payable == expected.total_payable
    assert set(expected.required_rules) <= set(dec.applied_rules)
    assert not set(expected.forbidden_rules) & set(dec.applied_rules)


def _c2(ruleset):
    claim = load_claim(DATA / "claims" / "dev" / "C0002.json")
    facts = load_expected(DATA / "expected" / "dev" / "C0002.json").facts
    return claim, facts


def test_proportionate_deduction_spares_unassociated_lines(ruleset):
    claim, facts = _c2(ruleset)
    dec = adjudicate(claim, facts, ruleset)
    payable = {ln.category: ln.payable for ln in dec.lines}
    assert payable["pharmacy"] == Decimal("15000.00")
    assert payable["diagnostics"] == Decimal("8000.00")
    assert payable["ot_charges"] == Decimal("13333.33")


def test_unreviewed_rules_are_ignored_unless_asked(ruleset):
    claim, facts = _c2(ruleset)
    rules = [replace(r, status="candidate") if r.id == "SYN-RR" else r for r in ruleset.rules]
    rs = RuleSet(ruleset.policy_id, rules, ruleset.calculation_order)
    assert adjudicate(claim, facts, rs).total_payable == Decimal("91000.00")
    assert adjudicate(claim, facts, rs, allow_unreviewed=True).total_payable == Decimal("68333.33")


def test_calculation_order_changes_the_result(ruleset):
    """Sub-limit then co-pay is not the same as co-pay then sub-limit. Order is policy data."""
    claim = load_claim(DATA / "claims" / "dev" / "C0004.json")
    claim = replace(claim, dob=claim.dob.replace(year=1950))  # make the claimant a senior
    facts = load_expected(DATA / "expected" / "dev" / "C0004.json").facts
    default = adjudicate(claim, facts, ruleset).total_payable
    swapped = RuleSet(
        ruleset.policy_id, ruleset.rules, ["non_payable", "room_rent", "copay", "sub_limit", "sum_insured_cap"]
    )
    assert default == Decimal("32000.00")  # 57,000 capped at 40,000, then 20% co-pay
    assert adjudicate(claim, facts, swapped).total_payable == Decimal("40000.00")  # 45,600 after co-pay, then capped


def test_sum_insured_cap(ruleset):
    claim, facts = _c2(ruleset)
    claim = replace(claim, sum_insured_available=Decimal("50000.00"))
    assert adjudicate(claim, facts, ruleset).total_payable == Decimal("50000.00")


def test_route_beats_reject(ruleset):
    """If one rule rejects and another needs a human, a human sees it."""
    claim = load_claim(DATA / "claims" / "dev" / "C0007.json")
    facts = Facts({"cosmetic_surgery"}, set(), False, {b.line_id: "other" for b in claim.bill})
    dec = adjudicate(claim, facts, ruleset)
    assert dec.status == "route_to_human"


def test_missing_line_category_is_an_error(ruleset):
    claim, facts = _c2(ruleset)
    facts = Facts(facts.condition_tags, facts.procedure_tags, facts.is_accident, {})
    with pytest.raises(EngineError):
        adjudicate(claim, facts, ruleset)


def test_unknown_step_is_an_error(ruleset):
    claim, facts = _c2(ruleset)
    rs = RuleSet(ruleset.policy_id, ruleset.rules, ["room_rent", "discount"])
    with pytest.raises(EngineError):
        adjudicate(claim, facts, rs)


def test_rider_rule_needs_its_rider(ruleset):
    claim, facts = _c2(ruleset)
    rider_rule = next(r for r in ruleset.rules if r.id == "SYN-END-RR-WAIVER")
    assert isinstance(rider_rule, Rule)
    assert "SYN-END-RR-WAIVER" not in adjudicate(claim, facts, ruleset).applied_rules
