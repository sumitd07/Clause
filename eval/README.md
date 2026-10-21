# Test results

Each run of a system on a set of cases writes a folder: `eval/results/<system>-<set>/`, for example `eval/results/clause-dev/`.

| File | Kept in git | What it holds |
|---|---|---|
| `run.json` | Yes | What produced the run: the system, the rules and cases (with their hashes), the model asked for and the model that answered, tokens, time, and the git commit |
| `summary.json` | Yes | The scores: fully right (with its likely range), partly right, confident mistakes, "can't tell" when needed and justified, paid more or less than it should, by trap kind |
| `decisions/` | No | One answer per case. Rebuild it from the saved replies with the same command |
| `calls.jsonl` | No | One line per model call |
| `errors.jsonl` | No | Only when a case hit a run error. The run is then incomplete |

Only test-set runs listed in the test-run log in [docs/EVAL.md](../docs/EVAL.md) are reported. Dev runs are for building.

## Rule writer

Filled in week 2. For the 2 policies whose rules were written by hand first: how many of the written rules the rule writer found, how many of its rules were right, and how often the person checking them had to edit one.

| Rule type | Written by hand | Written by the rule writer | Matching | Share of its rules that were right | Share of hand rules it found | Edited when checked |
|---|---|---|---|---|---|---|

## Results

Filled in week 4. The tables are laid out in [docs/EVAL.md](../docs/EVAL.md).
