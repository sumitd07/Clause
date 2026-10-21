# Where the data comes from

## At a glance

| | |
|---|---|
| Policies | SYNTH-01, a made-up policy, is in the repo now. Five real wordings from three insurers come in week 1. They are downloaded from a list, never committed |
| Test cases and schedules | All made up and worked out by hand. No real patient data, ever |
| Company policies | Built from the terms the person types, because their wordings are rarely public |
| In git | The list of documents with a fingerprint of each, the rules with short quotes, the cases and their answers |
| Not in git | Insurer PDFs and the text taken from them ([decision 0007](decisions/0007-insurer-documents-are-fetched.md)) |
| Before writing any IRDAI number into a rule | Check it against IRDAI's current master circular on health insurance |

## Picking the 5 policies

Rules for choosing, set before looking at any document:

1. Both the policy wording and its Customer Information Sheet are published. The Customer Information Sheet lists the key terms in a fixed table, which makes it a free answer key for the rule writer.
2. Three insurers sell the same standard product, so the same clause appears in three wordings with small differences.
3. One insurer has two products that differ by one small term, such as a waiting period. Look-alike-rule cases come from that pair.
4. The wordings use numbered sections, so a clause can be pointed to.
5. The PDF has real text in it, not a scanned image.

A good starting set:

| # | Product | Why |
|---|---|---|
| 1 to 3 | Arogya Sanjeevani from three insurers | IRDAI's standard product, which every health insurer must offer. Same layout, so the differences are easy to see |
| 4 | One insurer's main product | A fuller wording: riders, more caps, more exclusions |
| 5 | A second main product, or a version of 4 that differs by one term | The look-alike pair |

Plus IRDAI's standard definitions and standard exclusions, which every wording includes.

To find them, open the insurer's website and look for its downloads or policy wordings page. Products are usually listed by name and UIN, the product's IRDAI number, which is printed on the wording. IRDAI's website lists approved health products, so you can confirm a UIN and its latest version.

## The document list

`data/manifest.csv` has one row per document:

| Column | Example | Notes |
|---|---|---|
| `doc_id` | `INS1-AS-WORDING` | Short and stable. Rules use it to say where they come from |
| `insurer` | The insurer's name | |
| `product` | Arogya Sanjeevani Policy | |
| `uin` | As printed on the wording | Also how an uploaded wording is matched to a supported policy |
| `doc_type` | `wording`, `cis`, `endorsement` or `irdai` | |
| `version_date` | `2024-06-01` | The date on the document, if it has one |
| `url` | The insurer's direct PDF link | |
| `sha256` | Filled in on the first download | A fingerprint of the file's exact bytes |
| `fetched_on` | Filled in on the first download | |
| `notes` | Anything odd, such as a two-column layout | |

```bash
pip install -e ".[pdf]"                    # adds pypdf, to take the text out of each PDF
python scripts/fetch_policies.py --record  # first time: download, fingerprint, write the fingerprints back
python scripts/fetch_policies.py           # later: check every file still matches its fingerprint
```

PDFs land in `data/policies/raw/` and their text in `data/policies/text/`. Git ignores both. Anyone can rebuild the same set from the list and confirm they have the same files.

**When a fingerprint doesn't match,** the insurer has published a new version. Don't overwrite the fingerprint. Add the new version as a new row with a new `doc_id`, and review every rule that quotes the old one. A changed document means changed rules.

## From PDF to sections

Clause finds sections by their headings, one per line, like `4.2 Specific waiting period`. Real PDFs need a clean-up first: two-column pages, page headers, and page numbers in the middle of sentences. Do the clean-up with a script, not by hand, so it can be rerun when a document changes. Record the page number of every real rule, because the person checking the rules needs it.

## IRDAI checks in week 1

IRDAI brought its health insurance rules together in one master circular in 2024. Several limits changed from what older wordings and most articles online say. Before writing any of these into a rule, check IRDAI's current text, and put the circular's reference in the rule's review comment:

| Topic | What to check |
|---|---|
| Pre-existing disease waiting period | The current longest wait allowed |
| Waiting periods for listed conditions | The current longest wait allowed |
| Moratorium | After how many years of continuous cover a claim can no longer be questioned, and on what grounds |
| Room rent cuts | Which charges may not be cut in proportion (medicines, implants, consumables and tests in standard wordings), and the rule for ICU |
| Items not paid | The current list of items that are not paid, or are counted inside other charges |
| Standard exclusions and definitions | The standard wording of exclusions, and of accident, hospital, pre-existing disease and day care |
| Claiming from two policies | Whether you can choose which policy to claim from first, and how the second policy pays what is still unpaid. "Which policy first" is built on this, so it is checked before that code is written |

An older wording that differs from the current circular is still what that policy says. Write the rule from the wording. Add a case that tests the difference only if the write-up will discuss it.

## Made-up data

SYNTH-01 (`data/policies/SYNTH-01.md`) is a made-up policy for tests and dev cases. Its numbers are picked to make the sums easy to check, not to match any regulation. Its 8 dev cases cover every kind of trap, and CI checks them on every push.

Cases on real policies follow [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md). Names, dates of birth, what the person typed, and the 10 schedules are all invented. If an AI helps draft the wording of cases for variety, the answers are still worked out by hand. Each draft is also checked, so no policy wording slips into what the person "typed".

**Company policies.** Group policies from employers rarely publish their wordings. So Clause builds their rules from the key terms the person types, from the HR benefits sheet: sum insured, room rent limit, co-payment for parents, caps, and which waiting periods are waived. Answers based on these say "Rules from the terms you typed, not from the policy wording".

## Privacy

v1 runs on your computer. The only thing it keeps is the "My policies" file, on your computer. What you type goes only to the AI providers: Anthropic, and TypeSafe for the Jev runs. All test cases are made up, and no real patient data is used. Health data is sensitive under India's Digital Personal Data Protection Act 2023, so a hosted version would need consent and a way to delete data.

## Copyright

Insurers publish their wordings for policyholders and buyers. Clause does not share them. Rules carry only the shortest quote needed to point to the clause. The extracted text stays on your computer.

## Watch-outs

- Some insurer PDFs are scanned images, with no text to take out. Pick a different product rather than adding text recognition to v1.
- Insurers sometimes reuse the same link for a new version of a PDF. The fingerprint check is the only thing that notices.
- A Customer Information Sheet and its wording can disagree. The wording wins. Note the disagreement, because it makes a good test case.
