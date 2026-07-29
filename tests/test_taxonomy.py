"""Taxonomy and links.

Everything in this file that touches `taxonomy` skips until
`_data/taxonomy.yml` exists. That is deliberate: these tests are the written
specification for a file that has not been created yet (ARCHITECTURE_v22.md,
Phase 2.1). Create the file and they start enforcing it with no further work.

The point of declaring stars rather than deriving them from front matter is
exactly this: a typo currently mints a brand new star ingredient with one
recipe under it, silently. Once taxonomy.yml exists, a typo is a failing test.
"""
from __future__ import annotations

import re

import pytest

from conftest import ALL_RECIPES, where

# Co-tag rules from HANDOVER section 5.
CO_TAGS = {
    "soup": ["one-handed food"],
    "ice cream": ["dessert", "freezable", "make-ahead"],
}

# Recipes that are legitimately exempt, with the reason recorded so the
# exemption is a decision rather than a mystery.
CO_TAG_EXEMPT = {
    ("double-chocolate-frap", "ice cream"): "blended frozen drink, not a scoopable ice cream",
}


def test_star_ingredient_is_declared(recipe, taxonomy):
    star = recipe.fm.get("star_ingredient")
    if star in (None, ""):
        return
    declared = taxonomy.get("star_ingredients") or []
    assert star in declared, (
        f"{where(recipe)} has `star_ingredient: {star!r}`, which is not declared "
        f"in _data/taxonomy.yml.\n"
        f"Declared stars are: {', '.join(declared)}.\n"
        f"Either this is a typo, or the star is real and needs adding to the "
        f"taxonomy — it will not get a filter button until it is."
    )


def test_tags_are_declared(recipe, taxonomy):
    declared = set()
    for group in (taxonomy.get("tags") or {}).values():
        declared.update(group)
    unknown = [t for t in (recipe.fm.get("tags") or []) if t not in declared]
    assert not unknown, (
        f"{where(recipe)} uses undeclared tag(s) {unknown}.\n"
        f"A tag that is not in _data/taxonomy.yml renders on the recipe page but "
        f"has no filter button on the index, so it is invisible to anyone "
        f"browsing. Declared tags: {', '.join(sorted(declared))}."
    )


@pytest.mark.parametrize("trigger,required", sorted(CO_TAGS.items()))
def test_co_tag_rules(recipe, trigger, required):
    tags = recipe.fm.get("tags") or []
    if trigger not in tags:
        return
    reason = CO_TAG_EXEMPT.get((recipe.slug, trigger))
    if reason:
        pytest.skip(f"exempt: {reason}")
    missing = [t for t in required if t not in tags]
    assert not missing, (
        f"{where(recipe)} is tagged `{trigger}` but is missing {missing}.\n"
        f"Anything tagged `{trigger}` must also carry {required}. If this recipe "
        f"is a genuine exception, add it to CO_TAG_EXEMPT in this file with the "
        f"reason, so the exemption is recorded rather than silently tolerated."
    )


def test_no_cook_tag_implies_no_cook_time(recipe):
    """One-directional, deliberately.

    `cook_time: "None"` is a FACT about the recipe. `no-cook` is a FILTER
    AFFORDANCE — it answers "can I put this on the table without cooking?".
    They are different layers, so the implication only runs one way:

        tagged no-cook  ->  must have cook_time "None"
        cook_time None  ->  MAY be tagged, but need not be

    That is what lets a base recipe like mixed-spice be honestly uncooked
    without cluttering the no-cook filter, which exists to answer a dinner
    question, not a spice-blend question.
    """
    if "no-cook" not in (recipe.fm.get("tags") or []):
        return
    cook = recipe.fm.get("cook_time")
    declared_none = isinstance(cook, str) and cook.strip().lower() == "none"
    assert declared_none, (
        f"{where(recipe)} is tagged `no-cook` but has `cook_time: {cook!r}`.\n"
        f'Anything advertised as no-cook must say so in the data: cook_time: "None". '
        f"A blank or QQ cook_time means you have not decided yet, which is not "
        f"the same as deciding there is no cooking."
    )


def test_no_oven_conversions(recipe):
    """Fan oven only. Conversions are noise, and worse, a trap.

    A conventional temperature left in place is 20 degrees too hot in this
    kitchen, so a stray conversion is not merely untidy.
    """
    hits = re.findall(r"[^\s]*\s*(?:non-fan|fan\b|gas mark \d|gas \d)[^,.\"]{0,10}", recipe.raw)
    hits = [h for h in hits if "fancy" not in h]
    assert not hits, (
        f"{where(recipe)} contains oven conversion(s): {hits}.\n"
        f"This site is fan-oven only. Keep the fan temperature and delete the "
        f"conventional and gas equivalents — but check which of the two figures "
        f"is the fan one before deleting, they are not always in the same order."
    )


# --- links -----------------------------------------------------------------

LINK = re.compile(r"\]\(/recipes/([a-z0-9-]+)/\)")
PUBLISHED = {r.slug for r in ALL_RECIPES}


def test_internal_recipe_links_resolve(recipe):
    """A link to an unpublished recipe is a 404 on a live site."""
    broken = [slug for slug in LINK.findall(recipe.raw) if slug not in PUBLISHED]
    assert not broken, (
        f"{where(recipe)} links to recipe slug(s) {broken}, which are not in "
        f"_recipes/.\n"
        f"Either the target is still in _drafts/ (in which case the link 404s "
        f"until it is promoted) or the slug has been renamed and this link was "
        f"not updated."
    )


def test_no_claude_markers_left(recipe):
    """`QQ CLAUDE ...` markers are instructions to me, not content."""
    markers = re.findall(r"QQ\s+CLAUDE[^\"\n]*", recipe.raw)
    assert not markers, (
        f"{where(recipe)} still contains marker(s) {markers}. "
        f"These are instructions left for a future session and should be "
        f"actioned and removed before publication."
    )
