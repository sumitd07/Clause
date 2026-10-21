"""The answer a person reads: a fixed form, filled in by code from the engine's result.

A question about a treatment always gets the same sections, in the same order:
what Clause understood, is it covered, from when, limits, what you pay, line by line,
what would settle it (only when Clause can't tell), and the clauses behind the answer.

No model writes any of it. The everyday-words line under each clause is the rule's
`plain` text, written once when the rule is made and checked by a person with the rule
(docs/decisions/0011-answers-are-a-fixed-form.md).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal

from .engine import ELIGIBILITY_TYPES, active_rules, matches
from .models import Claim, Decision, Facts, Rule, RuleSet, money

VERDICTS = {
    "approved": "Yes",
    "partially_approved": "Partly",
    "rejected": "No",
    "route_to_human": "Can't tell",
}

CUT_REASONS = {
    "non_payable": "items the policy does not pay for",
    "room_rent": "room above the limit, so related charges are cut in proportion",
    "sub_limit": "the cap for this treatment",
    "copay": "your share (co-payment)",
    "sum_insured_cap": "more than the sum insured left",
}


@dataclass
class Section:
    title: str
    lines: list[str]


@dataclass
class Answer:
    claim_id: str
    verdict: str
    rules_checked: bool
    sections: list[Section]

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "verdict": self.verdict,
            "rules_checked": self.rules_checked,
            "sections": [{"title": s.title, "lines": s.lines} for s in self.sections],
        }

    def text(self) -> str:
        out = []
        for s in self.sections:
            out.append(s.title)
            out.extend(f"  {line}" for line in s.lines)
            out.append("")
        return "\n".join(out).rstrip() + "\n"


# Formatting -----------------------------------------------------------------------------------


def inr(x: Decimal) -> str:
    """Rupees with Indian digit grouping: 500000 -> ₹5,00,000. Paise shown only when present."""
    x = money(x)
    sign = "-" if x < 0 else ""
    whole, paise = f"{abs(x):.2f}".split(".")
    if len(whole) > 3:
        head, groups = whole[:-3], [whole[-3:]]
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        whole = ",".join([head, *groups]) if head else ",".join(groups)
    return f"{sign}₹{whole}" + ("" if paise == "00" else f".{paise}")


def day(d: date) -> str:
    return f"{d.day} {d:%b %Y}"


def span(days: int) -> str:
    """730 -> "2-year", 30 -> "30-day", for "the 2-year waiting period"."""
    return f"{days // 365}-year" if days % 365 == 0 else f"{days}-day"


def label(tag: str) -> str:
    return tag.replace("_", " ")


def topic(facts: Facts) -> str:
    tags = [label(t) for t in sorted(facts.condition_tags | facts.procedure_tags)]
    if not tags:
        return "this condition"
    return tags[0] if len(tags) == 1 else ", ".join(tags[:-1]) + " and " + tags[-1]


def section_ref(rule: Rule) -> str:
    return f"section {rule.citation.section}"


# The pieces -----------------------------------------------------------------------------------


def _understood(claim: Claim, facts: Facts) -> list[str]:
    lines = [f'You said: "{claim.narrative}"']
    named = topic(facts) if facts.condition_tags | facts.procedure_tags else "none"
    lines.append(f"Conditions with their own rules in this policy: {named}.")
    when = day(claim.admit_date)
    if claim.discharge_date != claim.admit_date:
        when += f" to {day(claim.discharge_date)}"
    lines.append(f"Hospital stay: {when}. " + ("After an accident." if facts.is_accident else "Not after an accident."))
    if claim.bill:
        total = money(sum(b.amount for b in claim.bill))
        lines.append(f"Amounts: {inr(total)} in {len(claim.bill)} lines. Room: {inr(claim.room_rent_per_day)} a day.")
    else:
        lines.append("Amounts: none given.")
    riders = ", ".join(f"{label(r)} rider" for r in claim.riders) if claim.riders else "no riders"
    lines.append(
        f"Policy: {claim.policy_id}, started {day(claim.policy_start)}, sum insured {inr(claim.sum_insured)}, {riders}."
    )
    if claim.declared_ped is None:
        declared = "not sure"
    elif claim.declared_ped:
        declared = ", ".join(label(t) for t in claim.declared_ped)
    else:
        declared = "none"
    lines.append(f"Patient: aged {claim.age_at_admission()}. Conditions declared when buying: {declared}.")
    return lines


def _waiting(rule: Rule, claim: Claim, facts: Facts) -> str | None:
    """One line about one waiting period, or None when it has nothing to do with this treatment."""
    p = rule.params
    ends = claim.policy_start + timedelta(days=p["days"])
    scope = p["scope"]
    scope_text = f" for {topic(facts)}" if scope == "listed_conditions" else ""
    what = f"the {span(p['days'])} waiting period{scope_text} ({section_ref(rule)})"
    if scope == "listed_conditions" and not matches(rule, facts):
        return None
    if scope == "pre_existing":
        if claim.declared_ped is None:
            return f"Can't tell whether {what} applies: Clause doesn't know if {topic(facts)} was declared."
        if not claim.declared_ped:
            return f"No pre-existing disease wait: no conditions were declared when buying ({section_ref(rule)})."
        if not facts.condition_tags & set(claim.declared_ped):
            declared = ", ".join(label(t) for t in claim.declared_ped)
            return (
                f"No pre-existing disease wait: you declared {declared}, and that is not what is being treated "
                f"({section_ref(rule)})."
            )
    if claim.admit_date >= ends:
        return f"Covered from {day(ends)}, when {what} ended."
    if p.get("waived_for_accident") and facts.is_accident:
        return f"Covered now: {what} does not apply after an accident."
    return f"Not covered until {day(ends)}, because of {what}."


def _limit(rule: Rule, claim: Claim, facts: Facts, overridden: dict[str, Rule]) -> str | None:
    """One line about one limit, or None when it does not touch this treatment."""
    p = rule.params
    if rule.id in overridden:
        short = {"room_rent_limit": "room rent limit", "sub_limit": "cap", "copay": "co-payment"}
        name = short.get(rule.type, rule.title.lower())
        return f"No {name}: your rider removes it ({section_ref(overridden[rule.id])})."
    if rule.type == "room_rent_limit":
        if p["limit_type"] == "percent_si":
            eligible = money(claim.sum_insured * Decimal(str(p["value"])) / Decimal(100))
            basis = f"{p['value']}% of your sum insured"
        else:
            eligible = money(p["value"])
            basis = "a fixed amount"
        line = f"Room rent: up to {inr(eligible)} a day ({basis}, {section_ref(rule)})."
        if claim.bill and claim.room_rent_per_day > eligible:
            share = eligible / claim.room_rent_per_day * 100
            line += (
                f" Your room is {inr(claim.room_rent_per_day)} a day, so room, doctor, nursing and operation "
                f"theatre charges are paid at {share:.1f}%."
            )
        elif claim.bill:
            line += f" Your room is {inr(claim.room_rent_per_day)} a day, within the limit."
        return line
    if rule.type == "sub_limit":
        if not matches(rule, facts):
            return None
        if p["cap_type"] == "fixed":
            cap = money(p["value"])
        else:
            cap = money(claim.sum_insured * Decimal(str(p["value"])) / Decimal(100))
        return f"Cap: {topic(facts)} is paid up to {inr(cap)} ({section_ref(rule)})."
    if rule.type == "copay":
        age, start = claim.age_at_admission(), p.get("min_age", 0)
        if age >= start:
            return f"Co-payment: you pay {p['percent']}%, because the patient is {age} ({section_ref(rule)})."
        return f"No co-payment: it starts at age {start}, and the patient is {age} ({section_ref(rule)})."
    if rule.type == "non_payable_items":
        return f"Not paid: {rule.title.lower()} ({section_ref(rule)})."
    return None


def _cuts(decision: Decision) -> list[tuple[str, str | None, Decimal]]:
    """Every cut, summed per (step, rule), in the order the engine made them."""
    totals: dict[tuple[str, str | None], Decimal] = {}
    for adj in [a for ln in decision.lines for a in ln.adjustments] + decision.claim_adjustments:
        key = (adj.step, adj.rule_id)
        totals[key] = totals.get(key, Decimal(0)) + adj.amount
    return [(step, rule_id, amount) for (step, rule_id), amount in totals.items() if amount != 0]


def _stop_line(rule: Rule, claim: Claim, facts: Facts) -> str:
    if rule.type == "exclusion":
        return f"The policy does not pay for {topic(facts)} ({section_ref(rule)})."
    if rule.type == "requires_review":
        return f"The policy says {topic(facts)} needs the insurer's review first ({section_ref(rule)})."
    return _waiting(rule, claim, facts) or rule.title


def _settle(rule: Rule, facts: Facts) -> str:
    if rule.type == "waiting_period" and rule.params.get("scope") == "pre_existing":
        return (
            f"Was {topic(facts)} declared as a pre-existing condition when the policy was bought? "
            "Your policy schedule lists what was declared. Add it to your details and ask again."
        )
    if rule.type == "requires_review":
        return "Ask your insurer for approval before admission. The policy says a doctor of theirs must review it."
    return f"Ask your insurer about {rule.title.lower()} ({section_ref(rule)})."


# The form -------------------------------------------------------------------------------------


def build_answer(
    claim: Claim, facts: Facts, decision: Decision, ruleset: RuleSet, allow_unreviewed: bool = False
) -> Answer:
    rules, pairs = active_rules(claim, ruleset, allow_unreviewed)
    by_id = ruleset.by_id()
    overridden = {target: by_id[overrider] for overrider, target in pairs}
    applied = [by_id[r] for r in decision.applied_rules if r in by_id]
    status = decision.status
    has_amounts = bool(claim.bill)

    # Is it covered?
    limits = [line for r in rules + [by_id[t] for t in overridden] if (line := _limit(r, claim, facts, overridden))]
    stoppers = [r for r in applied if r.type in ELIGIBILITY_TYPES]
    if status == "route_to_human":
        covered = ['Can\'t tell yet. See "What would settle it" below.']
        covered += [_stop_line(r, claim, facts) for r in stoppers]
    elif status == "rejected":
        covered = ["No."] + [_stop_line(r, claim, facts) for r in stoppers]
    elif has_amounts and status == "approved":
        covered = [f"Yes. The policy pays the full {inr(decision.total_billed)}."]
    elif has_amounts:
        covered = [f"Partly. The policy pays {inr(decision.total_payable)} of {inr(decision.total_billed)}."]
    else:
        covered = ["Yes, within the limits below." if limits else "Yes."]
    exclusions = [r for r in rules if r.type == "exclusion" and r not in stoppers]
    if exclusions and status != "rejected":
        checked = ", ".join(f"{r.title.lower()} ({section_ref(r)})" for r in exclusions)
        covered.append(f"Not excluded. Checked against: {checked}.")

    # From when?
    waits = [w for r in rules if r.type == "waiting_period" and (w := _waiting(r, claim, facts))]
    when = waits or ["No waiting period applies."]

    # What you pay
    if status == "route_to_human":
        pay = ["Not worked out until the missing fact is settled."]
    elif not has_amounts:
        pay = ["Add the hospital's estimate to see what the policy pays and what you pay."]
    elif status == "rejected":
        pay = [f"The policy pays nothing. You pay the full {inr(decision.total_billed)}."]
    else:
        you = decision.total_billed - decision.total_payable
        pay = [f"The policy pays {inr(decision.total_payable)}. You pay {inr(you)}."]
        for step, rule_id, amount in _cuts(decision):
            where = f", {section_ref(by_id[rule_id])}" if rule_id in by_id else ""
            pay.append(f"{inr(-amount)}: {CUT_REASONS.get(step, step)}{where}.")

    sections = [
        Section("What Clause understood (correct it if it's wrong)", _understood(claim, facts)),
        Section("Is it covered?", covered),
        Section("From when?", when),
        Section("Limits", limits or ["No limits apply to this treatment."]),
        Section("What you pay", pay),
    ]
    if has_amounts and decision.lines:
        rows = [f"{'':4} {'Item':<40} {'Billed':>12} {'Paid':>12}"]
        rows += [
            f"{ln.line_id:<4} {_desc(claim, ln.line_id):<40} {inr(ln.billed):>12} {inr(ln.payable):>12}"
            for ln in decision.lines
        ]
        for a in decision.claim_adjustments:
            reason = CUT_REASONS.get(a.step, a.step)
            rows.append(f"{'':4} {reason[0].upper() + reason[1:40]:<40} {'':>12} {inr(a.amount):>12}")
        rows.append(f"{'':4} {'Total':<40} {inr(decision.total_billed):>12} {inr(decision.total_payable):>12}")
        sections.append(Section("Line by line", rows))
    if status == "route_to_human":
        settle = [_settle(r, facts) for r in stoppers]
        if not settle:
            settle = [
                f"Clause couldn't work it out: {decision.route_reason}. Check what it understood, then ask again."
            ]
        sections.append(Section("What would settle it", settle))

    sources = []
    for r in applied:
        sources.append(f'Section {r.citation.section}, {r.title}: "{r.citation.quote}"')
        if r.plain:
            sources.append(f"  In plain words: {r.plain}")
    sections.append(Section("Where this comes from", sources or ["No clause changed this answer."]))

    rules_checked = all(r.status == "approved" for r in rules)
    footer = "Rules checked by a person." if rules_checked else "Rules read automatically, not checked by a person."
    sections.append(Section("Note", [f"{footer} This is not the insurer's decision."]))
    return Answer(claim.claim_id, VERDICTS[status], rules_checked, sections)


def _desc(claim: Claim, line_id: str) -> str:
    text = next((b.description for b in claim.bill if b.line_id == line_id), line_id)
    return text if len(text) <= 40 else text[:39] + "…"


def explain_term(rule: Rule, claim: Claim) -> Answer:
    """A question about one clause or term: what it says, in plain words, and what it means for you."""
    facts = Facts(set(rule.params.get("conditions", [])), set(rule.params.get("procedures", [])), False, {})
    blank = replace(claim, bill=[])
    if rule.type == "waiting_period":
        mine = _waiting(rule, blank, facts)
    elif rule.type == "waiver":
        has = rule.requires_rider in claim.riders
        mine = "You have this rider." if has else "You don't have this rider, so it changes nothing for you."
    else:
        mine = _limit(rule, blank, facts, {})
    sections = [
        Section("What the policy says", [f'Section {rule.citation.section}, {rule.title}: "{rule.citation.quote}"']),
        Section("In plain words", [rule.plain or "Not written yet for this rule."]),
    ]
    if mine:
        sections.append(Section("What it means for you", [mine]))
    checked = "Rule checked by a person." if rule.status == "approved" else "Rule not checked by a person."
    sections.append(Section("Note", [f"{checked} This is not the insurer's decision."]))
    return Answer(claim.claim_id, "", rule.status == "approved", sections)
