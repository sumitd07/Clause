"""Every data file must match its schema, and every rule quote must be verbatim in the wording."""

import json

import pytest
from jsonschema import Draft202012Validator

from clause.compiler import check_candidate, split_sections

from .conftest import DATA, ROOT

SCHEMAS = ROOT / "schemas"


def _validator(name):
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize(
    "schema,folder",
    [("rules", "rules"), ("claim", "claims"), ("expected", "expected")],
)
def test_files_match_schema(schema, folder):
    v = _validator(schema)
    files = sorted((DATA / folder).rglob("*.json"))
    assert files, f"no files under data/{folder}"
    for f in files:
        errors = sorted(v.iter_errors(json.loads(f.read_text())), key=str)
        assert not errors, f"{f.relative_to(ROOT)}: {errors[0].message}"


def test_every_claim_has_an_expected_outcome():
    claims = {p.name for p in (DATA / "claims").rglob("*.json")}
    expected = {p.name for p in (DATA / "expected").rglob("*.json")}
    assert claims == expected


def test_rule_quotes_are_verbatim(ruleset):
    sections = split_sections((DATA / "policies" / "SYNTH-01.md").read_text())
    for rule in ruleset.rules:
        assert check_candidate(rule, sections) == [], rule.id


def test_quote_check_catches_paraphrase(ruleset):
    from dataclasses import replace

    sections = split_sections((DATA / "policies" / "SYNTH-01.md").read_text())
    rule = ruleset.by_id()["SYN-RR"]
    bad = replace(rule, citation=replace(rule.citation, quote="Room rent is capped at one percent of cover."))
    assert check_candidate(bad, sections) == ["quote is not verbatim in the cited section"]


def test_decision_schema_accepts_engine_output(ruleset):
    from clause.engine import adjudicate
    from clause.io import decision_to_dict, load_claim, load_expected

    v = _validator("decision")
    for p in sorted((DATA / "claims" / "dev").glob("*.json")):
        exp = load_expected(DATA / "expected" / "dev" / p.name)
        out = decision_to_dict(adjudicate(load_claim(p), exp.facts, ruleset))
        assert not list(v.iter_errors(out)), p.stem
