from dataclasses import replace
from decimal import Decimal

import pytest

from clause.answer import build_answer, explain_term, inr
from clause.engine import adjudicate
from clause.io import load_claim, load_expected
from clause.models import RuleSet

from .conftest import DATA

FIXED = ["What Clause understood (correct it if it's wrong)", "Is it covered?", "From when?", "Limits", "What you pay"]


def _answer(claim_id, ruleset, **claim_changes):
    claim = load_claim(DATA / "claims" / "dev" / f"{claim_id}.json")
    facts = load_expected(DATA / "expected" / "dev" / f"{claim_id}.json").facts
    if claim_changes:
        claim = replace(claim, **claim_changes)
        if "bill" in claim_changes:
            facts = replace(facts, line_categories={})
    decision = adjudicate(claim, facts, ruleset)
    return build_answer(claim, facts, decision, ruleset)


@pytest.mark.parametrize("claim_id", [f"C000{i}" for i in range(1, 9)])
def test_every_answer_has_the_same_sections_in_the_same_order(claim_id, ruleset):
    answer = _answer(claim_id, ruleset)
    titles = [s.title for s in answer.sections]
    assert titles[: len(FIXED)] == FIXED
    assert titles[-2:] == ["Where this comes from", "Note"]
    assert ("What would settle it" in titles) == (answer.verdict == "Can't tell")


def test_room_rent_answer_shows_the_cut_and_the_clause(ruleset):
    text = _answer("C0002", ruleset).text()
    assert "Partly. The policy pays ₹68,333.33 of ₹91,000." in text
    assert "You pay ₹22,666.67." in text
    assert "paid at 66.7%" in text
    assert 'Section 3.2, Room rent limit with proportionate deduction: "Room rent is payable' in text


def test_cataract_answer_says_from_when_and_the_cap(ruleset):
    text = _answer("C0004", ruleset).text()
    assert "Covered from 31 May 2025, when the 2-year waiting period for cataract (section 4.2) ended." in text
    assert "Cap: cataract is paid up to ₹40,000 (section 3.5)." in text


def test_cant_tell_ends_in_the_question_that_settles_it(ruleset):
    answer = _answer("C0007", ruleset)
    settle = next(s for s in answer.sections if s.title == "What would settle it")
    assert answer.verdict == "Can't tell"
    assert settle.lines[0].startswith("Was ")
    assert "?" in settle.lines[0]


def test_a_question_without_amounts_still_gets_cover_and_limits(ruleset):
    text = _answer("C0004", ruleset, bill=[]).text()
    assert "Yes, within the limits below." in text
    assert "Cap: cataract is paid up to ₹40,000" in text
    assert "Add the hospital's estimate" in text
    assert "Line by line" not in text


def test_unchecked_rules_are_labelled(ruleset):
    unchecked = RuleSet(ruleset.policy_id, [replace(r, status="candidate") for r in ruleset.rules])
    claim = load_claim(DATA / "claims" / "dev" / "C0001.json")
    facts = load_expected(DATA / "expected" / "dev" / "C0001.json").facts
    decision = adjudicate(claim, facts, unchecked, allow_unreviewed=True)
    answer = build_answer(claim, facts, decision, unchecked, allow_unreviewed=True)
    assert not answer.rules_checked
    assert "not checked by a person" in answer.text()


def test_explaining_a_clause_uses_the_persons_numbers(ruleset):
    claim = load_claim(DATA / "claims" / "dev" / "C0002.json")
    text = explain_term(ruleset.by_id()["SYN-RR"], claim).text()
    assert "In plain words" in text
    assert "up to ₹5,000 a day" in text


@pytest.mark.parametrize(
    "amount, shown",
    [
        ("500000", "₹5,00,000"),
        ("68333.33", "₹68,333.33"),
        ("1234567.5", "₹12,34,567.50"),
        ("999", "₹999"),
        ("-17000", "-₹17,000"),
    ],
)
def test_rupees_use_indian_grouping(amount, shown):
    assert inr(Decimal(amount)) == shown
