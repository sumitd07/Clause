from decimal import Decimal

from clause.io import load_expected
from clause.models import Decision
from clause.scoring import bootstrap_ci, score_claim, summarize

from .conftest import DATA


def _dec(**kw):
    base = {
        "claim_id": "C0002",
        "arm": "test",
        "status": "partially_approved",
        "total_billed": Decimal(91000),
        "total_payable": Decimal("68333.33"),
    }
    base.update(kw)
    return Decision(**base)


def test_task_pass_needs_all_four_checks(ruleset):
    exp = load_expected(DATA / "expected" / "dev" / "C0002.json")
    assert score_claim(_dec(applied_rules=["SYN-RR"]), exp, ruleset).task_pass
    assert not score_claim(_dec(applied_rules=[]), exp, ruleset).task_pass
    assert not score_claim(_dec(applied_rules=["SYN-RR", "SYN-END-RR-WAIVER"]), exp, ruleset).task_pass
    assert not score_claim(_dec(applied_rules=["SYN-RR"], total_payable=Decimal(68335)), exp, ruleset).task_pass


def test_one_rupee_tolerance(ruleset):
    exp = load_expected(DATA / "expected" / "dev" / "C0002.json")
    assert score_claim(_dec(applied_rules=["SYN-RR"], total_payable=Decimal("68334.33")), exp, ruleset).checks["amount"]


def test_section_citations_map_to_rules(ruleset):
    """Arms A and B cite section numbers; 3.2 maps to SYN-RR."""
    exp = load_expected(DATA / "expected" / "dev" / "C0002.json")
    assert score_claim(_dec(cited_sections=["3.2"]), exp, ruleset).task_pass
    assert not score_claim(_dec(cited_sections=["3.2", "E1"]), exp, ruleset).task_pass


def test_route_ignores_amount(ruleset):
    exp = load_expected(DATA / "expected" / "dev" / "C0007.json")
    dec = _dec(claim_id="C0007", status="route_to_human", total_payable=Decimal(0), applied_rules=["SYN-WP-PED"])
    assert score_claim(dec, exp, ruleset).task_pass


def test_rubric_is_partial_credit(ruleset):
    exp = load_expected(DATA / "expected" / "dev" / "C0002.json")
    assert score_claim(_dec(applied_rules=[]), exp, ruleset).rubric == 0.75


def test_bootstrap_is_seeded_and_bounded():
    vals = [1.0] * 30 + [0.0] * 10
    assert bootstrap_ci(vals) == bootstrap_ci(vals)
    lo, hi = bootstrap_ci(vals)
    assert 0.0 <= lo <= 0.75 <= hi <= 1.0


def test_summary_groups_by_distractor_type(ruleset):
    exp = load_expected(DATA / "expected" / "dev" / "C0002.json")
    s = summarize([score_claim(_dec(applied_rules=["SYN-RR"]), exp, ruleset)])
    assert s["by_distractor_type"]["conditional"]["task_pass"] == 1.0


def test_confident_error_and_overpayment_are_reported_separately(ruleset):
    """A wrong amount stated with confidence is the costliest failure; it gets its own line."""
    c2 = load_expected(DATA / "expected" / "dev" / "C0002.json")
    c7 = load_expected(DATA / "expected" / "dev" / "C0007.json")
    overestimate = _dec(status="approved", total_payable=Decimal(91000))  # ignored the room rent limit
    paid_instead_of_routed = _dec(claim_id="C0007", status="approved", total_payable=Decimal(50000))
    s = summarize([score_claim(overestimate, c2, ruleset), score_claim(paid_instead_of_routed, c7, ruleset)])
    assert s["confident_errors"] == ["C0002", "C0007"]
    assert s["money_errors"]["overestimated"] == {"n": 1, "amount": "22666.67"}
    assert s["abstention"] == {"routed": 0, "should_route": 1, "precision": None, "recall": 0.0}


def test_cant_tell_on_a_payable_claim_costs_precision_not_a_confident_error(ruleset):
    c2 = load_expected(DATA / "expected" / "dev" / "C0002.json")
    routed = _dec(status="route_to_human", total_payable=Decimal(0))
    s = summarize([score_claim(routed, c2, ruleset)])
    assert s["confident_errors"] == []
    assert s["abstention"]["precision"] == 0.0
    assert s["money_errors"]["underestimated"]["n"] == 0
