# Product plan

## At a glance

| | |
|---|---|
| What | Ask a question about your health insurance. Get a clear answer in a fixed form, with the policy's own words behind every line |
| For | People with an Indian health insurance policy, and the family member who handles the hospital paperwork |
| Why | A policy's rules work together. A chatbot often misses one of them, and that is usually the one that costs money |
| How | The rules are written down once and checked by a person. Code applies all of them to each question and fills in the answer |
| First version | Questions about a treatment, a term in the policy, or which of two policies to claim from first. Runs on your computer |
| Status | Work in progress. The engine and the answer form are built; the rest takes four weeks ([build plan](BUILD_PLAN.md)) |

## The problem

Someone in the family needs hospital care. The questions come up fast:

- "Is my mother's cataract surgery covered?"
- "The hospital wants ₹7,500 a day for a deluxe room. What will we pay?"
- "We have my company's policy and our own. Which one do we claim from first?"
- "The policy says 'proportionate deduction'. What does that mean for us?"

The answers are in the policy wording, which runs to 30 to 80 pages. An answer rarely comes from one clause. It usually takes a chain like this:

1. Has the policy been running long enough? Most policies make you wait 30 days for anything, and 2 to 3 years for some conditions.
2. Is this treatment excluded?
3. Is there a cap for it?
4. Is the room above the limit? Then the doctor's, nursing and operation theatre charges are cut too, in the same proportion. Most people find this out only from the settlement letter.
5. Does the patient pay a share themselves (a co-payment)? Some policies charge one from age 60 or 61, and many company policies charge 10% to 20% for parents.

## Why not just ask a chatbot?

Give a chatbot the policy and ask "Is my mother's cataract surgery covered?" It will probably say "Yes."

For many policies the true answer is: "Yes, but only after the policy is 2 years old, only up to ₹40,000, and you get less back if you pick an expensive room." Those three conditions are on three different pages.

Clause is built so it doesn't miss them:

- It writes down every rule in the policy once, ahead of time, and a person checks the list.
- For each question, it goes through every rule on that list.
- Ordinary code works out the money. The AI never does the maths.
- It shows the policy's own words behind each line.
- The same question always gets the same answer.

We don't assume this beats a chatbot. We test it on a fixed set of hand-checked questions ([how Clause is tested](EVAL.md)). If the chatbot does as well, that is the result.

## How someone uses it

1. **Ask first.** Type the question. Nothing else is needed to start.
2. **Clause asks only what that question needs.** For "Is cataract surgery covered?" it needs the policy, its start date and the patient's age. It doesn't need the sum insured left, so it doesn't ask. If it assumes something, it says so ("Assuming no claims yet this year").
3. **Upload your policy schedule to fill in the details.** That's the PDF the insurer emails when you buy or renew. It lists the product, start date, sum insured, riders, everyone covered with their date of birth, and the conditions declared. Clause shows what it read, and you confirm or fix it. Typing stays as a fallback. For a company policy, use the e-card and the HR benefits sheet, or type the terms.
4. **It remembers.** Your policies and the people they cover are saved in a file on your computer ("My policies"), so the next question is just a question.

## Three kinds of question

| Kind | Example | What the answer gives |
|---|---|---|
| A treatment | "My mother needs cataract surgery. Is it covered?" | Covered or not, from when, the limits, and, if you give the hospital's amounts, what the policy pays and what you pay, line by line |
| A term in the policy | "What does proportionate deduction mean for us?" | What the policy says, in plain words, and what it means with your numbers ("Your room rent limit is ₹5,000 a day") |
| Which policy first | "Company policy or our own, which first?" | What each policy pays on its own, then both orders side by side, and what you pay in each |

Anything else, such as which policy to buy, gets a polite "Clause can't help with this one", with a line on what it can do.

## What an answer looks like

A question about a treatment always gets these parts, in this order:

1. **What Clause understood.** What you typed, the details it used, and anything it assumed. You correct it if it's wrong.
2. **Is it covered?** Yes, partly, no, or can't tell. It also lists which exclusions it checked.
3. **From when?** Each waiting period: when it ended, or when it will end.
4. **Limits.** Room rent limit, caps, co-payment, items not paid.
5. **What you pay.** What the policy pays, what you pay, and each cut with its section. With no amounts given, it says how to get this.
6. **Line by line.** Only when you gave the amounts.
7. **What would settle it.** Only when Clause can't tell. It ends with a question, for example: "Was diabetes declared when the policy was bought? Your policy schedule lists it."
8. **Where this comes from.** Each clause that changed the answer, quoted word for word, with a line in plain words.
9. **Note.** "Rules checked by a person" (or "not checked"), and "This is not the insurer's decision."

No AI writes any of it. Code fills in the form from the rules. The plain-words line for each rule is written once, when the rule is made, and checked by a person with the rule ([why](decisions/0011-answers-are-a-fixed-form.md)). See a real example in the [README](../README.md).

