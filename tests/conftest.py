from pathlib import Path

import pytest

from clause.io import load_rules

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


@pytest.fixture
def ruleset():
    return load_rules(DATA / "rules" / "SYNTH-01.rules.json")
