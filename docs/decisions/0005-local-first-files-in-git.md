# 0005. Files in git, no database

Status: accepted, 2026-10-21

## What we decided

Rules, test cases, expected answers and run summaries are JSON files in git. Each run writes a folder under `eval/results/`. There is no database and no server in v1. Clause runs on your own computer.

## Why

The whole project holds a few hundred rules and cases, and one person builds it, two hours a day. A database would take setup time and give nothing back at this size. Files in git make every change to a rule or an expected answer easy to see. The freeze is just a git tag.

## What it costs us

Two people can't edit the rules at the same time without stepping on each other. A web review queue or a hosted app will need a small store. Until then, the files stay the source of truth.
