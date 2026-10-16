"""The shopping list's data — GitHub issues #801 and #815.

`_data/food/aisles.yml` says where an ingredient is found in a shop. How many
people a recipe feeds is in the RECIPE, in `serves:` or, where that does not
state a number, in `serves_estimate:`. `_plugins/food_shopping.rb` reads both.

These check the files: every recipe states how many it feeds, an estimate is
present only where it is needed, the aisles are well-formed and no keyword is
claimed twice. They do not check the aisle matching, which is Ruby and runs
inside Jekyll: tests/test_rendered_pages.py does, against the real build. A
second matcher written in Python to test here would pass while the site was
wrong.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.food

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data" / "food"

AISLES = yaml.safe_load((DATA / "aisles.yml").read_text(encoding="utf-8"))

# Drafts are gitignored and absent in CI and in a fresh worktree, so the two
# published collections are what every machine can check. The draft half runs
# only where they have been cloned.
PUBLISHED_DIRS = ("_food_recipes", "_food_magic_bag")
ALL_DIRS = PUBLISHED_DIRS + ("_food_drafts",)

# `serves:` counts as stated when it OPENS with a number -- the plugin's own
# rule, restated here because it cannot be imported from Ruby.
# `_plugins/food_shopping.rb`'s LEADING_NUMBER is the original.
LEADING_NUMBER = re.compile(r"^\s*(\d+)")


def recipe_paths(dirs=ALL_DIRS):
    for folder in dirs:
        yield from sorted((ROOT / folder).glob("*.md"))


def published_paths(folder):
    """One published collection's files, never an empty pass.

    The magic bag may legitimately hold nothing, and git keeps no empty
    directory, so an empty magic bag skips; an empty `_food_recipes/` is a
    broken glob and fails.
    """
    paths = list(recipe_paths([folder]))
    if not paths:
        if folder == "_food_magic_bag":
            pytest.skip("_food_magic_bag/ has no entries yet; this runs on the first one.")
        pytest.fail(f"{folder}/ yielded no recipe files, so this would check nothing.")
    return paths


def front_matter(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1]) or {}
    except (IndexError, yaml.YAMLError):
        return {}


def states_people(fm: dict) -> bool:
    """Does `serves:` open with a number? `makes:` never counts people."""
    return bool(fm.get("serves") and LEADING_NUMBER.match(str(fm["serves"])))


# --- how many people ----------------------------------------------------------

@pytest.mark.parametrize("folder", PUBLISHED_DIRS)
def test_every_published_recipe_states_how_many_it_feeds(folder):
    """The scaler divides by this number, so every recipe needs one (#815).

    Either `serves:` opens with a number, or `serves_estimate:` carries an
    integer. `makes:` is never read as people however numeric it looks:
    950 ml is not 950 portions.
    """
    missing = []
    for path in published_paths(folder):
        fm = front_matter(path)
        if states_people(fm):
            continue
        if isinstance(fm.get("serves_estimate"), int):
            continue
        missing.append(f"{path.name}  serves={fm.get('serves')!r} "
                       f"makes={fm.get('makes')!r}")
    assert not missing, (
        "these recipes say nothing about how many people they feed, so the "
        "shopping list cannot scale them. Add `serves_estimate:` — an integer, "
        "people — beside the `makes:` it is read from:\n  " + "\n  ".join(missing)
    )


def test_every_draft_states_how_many_it_feeds():
    """The same rule on drafts, which Helen browses locally: a draft with no
    figure is a recipe the shopping list cannot scale.

    Skipped where the private repo is not cloned (CI, a fresh worktree).
    """
    folder = ROOT / "_food_drafts"
    if not folder.is_dir():
        pytest.skip("_food_drafts/ is not cloned here, so there is no draft to "
                    "check: sh scripts/git-clone-agent.sh "
                    "helen-triages-food-private _food_drafts")

    missing = []
    for path in recipe_paths(["_food_drafts"]):
        fm = front_matter(path)
        if not fm:
            continue        # README.md and anything without front matter
        if states_people(fm) or isinstance(fm.get("serves_estimate"), int):
            continue
        missing.append(f"{path.name}  serves={fm.get('serves')!r} "
                       f"makes={fm.get('makes')!r}")
    assert not missing, (
        "these drafts say nothing about how many people they feed:\n  "
        + "\n  ".join(missing)
    )


@pytest.mark.parametrize("folder", PUBLISHED_DIRS)
def test_serves_estimate_is_a_positive_whole_number_of_people(folder):
    bad = []
    for path in published_paths(folder):
        value = front_matter(path).get("serves_estimate")
        if value is None:
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            bad.append(f"{path.name}: {value!r}")
    assert not bad, (
        "`serves_estimate:` is a whole number of people, one or more, and "
        "unquoted — a quoted `\"6\"` is the string and the plugin will not read "
        "it: " + ", ".join(bad)
    )


@pytest.mark.parametrize("folder", PUBLISHED_DIRS)
def test_no_estimate_contradicts_a_serving_size_helen_wrote(folder):
    """The recipe wins. The estimate fills a gap and never argues with one.

    A `serves_estimate:` on a recipe whose `serves:` already states a number is
    dead weight at best — the plugin reads `serves:` first — and a lie about
    where the figure came from at worst, because an estimate is printed with a
    `~` and a stated one is not.
    """
    shadowed = []
    for path in published_paths(folder):
        fm = front_matter(path)
        if states_people(fm) and "serves_estimate" in fm:
            shadowed.append(f"{path.name} (serves: {fm['serves']!r})")
    assert not shadowed, (
        "these recipes state their own serving size and carry an estimate too: "
        + ", ".join(shadowed)
    )


def test_the_deleted_servings_file_stays_deleted():
    """The estimate has one home, the recipe's front matter (#815).

    A `_data/food/servings.yml` would be a second home for the figure, which
    is how the page and the file come to disagree about how many a recipe
    feeds.
    """
    assert not (DATA / "servings.yml").exists(), (
        "_data/food/servings.yml is back. `serves_estimate:` in the recipe is "
        "the single source since #815; see this module's docstring."
    )


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

    Last, because food-shopping-list.js sends an aisle it does not recognise
    to the final entry, so no ingredient silently vanishes from a list.
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

    The longest keyword wins and there is no tie-break, so one word under two
    aisles is decided by how the YAML loaded. `garlic cloves` in produce
    against `cloves` in spices is fine: different strings, different lengths.
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

    It is matched on the whole folded name, not as a keyword, which keeps
    "water mixed with 3 tsp cornstarch" on the list while plain "water" stays
    off. Anything added disappears from every shopping list with no line to
    say so, so this asserts the contents and not the shape.
    """
    assert sorted(AISLES["never"]) == ["cold water", "ice", "water"], (
        "the `never` list has changed. Everything on it vanishes from every "
        "shopping list silently; adding to it is Helen's call, not a tidy-up."
    )
