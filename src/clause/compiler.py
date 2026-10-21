"""Policy wording -> candidate rules. Candidates go live only after human review (ADR 0003).

Implemented now: the deterministic guards that every candidate must pass.
Built in week 2: the model call that proposes candidates per section (docs/BUILD_PLAN.md).
"""

from __future__ import annotations

import re

from .models import RULE_TYPES, Rule

SECTION_RE = re.compile(r"^(?:#+\s*)?(\d+(?:\.\d+)*|E\d+)\s+(.+)$")


def split_sections(text: str) -> dict[str, str]:
    """Split wording into {section number: text}. Headings look like '4.2 Specific waiting period'."""
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        m = SECTION_RE.match(line.strip())
        if m:
            current = m.group(1)
            sections[current] = [m.group(2)]
        elif current is not None:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _norm(s: str) -> str:
    return " ".join(s.split()).lower()


def check_candidate(rule: Rule, sections: dict[str, str]) -> list[str]:
    """Problems that block a candidate before a human sees it. Empty list means it may be reviewed."""
    problems = []
    if rule.type not in RULE_TYPES:
        problems.append(f"unknown rule type {rule.type!r}")
    section = sections.get(rule.citation.section)
    if section is None:
        problems.append(f"cited section {rule.citation.section!r} not found in wording")
    elif _norm(rule.citation.quote) not in _norm(section):
        problems.append("quote is not verbatim in the cited section")
    return problems


def compile_policy(text: str, llm) -> list[Rule]:
    raise NotImplementedError("rule compiler lands in week 2: see docs/BUILD_PLAN.md")
