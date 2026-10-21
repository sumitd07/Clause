# 0011. The answer is a fixed form, filled in by code

Status: accepted, 2026-10-21

## What we decided

A question about a treatment always gets the same sections, in the same order: what Clause understood, is it covered, from when, limits, what you pay, line by line (when you gave amounts), what would settle it (when Clause can't tell), where this comes from, and a note on whether a person checked the rules.

Code fills in every line from the engine's result (`src/clause/answer.py`). No model writes any of it. The "In plain words" line under each clause is the rule's `plain` text, written once and checked by a person with the rest of the rule.

## Why

The same question gets the same shape, so it's easy to scan under stress. Nothing can be made up: every number comes from the result, and every quote from the policy.

## What it costs us

It reads less naturally than a written reply, and each new kind of question needs its own form.
