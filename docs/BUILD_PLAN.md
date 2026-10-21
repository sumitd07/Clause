# Build plan

About 44 hours over four weeks, at about 2 hours a day. The write-up and a short demo come in week 5.

## At a glance

| Week | Hours | Goal |
|---|---|---|
| Day 0 | done | The engine, scoring and the answer form work on a made-up policy |
| 1 | 14 | Real policies in, rules for two of them written by hand, the first 30 test cases |
| 2 | 14 | All test cases written and frozen, then the rule writer and review queue |
| 3 | 9 | Question first, schedule upload, two policies, Claude with search |
| 4 | 7 | Jev, the test runs, the results |
| 5 | not counted | Write-up and a two-minute demo |

The plan grew from 32 hours. The new features are two policies with "which first", question first with schedule upload, and Jev.

## Day 0: already done

The formats for rules, test cases and answers (`schemas/`). The engine, which works out what the policy pays (`engine.py`). Scoring by code (`scoring.py`). The answer form (`answer.py`). Claude reading a case, and Claude with the whole policy (`facts.py`, `arms.py`, `llm.py`). Run records (`runlog.py`). SYNTH-01, a made-up policy, with 8 dev cases. 58 tests, and CI that runs them.

## Week 1: real policies and hand-written rules (14 hours)

| # | Task | Hours | Done when |
|---|---|---|---|
| 1.1 | Reread [PRODUCT.md](PRODUCT.md) and [EVAL.md](EVAL.md). Change anything you disagree with now | 1 | You agree with every line |
| 1.2 | Pick 5 policies from 3 insurers, fill `data/manifest.csv`, download them | 2 | `make fetch` says ok for every row |
| 1.3 | Check the IRDAI numbers, and the rule for claiming from two policies, against the current master circular | 1 | Every number has a source in [DATA.md](DATA.md) |
| 1.4 | Clean the text of 2 policies so Clause finds every numbered section | 1.5 | No section is missed |
| 1.5 | Write down every rule in those 2 policies by hand, with its plain words | 4 | `make check-rules` passes on both |
| 1.6 | Add what the engine lacks: co-payment for parents, and anything else the 2 policies need | 1.5 | `make test` and `make oracle` pass |
| 1.7 | Write the first 30 test cases, in the words a person would type | 3 | Each one passes `make oracle` |

## Week 2: freeze the test, then build the rule writer (14 hours)

| # | Task | Hours | Done when |
|---|---|---|---|
| 2.1 | The other 30 test cases, 10 two-policy cases, 10 made-up policy schedules, about 12 dev cases | 5 | The mix matches [EVAL.md](EVAL.md) |
| 2.2 | Check every expected answer a second time, without looking at any system's output | 1 | Every disagreement settled by working it out again by hand |
| 2.3 | **Freeze**: commit, tag `eval-frozen-v1`, push the tag | 0.25 | The tag is on GitHub before 2.4 starts |
| 2.4 | Rule writer: Claude reads each section and proposes rules; quotes that aren't word for word are blocked | 3 | Runs on all 5 policies |
| 2.5 | How good the rule writer is, against the 2 policies written by hand in 1.5 | 1 | A table in `eval/README.md` |
| 2.6 | Review queue: see each proposed rule with its quote, then approve, edit or reject it | 1.5 | All 5 policies reviewed, edits counted |
| 2.7 | Upload: match the UIN to a supported policy, or write rules on the spot and label them "not checked" | 1 | Works on one uploaded wording |
| 2.8 | Run Claude with the whole policy, and Clause, on the dev cases | 1.25 | Both runs finish and are scored |

## Week 3: make it easy to use (9 hours)

| # | Task | Hours | Done when |
|---|---|---|---|
| 3.1 | Question type: a treatment, a term, which policy first, or something else | 1 | Right on the dev cases |
| 3.2 | Ask only what the question needs | 1.5 | A cataract question asks for the start date and age, not the sum insured left |
| 3.3 | Read the policy schedule, show what was read, save "My policies" on your computer | 2.5 | Field accuracy on the 10 made-up schedules is reported |
| 3.4 | A company policy from typed terms, and which policy to claim from first | 2.5 | Works on the dev two-policy cases |
| 3.5 | Claude with search: the 6 best-matching sections, same question as Claude with the whole policy | 1.5 | Runs on dev and is scored |

## Week 4: Jev, test runs, results (7 hours)

| # | Task | Hours | Done when |
|---|---|---|---|
| 4.1 | Jev and plain-code readers. Set Jev's "unsure" cut-offs on dev and write them down | 3 | Both run on dev; cut-offs committed |
| 4.2 | Test runs for every system, each logged in [EVAL.md](EVAL.md) | 0.5 | All runs finish and are comparable |
| 4.3 | Results table and mistakes table | 1.5 | Every wrong answer has one named cause |
| 4.4 | A simple local page: your question, your details, the answer form | 2 | A question goes in, the form comes out |

## Week 5: write-up

Not counted in the 44 hours. One page: the problem, how Clause works, the results, the mistakes, and what comes next. Plus a two-minute recording of a question going in and the answer coming out.

## If you fall behind

Cut in this order, and say so in the README:

1. The local page. The demo runs in the terminal instead.
2. Claude with search. Claude with the whole policy is the main comparison.
3. The plain-code reader.

Never cut the freeze, the second check of the expected answers, or the rules-not-checked run. They are what make the results believable.

## Month two

A double check (Jev and Claude both read; "can't tell" when they disagree and it matters). More than two policies, top-up policies, and the no-claim bonus in "which first". Digital estimates and settlement letters, so Clause can check an insurer's deductions, then prescriptions and photos. Follow-up questions and Hindi. A hosted app with consent and a way to delete data. An agent version, measured against this one. A web review queue.

## Watch-outs

- Write the test cases before you build the thing they test. Cases written after seeing the output tend to match it.
- Do the freeze before the rule writer runs. Writing cases is slower than writing code, so this is the step most likely to slip.
- If Claude with the whole policy wins on dev, keep going. That is a result worth reporting, and the mistakes table will show where it wins.
