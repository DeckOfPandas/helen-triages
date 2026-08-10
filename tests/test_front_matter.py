"""Structural rules: what a recipe file must contain, and what it must not.

These come from HANDOVER section 7. Each one asserts a single rule so that a
failure tells you exactly which rule broke, on which file.
"""
from __future__ import annotations

import re

import pytest

from conftest import where

REQUIRED = ["title", "short_name", "tagline", "source", "main_ingredients",
            "tags", "ingredient_groups", "method_short", "meta"]

RETIRED = {
    "published": "removed from the schema",
    "date_added": "renamed to meta.date_last_edited",
    "difficulty": "removed from the schema",
    "nutrition": "removed from the schema",
    "filling_note": "folded into notes:",
    "headline_ingredient": "renamed to star_ingredient",
}

MISPLACED_META = ["rewritten", "proofread", "cooked_before", "date_last_edited"]


@pytest.mark.parametrize("field", REQUIRED)
def test_required_field_present(recipe, field):
    assert field in recipe.fm, (
        f"{where(recipe)} is missing the required field `{field}:`.\n"
        f"Every recipe needs all of: {', '.join(REQUIRED)}."
    )


def test_tagline_is_not_blank(recipe):
    """Present is not the same as written.

    `test_required_field_present` only checks the key exists — a recipe with
    `tagline: ""` passes it happily. A blank tagline is a real gap on a
    published recipe (it's the one line of prose every recipe page shows
    unconditionally), distinct from `_food_drafts/`, where a blank tagline is
    completely normal for a stub not written up yet.
    """
    tagline = recipe.fm.get("tagline")
    assert isinstance(tagline, str) and tagline.strip(), (
        f"{where(recipe)} has a blank tagline ({tagline!r}).\n"
        f"Fine in _food_drafts/, not fine here — every published recipe "
        f"needs its one-line tagline written."
    )


def test_no_retired_fields(recipe):
    found = {f: why for f, why in RETIRED.items() if f in recipe.fm}
    assert not found, (
        f"{where(recipe)} still has retired field(s): "
        + "; ".join(f"`{f}` ({why})" for f, why in found.items())
    )


def test_meta_fields_are_nested_not_top_level(recipe):
    stray = [f for f in MISPLACED_META if f in recipe.fm]
    assert not stray, (
        f"{where(recipe)} has {stray} at the top level. "
        f"These belong inside the `meta:` block — nothing in the templates "
        f"reads them from the top level, so they are silently ignored."
    )


def test_meta_block_complete(recipe):
    meta = recipe.fm.get("meta")
    assert isinstance(meta, dict), (
        f"{where(recipe)} has no `meta:` block, or it is not a mapping."
    )
    missing = [f for f in ("rewritten", "proofread", "cooked_before") if f not in meta]
    assert not missing, (
        f"{where(recipe)} `meta:` is missing {missing}. "
        f"All three are booleans and all three must be present — a missing one "
        f"reads as false, which is indistinguishable from a deliberate false."
    )


def test_cooked_before_is_true(recipe):
    """`_food_recipes/` is the published collection (`output: true` in
    _config.yml) — every file in it gets a live URL unconditionally. Helen:
    "I never want to publish anything I haven't tested." A recipe she's
    still collecting but hasn't cooked yet belongs in `_food_drafts/`
    (`output: false`, no URL) until `meta.cooked_before` is genuinely true.
    """
    meta = recipe.fm.get("meta")
    if not isinstance(meta, dict):
        return  # test_meta_block_complete already reports the missing block
    assert meta.get("cooked_before") is True, (
        f"{where(recipe)} has `meta.cooked_before: {meta.get('cooked_before')!r}`. "
        f"Either cook it and flip this to true, or move the file back to "
        f"_food_drafts/ until you have."
    )


def test_serves_xor_makes(recipe):
    has_serves = "serves" in recipe.fm
    has_makes = "makes" in recipe.fm
    assert has_serves != has_makes, (
        f"{where(recipe)} has "
        + ("neither `serves:` nor `makes:`" if not (has_serves or has_makes)
           else "both `serves:` and `makes:`")
        + ".\nUse `makes:` for anything you produce a quantity of (bakes, "
          "confectionery, sauces, base recipes) and `serves:` for dishes you "
          "portion out to people. Exactly one, never both."
    )


def test_method_xor_method_groups(recipe):
    has_flat = "method" in recipe.fm
    has_groups = "method_groups" in recipe.fm
    assert has_flat != has_groups, (
        f"{where(recipe)} has "
        + ("neither `method:` nor `method_groups:`" if not (has_flat or has_groups)
           else "both `method:` and `method_groups:`")
        + ".\nThey are mutually exclusive; the recipe layout renders one or the "
          "other, and having both means the second is silently dropped."
    )


