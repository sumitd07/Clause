# Clause

Tells people what their health insurance policy covers and pays for a hospital stay, and why. The answer is a fixed form (is it covered, from when, limits, what you pay), and every line quotes the clause behind it. Read `README.md`, then `docs/ARCHITECTURE.md` and `docs/EVAL.md` before changing code. `docs/BUILD_PLAN.md` says what is next.

## Commands

```bash
make test               # must pass before and after every change
make lint               # ruff check and format check, as CI runs them
make check-rules        # rule quotes must be word for word
make oracle             # correct facts through the engine: must stay at 100%
make answer CLAIM=C0004 # the answer form for one dev case
make eval ARM=clause    # live model run on dev; needs ANTHROPIC_API_KEY, spends credit
```

`clause answer --rules R --claim C --expected E` prints the answer form. `clause explain --rules R --claim C --rule SYN-RR` explains one clause for this person.

## Rules that do not bend

- No model does arithmetic or decides an amount. Money is worked out in `engine.py`, as `Decimal`, through `models.money()`.
- No model writes the answer a person reads. `answer.py` fills in the form from the engine's decision. The plain-words line is each rule's `plain` text, checked by a person with the rule.
- `llm.py` is the only place that calls Claude. The model and effort come from `CLAUSE_MODEL` and `CLAUSE_EFFORT`. Never hardcode them elsewhere.
- No AI grader in any headline number. Grading is `scoring.py` against hand-worked answers.
- Never edit an expected answer to make a test or the oracle pass. Work it out again by hand. If it still stands, the engine is wrong, so write a failing test first.
- Never run a system on `data/claims/test/` except for the logged test runs in `docs/EVAL.md`. Never put an example from dev or test into a prompt.
- A run error (a reply cut off, invalid JSON, an API failure) is never scored as an answer. Keep it in `errors.jsonl`.
- Every new rule type ships together with its schema branch, engine code, a hand-worked test and a dev case.
- Never commit `.env`, insurer PDFs, extracted policy text or `.cache/`.

## Conventions

- Python 3.11+, the standard library plus `anthropic`. Ask before adding a dependency.
- Rule ids: `<INSURER>-<TYPE>-<NAME>`, stable, never reused.
- Docs: plain everyday words, an example first, short sentences, no jargon. Keep them short. No em-dashes. "At a glance" at the top and "Watch-outs" at the end of design docs.
- A decision that changes the design gets a record in `docs/decisions/`.

## When you finish a change

End with a GitHub-ready summary: a one-line commit message, then a short list of what changed. I commit through GitHub Desktop.
