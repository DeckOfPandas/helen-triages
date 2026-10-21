"""`_data/food/sources.yml`: Helen's rulings about a whole book or magazine.

The file is read three ways: printed into INGEST_ONE_RECIPE.md by
`build_ingest_vocab.py`, used by `ingest_inbox.py` to fold the hand-back
bullets an entry settles, and read here for its shape. `_food_sources` is the
one loader all three import, so a key the code reads cannot drift from the key
this file checks.
"""
from __future__ import annotations

import datetime
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.shared

SOURCES = Path(__file__).resolve().parent.parent / "_data" / "food" / "sources.yml"

KEYS = {"name", "match", "oven", "units", "rulings"}
RULING_KEYS = {"rule", "helen", "date"}
# The values code acts on. `conventional`: one printed figure, fan is 20
# lower. `metric` / `imperial`: which figure of a printed pair is kept.
OVEN = {"conventional"}
UNITS = {"metric", "imperial"}


def _food_sources() -> list:
    return yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or []


def source_for(citation: str):
    """The entry whose `match` the citation contains, or None."""
    for entry in _food_sources():
        if entry["match"] in (citation or ""):
            return entry
    return None


def test_every_entry_has_the_declared_shape():
    entries = _food_sources()
    assert entries, "sources.yml is empty, so every check below checks nothing"
    for entry in entries:
        assert set(entry) <= KEYS and {"name", "match", "rulings"} <= set(entry), (
            f"{entry.get('name')!r}: keys {sorted(entry)}; allowed {sorted(KEYS)}")
        assert entry.get("oven", "conventional") in OVEN, entry["name"]
        assert entry.get("units", "metric") in UNITS, entry["name"]
        assert entry["rulings"], f"{entry['name']!r} has no rulings"
        for ruling in entry["rulings"]:
            assert set(ruling) <= RULING_KEYS and ruling.get("rule"), (
                f"{entry['name']!r}: a ruling is {{rule, helen?, date?}}: {ruling!r}")
            if "date" in ruling:
                assert isinstance(ruling["date"], datetime.date), ruling


def test_no_citation_matches_two_entries():
    """`source_for` takes the first match, so an overlap would hide a ruling."""
    entries = _food_sources()
    for a in entries:
        for b in entries:
            if a is not b:
                assert a["match"] not in b["match"], (a["name"], b["name"])
