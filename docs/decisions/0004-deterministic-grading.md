# 0004. Code does the grading, not an AI

Status: accepted, 2026-10-21

## What we decided

Every test case has an expected answer, worked out by hand. Code compares each system's answer with it. A case is fully right only when four things all hold:

- the verdict is right;
- the amount is within ₹1;
- every clause that matters is named;
- no clause that doesn't apply is named.

No AI grades any headline number.

## Why

AI graders aren't steady. Two of them can disagree about the same answers by more than the systems being compared differ from each other, so the choice of grader ends up deciding the result. A question about what a policy pays has a right answer, so code can check it.

## What it costs us

The expected answers have to be right. Two checks guard them. Perfect reading (correct facts through the engine) must score 100% in CI. A second hand check, done without looking at any system's output, catches a mistake the engine and the answer share. Anything without a checkable answer, such as how clear the wording is, stays out of the headline.
