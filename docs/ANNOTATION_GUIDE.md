# How to write test cases

A test case is one person's question, with their details and the answer worked out by hand. Every case follows this guide, so anyone can check its answer.

## At a glance

1. Pick what the case tests: one trap, or none. Say so in `notes`.
2. Write the case in `data/claims/<set>/Cnnnn.json`.
3. Write down the facts a perfect reader would take from it.
4. Work out the answer by hand, then run `make oracle`.
5. List the clauses that must be named, and the ones that must not.
6. A day later, check it again from the case alone, and log it in `data/expected/LOG.md`.

## Write it the way a person would type it

Write what someone would type in the text box: "My father, 67, needs a hernia operation next month. The hospital quoted ₹42,000." Don't write a doctor's summary, and never use the policy's own words. A case that says "this is excluded under 5.1" tests nothing.

All cases are made up. Never copy a real person's records, even with the names removed.

| Field | What to write |
|---|---|
| `policy.start_date` | Land the hospital stay clearly before or after each waiting period, or exactly on the boundary if that is the point |
| `sum_insured`, `sum_insured_available` | Round numbers. Lower the amount left only when the case is about running out |
| `riders` | Empty, unless the case tests a rider |
| `claimant.dob` | Age counts in whole years on the day of admission. For co-payment cases, keep the birthday clearly away from that day |
| `declared_ped` | Conditions declared when buying: `[]` for none, `null` for "not sure" |
| `narrative` | What the person typed |
| `bill` | Optional amounts as typed: `L1`, `L2` and so on, each with a description and an amount. Empty for a question about cover alone |

## Write down the facts

| Fact | Rule |
|---|---|
| `condition_tags` | The condition treated now, and only if a rule uses that tag. A diabetic admitted for pneumonia is tagged for pneumonia only |
| `procedure_tags` | Procedures in this stay, if a rule uses them |
| `is_accident` | True only when the case says the stay follows an accident or injury |
| `line_categories` | One kind of charge per line, by what the item is, never by whether it is paid |

Kinds of charge: `room`, `icu`, `doctor_fees`, `nursing`, `ot_charges` (operation theatre), `pharmacy`, `consumables` (gloves, syringes, dressings), `implants` (lens, stent, plates), `diagnostics` (tests, scans), `non_medical` (attendant charges, toiletries, registration), and `other` (rarely, with a note).

## Work out the answer by hand

Do it on paper before running anything. The example is C0002: a ₹5,00,000 policy, a deluxe room at ₹7,500 a day for 4 days, and a ₹91,000 bill.

1. **Which rules count.** Checked rules, plus rider rules if the policy has the rider. Strike out any rule a rider switches off. C0002 has no rider, so the room rent waiver is out.
2. **Is it covered at all?** Check every waiting period, exclusion and "needs the insurer's review" rule. "Can't tell" beats "no". If it stops here, the policy pays ₹0. C0002: the policy is nearly 3 years old and nothing is excluded.
3. **The money, in the policy's order:** items not paid, room rent, caps, co-payment, then the sum insured left. Round each line to the paisa. C0002: the room rent limit is 1% of ₹5,00,000, so ₹5,000 a day. The room costs ₹7,500, so room, doctor, nursing and operation theatre charges are paid at two thirds. Medicines and tests are paid in full.
4. **The verdict:** covered in full, partly, not covered, or can't tell (`approved`, `partially_approved`, `rejected`, `route_to_human`).
5. **Write the sums in `notes`** on one line: `Eligible 5,000/day vs actual 7,500/day, ratio 2/3 on room, doctor, nursing and OT (3.2). 20,000 + 8,000 + 4,000 + 13,333.33 + 15,000 + 8,000 = 68,333.33.`

Then run `make oracle`. If it fails on your case, work the answer out again from the case alone. If your number still stands, the code has a bug: write a failing test first. **Never change an answer to match the code or any system without working it out again.**

## Clauses that must and must not be named

- `required_rules`: every rule that changed the answer. It stopped the claim, changed an amount, or switched another rule off.
- `forbidden_rules`: rules a careless reader would apply. For example, the waiver on a policy without the rider, the cosmetic exclusion after an accident, or a waiting period that has ended.

A rule that changed nothing goes in neither list.

## Traps

One trap per case. With two, you can't tell which one a system fell for.

| Trap (`distractor_type`) | How to build it | Dev example |
|---|---|---|
| Look-alike rule (`near_distractor`) | Two rules mention the same condition; make one apply, by date or amount | C0004: the cataract cap applies; the wait has ended |
| Hidden trigger (`conditional`) | Mention the deciding detail in passing | C0002: the deluxe room |
| Misleading word (`decoy`) | A word that sounds excluded, where the rule doesn't apply | C0006: reconstruction after an accident |
| Switched off (`override`) | Add the rider that turns a rule off | C0003: the room rent waiver |
| Can't tell (`route`) | Leave out a fact a rule needs | C0007: nobody knows if diabetes was declared |

A can't-tell case names the missing fact in `notes`. If one more detail already in the case would settle it, it is not a can't-tell case.

## Other cases

- **Two-policy cases.** One patient on two policies, often a company policy and their own. Work out what each pays alone, then both orders, and what the person pays each way. Follow the rule for claiming from two policies, as checked against IRDAI's current rules in week 1.
- **Made-up schedules.** Use the layout real insurers use: product and UIN, start date, sum insured, riders, everyone covered with date of birth and relationship, and declared conditions. Record each field's right value. Invent every name and date.
- **Question-type checks.** 10 questions about a term ("What does proportionate deduction mean?"), each with the rule it should explain. And 5 off-topic questions ("Which policy should I buy?"), where the right answer is "Clause can't help with this one".

## Writing rules from a policy by hand

Before the rule writer exists, write down every rule in 2 of the 5 policies by hand. The rule writer is scored against this list, so the list must come first.

- One rule per effect. A cataract cap and a cataract wait are two rules.
- Quote the shortest span of the policy's words that carries the rule, exactly. `make check-rules` checks the quote.
- Use the section number as printed. Periods are counted in days: if the policy gives only months, use 365 days per 12 months, and say so in the review comment.
- Write the `plain` line: the rule in everyday words.
- If the code can't apply a rule yet, still write it down, as "needs the insurer's review", with a comment.

## Watch-outs

- Writing an answer after seeing a system's answer makes it agree with the system. Write and check answers first.
- A case that echoes the policy's words makes search look better than it is. Write like a worried family member, not like the insurer.
- Add a tag only if a rule uses it. Unused tags give the readers more ways to be wrong.
