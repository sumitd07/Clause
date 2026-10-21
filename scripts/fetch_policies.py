"""Download the insurer wordings listed in data/manifest.csv, verify them, and extract text.

Raw files go to data/policies/raw/ and text to data/policies/text/. Both folders are
git-ignored (ADR 0007). The manifest is the record: anyone can rebuild the corpus and
check they have the same bytes by the SHA256 column.

    python scripts/fetch_policies.py            # fetch, verify, extract
    python scripts/fetch_policies.py --record   # first fetch: write hashes into the manifest

Text extraction needs the optional extra: pip install -e ".[pdf]"
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifest.csv"
RAW = ROOT / "data" / "policies" / "raw"
TEXT = ROOT / "data" / "policies" / "text"
FIELDS = ["doc_id", "insurer", "product", "uin", "doc_type", "version_date", "url", "sha256", "fetched_on", "notes"]


def read_manifest() -> list[dict]:
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if rows and list(rows[0].keys()) != FIELDS:
        sys.exit(f"manifest columns must be {FIELDS}")
    return [r for r in rows if r["doc_id"] and not r["doc_id"].startswith("#")]


def write_manifest(rows: list[dict]) -> None:
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def fetch(row: dict) -> Path:
    path = RAW / f"{row['doc_id']}.pdf"
    if not path.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(row["url"], headers={"User-Agent": "clause-corpus-fetch/0.1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())
    return path


def extract_text(pdf: Path, out: Path) -> None:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("  skip text: install the pdf extra (pip install -e '.[pdf]')")
        return
    reader = PdfReader(str(pdf))
    pages = [f"[page {i}]\n{(p.extract_text() or '').strip()}" for i, p in enumerate(reader.pages, 1)]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n\n".join(pages), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true", help="write missing hashes and fetch dates into the manifest")
    a = ap.parse_args()
    rows = read_manifest()
    if not rows:
        print("manifest is empty: add one row per document (see docs/DATA.md)")
        return 0
    bad = 0
    for row in rows:
        path = fetch(row)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if not row["sha256"]:
            if a.record:
                row["sha256"], row["fetched_on"] = digest, date.today().isoformat()
                print(f"{row['doc_id']}: recorded {digest[:12]}")
            else:
                print(f"{row['doc_id']}: no hash in manifest, rerun with --record")
        elif row["sha256"] != digest:
            print(f"{row['doc_id']}: HASH MISMATCH. The insurer may have revised the document. See docs/DATA.md.")
            bad += 1
            continue
        else:
            print(f"{row['doc_id']}: ok")
        extract_text(path, TEXT / f"{row['doc_id']}.txt")
    if a.record:
        write_manifest(rows)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
