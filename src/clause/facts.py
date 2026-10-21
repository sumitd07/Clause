"""Turn a claim's free text into Facts in the rule vocabulary. The model's only job in arm C.

The model reads the narrative and bill descriptions and returns tags and categories.
It never sees amounts as something to compute, and it never decides payable.
"""

from __future__ import annotations

import json

from .llm import LLM
from .models import BILL_CATEGORIES, Claim, Facts, RuleSet


def vocabulary(ruleset: RuleSet) -> tuple[list[str], list[str]]:
    conditions, procedures = set(), set()
    for r in ruleset.rules:
        conditions |= set(r.params.get("conditions", []))
        procedures |= set(r.params.get("procedures", []))
    return sorted(conditions), sorted(procedures)


def facts_schema(line_ids: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "condition_tags": {"type": "array", "items": {"type": "string"}},
            "procedure_tags": {"type": "array", "items": {"type": "string"}},
            "is_accident": {"type": "boolean"},
            "line_categories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "line_id": {"type": "string", "enum": line_ids},
                        "category": {"type": "string", "enum": sorted(BILL_CATEGORIES)},
                    },
                    "required": ["line_id", "category"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["condition_tags", "procedure_tags", "is_accident", "line_categories"],
        "additionalProperties": False,
    }


SYSTEM = """You label health insurance claims for a rules engine. You do not decide coverage.

Condition tags in use: {conditions}
Procedure tags in use: {procedures}
Bill categories: {categories}

Rules for labelling:
- Tag the condition being treated in this hospitalisation, not comorbidities. Use a tag only when the
  narrative states it. Do not infer from keywords alone; a narrative that mentions a word in a negated
  or unrelated context does not earn the tag.
- If the claim involves a condition or procedure outside the tag list, leave it out.
- is_accident is true only when the narrative says the hospitalisation follows an accident or injury.
- Give every bill line exactly one category, based on what the item is, not on its price."""


def extract_facts(claim: Claim, ruleset: RuleSet, llm: LLM) -> Facts:
    conditions, procedures = vocabulary(ruleset)
    # Declared pre-existing diseases are matched against condition tags, so they join the vocabulary.
    conditions = sorted(set(conditions) | set(claim.declared_ped or []))
    system = SYSTEM.format(
        conditions=", ".join(conditions) or "(none)",
        procedures=", ".join(procedures) or "(none)",
        categories=", ".join(sorted(BILL_CATEGORIES)),
    )
    user = json.dumps(
        {
            "narrative": claim.narrative,
            "bill": [{"line_id": b.line_id, "description": b.description} for b in claim.bill],
        },
        indent=2,
    )
    out = llm.json(system, user, facts_schema([b.line_id for b in claim.bill]))
    return Facts(
        condition_tags=set(out["condition_tags"]),
        procedure_tags=set(out["procedure_tags"]),
        is_accident=out["is_accident"],
        line_categories={x["line_id"]: x["category"] for x in out["line_categories"]},
    )
