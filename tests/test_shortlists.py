"""Regression guards for named shortlists (#1521). MANUAL §8.9.

The behaviour is tested in tests/js/shortlists-store.test.js; these hold the
source to the rules a behaviour test cannot see.
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.shared

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "assets/js/shortlists-store.js"
SOURCES = [p for d in ("assets/js", "_includes", "_layouts", "food", "cocktails")
           for p in (ROOT / d).rglob("*") if p.suffix in (".js", ".html")]

FOOD_OLD_KEYS = [
    "htf-shortlist-food-v1", "htf-shortlist-glasses-food-v1",
    "htf-shortlist-portions-food-v1", "htf-shortlist-portions-food-v2",
    "htf-shortlist-batches-food-v1", "htf-shortlist-ticked-food-v1",
    "htf-shortlists-food-v1",
]


def test_the_storage_key_is_named_in_one_place():
    assert SOURCES, "found no source files to scan: the paths above are wrong"
    naming = sorted(str(p.relative_to(ROOT)) for p in SOURCES
                    if "'htf-lists-'" in p.read_text(encoding="utf-8"))
    assert naming == ["assets/js/shortlists-store.js"], (
        "The shortlists key must be built in shortlists-store.js and nowhere "
        f"else, so there is one place to change it; found it in {naming}")


def test_nothing_calls_localstorage_clear():
    offenders = sorted(str(p.relative_to(ROOT)) for p in SOURCES
                       if re.search(r"localStorage\s*\.\s*clear\s*\(", p.read_text(encoding="utf-8")))
    assert not offenders, (
        "localStorage.clear() empties every deckofpandas.github.io site on the "
        f"origin, Is It Rhubarb Yet included: {offenders}")


def test_foods_old_keys_are_removed_by_name_and_no_cocktail_key_is():
    text = STORE.read_text(encoding="utf-8")
    block = re.search(r"var OLD_KEYS = \{(.*?)\};", text, re.S)
    assert block, "shortlists-store.js has no OLD_KEYS map: the old keys are not being removed"
    named = re.findall(r"'([^']+)'", block.group(1))
    missing = [k for k in FOOD_OLD_KEYS if k not in named]
    assert not missing, f"food's old keys must each be removed by name; missing {missing}"
    cocktail = [k for k in named if "cocktail" in k]
    assert not cocktail, f"cocktails' shortlist is still live and must not be removed: {cocktail}"
    assert "removeItem" in text, "the old keys are listed but never removed"
