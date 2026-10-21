# 0013. v1 reads no medical papers

Status: accepted, 2026-10-21

## What we decided

v1 reads what you type, plus two digital PDFs: the policy wording, and the policy schedule (the summary your insurer emails when you buy or renew). It doesn't read:

- prescriptions;
- discharge summaries;
- estimates or bills;
- settlement letters;
- photos or scans of anything.

You type the facts instead, such as the condition, the room rent per day and the estimate's lines.

## Why

Reading those papers well is a hard problem of its own: handwriting, scans, tables. Mixing it in would hide whether Clause applies the policy correctly. The papers are also personal health data. The schedule is different: it's a digital PDF with fixed fields, it holds no treatment details, and every answer needs what's in it.

## What it costs us

More typing for questions with amounts. Clause also can't check an insurer's deductions yet, because that needs the settlement letter. v2 starts with digital estimates and settlement letters, then prescriptions and photos.
