# 0009. "Claude with search" uses keyword search

Status: accepted, 2026-10-21

## What we decided

One of the systems Clause is compared with is "Claude with search". It finds the 6 sections of the policy that best match the question, using BM25, a standard keyword search that scores sections by the words they share with the question. Claude then answers from those 6 sections, with the same instructions as "Claude with the whole policy". The number 6 is fixed before the first run.

## Why

Policy wordings are numbered and full of exact terms, such as condition names, section numbers and "proportionate". Keyword search handles them well. It needs no extra service and gives the same result every time.

## What it costs us

This is a fair, simple version of search, not the best search possible. The write-up will say so. The number of sections isn't raised after seeing results to help it score better. If "Claude with search" comes close to Clause, a stronger search gets tested before any gap is claimed.
