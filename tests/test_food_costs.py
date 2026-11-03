"""What a food recipe costs: the data and the matcher (#1458, DECISIONS §8.2).

`_data/food/costs.yml` holds keyword price ranges and the unit table;
`_plugins/food_costs.rb` matches each shopping-list ingredient to a rate at
build, and assets/js/food-shopping-list.js multiplies
(tests/js/food-shopping-list.test.js). The matcher is asked through
scripts/food_costs.rb, never restated in Python.
"""
from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.food

ROOT = Path(__file__).resolve().parent.parent
COSTS = yaml.safe_load((ROOT / "_data" / "food" / "costs.yml").read_text(encoding="utf-8"))
FAMILIES = {"g", "ml", "each", "pack", "free"}
BASES = {"kg", "l", "each", "pack"}


def _fold(word: str) -> str:
    return " ".join(str(word).replace("’", "'").lower().split())


def test_the_prices_were_checked_within_two_years():
    """A price decays. The fix is re-reading the prices against a shop, never
    moving the date alone (the cocktail file's rule, #749)."""
    raw = COSTS.get("checked")
    checked = datetime.date.fromisoformat(str(raw))
    age = (datetime.date.today() - checked).days
    assert age <= 730, (
        f"_data/food/costs.yml says its prices were checked on {checked}, "
        f"{age} days ago. Re-read them and move `checked:` forward."
    )


def test_every_price_is_a_low_and_high_range_in_a_known_unit():
    bad = []
    for word, row in (COSTS.get("prices") or {}).items():
        if not isinstance(row, dict) or not row:
            bad.append(f"{word}: {row!r} is not a mapping of unit to range")
            continue
        for unit, value in row.items():
            if unit == "confidence":
                if value not in ("low", "medium", "high"):
                    bad.append(f"{word}: confidence {value!r}")
                continue
            if unit not in BASES and unit not in COSTS["units"] and unit not in ("head", "cm"):
                bad.append(f"{word}: unit {unit!r} is neither a base nor a declared unit")
            if (not isinstance(value, list) or len(value) != 2
                    or not all(isinstance(v, (int, float)) for v in value)
                    or not 0 <= value[0] <= value[1]):
                bad.append(f"{word}: {unit} {value!r} is not [low, high] with low <= high")
    assert not bad, "_data/food/costs.yml:\n  " + "\n  ".join(bad)


def test_every_unit_names_a_family_and_a_positive_factor():
    bad = []
    for unit, spec in COSTS["units"].items():
        family, factor = (spec + [None, None])[:2] if isinstance(spec, list) else (None, None)
        if family not in FAMILIES:
            bad.append(f"{unit!r}: family {family!r} is not one of {sorted(FAMILIES)}")
        elif family != "free" and not (isinstance(factor, (int, float)) and factor > 0):
            bad.append(f"{unit!r}: factor {factor!r} must be a positive number")
    assert not bad, "_data/food/costs.yml `units:`:\n  " + "\n  ".join(bad)


def test_no_keyword_is_both_free_and_priced_or_written_twice():
    """Two rows for one folded keyword leave the price to sort order."""
    seen, dupes = {}, []
    for word in list(COSTS.get("free") or []) + list((COSTS.get("prices") or {}).keys()):
        key = _fold(word)
        if key in seen:
            dupes.append(f"{word!r} and {seen[key]!r}")
        seen[key] = word
    assert not dupes, "keywords written twice in _data/food/costs.yml: " + ", ".join(dupes)


def _ask(names):
    if shutil.which("ruby") is None:
        if os.environ.get("CI"):
            pytest.fail("No ruby in CI, so _plugins/food_costs.rb cannot be asked "
                        "anything, and skipping would report the matcher green.")
        pytest.skip("no ruby on this machine; the cost matcher is Ruby")
    result = subprocess.run(["ruby", "scripts/food_costs.rb", *names],
                            cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    return json.loads(result.stdout)


# The name, and the base unit its rate must carry (None: no rate at all).
MATCHES = {
    "plain flour": "g",
    "unsalted butter": "g",
    "double cream": "ml",
    "eggs": "each",
    "garlic cloves": "each",
    # The longer keyword wins: each of these would otherwise be priced as the
    # shorter word inside it.
    "chicken stock": "ml",
    "butter beans": "g",
    "peanut butter": "g",
    "white wine vinegar": "ml",
    "coconut milk": "ml",
    "sugar snap peas": "g",
    # Seasoning, and zest off a fruit bought anyway, are free.
    "salt and black pepper": "free",
    "sea salt flakes": "free",
    "lemon zest": "free",
    # Whole words: `salt` is not inside `unsalted`.
    "salted butter": "g",
    # Another recipe, linked, is never priced by a word in its title.
    "[grandma's lemon curd](../grandmas-lemon-curd/)": None,
    "kohlrabi": None,
}


def test_the_matcher_prices_each_name_by_its_longest_keyword():
    answers = _ask(list(MATCHES))
    wrong = []
    for name, base in MATCHES.items():
        rate = answers[name]
        if base is None:
            if rate is not None:
                wrong.append(f"{name!r} was priced {rate!r}; it should have no rate")
        elif rate is None or base not in rate:
            wrong.append(f"{name!r} got {rate!r}; expected a {base!r} rate")
    assert not wrong, "\n".join(wrong)


def test_a_rate_is_per_gram_and_per_millilitre_not_per_kilo():
    """The browser multiplies a total in grams by the rate, so a kilo price
    left unconverted would print a thousand times too much."""
    answers = _ask(["plain flour", "double cream"])
    flour_kg = COSTS["prices"]["flour"]["kg"]
    cream_l = COSTS["prices"]["double cream"]["l"]
    assert answers["plain flour"]["g"] == pytest.approx([p / 1000 for p in flour_kg])
    assert answers["double cream"]["ml"] == pytest.approx([p / 1000 for p in cream_l])


def test_prices_reach_the_page_only_behind_show_costs():
    """A production build must carry no rate and no unit table (DECISIONS
    §8.2): `site.show_costs` is declared in _config_local.yml alone."""
    prod = yaml.safe_load((ROOT / "_config.yml").read_text(encoding="utf-8"))
    assert not prod.get("show_costs"), "_config.yml must not set show_costs"
    page = (ROOT / "food" / "index.html").read_text(encoding="utf-8")
    assert '{% if site.show_costs and ing.rate %},"r":' in page, (
        "food/index.html emits a rate without the show_costs gate")
    units_at = page.index('id="food-cost-units"')
    assert page.rfind("{% if site.show_costs %}", 0, units_at) > page.rfind("{% endif %}", 0, units_at), (
        "#food-cost-units is emitted outside a show_costs block")
