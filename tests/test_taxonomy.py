"""Taxonomy and links.

Everything in this file that touches `taxonomy` skips until
`_data/food/taxonomy.yml` exists. That is deliberate: these tests are the written
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

def test_star_ingredient_is_declared(recipe, taxonomy):
    star = recipe.fm.get("star_ingredient")
    if star in (None, ""):
        return
    declared = taxonomy.get("star_ingredients") or []
    assert star in declared, (
        f"{where(recipe)} has `star_ingredient: {star!r}`, which is not declared "
        f"in _data/food/taxonomy.yml.\n"
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
        f"A tag that is not in _data/food/taxonomy.yml renders NOWHERE — not as a "
        f"badge on the recipe page and not as a filter button on the index. "
        f"_includes/recipe_badges.html builds badges by iterating "
        f"_data/food/filter_sections.yml's tag_groups and looking each one up "
        f"here, so both come from the same place. This message used to claim the "
        f"tag still showed on the recipe page; it does not. "
        f"Declared tags: {', '.join(sorted(declared))}."
    )


def test_co_tag_rules(recipe, taxonomy):
    """Tags that imply other tags, declared in _data/food/taxonomy.yml.

    The rules live in the data layer rather than in this file so that changing
    one is a YAML edit, not a code edit. The reasoning for each — and for the
    two that were removed — is recorded in taxonomy.yml alongside them.
    """
    tags = recipe.fm.get("tags") or []
    problems = []
    for trigger, required in (taxonomy.get("co_tags") or {}).items():
        if trigger not in tags:
            continue
        missing = [t for t in required if t not in tags]
        if missing:
            problems.append(f"tagged `{trigger}` but missing {missing}")
    assert not problems, (
        f"{where(recipe)} breaks co-tag rule(s):\n  " + "\n  ".join(problems)
        + "\n\nEither add the missing tag(s), or — if this recipe is a real "
          "exception — the rule itself may be unsound. See the test for adding "
          "a co-tag at the top of the co_tags section in _data/food/taxonomy.yml."
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

LINK = re.compile(r"\]\(\.\./([a-z0-9-]+)/\)")
PUBLISHED = {r.slug for r in ALL_RECIPES}


def test_internal_recipe_links_resolve(recipe):
    """A link to an unpublished recipe is a 404 on a live site."""
    broken = [slug for slug in LINK.findall(recipe.raw) if slug not in PUBLISHED]
    assert not broken, (
        f"{where(recipe)} links to recipe slug(s) {broken}, which are not in "
        f"_food_recipes/.\n"
        f"Either the target is still in _food_drafts/ (in which case the link 404s "
        f"until it is promoted) or the slug has been renamed and this link was "
        f"not updated."
    )


def test_no_claude_markers_left(recipe):
    """A note addressed to me is an instruction for a future session, not
    content ready to publish -- in any form, not just the "QQ CLAUDE ..."
    one this test used to be scoped to. Broadened 2026-08-02 after a bare
    "CLAUDE, I'd like bullet points here" note (no QQ prefix) slipped
    through undetected in dark-chocolate-ganache.md.
    """
    markers = re.findall(r"[^\"\n]{0,10}\bCLAUDE\b[^\"\n]{0,40}", recipe.raw)
    assert not markers, (
        f"{where(recipe)} still contains marker(s) {markers}. "
        f"These are instructions left for a future session and should be "
        f"actioned and removed before publication."
    )


# --- ingredient spelling collisions -----------------------------------------

def _fold(text: str) -> str:
    """Strip diacritics and case — the form the search layer compares on."""
    import unicodedata
    stripped = "".join(
        c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c)
    )
    return stripped.lower()


def test_no_main_ingredient_spelling_collisions():
    """No two ingredient entries anywhere differing only by accent or case.

    Two spellings of one ingredient means two filter buttons for one thing —
    a `comté` button and a `comte` button, each holding half the recipes. The
    search layer folds accents when matching, so the collision is invisible
    until someone browses the buttons.

    This test covers drafts as well as published recipes: a draft carries its
    spelling with it when it is promoted.
    """
    from collections import defaultdict
    from conftest import ALL_RECIPES, ALL_DRAFTS

    forms = defaultdict(set)
    sources = defaultdict(set)
    for r in ALL_RECIPES + ALL_DRAFTS:
        for entry in (r.fm.get("main_ingredients") or []):
            entry = str(entry)
            forms[_fold(entry)].add(entry)
            sources[_fold(entry)].add(r.slug)

    collisions = {k: v for k, v in forms.items() if len(v) > 1}
    assert not collisions, (
        "main_ingredients contains the same ingredient spelled more than one way:\n  "
        + "\n  ".join(
            f"{sorted(v)} — in {sorted(sources[k])[:4]}" for k, v in sorted(collisions.items())
        )
        + "\n\nPick one spelling and use it everywhere. Proper nouns keep their "
          "capital (Parma ham, Dijon mustard); everything else is lowercase."
    )


def test_incidental_not_in_main_ingredients(recipe):
    """An ingredient item marked `incidental: true` (see HANDOVER "Easy to
    get wrong") is a cooking fluid, not a real recipe component. It has no
    business turning up as a recipe-row ingredient pill or an
    ingredient-search hit on the index page -- both read from
    `main_ingredients` -- so it should never also be listed there.
    """
    main = {_fold(str(m)) for m in (recipe.fm.get("main_ingredients") or [])}
    if not main:
        return
    offenders = []
    for group in recipe.fm.get("ingredient_groups") or []:
        for item in group.get("items") or []:
            if not isinstance(item, dict) or not item.get("incidental"):
                continue
            name = _fold(str(item.get("item", "")).split(",")[0].strip())
            hits = [m for m in main if name and (name in m or m in name)]
            if hits:
                offenders.append((item.get("item"), hits))
    assert not offenders, (
        f"{where(recipe)} marks ingredient(s) `incidental: true` that still "
        f"appear in main_ingredients: {offenders}. An incidental cooking "
        f"fluid shouldn't show up as a recipe-row pill or an ingredient-"
        f"search hit -- remove it from main_ingredients, or drop the "
        f"incidental flag if it's actually core."
    )
