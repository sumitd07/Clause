"""Deterministic adjudication. No model calls, no randomness.

Given a claim, the facts extracted from it, and an approved rule set, compute the
decision line by line. Every change to a payable amount is recorded as an
Adjustment that names the rule that caused it. See docs/ARCHITECTURE.md.
"""

from __future__ import annotations

from decimal import Decimal

from .models import (
    Adjustment,
    Claim,
    Decision,
    Facts,
    LineResult,
    Rule,
    RuleSet,
    money,
)

ELIGIBILITY_TYPES = ("requires_review", "waiting_period", "exclusion")


class EngineError(ValueError):
    """The inputs are inconsistent (unknown category, unknown step, missing line)."""


def active_rules(
    claim: Claim, ruleset: RuleSet, allow_unreviewed: bool = False
) -> tuple[list[Rule], list[tuple[str, str]]]:
    """Rules in force for this claim, and the (overrider, overridden) pairs that removed others.

    A rule is in force when it is approved (or a candidate, in the unreviewed ablation) and any
    rider it needs is on the policy. An in-force rule with an `overrides` edge removes its target.
    """
    allowed = {"approved", "candidate"} if allow_unreviewed else {"approved"}
    in_force = [
        r
        for r in ruleset.rules
        if r.status in allowed and (r.requires_rider is None or r.requires_rider in claim.riders)
    ]
    in_force_ids = {r.id for r in in_force}
    pairs = [(r.id, e.target) for r in in_force for e in r.edges if e.type == "overrides" and e.target in in_force_ids]
    overridden = {target for _, target in pairs}
    return [r for r in in_force if r.id not in overridden], pairs


def matches(rule: Rule, facts: Facts) -> bool:
    p = rule.params
    return bool(
        facts.condition_tags & set(p.get("conditions", [])) or facts.procedure_tags & set(p.get("procedures", []))
    )


def _eligibility(rule: Rule, claim: Claim, facts: Facts) -> tuple[str, str] | None:
    """Return ("reject" | "route", reason) if the rule stops the claim, else None."""
    p = rule.params
    if rule.type == "requires_review":
        if matches(rule, facts):
            return "route", p.get("reason", rule.title)
        return None

    if rule.type == "exclusion":
        if matches(rule, facts):
            return "reject", rule.title
        return None

    if rule.type == "waiting_period":
        days_in_force = (claim.admit_date - claim.policy_start).days
        if days_in_force >= p["days"]:
            return None
        if p.get("waived_for_accident") and facts.is_accident:
            return None
        scope = p["scope"]
        if scope == "all":
            return "reject", f"{rule.title}: admitted on day {days_in_force} of {p['days']}"
        if scope == "listed_conditions":
            if matches(rule, facts):
                return "reject", f"{rule.title}: admitted on day {days_in_force} of {p['days']}"
            return None
        if scope == "pre_existing":
            if claim.declared_ped is None:
                return "route", f"{rule.title}: pre-existing status not established"
            if facts.condition_tags & set(claim.declared_ped):
                return "reject", f"{rule.title}: admitted on day {days_in_force} of {p['days']}"
            return None
        raise EngineError(f"{rule.id}: unknown waiting_period scope {scope!r}")

    return None


def _new_lines(claim: Claim, facts: Facts) -> list[LineResult]:
    lines = []
    for b in claim.bill:
        if b.line_id not in facts.line_categories:
            raise EngineError(f"line {b.line_id} has no category")
        lines.append(LineResult(b.line_id, facts.line_categories[b.line_id], b.amount, b.amount))
    return lines


def _adjust_line(line: LineResult, new_payable: Decimal, step: str, rule: Rule, note: str) -> bool:
    new_payable = money(new_payable)
    delta = new_payable - line.payable
    if delta == 0:
        return False
    line.adjustments.append(Adjustment(step, delta, rule.id, note))
    line.payable = new_payable
    return True


def _running_total(lines: list[LineResult], claim_adj: list[Adjustment]) -> Decimal:
    return sum((ln.payable for ln in lines), Decimal(0)) + sum((a.amount for a in claim_adj), Decimal(0))


