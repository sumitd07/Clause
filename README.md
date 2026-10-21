# Clause

Ask a question about your health insurance policy and get a clear answer: is it covered, from when, what limits apply, and what you will pay. Every line points to the part of your policy it comes from, quoted word for word.

**Work in progress.** The code that works out answers, and the answer form, are built and tested. Real policies and the AI parts come next, over four weeks ([build plan](docs/BUILD_PLAN.md)).

[![ci](https://github.com/sumitd07/clause/actions/workflows/ci.yml/badge.svg)](https://github.com/sumitd07/clause/actions/workflows/ci.yml)

## The problem

Ask a chatbot "Is my mother's cataract surgery covered?" and it will probably say "Yes."

For many policies the true answer is longer: "Yes, but only after the policy is 2 years old, only up to ₹40,000, and you get less back if you pick an expensive room." Those three conditions sit on three different pages of the policy. Miss one and the family gets a surprise bill at discharge.

## What Clause does differently

- It writes down every rule in the policy once, ahead of time, and a person checks the list.
- For each question, it goes through every rule on that list.
- Ordinary code works out the money. The AI never does the maths.
- Every answer shows the policy's own words behind it.
- When it can't tell, it says what is missing and asks the one question that would settle it.

Whether this beats a chatbot is tested, not assumed. Clause is compared with Claude given the whole policy, on a fixed set of hand-checked questions ([how Clause is tested](docs/EVAL.md)). If Claude does as well, that is the result, and it will be reported.

## What an answer looks like

Every answer about a treatment has the same parts, in the same order. This is real output from `make answer CLAIM=C0004`, on SYNTH-01, a made-up policy used for testing (two parts left out to keep it short):

```
Is it covered?
  Partly. The policy pays ₹40,000 of ₹57,000.
  Not excluded. Checked against: cosmetic surgery exclusion (section 5.1).

From when?
  Covered from 1 Jul 2023, when the 30-day waiting period (section 4.1) ended.
  Covered from 31 May 2025, when the 2-year waiting period for cataract (section 4.2) ended.
  No pre-existing disease wait: no conditions were declared when buying (section 4.3).

Limits
  Room rent: up to ₹5,000 a day (1% of your sum insured, section 3.2). Your room is ₹3,000 a day, within the limit.
  Cap: cataract is paid up to ₹40,000 (section 3.5).
  Not paid: non-medical items (section 5.2).
  No co-payment: it starts at age 61, and the patient is 58 (section 6.1).

What you pay
  The policy pays ₹40,000. You pay ₹17,000.
  ₹17,000: the cap for this treatment, section 3.5.

Where this comes from
  Section 3.5, Cataract sub-limit: "Claims for cataract treatment are payable up to Rs 40,000 per hospitalisation."
    In plain words: Cataract treatment is paid up to ₹40,000 per hospital stay, whatever the hospital charges.

Note
  Rules checked by a person. This is not the insurer's decision.
```

The parts left out are "What Clause understood", which shows what it read so you can correct it, and a line-by-line table of the bill. No AI writes any of this. Code fills in the form from the rules ([why](docs/decisions/0011-answers-are-a-fixed-form.md)).

## How it works

```
Once per policy:  policy wording ──► AI writes down the rules ──► a person checks them

Each question:    your question ──► AI works out what it is about ──► code applies every rule ──► the answer
                  + your details     (which condition, accident or not)
```

The AI is used in two places only: writing down the rules, and understanding the question. For the second, Clause also tries Jev, a small model built for yes/no checks, and plain keyword matching, to see whether a big model is needed at all ([why](docs/decisions/0012-jev-for-yes-no-checks.md)).

## What the first version covers

- **Questions:** about a treatment ("Is cataract surgery covered?"), about a term in your policy ("What does proportionate deduction mean for us?"), and, if you have two policies, which to claim from first.
- **Policies:** 5 real policies from 3 insurers. You can also upload your own policy wording. Its answers say the rules were not checked by a person.
- **Your details:** upload your policy schedule, the PDF your insurer emails you, and Clause fills in the details for you to confirm. It only asks for what your question needs.
- **Not yet:** prescriptions, bills or other medical papers, photos, follow-up questions, languages other than English. The full list, with reasons, is in the [product plan](docs/PRODUCT.md).

## Try it

Needs Python 3.11 or later.

```bash
python -m venv .venv && source .venv/bin/activate
make install                 # installs Clause and its test tools
make test                    # 58 tests, no internet or API key needed
make answer CLAIM=C0002      # the answer when the patient took a costlier room
make oracle                  # checks the code against the hand-worked answers: must be 100%
```

With an Anthropic API key, you can run the AI version on the practice questions: `cp .env.example .env`, add the key, then `make eval ARM=clause`.

## Results

Not run yet. The test questions are fixed before any system sees them. This table fills in at the end of week 4.

| System | Fully right | Confident mistakes | Cost per answer |
|---|---|---|---|
| Claude with the whole policy | | | |
| Claude with search | | | |
| Clause | | | |
| Clause, rules not checked by a person | | | |

"Fully right" means the verdict, the amount (to the rupee) and the clauses named are all correct. "Confident mistakes" are wrong answers given without a "can't tell". These are the ones people act on.

## What's where

| Folder | What it holds |
|---|---|
| `src/clause/` | The code. `engine.py` works out answers, `answer.py` fills in the form, `scoring.py` grades the tests |
| `data/` | SYNTH-01 and its rules, the practice questions, and the hand-worked answers |
| `docs/` | [Product plan](docs/PRODUCT.md), [how it works](docs/ARCHITECTURE.md), [how it's tested](docs/EVAL.md), [build plan](docs/BUILD_PLAN.md), [decisions](docs/decisions/) |

## Limits

- Clause is not the insurer's decision, and not legal or financial advice.
- SYNTH-01 is made up for testing. Real policies come in week 1.
- All test questions are made up. No real patient data is used.

## License

MIT for the code. Policy wordings belong to their insurers and are not copied into this repository.
