# 0014. Ask first, then fill in only what's needed

Status: accepted, 2026-10-21

## What we decided

You type your question first. Clause then asks only for the details that question needs. "Is cataract surgery covered?" needs the policy, its start date and the patient's age, not the sum insured left. Anything not given is asked for, or stated as an assumption ("Assuming no claims yet this year").

The quick way to give those details is to upload your policy schedule. Clause shows what it read, and you confirm or fix it. Typing still works. Your policies and the people they cover are saved in a "My policies" file on your own computer, which you can delete at any time.

## Why

Ten fields before you can ask anything is enough to make most people give up. The schedule already holds almost everything an answer needs.

## What it costs us

Clause has to know which details each rule depends on. Schedule reading can go wrong, so Clause shows what it read, and its accuracy is measured on 10 made-up schedules.
