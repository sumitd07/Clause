"""The one place that talks to a model.

Every call returns schema-valid JSON and is cached on disk by a hash of the full
request, so an eval rerun from cache costs nothing and gives identical results.
The model is set by CLAUSE_MODEL; change it there, never in calling code.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class RefusalError(RuntimeError):
    """The model (and its fallback) declined. Treated as route_to_human by callers."""


class TruncatedError(RuntimeError):
    """Output hit max_tokens before the JSON finished. A harness problem, not a product result."""


class MalformedOutputError(RuntimeError):
    """The reply was not valid JSON. The raw reply is saved next to the cache so it can be read."""


@dataclass
class CallRecord:
    model_served: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    request_id: str | None
    from_cache: bool
    latency_ms: int = 0
    stop_reason: str | None = None


class LLM:
    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
        cache_dir: str | Path = ".cache/llm",
        client=None,
    ):
        self.model = model or os.environ.get("CLAUSE_MODEL", DEFAULT_MODEL)
        self.effort = effort or os.environ.get("CLAUSE_EFFORT", DEFAULT_EFFORT)
        self.cache_dir = Path(cache_dir)
        self._client = client
        self.calls: list[CallRecord] = []

    @property
    def client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def _key(self, request: dict) -> str:
        return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()

    def json(self, system: str, user: str, schema: dict, max_tokens: int = 16000) -> dict:
        """One structured call. `system` should hold the stable, cacheable context (policy text)."""
        request = {
            "model": self.model,
            "effort": self.effort,
            "system": system,
            "user": user,
            "schema": schema,
            "max_tokens": max_tokens,
        }
        path = self.cache_dir / f"{self._key(request)}.json"
        if path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            self.calls.append(CallRecord(**{**cached["record"], "from_cache": True}))
            return cached["output"]

        started = time.perf_counter()
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            betas=[FALLBACK_BETA],
            fallbacks="default",
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": schema},
            },
        )
        usage = response.usage
        record = CallRecord(
            model_served=response.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            request_id=getattr(response, "_request_id", None),
            from_cache=False,
            latency_ms=round((time.perf_counter() - started) * 1000),
            stop_reason=response.stop_reason,
        )
        # Every call is recorded, including the ones that fail below: they cost tokens too.
        self.calls.append(record)

        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None) if response.stop_details else None
            raise RefusalError(f"declined (category={category})")
        if response.stop_reason == "max_tokens":
            raise TruncatedError(f"hit max_tokens={max_tokens}; raise the ceiling, this is not a model answer")

        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            output = json.loads(text)
        except json.JSONDecodeError as e:
            raw = path.with_suffix(".raw.txt")
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text(text, encoding="utf-8")
            raise MalformedOutputError(f"reply was not JSON ({e}); raw reply saved to {raw}") from e

        path.parent.mkdir(parents=True, exist_ok=True)
        rec = {k: v for k, v in asdict(record).items() if k != "from_cache"}
        path.write_text(json.dumps({"record": rec, "output": output}, indent=2), encoding="utf-8")
        return output
