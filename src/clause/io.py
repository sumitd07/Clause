"""Load and dump the JSON files under data/ and eval/. Schemas live in schemas/."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import (
    DEFAULT_ORDER,
    BillLine,
    Citation,
    Claim,
    Decision,
    Edge,
    Expected,
    Facts,
    Rule,
    RuleSet,
    money,
)


def _read(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rule_from_dict(d: dict) -> Rule:
    c = d["citation"]
    return Rule(
        id=d["id"],
        type=d["type"],
        title=d["title"],
        citation=Citation(doc=c["doc"], section=c["section"], quote=c["quote"], page=c.get("page")),
        params=d.get("params", {}),
        status=d.get("status", "candidate"),
        requires_rider=d.get("requires_rider"),
        edges=tuple(Edge(type=e["type"], target=e["target"]) for e in d.get("edges", [])),
        plain=d.get("plain"),
    )


def load_rules(path: str | Path) -> RuleSet:
    d = _read(path)
    return RuleSet(
        policy_id=d["policy_id"],
        rules=[rule_from_dict(r) for r in d["rules"]],
        calculation_order=d.get("calculation_order", list(DEFAULT_ORDER)),
    )


def claim_from_dict(d: dict) -> Claim:
    p, c, a = d["policy"], d["claimant"], d["admission"]
    return Claim(
        claim_id=d["claim_id"],
        policy_id=d["policy_id"],
        policy_start=date.fromisoformat(p["start_date"]),
        sum_insured=money(p["sum_insured"]),
        sum_insured_available=money(p["sum_insured_available"]),
        riders=list(p.get("riders", [])),
        dob=date.fromisoformat(c["dob"]),
        declared_ped=c["declared_ped"],
        admit_date=date.fromisoformat(a["admit_date"]),
        discharge_date=date.fromisoformat(a["discharge_date"]),
        room_rent_per_day=money(a["room_rent_per_day"]),
        narrative=d["narrative"],
        bill=[BillLine(b["line_id"], b["description"], money(b["amount"])) for b in d["bill"]],
    )


def load_claim(path: str | Path) -> Claim:
    return claim_from_dict(_read(path))


def facts_from_dict(d: dict) -> Facts:
    return Facts(
        condition_tags=set(d.get("condition_tags", [])),
        procedure_tags=set(d.get("procedure_tags", [])),
        is_accident=bool(d.get("is_accident", False)),
        line_categories=dict(d["line_categories"]),
    )


def facts_to_dict(f: Facts) -> dict:
    return {
        "condition_tags": sorted(f.condition_tags),
        "procedure_tags": sorted(f.procedure_tags),
        "is_accident": f.is_accident,
        "line_categories": dict(sorted(f.line_categories.items())),
    }


def expected_from_dict(d: dict) -> Expected:
    payable = d.get("total_payable")
    return Expected(
        claim_id=d["claim_id"],
        status=d["status"],
        total_payable=None if payable is None else money(payable),
        required_rules=list(d.get("required_rules", [])),
        forbidden_rules=list(d.get("forbidden_rules", [])),
        distractor_type=d.get("distractor_type", "none"),
        facts=facts_from_dict(d["facts"]),
        notes=d.get("notes", ""),
    )


def load_expected(path: str | Path) -> Expected:
    return expected_from_dict(_read(path))


def _num(x: Decimal) -> str:
    return str(money(x))


def decision_to_dict(dec: Decision) -> dict:
    def adj(a):
        return {"step": a.step, "amount": _num(a.amount), "rule_id": a.rule_id, "note": a.note}

    return {
        "claim_id": dec.claim_id,
        "arm": dec.arm,
        "status": dec.status,
        "total_billed": _num(dec.total_billed),
        "total_payable": _num(dec.total_payable),
        "lines": [
            {
                "line_id": ln.line_id,
                "category": ln.category,
                "billed": _num(ln.billed),
                "payable": _num(ln.payable),
                "adjustments": [adj(a) for a in ln.adjustments],
            }
            for ln in dec.lines
        ],
        "claim_adjustments": [adj(a) for a in dec.claim_adjustments],
        "applied_rules": dec.applied_rules,
        "cited_sections": dec.cited_sections,
        "reasons": dec.reasons,
        "route_reason": dec.route_reason,
    }


def decision_from_dict(d: dict) -> Decision:
    """Lenient loader: arms A and B only need status, totals and citations."""
    return Decision(
        claim_id=d["claim_id"],
        arm=d.get("arm", "unknown"),
        status=d["status"],
        total_billed=money(d.get("total_billed", 0)),
        total_payable=money(d.get("total_payable", 0)),
        applied_rules=list(d.get("applied_rules", [])),
        cited_sections=list(d.get("cited_sections", [])),
        reasons=list(d.get("reasons", [])),
        route_reason=d.get("route_reason"),
    )


def write_json(path: str | Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
