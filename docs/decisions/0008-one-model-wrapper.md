# 0008. One place talks to Claude

Status: accepted, 2026-10-21

## What we decided

`src/clause/llm.py` is the only code that calls Claude. The model and effort come from `CLAUSE_MODEL` and `CLAUSE_EFFORT` in `.env`, never from the code. Every reply must match a fixed format, and is saved on disk by its exact request, so asking again costs nothing and gives the same answer. Every call records which model answered, the tokens used and how long it took.

If Claude declines, a fallback model may answer, and the record shows it. If nothing answers, the case gets "can't tell". A cut-off or garbled reply marks the run as broken, not the answer as wrong.

## Why

Scores can only be compared when the model, settings and inputs are the same. Re-running a test shouldn't cost money or change answers.

## What it costs us

A run where any call was answered by a fallback model is marked "not comparable". Jev gets the same treatment: one place, a pinned version, every call recorded ([0012](0012-jev-for-yes-no-checks.md)).
