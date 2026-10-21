# Common tasks. Run `make help` for the list.
PY      ?= python
RULES   ?= data/rules/SYNTH-01.rules.json
POLICY  ?= data/policies/SYNTH-01.md
SPLIT   ?= dev
ARM     ?= clause
RUN     ?= $(ARM)-$(SPLIT)
OUT     := eval/results/$(RUN)
ORACLE  := eval/results/oracle-$(SPLIT)
CLAIM   ?= C0004

.PHONY: help install test lint format check-rules oracle answer eval fetch clean

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## install the package and dev tools in the active environment
	$(PY) -m pip install -e ".[dev]"

test: ## run the test suite
	$(PY) -m pytest

lint: ## lint and check formatting
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

format: ## apply formatting and safe lint fixes
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

check-rules: ## every rule quote must appear verbatim in its cited section
	$(PY) -m clause.cli check-rules --rules $(RULES) --policy $(POLICY)

oracle: ## gold facts through the engine; must score 100% or the labels and engine disagree
	$(PY) -m clause.cli run --arm oracle --rules $(RULES) --claims data/claims/$(SPLIT) --expected data/expected/$(SPLIT) --out $(ORACLE)
	$(PY) -m clause.cli score --rules $(RULES) --run $(ORACLE) --expected data/expected/$(SPLIT) --min-task-pass 1.0

answer: ## the answer form for one dev case (CLAIM=C0004), from its hand-checked facts
	$(PY) -m clause.cli answer --rules $(RULES) --claim data/claims/dev/$(CLAIM).json --expected data/expected/dev/$(CLAIM).json

eval: ## run one arm (ARM=clause|long_context|clause_unreviewed) on one split; needs ANTHROPIC_API_KEY
	$(PY) -m clause.cli run --arm $(ARM) --rules $(RULES) --policy $(POLICY) --claims data/claims/$(SPLIT) --out $(OUT)
	$(PY) -m clause.cli score --rules $(RULES) --run $(OUT) --expected data/expected/$(SPLIT)

fetch: ## download insurer wordings listed in data/manifest.csv and verify their hashes
	$(PY) scripts/fetch_policies.py

clean: ## remove build files and tool caches (keeps run folders and the model call cache)
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
