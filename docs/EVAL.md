# How Clause is tested

This file is written and committed before any system runs on the test cases. Any later change goes in the change log at the bottom, with the reason.

## At a glance

| | |
|---|---|
| The question | Does Clause answer "what will my policy pay?" more reliably than Claude reading the policy? |
| One test case | A person's details, what they typed, any amounts, and the answer worked out by hand |
| Who grades | Code. No AI grades the main results |
| Test cases | 60, across 5 real policies, locked before any system sees them |
| Main score | Fully right: the right verdict, amount and clauses |

## What is compared

Every system gets the same cases, and the same Claude model and settings.

| System | Code name | Who reads the question | Who works out the answer |
|---|---|---|---|
| Perfect reading | `oracle` | Nobody: the correct facts, typed by hand | Code |
| Claude with the whole policy | `long_context` | Claude | Claude |
| Claude with search | `rag` | Claude, given the 6 best-matching sections | Claude |
| Clause | `clause` | Claude | Code |
| Clause, rules not checked | `clause_unreviewed` | Claude | Code, with rules no person checked |
| Clause, plain code reads | `clause_keywords` | Keyword matching | Code |
| Clause with Jev | `clause_jev` | Jev, or Claude when Jev is unsure and it matters | Code |

Perfect reading is a check, not a contender. It must score 100% on the dev cases, and CI checks this on every push. Anything less means the code or a hand-worked answer is wrong.

"Rules not checked" is also how uploaded policies work, so its score is the number for uploads.

Search uses 6 sections, fixed before the first run. If search does badly, the number is not raised to rescue it.

## What we expect, written down first

Each is reported as supported, not supported, or unclear, with its range.

| # | Expectation | How it is checked |
|---|---|---|
| H1 | Clause gets more cases fully right than both Claude systems | Same cases, compared pair by pair. Supported if the range of the difference stays above zero |
| H2 | The gap is biggest on cases with a trap | Scores by trap kind. Description only: about 5 cases each |
| H3 | Checking rules by hand makes Clause better | Clause against "rules not checked". This is also the number for uploads |
| H4 | Clause with Jev gets as many cases fully right as Clause, for less money and time | 60 cases only show big differences, so this is claimed only as "no difference found", next to Jev's accuracy on each check |
| H5 | For "which policy first", Clause picks the cheaper order more often than Claude given both policies | Description only: 10 cases |

If H1 fails, that is the result, and the write-up says so.

## How an answer is scored

A case is **fully right** when all four hold:

1. The verdict is right: covered, partly, not covered, or can't tell.
2. The amount is within ₹1 of the hand-worked answer. Skipped when the right answer is "can't tell" (`route_to_human` in code).
3. It names every clause that changed the answer.
4. It names no clause a careless reader would wrongly apply, such as the room rent waiver on a policy without that rider.

For Clause, "names" means the rules its code applied. For the Claude systems, it means the sections Claude cites. **Partly right** is the share of the four checks passed. It shows progress, but never replaces fully right.

Reported on their own, never mixed into one number:

| Measure | What it means |
|---|---|
| Confident mistakes | Wrong answers given without a "can't tell". People act on these. Target 0, each with a written cause |
| "Can't tell" when needed | Of the cases that needed it, how many got it |
| "Can't tell" justified | Of its "can't tell" answers, how many were right to be |
| Said more, said less | Cases where it said the policy pays more, or less, than it does, beyond ₹1. Count and rupees |
| Cost and time per answer | From the run record. A better score at ten times the cost is a different result |

## The cases

| Set | Size | Used for |
|---|---|---|
| Dev | 8 on SYNTH-01 now, about 12 on real policies by week 2 | Building and tuning. Never reported |
| Test | 60 questions about a treatment | The main results. Locked with the git tag `eval-frozen-v1` |
| Two-policy cases | 10 | Which policy to claim from first |
| Question-type checks | 10 questions about a term, 5 off-topic | Right kind of answer, or "can't help" |
| Made-up schedules | 10 | How well Clause reads a schedule |
| Hand-written rules | Every rule in 2 of the 5 policies | How well the rule writer reads a policy |

The test mix, fixed before writing: 40% plain, 40% with one trap each, 20% where the right answer is "can't tell". Each case records its trap in `distractor_type`:

