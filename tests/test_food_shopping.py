"""The shopping list's two data files — GitHub issue #801.

_data/food/aisles.yml says where an ingredient is found in a shop;
_data/food/servings.yml says how many people a recipe feeds when the recipe
itself does not. _plugins/food_shopping.rb reads both at build.

WHAT THESE CAN AND CANNOT CHECK. They check the FILES: that the aisles are
well-formed, that no keyword is claimed by two of them, that every guess is for
a recipe that exists and is only there because it is needed. They cannot check
the MATCHING, because the matcher is Ruby and runs inside Jekyll -- that is
tests/test_rendered_pages.py's job, and it does it against the real build,
which is the only place the two could ever disagree.

The division is deliberate rather than accidental: a second implementation of
the aisle rule written in Python to make it testable here is exactly the drift
MANUAL 11.2 is about, and it would pass while the site was wrong.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

# Suite marker, so `pytest -m food` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.food

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data" / "food"

AISLES = yaml.safe_load((DATA / "aisles.yml").read_text(encoding="utf-8"))
SERVINGS = yaml.safe_load((DATA / "servings.yml").read_text(encoding="utf-8"))

RECIPE_DIRS = ("_food_recipes", "_food_magic_bag")

# `serves:` counts as stated when it OPENS with a number -- the plugin's own
# rule, restated here rather than imported because it cannot be imported.
# _plugins/food_shopping.rb's LEADING_NUMBER is the original; if one moves, the
# test below that counts the guesses is what notices.
LEADING_NUMBER = re.compile(r"^\s*(\d+)")


def recipe_paths():
    for folder in RECIPE_DIRS:
        yield from sorted((ROOT / folder).glob("*.md"))


def front_matter(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1]) or {}


# --- the aisles ---------------------------------------------------------------

def test_the_aisle_order_is_a_list_of_keys_and_labels():
    order = AISLES["order"]
    assert order, "_data/food/aisles.yml has no `order`, so the list has no headings."
    for aisle in order:
        assert set(aisle) == {"key", "label"}, (
            f"aisle {aisle!r} should have exactly `key` and `label`. The key is "
            "what _plugins/food_shopping.rb stamps on an ingredient; the label "
            "is what the page prints."
        )
        assert aisle["key"] == aisle["key"].lower()


def test_other_is_last_and_exists():
    """`other` is where an unmatched ingredient lands, so it has to be there.

    LAST, because food-shopping-list.js sends an aisle it does not recognise to
    the final entry -- a blob emitted by an older build, or a key removed from
    this file. An ingredient must never silently vanish from a shopping list:
    a line you do not see is a thing you do not buy.
    """
    keys = [a["key"] for a in AISLES["order"]]
    assert keys[-1] == "other", (
        f"`other` must be the last aisle; the order ends {keys[-3:]}."
    )


def test_every_keyword_aisle_is_a_declared_aisle():
    declared = {a["key"] for a in AISLES["order"]}
    for aisle in AISLES["keywords"]:
        assert aisle in declared, (
            f"`keywords` has a block for `{aisle}`, which is not in `order`. "
            "Nothing would ever be shown under it."
        )


def test_no_keyword_is_claimed_by_two_aisles():
    """One word, one shelf.

    The matching rule is "the longest keyword wins", which has no tie-break
    worth relying on -- so the same word under two aisles is a coin toss
    decided by how the YAML happened to load. `garlic cloves` in produce
    against `cloves` in spices is the RIGHT shape for this: different strings,
    different lengths, a decidable answer.
    """
    seen: dict[str, str] = {}
    clashes = []
    for aisle, words in AISLES["keywords"].items():
        for word in words or []:
            if word in seen and seen[word] != aisle:
                clashes.append(f"{word!r} in both {seen[word]} and {aisle}")
            seen[word] = aisle
    assert not clashes, "keywords claimed by two aisles: " + "; ".join(clashes)


def test_keywords_are_lowercase_and_singular_spaced():
    """Matching folds the ingredient name to lowercase; a capital here never fires."""
    bad = []
    for aisle, words in AISLES["keywords"].items():
        for word in words or []:
            if word != word.lower():
                bad.append(f"{word!r} ({aisle}) is not lowercase")
            if word != " ".join(word.split()):
                bad.append(f"{word!r} ({aisle}) has stray whitespace")
    assert not bad, "; ".join(bad)


def test_never_is_matched_on_the_whole_name_and_stays_short():
    """`never` drops an ingredient outright, so it is the one list that must not grow.

    It is matched on the WHOLE folded name, not as a keyword -- that is what
    keeps "water mixed with 3 tsp cornstarch" on the list while plain "water"
    stays off it. Anything added here disappears from every shopping list with
    no line to say so, which is why this asserts the contents rather than the
    shape.
    """
    assert sorted(AISLES["never"]) == ["cold water", "ice", "water"], (
        "the `never` list has changed. Everything on it vanishes from every "
        "shopping list silently; adding to it is Helen's call, not a tidy-up."
    )


# --- the serving-size guesses --------------------------------------------------

def test_every_food_recipe_resolves_to_a_portion_count():
    """The scaler divides by this number, so every recipe needs one.

    Either the recipe's own `serves:` opens with a number, or
    _data/food/servings.yml carries a guess for its slug. A recipe with
    neither still builds -- `portions` is simply null and the page offers no
    scaling for it -- which is the right way round: a missing guess must not
    stop a build. It stops THIS instead.

    Helen, #801: "When serving size is unclear, please make your best guess."
    """
    missing = []
    for path in recipe_paths():
        data = front_matter(path)
        if LEADING_NUMBER.match(str(data.get("serves") or "")):
            continue
        if path.stem in SERVINGS["portions"]:
            continue
        missing.append(f"{path.parent.name}/{path.name}"
                       f"  serves={data.get('serves')!r} makes={data.get('makes')!r}")
    assert not missing, (
        "these recipes have no portion count and no guess in "
        "_data/food/servings.yml, so the shopping list cannot scale them:\n  "
        + "\n  ".join(missing)
    )


def test_every_guess_names_a_recipe_that_exists():
    """A guess for a renamed or deleted recipe is read by nothing and says so."""
    slugs = {path.stem for path in recipe_paths()}
    orphans = sorted(set(SERVINGS["portions"]) - slugs)
    assert not orphans, (
        f"_data/food/servings.yml has guesses for recipes that do not exist: "
        f"{orphans}. A renamed recipe needs its guess renamed with it, or it "
        "quietly falls back to no scaling at all."
    )


def test_no_guess_overrides_a_serving_size_helen_wrote():
    """The recipe wins. This file fills gaps and never contradicts.

    A slug listed here whose `serves:` already opens with a number is dead
    weight at best -- the plugin reads the recipe first -- and a lie about
    where the number came from at worst, because everything in this file is
    flagged `estimated` and printed with a `~`.
    """
    shadowed = []
    for path in recipe_paths():
        if path.stem not in SERVINGS["portions"]:
            continue
        serves = str(front_matter(path).get("serves") or "")
        if LEADING_NUMBER.match(serves):
            shadowed.append(f"{path.stem} (serves: {serves!r})")
    assert not shadowed, (
        "these recipes state their own serving size and are also guessed at in "
        "_data/food/servings.yml: " + ", ".join(shadowed)
    )


def test_every_guess_is_a_positive_whole_number_of_people():
    bad = [f"{slug}: {n!r}" for slug, n in SERVINGS["portions"].items()
           if not isinstance(n, int) or isinstance(n, bool) or n < 1]
    assert not bad, (
        "portion counts must be whole numbers of people, one or more: "
        + ", ".join(bad)
    )
