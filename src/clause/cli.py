"""Command line entry point: `clause <command>`. Run `clause -h` for the list."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import arms, runlog
from .compiler import check_candidate, split_sections
from .engine import adjudicate
from .io import (
    decision_from_dict,
    decision_to_dict,
    facts_from_dict,
    load_claim,
    load_expected,
    load_rules,
    write_json,
)
from .scoring import score_claim, summarize


def cmd_answer(a) -> int:
    """The answer form for one claim. Day 0 reads the facts from a hand-checked expected file."""
    from .answer import build_answer

    claim, ruleset = load_claim(a.claim), load_rules(a.rules)
    facts = load_expected(a.expected).facts if a.expected else facts_from_dict(json.loads(Path(a.facts).read_text()))
    decision = adjudicate(claim, facts, ruleset, arm="answer")
    answer = build_answer(claim, facts, decision, ruleset)
    print(json.dumps(answer.to_dict(), indent=2, ensure_ascii=False) if a.json else answer.text(), end="")
    return 0


def cmd_explain(a) -> int:
    """What one clause says, in plain words, and what it means for this person."""
    from .answer import explain_term

    rule = load_rules(a.rules).by_id().get(a.rule)
    if rule is None:
        sys.exit(f"no rule {a.rule!r} in {a.rules}")
    print(explain_term(rule, load_claim(a.claim)).text(), end="")
    return 0


def _claims(claims_dir: Path) -> list[Path]:
    return sorted(claims_dir.glob("*.json"))


def cmd_adjudicate(a) -> int:
    claim = load_claim(a.claim)
    facts = facts_from_dict(json.loads(Path(a.facts).read_text()))
    dec = adjudicate(claim, facts, load_rules(a.rules))
    print(json.dumps(decision_to_dict(dec), indent=2))
    return 0


def _decide(a, path: Path, claim, ruleset, llm, policy_text):
    if a.arm == "oracle":
        return arms.oracle(claim, load_expected(Path(a.expected) / path.name).facts, ruleset)
    if a.arm == "long_context":
        return arms.long_context(claim, policy_text, llm)
    if a.arm == "clause":
        return arms.clause(claim, ruleset, llm)
    if a.arm == "clause_unreviewed":
        return arms.clause(claim, ruleset, llm, allow_unreviewed=True)
    raise SystemExit(f"unknown arm {a.arm}")


def cmd_run(a) -> int:
    """Run one arm over a claims folder. Writes <out>/decisions/, run.json, calls.jsonl, errors.jsonl."""
    out, claims_dir = Path(a.out), Path(a.claims)
    paths = _claims(claims_dir)
    git = runlog.git_state()
    if claims_dir.name == "test" and git["dirty"] and not a.allow_dirty:
        print(
            "refusing to run on the test split with uncommitted changes: commit first (docs/EVAL.md)", file=sys.stderr
        )
        return 2
    if a.arm == "oracle" and not a.expected:
        sys.exit("--expected is required for the oracle arm")
    if a.arm == "long_context" and not a.policy:
        sys.exit("--policy is required for long_context")

    out.mkdir(parents=True, exist_ok=True)
    ruleset = load_rules(a.rules)
    llm = None
    if a.arm != "oracle":
        from .llm import LLM

        llm = LLM()
    policy_text = Path(a.policy).read_text(encoding="utf-8") if a.policy else None
    manifest = {
        "arm": a.arm,
        "started": runlog.now(),
        "claims": {"dir": str(claims_dir), "n": len(paths), "sha256": runlog.sha256_files(paths)},
        "rules": {"path": a.rules, "sha256": runlog.sha256_files([Path(a.rules)])},
        "policy": {"path": a.policy, "sha256": runlog.sha256_files([Path(a.policy)])} if a.policy else None,
        "model": {"name": llm.model, "effort": llm.effort} if llm else None,
        "git": git,
        "env": runlog.environment(),
    }

    errors = []
    for path in paths:
        claim = load_claim(path)
        try:
            dec = _decide(a, path, claim, ruleset, llm, policy_text)
        except Exception as e:  # a harness failure must not end the run, or pass as a product result
            errors.append({"claim_id": claim.claim_id, "error": type(e).__name__, "detail": str(e)})
            print(f"{claim.claim_id}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        write_json(out / "decisions" / path.name, decision_to_dict(dec))

    manifest["finished"] = runlog.now()
    manifest["errors"] = len(errors)
    if llm is not None:
        manifest["calls"] = runlog.call_stats(llm.calls, llm.model)
        lines = runlog.call_lines(llm.calls)
        (out / "calls.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        c = manifest["calls"]
        print(
            f"{c['calls']} model calls ({c['fresh_calls']} new): {c['input_tokens']} in, {c['output_tokens']} out, "
            f"p50 {c['latency_ms_p50']} ms, served by {c['models_served']}"
        )
    if errors:
        (out / "errors.jsonl").write_text("".join(json.dumps(x) + "\n" for x in errors), encoding="utf-8")
    write_json(out / "run.json", manifest)
    print(f"wrote {len(paths) - len(errors)} decisions to {out / 'decisions'}")
    if errors:
        print(f"INCOMPLETE RUN: {len(errors)} claim(s) errored, see {out / 'errors.jsonl'}", file=sys.stderr)
        return 2
    return 0


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.1%}"


def cmd_score(a) -> int:
    run_dir = Path(a.run) if a.run else None
    decisions_dir = run_dir / "decisions" if run_dir else Path(a.decisions)
    summary_path = a.summary or (run_dir / "summary.json" if run_dir else None)
    manifest_path = (run_dir or decisions_dir.parent) / "run.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None

    ruleset = load_rules(a.rules)
    scores = []
    for path in sorted(Path(a.expected).glob("*.json")):
        expected = load_expected(path)
        dec_path = decisions_dir / path.name
        if not dec_path.exists():
            print(f"missing decision for {expected.claim_id}: incomplete run, not scored", file=sys.stderr)
            return 2
        decision = decision_from_dict(json.loads(dec_path.read_text()))
        scores.append(score_claim(decision, expected, ruleset))
    summary = summarize(scores)
    if manifest:
        summary["run"] = {k: manifest.get(k) for k in ("arm", "started", "claims", "rules", "model", "git")}
        calls = manifest.get("calls") or {}
        summary["comparable"] = calls.get("single_model", True) is not False
        if not summary["comparable"]:
            print(
                f"WARNING: calls were served by {calls['models_served']}, not only {calls['requested_model']}. "
                "Do not compare this run with single-model runs.",
                file=sys.stderr,
            )

    lo, hi = summary["task_pass_ci95"]
    ab, me = summary["abstention"], summary["money_errors"]
    print(
        f"n={summary['n']}  task pass {summary['task_pass']:.1%} (95% CI {lo:.1%} to {hi:.1%})"
        f"  rubric pass {summary['rubric_pass']:.1%}"
    )
    print(
        f"  confident errors {len(summary['confident_errors'])}"
        f"  abstention precision {_pct(ab['precision'])} recall {_pct(ab['recall'])}"
        f"  overestimated {me['overestimated']['n']} (Rs {me['overestimated']['amount']})"
        f"  underestimated {me['underestimated']['n']} (Rs {me['underestimated']['amount']})"
    )
    for t, v in summary["by_distractor_type"].items():
        print(f"  {t:<16} n={v['n']:<3} task pass {v['task_pass']:.1%}")
    if summary["failed_claims"]:
        print("  failed:", ", ".join(summary["failed_claims"]))
    if summary_path:
        write_json(summary_path, summary)
    if a.min_task_pass is not None and summary["task_pass"] < a.min_task_pass:
        print(f"GATE FAILED: task pass below {a.min_task_pass:.0%}", file=sys.stderr)
        return 1
    return 0


def cmd_check_rules(a) -> int:
    """Block candidates whose citation does not match the wording verbatim."""
    sections = split_sections(Path(a.policy).read_text(encoding="utf-8"))
    bad = 0
    for rule in load_rules(a.rules).rules:
        for problem in check_candidate(rule, sections):
            print(f"{rule.id}: {problem}")
            bad += 1
    print(f"{bad} problem(s)")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="clause")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("adjudicate", help="engine only: one claim, given facts")
    s.add_argument("--rules", required=True)
    s.add_argument("--claim", required=True)
    s.add_argument("--facts", required=True)
    s.set_defaults(func=cmd_adjudicate)

    s = sub.add_parser("answer", help="the answer form a person reads, for one claim")
    s.add_argument("--rules", required=True)
    s.add_argument("--claim", required=True)
    given = s.add_mutually_exclusive_group(required=True)
    given.add_argument("--expected", help="take the facts from a hand-checked expected file")
    given.add_argument("--facts", help="take the facts from a facts file")
    s.add_argument("--json", action="store_true", help="print the form as JSON")
    s.set_defaults(func=cmd_answer)

    s = sub.add_parser("explain", help="what one clause means for this person")
    s.add_argument("--rules", required=True)
    s.add_argument("--claim", required=True, help="the person's details")
    s.add_argument("--rule", required=True, help="rule id, e.g. SYN-RR")
    s.set_defaults(func=cmd_explain)

    s = sub.add_parser("run", help="run an arm over a folder of claims")
    s.add_argument("--arm", required=True, choices=["oracle", "long_context", "clause", "clause_unreviewed"])
    s.add_argument("--rules", required=True)
    s.add_argument("--claims", required=True)
    s.add_argument("--out", required=True, help="run folder, e.g. eval/results/clause-dev")
    s.add_argument("--expected", help="needed by the oracle arm (gold facts)")
    s.add_argument("--policy", help="policy wording text, needed by long_context")
    s.add_argument("--allow-dirty", action="store_true", help="permit a test-split run with uncommitted changes")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("score", help="grade decisions against expected outcomes")
    s.add_argument("--rules", required=True)
    where = s.add_mutually_exclusive_group(required=True)
    where.add_argument("--run", help="run folder written by `clause run`; summary goes to <run>/summary.json")
    where.add_argument("--decisions", help="a bare folder of decision files")
    s.add_argument("--expected", required=True)
    s.add_argument("--summary", help="write the summary JSON here")
    s.add_argument("--min-task-pass", type=float, help="exit 1 below this task pass rate (CI gate)")
    s.set_defaults(func=cmd_score)

    s = sub.add_parser("check-rules", help="verify every rule's quote appears in its cited section")
    s.add_argument("--rules", required=True)
    s.add_argument("--policy", required=True)
    s.set_defaults(func=cmd_check_rules)

    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
