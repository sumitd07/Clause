# 0010. Every run records what produced it

Status: accepted, 2026-10-21

## What we decided

Each run writes a `run.json` that records:

- fingerprints of the rules, the test cases and the policy;
- the model asked for, and the models that actually answered;
- the tokens used and how long the calls took;
- the git commit, and whether there were uncommitted changes.

A case that breaks goes into `errors.jsonl`, and the run is marked incomplete. Scoring refuses an incomplete run. It also flags a run answered by more than one model as not comparable. A run on the test cases refuses to start with uncommitted changes.

## Why

Scores go wrong quietly. Expected answers go stale when a document changes, an uncommitted change gets measured by mistake, or a lost reply gets scored as a wrong answer. Each of these is only caught if something records what produced the number.

## What it costs us

A little bookkeeping in every run. In return, two scores can be compared by checking a few fingerprints and a model name, not from memory.