| Trap | Code name | Dev example |
|---|---|---|
| Look-alike rule: two rules seem to apply, one does | `near_distractor` | C0004: cataract on day 1,202. The ₹40,000 cap applies; the 2-year wait has ended |
| Hidden trigger: a detail in passing triggers a rule | `conditional` | C0002: "chose a deluxe single room" triggers the room rent cut |
| Misleading word: it points at a rule that doesn't apply | `decoy` | C0006: "reconstruction" after a road accident is not cosmetic |
| Switched off: a rider turns a rule off | `override` | C0003: the room rent waiver rider |
| Can't tell: the facts can't settle it | `route` | C0007: nobody knows if the condition was declared |

[ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md) explains how to write cases.

## Other checks, reported separately

These explain the main results and are never mixed into them.

- **Rule writer:** how many of its rules are right, how many hand-written rules it found, and how often the checker edited a rule. Each product's Customer Information Sheet is a free extra answer key.
- **Reading:** for each check (the condition, accident or not, each line's kind of charge), how often plain code, Claude and Jev get it right.
- **Jev's cut-offs:** how often Jev was unsure, and how often that doubt changed the answer, for each cut-off tried on dev.
- **Schedule reading:** how often each field is right.
- **Question type:** how many of the 15 checks got the right kind of answer.
- **Run errors:** cut-off replies, broken replies, network errors. A run with any is incomplete and not scored.

## Rules for running tests

1. **Lock first.** Commit the cases, answers and this file, then tag `eval-frozen-v1`. `clause run` refuses the test cases while there are uncommitted changes.
2. **Tune on dev only.** No dev or test case ever goes in a prompt.
3. **Change one thing at a time,** and keep the negative results.
4. **Compare like with like:** same rules, cases, model and settings. `run.json` records them. A run where another model answered any call is marked `comparable: false`.
5. **Check the run before blaming the product.** Read its errors and a few raw answers first.
6. **At most 3 test runs per system,** each logged below.
7. **Answers before systems.** Work out every answer before any system sees the case, and do the second check without looking at any system's output.

## How sure the numbers are

Each score comes with a likely range. To get it, draw 60 cases at random from the 60, with repeats, score the draw, and do this 2,000 times (seed 0, so anyone gets the same range). On 60 cases the range is about ±10 points, so only bigger differences are claimed. Two systems are compared on the same draws.

## Results templates

Table 1: Clause against Claude, on the 60 test cases.

| System | Fully right (range) | Partly right | Confident mistakes | "Can't tell" needed / justified | Said more (n, ₹) | Said less (n, ₹) | Cost | Time | Run |
|---|---|---|---|---|---|---|---|---|---|
| Claude with the whole policy | | | | | | | | | |
| Claude with search | | | | | | | | | |
| Clause | | | | | | | | | |
| Clause, rules not checked | | | | | | | | | |

Table 2: Who reads the question. Same rules and code for all three.

| Reader | Fully right (range) | Confident mistakes | Reading accuracy | Cost | Time | Run |
|---|---|---|---|---|---|---|
| Plain code | | | | | | |
| Claude | | | | | | |
| Jev, Claude when unsure | | | | | | |

Table 3: Which policy first, on the 10 two-policy cases.

| System | Cheaper order picked | What you pay, within ₹1 | Run |
|---|---|---|---|
| Claude given both policies | | | |
| Clause | | | |

Mistakes table. Every wrong case gets exactly one cause.

| Cause \ trap | Plain | Look-alike | Hidden trigger | Misleading word | Switched off | Can't tell |
|---|---|---|---|---|---|---|
| Wrong or missing rule | | | | | | |
| Misread the question | | | | | | |
| Code | | | | | | |
| Claude's reasoning | | | | | | |

## Test-run log

| Date | System | Commit | Run folder | Why |
|---|---|---|---|---|
| | | | | |

## Change log

| Date | Change | Reason |
|---|---|---|
| 2026-10-21 | First version | |
| 2026-10-21 | Plain words. Added Jev and plain-code readers (Table 2), two-policy cases and H5, question-type checks and schedule reading. "Rules not checked" now also measures uploads. The old verifier is dropped; a double check where Jev and Claude must agree moves to month two. H4 is now about Jev | Product changes agreed before any test case existed |

## Watch-outs

- About 12 "can't tell" test cases is a thin base. Jev's cut-offs are set on dev, never on test.
- Perfect reading at 100% proves the code and the answers agree, not that both are right. The blind second check catches a shared mistake.
- "Which policy first" rests on how the second policy pays. If the IRDAI check in week 1 changes that, the two-policy answers are reworked before the lock.
