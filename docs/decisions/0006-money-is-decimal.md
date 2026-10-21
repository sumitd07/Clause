# 0006. Money is exact, to the paisa

Status: accepted, 2026-10-21

## What we decided

Every amount is a Python `Decimal`, not a float. It is rounded half up to the paisa after each step, always through `models.money()`. In files, amounts are written as strings such as `"68333.33"`.

## Why

Ordinary computer numbers (floats) can't hold ₹68,333.33 exactly. The tiny errors add up across the room rent cut, the cap and the co-payment. Exact decimals give the same answer on every machine.

## What it costs us

Amounts from Claude arrive as plain numbers and have to be converted on the way in. Grading allows ₹1 of difference. That covers two correct methods rounding at different steps, not a wrong sum. If a policy ever states its own rounding rule, rounding becomes part of the rule.