def adjudicate(
    claim: Claim,
    facts: Facts,
    ruleset: RuleSet,
    arm: str = "engine",
    allow_unreviewed: bool = False,
) -> Decision:
    rules, overrides = active_rules(claim, ruleset, allow_unreviewed)
    total_billed = money(sum((b.amount for b in claim.bill), Decimal(0)))
    applied: list[str] = []

    def mark(rule_id: str | None) -> None:
        if rule_id and rule_id not in applied:
            applied.append(rule_id)

    # A rule counts as applied when it stopped the claim, changed an amount,
    # or displaced another rule that was in force.
    for overrider, _ in overrides:
        mark(overrider)

    # 1. Eligibility always runs first. Routing beats rejection: a human sees it.
    stops = [(r, _eligibility(r, claim, facts)) for r in rules if r.type in ELIGIBILITY_TYPES]
    stops = [(r, s) for r, s in stops if s is not None]
    routes = [(r, s) for r, s in stops if s[0] == "route"]
    if routes:
        for r, _ in routes:
            mark(r.id)
        return Decision(
            claim_id=claim.claim_id,
            arm=arm,
            status="route_to_human",
            total_billed=total_billed,
            total_payable=money(0),
            applied_rules=applied,
            reasons=[s[1] for _, s in routes],
            route_reason="; ".join(s[1] for _, s in routes),
        )
    if stops:
        for r, _ in stops:
            mark(r.id)
        return Decision(
            claim_id=claim.claim_id,
            arm=arm,
            status="rejected",
            total_billed=total_billed,
            total_payable=money(0),
            applied_rules=applied,
            reasons=[s[1] for _, s in stops],
        )

    # 2. Money steps, in the policy's calculation order.
    lines = _new_lines(claim, facts)
    claim_adj: list[Adjustment] = []
    reasons: list[str] = []
    by_type: dict[str, list[Rule]] = {}
    for r in rules:
        by_type.setdefault(r.type, []).append(r)

    for step in ruleset.calculation_order:
        if step == "non_payable":
            for r in by_type.get("non_payable_items", []):
                cats = set(r.params["categories"])
                for ln in lines:
                    if ln.category in cats and _adjust_line(ln, 0, step, r, "non-payable item"):
                        mark(r.id)

        elif step == "room_rent":
            for r in by_type.get("room_rent_limit", []):
                p = r.params
                if p["limit_type"] == "percent_si":
                    eligible = claim.sum_insured * Decimal(str(p["value"])) / Decimal(100)
                elif p["limit_type"] == "fixed":
                    eligible = Decimal(str(p["value"]))
                else:
                    raise EngineError(f"{r.id}: unknown limit_type {p['limit_type']!r}")
                actual = claim.room_rent_per_day
                if actual <= eligible:
                    continue
                ratio = eligible / actual
                cats = {"room"}
                if p.get("proportionate_deduction"):
                    cats |= set(p.get("associated_categories", []))
                note = f"room rent {actual}/day above eligible {money(eligible)}/day, ratio {ratio:.4f}"
                for ln in lines:
                    if ln.category in cats and _adjust_line(ln, ln.payable * ratio, step, r, note):
                        mark(r.id)
                reasons.append(note)

        elif step == "sub_limit":
            for r in by_type.get("sub_limit", []):
                if not matches(r, facts):
                    continue
                p = r.params
                if p["cap_type"] == "fixed":
                    cap = money(p["value"])
                elif p["cap_type"] == "percent_si":
                    cap = money(claim.sum_insured * Decimal(str(p["value"])) / Decimal(100))
                else:
                    raise EngineError(f"{r.id}: unknown cap_type {p['cap_type']!r}")
                total = _running_total(lines, claim_adj)
                if total > cap:
                    claim_adj.append(Adjustment(step, cap - total, r.id, f"capped at {cap}"))
                    mark(r.id)

        elif step == "copay":
            for r in by_type.get("copay", []):
                if claim.age_at_admission() < r.params.get("min_age", 0):
                    continue
                total = _running_total(lines, claim_adj)
                cut = money(total * Decimal(str(r.params["percent"])) / Decimal(100))
                if cut > 0:
                    claim_adj.append(Adjustment(step, -cut, r.id, f"{r.params['percent']}% co-pay"))
                    mark(r.id)

        elif step == "sum_insured_cap":
            total = _running_total(lines, claim_adj)
            if total > claim.sum_insured_available:
                claim_adj.append(Adjustment(step, claim.sum_insured_available - total, None, "sum insured exhausted"))
        else:
            raise EngineError(f"unknown calculation step {step!r}")

    total_payable = money(_running_total(lines, claim_adj))
    status = "approved" if total_payable == total_billed else "partially_approved"
    return Decision(
        claim_id=claim.claim_id,
        arm=arm,
        status=status,
        total_billed=total_billed,
        total_payable=total_payable,
        lines=lines,
        claim_adjustments=claim_adj,
        applied_rules=applied,
        reasons=reasons,
    )
