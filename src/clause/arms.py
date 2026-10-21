"""The systems under test. Each arm takes a claim and returns a Decision.

| Arm | What the model sees | Who does the money math |
|---|---|---|
| oracle | nothing (gold facts) | engine |
| long_context (A) | the full policy text | the model |
| rag (B) | top-k retrieved policy passages | the model |
| clause (C) | the claim only, to extract facts | engine |

See docs/EVAL.md for the ablations.
"""

from __future__ import annotations

import json
from pathlib import Path

from .engine import EngineError, adjudicate
from .facts import extract_facts
from .llm import LLM, RefusalError
from .models import Claim, Decision, Facts, RuleSet, money


def oracle(claim: Claim, gold: Facts, ruleset: RuleSet) -> Decision:
    """Upper bound and consistency check: gold facts, approved rules, engine."""
    return adjudicate(claim, gold, ruleset, arm="oracle")


def clause(claim: Claim, ruleset: RuleSet, llm: LLM, allow_unreviewed: bool = False) -> Decision:
    """Arm C: model extracts facts, engine decides. Verifier is added in week 3 (docs/BUILD_PLAN.md)."""
    arm = "clause_unreviewed" if allow_unreviewed else "clause"
    try:
        facts = extract_facts(claim, ruleset, llm)
    except RefusalError as e:
        return _routed(claim, arm, f"fact extraction declined: {e}")
    try:
        return adjudicate(claim, facts, ruleset, arm=arm, allow_unreviewed=allow_unreviewed)
    except EngineError as e:
        # Facts the engine cannot use (a bill line with no category) are a product outcome: the
        # system could not decide, so a person does. It counts against routing precision.
        return _routed(claim, arm, f"extracted facts incomplete: {e}")


DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["approved", "partially_approved", "rejected", "route_to_human"],
        },
        "total_payable": {"type": "number"},
        "cited_sections": {"type": "array", "items": {"type": "string"}},
        "reasons": {"type": "array", "items": {"type": "string"}},
        "route_reason": {"type": "string"},
    },
    "required": ["status", "total_payable", "cited_sections", "reasons", "route_reason"],
    "additionalProperties": False,
}

ADJUDICATOR_SYSTEM = """You adjudicate health insurance claims against the policy wording below.

Decide the claim status and the total payable amount in rupees, rounded to paise.
Cite the section number of every clause that changed the outcome, and only those.
Use route_to_human with a reason when the facts needed to decide are missing; otherwise leave route_reason empty.
Status meanings: approved means the full billed amount is payable; partially_approved means some
but not all; rejected means nothing is payable under the policy.

POLICY WORDING
{policy}"""


def _claim_payload(claim: Claim) -> str:
    return json.dumps(
        {
            "claim_id": claim.claim_id,
            "policy": {
                "start_date": claim.policy_start.isoformat(),
                "sum_insured": str(claim.sum_insured),
                "sum_insured_available": str(claim.sum_insured_available),
                "riders": claim.riders,
            },
            "claimant": {"dob": claim.dob.isoformat(), "declared_ped": claim.declared_ped},
            "admission": {
                "admit_date": claim.admit_date.isoformat(),
                "discharge_date": claim.discharge_date.isoformat(),
                "room_rent_per_day": str(claim.room_rent_per_day),
            },
            "narrative": claim.narrative,
            "bill": [{"line_id": b.line_id, "description": b.description, "amount": str(b.amount)} for b in claim.bill],
        },
        indent=2,
    )


def _routed(claim: Claim, arm: str, reason: str) -> Decision:
    total = money(sum(b.amount for b in claim.bill))
    return Decision(claim.claim_id, arm, "route_to_human", total, money(0), route_reason=reason)


def long_context(claim: Claim, policy_text: str, llm: LLM) -> Decision:
    """Arm A: the whole wording in context; the model does everything, including arithmetic."""
    try:
        out = llm.json(ADJUDICATOR_SYSTEM.format(policy=policy_text), _claim_payload(claim), DECISION_SCHEMA)
    except RefusalError as e:
        return _routed(claim, "long_context", f"declined: {e}")
    return Decision(
        claim_id=claim.claim_id,
        arm="long_context",
        status=out["status"],
        total_billed=money(sum(b.amount for b in claim.bill)),
        total_payable=money(out["total_payable"]),
        cited_sections=out["cited_sections"],
        reasons=out["reasons"],
        route_reason=out["route_reason"] or None,
    )


def rag(claim: Claim, policy_dir: Path, llm: LLM, k: int = 6) -> Decision:
    """Arm B: BM25 over section chunks, top-k passages in context. Built in week 3."""
    raise NotImplementedError("arm B lands in week 3: see docs/BUILD_PLAN.md")