## When Clause says "can't tell"

These rules were written before any test, so they can't be bent to fit the results.

Clause says "can't tell" only when:

1. The policy says the insurer must review this kind of case first.
2. The answer depends on a fact nobody has given. For example, whether a condition was declared when the policy was bought, while its waiting period is still running.
3. Clause couldn't make sense of what was typed.
4. The question needs a rule Clause can't apply yet.

It never says "can't tell" because an amount is large, or to sound careful. It always says what is missing and asks the question that would settle it.

| Mistake | What it costs the family |
|---|---|
| Says the policy pays more than it does | A surprise bill at discharge |
| Says the policy pays less, or agrees with a wrong cut | They pay money the policy owes them |
| Says "can't tell" when it could have answered | A phone call to the insurer for nothing |
| Answers when it should have said "can't tell" | A guess dressed up as an answer |

The test counts each of these separately.

## First version: what's in and what's out

**In:**

- **Policies.** 5 real policy wordings from 3 insurers, plus SYNTH-01, a made-up policy for testing.
- **Your own policy wording**, uploaded as a PDF with real text (not a scan). If Clause already knows that product, it uses the checked rules. If not, it writes the rules on the spot and every answer says "Rules read automatically, not checked by a person". The test measures how good those answers are.
- **Company (group) policies.** Their wordings are rarely public, so you type the key terms from your HR benefits sheet. Answers say they come from the terms you typed.
- **Up to two policies per patient**, and which to claim from first. Clause assumes the second policy pays its own share of what is still unpaid. This gets checked against IRDAI's current rules before it is built.
- **The patient.** Who they are to the policyholder (self, spouse, child, parent, parent-in-law) and their date of birth, because co-payments often depend on both.
- **The policy schedule PDF**, to fill in your details.
- **Typed questions**, in English, with the hospital's amounts typed in if you have them.
- **On your computer:** a command line, and a simple page with the question box.

**Out, and why:**

- **Prescriptions, discharge summaries, estimates, bills, settlement letters, and photos or scans of any paper.** You type the facts instead. Reading these well is a hard problem of its own (handwriting, scans, tables), and they hold personal health data ([why](decisions/0013-v1-reads-no-medical-papers.md)). The schedule is the exception because it's a digital PDF with fixed fields, and every answer needs its details.
- **Checking an insurer's cuts on a settlement letter.** That needs the letter. It's the first thing for the next version.
- **More than two policies; top-up policies.** Top-ups only pay above a set amount, which needs different maths.
- **Co-payment by city or for hospitals outside the insurer's network.**
- **The no-claim bonus** when choosing which policy to claim from. The answer says it isn't counted yet.
- **Follow-up questions, other languages, and help buying or comparing policies.**
- **An online app or accounts.** Nothing is stored anywhere but your own computer.
- **Rules the engine can't apply yet:** ICU limits, refilling the sum insured, package rates, and several claims in one year.

## How we'll know it works

| Measure | Target |
|---|---|
| Questions answered fully right (verdict, amount to the rupee, and clauses) | More than Claude with the whole policy, by more than the margin of error |
| Confident mistakes | 0. Each one gets a written cause |
| "Can't tell" when it should, and only then | Both reported |
| Said the policy pays more, or less, than it does | Count and rupees, reported |
| Uploaded policies (rules not checked by a person) | Reported, so users know how far to trust them |
| Reading the schedule correctly | Accuracy per field, reported |
| Jev against Claude for understanding the question | Same accuracy for less money is the hope; reported either way |
| Cost and time per answer | Reported |

## Privacy

The first version runs on your computer. The only thing it keeps is the "My policies" file, which you can delete. What you type goes only to the AI providers that read it: Anthropic, and TypeSafe for the Jev test. All test questions are made up, with no real patient data. Health data is sensitive under India's Digital Personal Data Protection Act 2023, so an online version would need consent and a way to delete data.

## Risks

| Risk | What we do about it |
|---|---|
| People act on the answer | Every answer shows what Clause understood and the clauses it used, and says it is not the insurer's decision |
| Clause misunderstands the question | It shows what it understood, so the person can correct it |
| A rule is written down wrong | Code checks every quote word for word against the policy; a person checks each rule; IRDAI numbers are checked against the current rules ([DATA.md](DATA.md)) |
| A hand-worked answer has a sum wrong | A second check of every answer, done without looking at any system's output, plus an automatic check that the code and the answers agree |
| The test questions leak into development | They are frozen before any system sees them, and never used in a prompt |
| The test questions are too easy | 40% of them have a deliberate trap |

## Watch-outs

- People type what they remember, not what the form said. "Not sure" must stay an easy, honest answer, and it leads to "can't tell" only where it matters.
- Answers on an uploaded policy rest on rules no person checked. The label must never be hidden.
- "Which policy first" rests on how the second insurer pays the balance. Check IRDAI's current rules before building it.
- Policies change. A changed policy file means its rules must be checked again before anyone relies on them.
