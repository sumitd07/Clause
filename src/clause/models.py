"""Core data types. Money is always Decimal, dates are always datetime.date."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")

RULE_TYPES = {
    "waiting_period",
    "exclusion",
    "requires_review",
    "non_payable_items",
    "room_rent_limit",
    "sub_limit",
    "copay",
    "waiver",
}

BILL_CATEGORIES = {
    "room",
    "icu",
    "doctor_fees",
    "nursing",
    "ot_charges",
    "pharmacy",
    "consumables",
    "implants",
    "diagnostics",
    "non_medical",
    "other",
}

STATUSES = {"approved", "partially_approved", "rejected", "route_to_human"}

DEFAULT_ORDER = ["non_payable", "room_rent", "sub_limit", "copay", "sum_insured_cap"]


def money(value) -> Decimal:
    """Round to paise, half up. Every stored amount passes through here."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Citation:
    doc: str
    section: str
    quote: str
    page: int | None = None


@dataclass(frozen=True)
class Edge:
    type: str  # overrides | narrows | activates
    target: str


@dataclass(frozen=True)
class Rule:
    id: str
    type: str
    title: str
    citation: Citation
    params: dict
    status: str = "approved"  # candidate | approved | rejected
    requires_rider: str | None = None
    edges: tuple[Edge, ...] = ()
    plain: str | None = None  # the rule in everyday words, checked by a person with the rule


@dataclass
class RuleSet:
    policy_id: str
    rules: list[Rule]
    calculation_order: list[str] = field(default_factory=lambda: list(DEFAULT_ORDER))

    def by_id(self) -> dict[str, Rule]:
        return {r.id: r for r in self.rules}

    def section_index(self) -> dict[str, set[str]]:
        """Map a cited section number to the rule ids it supports."""
        index: dict[str, set[str]] = {}
        for r in self.rules:
            index.setdefault(r.citation.section, set()).add(r.id)
        return index


@dataclass(frozen=True)
class BillLine:
    line_id: str
    description: str
    amount: Decimal


@dataclass
class Claim:
    claim_id: str
    policy_id: str
    policy_start: date
    sum_insured: Decimal
    sum_insured_available: Decimal
    riders: list[str]
    dob: date
    declared_ped: list[str] | None  # None means pre-existing status is not established
    admit_date: date
    discharge_date: date
    room_rent_per_day: Decimal
    narrative: str
    bill: list[BillLine]

    def age_at_admission(self) -> int:
        d, a = self.dob, self.admit_date
        return a.year - d.year - ((a.month, a.day) < (d.month, d.day))


@dataclass
class Facts:
    """What the claim says, in the rule vocabulary. Extracted by a model or taken from gold labels."""

    condition_tags: set[str]
    procedure_tags: set[str]
    is_accident: bool
    line_categories: dict[str, str]


@dataclass
class Adjustment:
    step: str
    amount: Decimal  # negative reduces payable
    rule_id: str | None
    note: str


@dataclass
class LineResult:
    line_id: str
    category: str
    billed: Decimal
    payable: Decimal
    adjustments: list[Adjustment] = field(default_factory=list)


@dataclass
class Decision:
    claim_id: str
    arm: str
    status: str
    total_billed: Decimal
    total_payable: Decimal
    lines: list[LineResult] = field(default_factory=list)
    claim_adjustments: list[Adjustment] = field(default_factory=list)
    applied_rules: list[str] = field(default_factory=list)
    cited_sections: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    route_reason: str | None = None


@dataclass
class Expected:
    claim_id: str
    status: str
    total_payable: Decimal | None
    required_rules: list[str]
    forbidden_rules: list[str]
    distractor_type: str
    facts: Facts
    notes: str = ""
