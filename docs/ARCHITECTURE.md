# How Clause works

## At a glance

Someone asks: "My mother needs cataract surgery. Is it covered?" Clause handles it in three steps:

1. **Reading.** It works out what the question is about: cataract, not after an accident, and these amounts.
2. **Deciding.** Plain code goes through every rule written down from the policy and works out the answer to the rupee.
3. **Answering.** Code fills in a fixed form: Is it covered? From when? What limits apply? What will you pay? Each line quotes the clause behind it.

AI reads the question, and writes the rules from each policy once, ahead of time. It never decides an amount or writes the answer. The steps never change, so when quality changes, the cause can be found.

```
Once per policy
  policy wording ──► rule writer (AI) ──► a person checks ──► checked rules

For each question
  question ──► details ──► reading ──► engine (code) ──► answer form (code)
               (schedule    (AI or      covered? from      covered? from when?
                or typed)    keywords)  when? how much?    limits? what you pay?
```

Everything is JSON files in git, with no database ([0005](decisions/0005-local-first-files-in-git.md)). Every run records the rules, cases, code version and model that produced it ([0010](decisions/0010-every-run-is-stamped.md)).

## The parts

| File | What it does | Status |
|---|---|---|
| `engine.py` | Works out the decision. No AI, no randomness | Done |
| `answer.py` | Fills in the answer form | Done |
| `facts.py` | Reading, done by Claude | Done, not tuned |
| `llm.py` | The only code that calls Claude | Done |
| `arms.py` | The systems compared in the test ([EVAL.md](EVAL.md)) | Claude with the whole policy and Clause done. Search in week 3. Jev and plain code in week 4 |
| `compiler.py` | Checks that rule quotes are word for word. The rule writer | Checks done. Writer in week 2 |
| `scoring.py`, `runlog.py` | Grading by code, run records | Done |
| `models.py`, `io.py`, `cli.py` | Data types, files, commands | Done |
| Review queue, upload path | Checking rules; uploaded policies | Week 2 |
| Question first, schedule, two policies | See below | Week 3 |
| Local page | A text box on your own computer | Week 4 |

## A rule

```json
{
  "id": "SYN-RR",
  "type": "room_rent_limit",
  "title": "Room rent limit with proportionate deduction",
  "plain": "Room rent is paid up to 1% of your sum insured per day. If you take a costlier room, ...",
  "status": "approved",
  "citation": {"doc": "SYNTH-01", "section": "3.2", "quote": "Room rent is payable up to 1% of the sum insured per day. ..."},
  "params": {"limit_type": "percent_si", "value": 1, "proportionate_deduction": true,
             "associated_categories": ["doctor_fees", "nursing", "ot_charges"]}
}
```

- **`status`** is `candidate` (written, not checked) or `approved` (a person checked it). Only approved rules count, except for uploads and the "rules not checked" test run.
- **`quote`** must appear word for word in the cited section, or `make check-rules` fails.
- **`plain`** is the rule in everyday words. A person checks it with the rest of the rule, and the answer shows it.
- **`requires_rider`** and **`edges`** handle riders. An `overrides` edge switches another rule off, as the room rent waiver rider does to the room rent limit.

There are eight rule types: waiting periods, exclusions, "needs review", items not paid, room rent limits, caps, co-payment, and riders. Formats are in `schemas/rules.schema.json`.

## How the engine decides

**1. Which rules count.** A rule counts if it is approved and any rider it needs is on the policy. An `overrides` edge removes the rule it points to.

**2. Is it covered?** Waiting periods, exclusions and "needs review" rules are checked first.

- A waiting period stops cover if the stay falls inside it. Days are counted from the policy start, so day 30 is outside a 30-day wait. A wait can be waived after an accident, as SYNTH-01's first 30 days are.
- An exclusion stops cover if the condition is on its list.
- "Needs review" gives "can't tell" (`route_to_human` in code). So does the pre-existing disease wait when nobody knows whether the condition was declared.
- If any rule says "can't tell", the answer is "can't tell", even if another rule says no.

**3. How much is paid.** The money steps run in the order the policy sets: items not paid, room rent, caps, co-payment, then the sum insured left. Every cut is recorded with its rule. Order matters: in one test, cap then co-payment pays ₹32,000, while co-payment then cap pays ₹40,000.

Two dev cases:

- **C0002.** The room costs ₹7,500 a day against a limit of ₹5,000 (1% of ₹5,00,000). Room, doctor, nursing and operation theatre charges are paid at 66.7%, and medicines and tests in full. The policy pays ₹68,333.33 of ₹91,000.
- **C0004.** Cataract, with the policy 1,202 days old. The 2-year cataract wait has passed, but cataract is capped at ₹40,000. The policy pays ₹40,000 of ₹57,000.

