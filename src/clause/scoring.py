"""Deterministic grading. No LLM judge: every check compares against hand-verified labels.

Task pass is all-or-nothing per claim: right status, payable within one rupee,
every required rule cited, no forbidden rule cited. Rubric pass is the share of
those four checks passed.

Some numbers are reported on their own and never averaged into the others, because
they cost the user differently from an ordinary miss:

- confident errors: a wrong answer given without "can't tell". The user acts on it.
- abstention precision and recall: "can't tell" is a fair answer, not a failure.
- overestimates and underestimates of what the policy pays, in rupees.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from decimal import Decimal

from .models import Decision, Expected, Facts, RuleSet

TOLERANCE = Decimal("1.00")
CHECKS = ("status", "amount", "required_rules", "no_forbidden_rules")


@dataclass
class ClaimScore:
    claim_id: str
    distractor_type: str
    checks: dict[str, bool]
    expected_status: str = ""
    predicted_status: str = ""
    amount_delta: Decimal | None = None  # predicted minus expected; None when routing was expected

    @property
    def task_pass(self) -> bool:
        return all(self.checks.values())

    @property
    def rubric(self) -> float:
        return sum(self.checks.values()) / len(self.checks)


def cited_rules(decision: Decision, ruleset: RuleSet | None = None) -> set[str]:
    """Rule ids a decision relies on. Section citations (arms A and B) map through the rule set."""
    cited = set(decision.applied_rules)
    if ruleset is not None and decision.cited_sections:
        index = ruleset.section_index()
        for section in decision.cited_sections:
            cited |= index.get(section.strip(), set())
    return cited


def score_claim(decision: Decision, expected: Expected, ruleset: RuleSet | None = None) -> ClaimScore:
    cited = cited_rules(decision, ruleset)
    amount_ok = expected.status == "route_to_human" or (
        expected.total_payable is not None and abs(decision.total_payable - expected.total_payable) <= TOLERANCE
    )
    checks = {
        "status": decision.status == expected.status,
        "amount": amount_ok,
        "required_rules": set(expected.required_rules) <= cited,
        "no_forbidden_rules": not (set(expected.forbidden_rules) & cited),
    }
    delta = None
    if expected.status != "route_to_human" and expected.total_payable is not None:
        delta = decision.total_payable - expected.total_payable
    return ClaimScore(
        expected.claim_id,
        expected.distractor_type,
        checks,
        expected_status=expected.status,
        predicted_status=decision.status,
        amount_delta=delta,
    )


def score_facts(predicted: Facts, gold: Facts) -> dict[str, bool | float]:
    """Field-level accuracy of fact extraction, for attributing failures to the right layer."""
    lines = gold.line_categories
    correct = sum(predicted.line_categories.get(k) == v for k, v in lines.items())
    return {
        "condition_tags": predicted.condition_tags == gold.condition_tags,
        "procedure_tags": predicted.procedure_tags == gold.procedure_tags,
        "is_accident": predicted.is_accident == gold.is_accident,
        "line_category_accuracy": correct / len(lines) if lines else 1.0,
    }


def bootstrap_ci(values: list[float], n: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    """Percentile bootstrap interval for a mean. Seeded, so reports are reproducible."""
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    k = len(values)
    means = sorted(sum(rng.choice(values) for _ in range(k)) / k for _ in range(n))
    lo = means[int((alpha / 2) * n)]
    hi = means[min(n - 1, int((1 - alpha / 2) * n))]
    return (lo, hi)


def _ratio(num: int, den: int) -> float | None:
    return num / den if den else None


def abstention(scores: list[ClaimScore]) -> dict:
    """Routing as a classifier: of the claims routed, how many should have been; of those that should, how many were."""
    predicted = [s for s in scores if s.predicted_status == "route_to_human"]
    expected = [s for s in scores if s.expected_status == "route_to_human"]
    both = [s for s in predicted if s.expected_status == "route_to_human"]
    return {
        "routed": len(predicted),
        "should_route": len(expected),
        "precision": _ratio(len(both), len(predicted)),
        "recall": _ratio(len(both), len(expected)),
    }


def money_errors(scores: list[ClaimScore]) -> dict:
    """Errors in what the policy pays, beyond the one-rupee tolerance, on claims Clause answered."""
    paid = [s for s in scores if s.amount_delta is not None and s.predicted_status != "route_to_human"]
    over = [s.amount_delta for s in paid if s.amount_delta > TOLERANCE]
    under = [-s.amount_delta for s in paid if s.amount_delta < -TOLERANCE]
    return {
        "overestimated": {"n": len(over), "amount": str(sum(over, Decimal(0)))},
        "underestimated": {"n": len(under), "amount": str(sum(under, Decimal(0)))},
    }


def summarize(scores: list[ClaimScore]) -> dict:
    passes = [1.0 if s.task_pass else 0.0 for s in scores]
    rubrics = [s.rubric for s in scores]
    by_type: dict[str, list[ClaimScore]] = {}
    for s in scores:
        by_type.setdefault(s.distractor_type, []).append(s)
    return {
        "n": len(scores),
        "task_pass": sum(passes) / len(passes) if passes else 0.0,
        "task_pass_ci95": bootstrap_ci(passes),
        "rubric_pass": sum(rubrics) / len(rubrics) if rubrics else 0.0,
        "by_distractor_type": {
            t: {"n": len(v), "task_pass": sum(s.task_pass for s in v) / len(v)} for t, v in sorted(by_type.items())
        },
        "check_failures": {c: sum(not s.checks[c] for s in scores) for c in CHECKS},
        "confident_errors": [s.claim_id for s in scores if not s.task_pass and s.predicted_status != "route_to_human"],
        "abstention": abstention(scores),
        "money_errors": money_errors(scores),
        "failed_claims": [s.claim_id for s in scores if not s.task_pass],
    }
