# 0003. A person checks the rules before they count

Status: accepted, 2026-10-21. Amended 2026-10-21 for uploaded and company policies.

## What we decided

For a supported policy, every rule the rule writer proposes starts as "not checked". A person reads it next to its quote and approves, edits or rejects it. Only approved rules are used. Each rule records who checked it and what they changed.

Two cases can't wait for that check:

- **An uploaded policy** that doesn't match a supported one by UIN gets rules written on the spot. Every answer says "Rules read automatically, not checked by a person".
- **A company policy** uses rules built from the terms you type. Every answer says "Rules from the terms you typed, not from the policy wording".

## Why

The rule writer can get a number wrong (1% of the sum insured read as ₹1), miss an exception, or split one rule into two. Checking catches that before it reaches an answer. The label says when nobody checked.

## What it costs us

Time for each policy. The "rules not checked" run answers every test case with unchecked rules, so it measures what checking buys and how good uploads are.
