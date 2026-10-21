# 0002. Rules are data, with word-for-word quotes

Status: accepted, 2026-10-21

## What we decided

Each rule is a small JSON record in `data/rules/`. It says what the rule does, and quotes the policy word for word, with the section number. `make check-rules` fails if a quote isn't found, word for word, in the section it cites. CI runs this check on every change.

## Why

If you dispute a deduction, you need the exact words of your policy, not a summary. A quote that has been reworded can drift from what the policy actually says. A rule that can't be traced back to the wording can't be trusted.

## What it costs us

The rule writer can't paraphrase. Anything it rewords is blocked before a person ever sees it. When an insurer changes its wording, every rule has to be checked again, and the check flags each quote that no longer matches. Scanned policies with no text layer can't be checked this way, which is why they're out of v1.
