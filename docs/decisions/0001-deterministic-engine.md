# 0001. Plain code works out the money

Status: accepted, 2026-10-21

## What we decided

The engine (`src/clause/engine.py`) works out every amount: what the policy pays, what you pay, and every cut. It is ordinary code. It never calls a model, and it gives the same answer every time. The model only reads: which condition is being treated, whether there was an accident, and what each bill line is.

## Why

A room above the limit cuts the doctor's fees too, then the cap applies, then the co-payment. Each step is easy on its own. Getting all of them right, in the right order, to the paisa, is where a model doing its own sums slips. And a model's slip is hard to spot.

## What it costs us

The engine can only apply the kinds of rule it knows. A clause it can't apply becomes a "needs review" rule, so the answer is "can't tell". The test compares Clause with Claude reading the whole policy. If Claude does as well for less money, the engine isn't earning its keep, and the write-up will say so.