def test_method_groups_have_name_and_steps(recipe):
    """A method_groups entry needs both `name` and a non-empty `steps` --
    neither is a rendering requirement pytest can infer from
    test_method_xor_method_groups above, so a key typo (`step:` singular
    instead of `steps:`) or a missing `name` doesn't error, it just
    silently produces a group with no content. Caught for real on
    garam-masala-powder.md: every group used `step:` with no `name:` at
    all, so recipe.method_steps returned [] even though the file had three
    real steps -- invisible to every prose-scanning test, since there was
    nothing left for them to scan.
    """
    for i, group in enumerate(recipe.fm.get("method_groups") or []):
        assert group.get("name"), (
            f"{where(recipe)} method_groups entry {i} has no `name`."
        )
        assert group.get("steps"), (
            f"{where(recipe)} method_groups entry {i} "
            f"({group.get('name')!r}) has no `steps` -- check for a "
            f"`step:` (singular) typo."
        )


def test_method_produces_actual_steps(recipe):
    """Defense in depth alongside test_method_groups_have_name_and_steps
    above: whatever the specific cause, a recipe that declares `method` or
    `method_groups` but ends up with recipe.method_steps == [] has a real
    content bug that every prose-scanning test (typography, time-word
    abbreviations, ingredient annotation style...) would otherwise
    silently skip rather than fail, since they all iterate method_steps.
    """
    if "method" not in recipe.fm and "method_groups" not in recipe.fm:
        return
    assert recipe.method_steps, (
        f"{where(recipe)} declares method/method_groups but produces zero "
        f"actual steps."
    )


def test_notes_is_a_list(recipe):
    if "notes" not in recipe.fm:
        return
    assert isinstance(recipe.fm["notes"], list), (
        f"{where(recipe)} has `notes:` as a "
        f"{type(recipe.fm['notes']).__name__}, not a list. "
        f"Notes are always a list of separate entries, never one blob — the "
        f"renderer styles each note individually."
    )


def test_note_dicts_have_label_and_text(recipe):
    """GitHub issue #141. Every note is `{label, text}`, both present — the
    bare-string form (allowed since 2026-08-03 so each note box could carry
    a topical label like "Sinking"/"Portion size" instead of every box in
    the Notes grid saying the same static "note") is retired for published
    recipes as of this issue. A bare string, or a dict missing either key,
    renders blank or unlabelled with no error, so this is worth catching
    here rather than by eye. Zero recipes needed fixing when this landed --
    every published note was already `{label, text}`; the bare-string form
    is still deliberately allowed in _food_drafts/ (HANDOVER_v26.md §4/§9),
    which this test never reads.
    """
    for i, note in enumerate(recipe.fm.get("notes") or [], 1):
        assert isinstance(note, dict) and note.get("label") and note.get("text"), (
            f"{where(recipe)} note {i} must be `{{label, text}}`, both "
            f"present, not {note!r}."
        )


def test_method_short_is_a_list(recipe):
    ms = recipe.fm.get("method_short")
    assert isinstance(ms, list), (
        f"{where(recipe)} has `method_short:` as a "
        f"{type(ms).__name__}, not a list. The `has_short` check in index.html "
        f"iterates it, and iterating a bare string yields nothing."
    )


def test_method_short_uses_current_placeholder(recipe):
    ms = recipe.fm.get("method_short") or []
    retired = [s for s in ms if s in ("QQ", "none")]
    assert not retired, (
        f"{where(recipe)} uses retired method_short placeholder(s) {retired}. "
        f'The current convention is a single empty string: method_short: [""]'
    )


def test_ingredient_groups_named_when_there_is_more_than_one(recipe):
    groups = recipe.fm.get("ingredient_groups") or []
    if len(groups) < 2:
        return
    unnamed = [i for i, g in enumerate(groups) if not (isinstance(g, dict) and g.get("name"))]
    assert not unnamed, (
        f"{where(recipe)} has {len(groups)} ingredient groups but group(s) "
        f"{unnamed} have no `name:`. With more than one group every group needs "
        f"a name, or the reader gets an unlabelled block followed by labelled ones."
    )


def test_group_names_omit_leading_article(recipe):
    """Group names are bare nouns: `buttercream`, not `for the buttercream`.

    The recipe template renders ingredient group headings as "For the {name}:",
    so a name that already carries the article comes out as "For the for the
    dressing:" or "For the the icing:". Method groups render the name bare, so
    a leading article reads oddly there too.
    """
    offenders = []
    for key in ("ingredient_groups", "method_groups"):
        for group in recipe.fm.get(key) or []:
            name = group.get("name") if isinstance(group, dict) else None
            if name and re.match(r"^(for the |for |the )", name, re.I):
                offenders.append(f"{key}: {name!r}")
    assert not offenders, (
        f"{where(recipe)} has group name(s) with a leading article: {offenders}.\n"
        f'The template supplies "For the " itself, so `for the dressing` renders '
        f'as "For the for the dressing:". Strip the article — `dressing`.'
    )
