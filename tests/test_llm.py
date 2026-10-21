"""The model wrapper, with a fake client: caching, refusal handling, and arm wiring."""

import json
from types import SimpleNamespace

import pytest

from clause import arms
from clause.io import load_claim
from clause.llm import LLM, RefusalError

from .conftest import DATA


class FakeClient:
    def __init__(self, payload, stop_reason="end_turn"):
        self.payload, self.stop_reason, self.calls = payload, stop_reason, 0
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls += 1
        assert kw["fallbacks"] == "default"
        assert kw["output_config"]["format"]["type"] == "json_schema"
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            stop_details=SimpleNamespace(category="test") if self.stop_reason == "refusal" else None,
            content=[
                SimpleNamespace(type="thinking", text=""),
                SimpleNamespace(type="text", text=json.dumps(self.payload)),
            ],
            model="fake-model",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0),
        )


def test_second_identical_call_is_served_from_cache(tmp_path):
    client = FakeClient({"ok": True})
    llm = LLM(model="m", cache_dir=tmp_path, client=client)
    schema = {"type": "object"}
    assert llm.json("s", "u", schema) == {"ok": True}
    assert llm.json("s", "u", schema) == {"ok": True}
    assert client.calls == 1
    assert [c.from_cache for c in llm.calls] == [False, True]


def test_refusal_raises(tmp_path):
    llm = LLM(model="m", cache_dir=tmp_path, client=FakeClient({}, stop_reason="refusal"))
    with pytest.raises(RefusalError):
        llm.json("s", "u", {"type": "object"})


def test_refusal_routes_to_human_in_arm_c(tmp_path, ruleset):
    claim = load_claim(DATA / "claims" / "dev" / "C0001.json")
    llm = LLM(model="m", cache_dir=tmp_path, client=FakeClient({}, stop_reason="refusal"))
    assert arms.clause(claim, ruleset, llm).status == "route_to_human"


def test_arm_c_uses_extracted_facts(tmp_path, ruleset):
    claim = load_claim(DATA / "claims" / "dev" / "C0001.json")
    cats = ["room", "doctor_fees", "nursing", "pharmacy", "diagnostics", "non_medical"]
    payload = {
        "condition_tags": [],
        "procedure_tags": [],
        "is_accident": False,
        "line_categories": [{"line_id": f"L{i + 1}", "category": c} for i, c in enumerate(cats)],
    }
    llm = LLM(model="m", cache_dir=tmp_path, client=FakeClient(payload))
    dec = arms.clause(claim, ruleset, llm)
    assert str(dec.total_payable) == "34000.00"
    assert dec.applied_rules == ["SYN-NP-ITEMS"]