The answer quotes every rule that stopped cover, cut an amount or switched another rule off, and the test checks them.

## Reading the question

Reading turns what the person typed into three kinds of fact: the condition or treatment (from the names the rules use, such as `cataract`), whether the stay followed an accident, and what kind of charge each bill line is ("intraocular lens" is an implant).

Claude reads today, answering only with names from a fixed list. In week 4, two other readers are compared with it on the same cases:

- **Plain code**, matching keywords.
- **Jev**, a model from TypeSafe that answers yes/no and pick-one questions with a probability. It gets narrow questions, all in one request: "Is the condition being treated cataract?" "Did this stay follow an accident?" When Jev is unsure, Clause works the answer out both ways. If both agree, the doubt doesn't matter. If not, Claude reads the case ([0012](decisions/0012-jev-for-yes-no-checks.md)). Jev is also tried as a filter that skips policy sections with no rules before the rule writer runs.

## The answer form

A treatment question always gets these sections, in this order: what Clause understood, is it covered, from when, limits, what you pay, line by line (if amounts were given), what would settle it (only for "can't tell", ending in a question), where this comes from, and a note. The note says "Rules checked by a person" or "Rules read automatically, not checked by a person", and "This is not the insurer's decision".

A question about a term gets: what the policy says, in plain words, and what it means for you, worked out with your numbers.

No model writes any of it ([0011](decisions/0011-answers-are-a-fixed-form.md)). Try `make answer CLAIM=C0004`.

## Coming next

- **Uploaded policy (week 2).** A UIN that matches a supported policy uses its checked rules. Otherwise the rule writer runs on the spot, and the answer says the rules weren't checked. The "rules not checked" test run measures these answers ([0003](decisions/0003-human-approval-before-rules-go-live.md)).
- **Question first (week 3).** Clause asks only for what the rules that could apply need, such as the start date for a waiting period, and states other assumptions ([0014](decisions/0014-question-first.md)). The policy schedule PDF fills these in: Clause shows what it read, the person confirms, and the details are saved in a "My policies" file on their computer.
- **Company policy (week 3).** The person types the key terms from the HR benefits sheet. Answers say the rules came from those terms.
- **Which policy first (week 3).** Each policy on its own, then both orders, with what you pay each way. The second policy is assumed to pay its share of what is still unpaid, which is checked against IRDAI's rules in week 1. The no-claim bonus and network hospitals aren't weighed yet, and the answer says so.

## Calling Claude

`llm.py` is the only file that calls Claude ([0008](decisions/0008-one-model-wrapper.md)). The model and effort come from `CLAUSE_MODEL` (default `claude-opus-5-5`) and `CLAUSE_EFFORT` (default `medium`). Replies must match a JSON format and are saved on disk, so a rerun is free and identical. A refused request may go to a fallback model; if still refused, the answer is "can't tell". Every call records the model that answered, tokens, time and why it stopped.

## Answers and run errors

A network problem must never look like a wrong answer. "Can't tell" from a rule, or from reading that can't place a bill line, is an answer and is scored. A reply cut off, invalid JSON or an API failure is a run error: it goes in `errors.jsonl`, and `clause score` refuses the incomplete run. A run with calls answered by a fallback model is flagged as not comparable.

## Security

Policy text is untrusted. It reaches the engine only as an approved rule whose quote was checked word for word. Reading can only return names from a fixed list. API keys come from the environment, never from a file in the repo.

## What the engine covers

| Covered | Not yet |
|---|---|
| Waiting periods, waived after an accident | Moratorium after years of cover |
| Exclusions, "needs review", items not paid | IRDAI's item-by-item list of items not paid |
| Room rent limit, with cuts in proportion | ICU and room type limits |
| Caps per condition | "Lower of" caps, per-day caps |
| Co-payment from an age | Co-payment for parents (week 1), by city, outside the network |
| Riders that switch a rule off; sum insured left | Riders that change a number; restoring the sum insured; several claims a year |

To add a rule type: add it to the schema, write the engine code, add a hand-worked test and a dev case, and check `make oracle` still scores 100%.

## Watch-outs

- The engine trusts the facts. If reading mistakes another illness for the one being treated, the wrong waiting period applies. That is why reading is scored on its own.
- `narrows` and `activates` edges are accepted but ignored. Build them when a real policy needs one.
- Room rent uses one daily rate per stay. A stay that changes rooms needs a rate per day.
