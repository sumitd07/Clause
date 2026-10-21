# Decision records

One short file per design decision: what we decided, why, and what it costs us. When a decision changes, its record is amended and says so.

| # | Decision |
|---|---|
| [0001](0001-deterministic-engine.md) | Plain code works out the money |
| [0002](0002-rules-are-data-with-verbatim-citations.md) | Rules are data, with word-for-word quotes |
| [0003](0003-human-approval-before-rules-go-live.md) | A person checks the rules before they count (amended for uploaded and company policies) |
| [0004](0004-deterministic-grading.md) | Code does the grading, not an AI |
| [0005](0005-local-first-files-in-git.md) | Files in git, no database |
| [0006](0006-money-is-decimal.md) | Money is exact, to the paisa |
| [0007](0007-insurer-documents-are-fetched.md) | Insurer documents are downloaded, never committed |
| [0008](0008-one-model-wrapper.md) | One place talks to Claude |
| [0009](0009-arm-b-uses-bm25.md) | "Claude with search" uses keyword search |
| [0010](0010-every-run-is-stamped.md) | Every run records what produced it |
| [0011](0011-answers-are-a-fixed-form.md) | The answer is a fixed form, filled in by code |
| [0012](0012-jev-for-yes-no-checks.md) | Try Jev for the small yes/no checks |
| [0013](0013-v1-reads-no-medical-papers.md) | v1 reads no medical papers |
| [0014](0014-question-first.md) | Ask first, then fill in only what's needed |

## Format

```markdown
# NNNN. Title in plain words

Status: accepted, date

## What we decided
## Why
## What it costs us
```
