"""Run stamps. Every eval run records exactly what produced it.

A score is only comparable to another score produced the same way: same rules, same
claims, same model, same code. The stamp in run.json is what makes that checkable
later, instead of remembered.
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
from collections.abc import Iterable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from . import __version__


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_files(paths: Iterable[Path]) -> str:
    """One hash over several files, in name order, so a changed label or rule changes the stamp."""
    h = hashlib.sha256()
    for p in sorted(Path(x) for x in paths):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def git_state(cwd: Path | None = None) -> dict:
    def git(*args: str) -> str | None:
        try:
            r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return None
        return r.stdout.strip() if r.returncode == 0 else None

    commit = git("rev-parse", "HEAD")
    status = git("status", "--porcelain", "--untracked-files=no")
    return {"commit": commit, "dirty": None if status is None else bool(status)}


def percentile(values: list[int], q: float) -> int | None:
    if not values:
        return None
    s = sorted(values)
    return s[min(len(s) - 1, round(q * (len(s) - 1)))]


def call_stats(calls: list, requested_model: str | None) -> dict:
    fresh = [c for c in calls if not c.from_cache]
    served = sorted({c.model_served for c in calls})
    return {
        "requested_model": requested_model,
        "models_served": served,
        "single_model": served == [requested_model] if requested_model else None,
        "calls": len(calls),
        "fresh_calls": len(fresh),
        "input_tokens": sum(c.input_tokens for c in fresh),
        "output_tokens": sum(c.output_tokens for c in fresh),
        "cache_read_tokens": sum(c.cache_read_tokens for c in fresh),
        "latency_ms_p50": percentile([c.latency_ms for c in fresh], 0.5),
        "latency_ms_p95": percentile([c.latency_ms for c in fresh], 0.95),
        "stop_reasons": {
            r: sum(str(c.stop_reason) == r for c in fresh) for r in sorted({str(c.stop_reason) for c in fresh})
        },
    }


def call_lines(calls: list) -> list[dict]:
    return [asdict(c) for c in calls]


def environment() -> dict:
    return {"clause": __version__, "python": platform.python_version()}
