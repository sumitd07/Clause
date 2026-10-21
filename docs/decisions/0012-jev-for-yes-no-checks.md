# 0012. Try Jev for the small yes/no checks

Status: accepted, 2026-10-21. Not run yet: there is no TypeSafe key in this environment.

## What we decided

Most of reading a question is small checks: "Is the condition being treated cataract?" "Did this stay follow an accident?" "What kind of charge is this line?" Jev, a model from TypeSafe, answers yes/no and pick-one questions like these with a probability, fast and cheaply. We try it for these checks, and as a filter that skips policy sections with no rules before Claude writes rules.

When Jev is unsure, Clause works the answer out both ways. If both give the same answer, the doubt doesn't matter. If not, Claude reads the case. The "unsure" cut-offs start at 0.2 and 0.8, and are set on dev cases and written down before any test run.

Jev is optional, with its key in `TYPESAFE_API_KEY`. The version is pinned and recorded on every call.

## Why

A large model for every yes/no check is slow and costly. Jev, plain code (keyword matching) and Claude are measured on the same cases.

## What it costs us

A second provider sees what people type. With 60 test cases only big differences show, so claims stay modest ([EVAL.md](../EVAL.md)).
