"""What a food recipe costs: the data and the matcher (#1458, DECISIONS §8.2).

`_data/food/costs.yml` holds keyword price ranges and the unit table, a
researched unit naming its food's shop prices in `price_research.yml`;
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
RESEARCH_FILE = yaml.safe_load(
    (ROOT / "_data" / "food" / "price_research.yml").read_text(encoding="utf-8"))
RESEARCH = RESEARCH_FILE["foods"]
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


def test_the_research_was_checked_within_two_years():
    checked = datetime.date.fromisoformat(str(RESEARCH_FILE.get("checked")))
    age = (datetime.date.today() - checked).days
    assert age <= 730, (
        f"_data/food/price_research.yml was checked on {checked}, {age} days "
        "ago. Re-read the prices against shops and move `checked:` forward.")


def test_every_researched_price_is_a_positive_number_then_its_shop():
    bad = []
    for food, entry in RESEARCH.items():
        if not isinstance(entry, dict):
            bad.append(f"{food}: {entry!r} is not a mapping of unit to prices")
            continue
        for unit, prices in entry.items():
            if unit == "thin":
                if prices is not True:
                    bad.append(f"{food}: thin {prices!r} must be true or absent")
                continue
            if unit == "note":
                continue
            if unit not in BASES and unit not in COSTS["units"] and unit not in ("head", "cm"):
                bad.append(f"{food}: unit {unit!r} is neither a base nor a declared unit")
            if not isinstance(prices, list) or not prices:
                bad.append(f"{food}: {unit} is not a list of prices")
                continue
            for item in prices:
                number, _, shop = str(item).partition(" ")
                try:
                    ok = float(number) > 0 and shop.strip()
                except ValueError:
                    ok = False
                if not ok:
                    bad.append(f"{food}: {unit} {item!r} is not '<price> <shop>'")
    assert not bad, "_data/food/price_research.yml:\n  " + "\n  ".join(bad)


def _bracket(vals):
    """The rule in MANUAL §8.2, from Python's own quartiles, so the plugin's
    arithmetic is checked against an independent one."""
    import statistics
    if len(vals) >= 6:
        q1, _, q3 = statistics.quantiles(vals, n=4, method="inclusive")
        return [q1, q3]
    return [min(vals), max(vals)]


def test_a_researched_unit_is_priced_from_its_research_bracket():
    """Every costs.yml unit that names a food gets, at build, that food's
    bracket in its base unit (to the penny, as the plugin rounds). The base
    unit is per g and per ml: the browser multiplies a total in grams by the
    rate, so a kilo price left unconverted would print a thousand times over."""
    rows = {word: row for word, row in COSTS["prices"].items()
            if any(isinstance(v, str) for v in row.values())}
    assert rows, "no costs.yml row reads from price_research.yml"
    answers = _ask(list(rows))
    wrong = []
    for word, row in rows.items():
        for unit, food in row.items():
            if not isinstance(food, str) or unit == "confidence":
                continue
            vals = [float(str(p).split(" ", 1)[0]) for p in RESEARCH[food][unit]]
            base, per = {"kg": ("g", 1000), "l": ("ml", 1000)}.get(unit, (unit, 1))
            want = [v / per for v in _bracket(vals)]
            got = (answers.get(word) or {}).get(base)
            if got is None or any(abs(g - w) > 0.006 / per for g, w in zip(got, want)):
                wrong.append(f"{word} {unit} ({food}): got {got}, want {want}")
    assert not wrong, "\n".join(wrong)


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
            if isinstance(value, str):
                if not (RESEARCH.get(value) or {}).get(unit):
                    bad.append(f"{word}: {unit} names {value!r}, which "
                               f"price_research.yml has no {unit} prices for")
                continue
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
    # A keyword matches its plural, so costs.yml writes rows singular; a
    # plural row that prices differently still wins (`peppers` is not free).
    "cucumbers": "each",
    "cherries": "g",
    "bay leaves": "each",
    "red peppers": "each",
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


def test_prices_reach_the_page_only_behind_show_costs():
    """A production build must carry no rate and no unit table (DECISIONS
    §8.2): `site.show_costs` is declared in _config_local.yml alone."""
    prod = yaml.safe_load((ROOT / "_config.yml").read_text(encoding="utf-8"))
    assert not prod.get("show_costs"), "_config.yml must not set show_costs"
    page = (ROOT / "food" / "index.html").read_text(encoding="utf-8")
    assert '{% if site.show_costs and ing.rate %},"r":' in page, (
        "food/index.html emits a rate without the show_costs gate")
    _assert_gated(page, 'id="food-cost-units"', "food/index.html")

    # The recipe page's cost line: the footer, its data and its script.
    layout = (ROOT / "_layouts" / "recipe.html").read_text(encoding="utf-8")
    for marker in ('class="recipe-footer"', 'id="recipe-cost-data"', "/assets/js/recipe-cost.js"):
        _assert_gated(layout, marker, "_layouts/recipe.html")


def _assert_gated(text: str, marker: str, where: str) -> None:
    """`marker` sits inside an open `{% if site.show_costs ... %}` block."""
    at = text.index(marker)
    opened = max(text.rfind("{% if site.show_costs %}", 0, at),
                 text.rfind("{% if site.show_costs and", 0, at))
    assert opened > text.rfind("{% endif %}", 0, at), (
        f"{where}: {marker} is emitted outside a show_costs block, so a "
        "production build would carry it")
