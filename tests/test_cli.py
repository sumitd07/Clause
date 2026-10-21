"""End to end through the command line: run folders, stamps, and harness failures."""

import json

from clause import cli, llm

from .conftest import DATA
from .test_llm import FakeClient

RULES = str(DATA / "rules" / "SYNTH-01.rules.json")
CLAIMS = str(DATA / "claims" / "dev")
EXPECTED = str(DATA / "expected" / "dev")


def test_oracle_run_is_stamped_and_scores_100(tmp_path):
    run = tmp_path / "oracle-dev"
    assert (
        cli.main(
            ["run", "--arm", "oracle", "--rules", RULES, "--claims", CLAIMS, "--expected", EXPECTED, "--out", str(run)]
        )
        == 0
    )
    stamp = json.loads((run / "run.json").read_text())
    assert stamp["claims"]["n"] == 8 and len(stamp["rules"]["sha256"]) == 64 and stamp["errors"] == 0
    assert (
        cli.main(["score", "--rules", RULES, "--run", str(run), "--expected", EXPECTED, "--min-task-pass", "1.0"]) == 0
    )
    summary = json.loads((run / "summary.json").read_text())
    assert summary["task_pass"] == 1.0 and summary["confident_errors"] == []
    assert summary["abstention"] == {"routed": 1, "should_route": 1, "precision": 1.0, "recall": 1.0}


def test_truncated_replies_are_an_incomplete_run_not_a_score(tmp_path, monkeypatch):
    """A harness failure must never be scored as a product failure (or a pass)."""
    fake = llm.LLM(model="m", cache_dir=tmp_path / "cache", client=FakeClient({}, stop_reason="max_tokens"))
    monkeypatch.setattr(llm, "LLM", lambda: fake)
    run = tmp_path / "clause-dev"
    assert cli.main(["run", "--arm", "clause", "--rules", RULES, "--claims", CLAIMS, "--out", str(run)]) == 2
    errors = [json.loads(x) for x in (run / "errors.jsonl").read_text().splitlines()]
    assert len(errors) == 8 and {e["error"] for e in errors} == {"TruncatedError"}
    stamp = json.loads((run / "run.json").read_text())
    assert stamp["calls"]["stop_reasons"] == {"max_tokens": 8}
    assert cli.main(["score", "--rules", RULES, "--run", str(run), "--expected", EXPECTED]) == 2


def test_score_flags_runs_served_by_more_than_one_model(tmp_path, capsys):
    run = tmp_path / "r"
    cli.main(
        ["run", "--arm", "oracle", "--rules", RULES, "--claims", CLAIMS, "--expected", EXPECTED, "--out", str(run)]
    )
    stamp = json.loads((run / "run.json").read_text())
    stamp["calls"] = {"requested_model": "a", "models_served": ["a", "b"], "single_model": False}
    (run / "run.json").write_text(json.dumps(stamp))
    cli.main(["score", "--rules", RULES, "--run", str(run), "--expected", EXPECTED])
    assert "Do not compare" in capsys.readouterr().err
    assert json.loads((run / "summary.json").read_text())["comparable"] is False
