# 0007. Insurer documents are downloaded, never committed

Status: accepted, 2026-10-21

## What we decided

`data/manifest.csv` lists each policy document with its web address and a fingerprint (a SHA256 hash). `make fetch` downloads each one, checks the fingerprint, and pulls out the text into folders that git ignores. Rules keep only the short quote they need.

## Why

Policy wordings belong to the insurers. They're published for policyholders, but sharing copies in a public repo isn't ours to do. Insurers also update documents without changing the web address. The fingerprint catches that, so the rules are never silently checked against a different document.

## What it costs us

Anyone who wants the real documents has to run the download. CI can only check quotes against SYNTH-01, the made-up policy that lives in the repo.
