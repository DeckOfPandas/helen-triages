"""Structural rules: what a recipe file must contain, and what it must not.

These come from HANDOVER section 7. Each one asserts a single rule so that a
failure tells you exactly which rule broke, on which file.
"""
from __future__ import annotations

import re

import pytest
import yaml

from conftest import where

# Suite marker, so `pytest -m food` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.food

# `source_type` joined this list on 2026-08-20 (issue #406). It is not
# decoration: nothing in a source STRING says whether it is a magazine or a
# book -- `Adapted from Good Food` and `Adapted from Gordon Ramsay's Ultimate
# Cookery Course` are the same shape -- so every rule in
# tests/test_source_attribution.py reads the type rather than guessing. A recipe
# without one is a recipe none of those rules can judge, which is worse than a
# recipe that breaks them.
REQUIRED = ["title", "tagline", "source", "source_type", "main_ingredients",
            "tags", "ingredient_groups", "method_short", "meta"]

RETIRED = {
    "published": "removed from the schema",
    "date_added": "renamed to meta.date_last_edited",
    "difficulty": "removed from the schema",
    "nutrition": "removed from the schema",
    "filling_note": "folded into notes:",
    "headline_ingredient": "renamed to star_ingredient",
    "short_name": "removed from the schema, GitHub issue #169 -- confirmed "
                  "zero references in any template/JS/SCSS before removal, "
                  "2026-08-12; a leftover value is dead weight, not data",
}

MISPLACED_META = ["rewritten", "proofread", "cooked_before", "date_last_edited",
                   "claude_rewritten"]


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


def test_doneness_names_a_real_level(recipe, internal_temperatures):
    """`doneness` has to name a level the resolved node actually offers, and the
    node has to be one that offers levels at all.

    Both failures are silent in Liquid. A typo'd level resolves to nothing, so
    the meta line renders its label and its link with no figure between them;
    and `doneness` on a single-figure node (poultry, a tough cut) does nothing
    while looking like it configures something.

    This became worth testing when issue #189's doneness chart landed: the front
    matter now drives which row is marked as the recipe's own suggestion, so a
    wrong level means a chart that recommends nothing, with no error anywhere.
    """
    ref, level = recipe.fm.get("internal_temp_ref"), recipe.fm.get("doneness")
    if not ref or not level:
        return

    node = internal_temperatures
    for key in ref.split("."):
        node = node.get(key) if isinstance(node, dict) else None
    if node is None:
        return                      # test_internal_temp_ref_resolves owns this

    assert "doneness" in node, (
        f"{where(recipe)} sets `doneness: {level}`, but {ref} has no doneness "
        f"levels — it is a single figure, so there is nothing to choose."
    )
    assert level in node["doneness"], (
        f"{where(recipe)} sets `doneness: {level}`, which {ref} doesn't offer. "
        f"It has: {sorted(node['doneness'])}"
    )


def test_internal_temp_ref_resolves(recipe, internal_temperatures):
    """`internal_temp_ref` (+ optional `doneness`) must resolve to a real

    path in _data/food/internal_temperatures.yml. _layouts/recipe.html
    resolves this the same way, dot-segment by dot-segment, via Liquid's
    `hash[variable]` lookup — Liquid has no equivalent of this assertion, so
    a typo'd path there doesn't error, it just silently renders no "Internal
    temp" line at all. This is the only thing that would ever catch that.
    """
    ref = recipe.fm.get("internal_temp_ref")
    doneness = recipe.fm.get("doneness")

    if ref is None:
        assert doneness is None, (
            f"{where(recipe)} sets `doneness: {doneness!r}` with no "
            f"`internal_temp_ref:` to apply it to — it does nothing on its own."
        )
        return

    node = internal_temperatures
    walked = []
    for key in ref.split("."):
        walked.append(key)
        assert isinstance(node, dict) and key in node, (
            f"{where(recipe)} has `internal_temp_ref: {ref}`, but "
            f"{'.'.join(walked)} doesn't exist in "
            f"_data/food/internal_temperatures.yml."
        )
        node = node[key]

    if doneness is not None:
        assert isinstance(node, dict) and "doneness" in node, (
            f"{where(recipe)} sets `doneness: {doneness!r}`, but "
            f"internal_temp_ref: {ref} has no `doneness` map in "
            f"_data/food/internal_temperatures.yml -- that entry uses a "
            f"different shape (endpoint/target/tender_at), which doesn't "
            f"take a doneness level."
        )
        assert doneness in node["doneness"], (
            f"{where(recipe)} has `doneness: {doneness!r}`, which isn't one "
            f"of {sorted(node['doneness'].keys())} under "
            f"internal_temp_ref: {ref} in "
            f"_data/food/internal_temperatures.yml."
        )


# --- duplicate YAML keys are silent data loss ------------------------------

class _StrictLoader(yaml.SafeLoader):
    """A SafeLoader that refuses to quietly discard a repeated key."""


def _no_duplicates(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates
)


def test_front_matter_has_no_duplicate_keys(recipe):
    """A repeated key in a YAML mapping is DISCARDED, silently, last one wins.

    Found for real 2026-08-16 in indonesian-chicken-curry-gulai-ayam.md, which
    had an ingredient entry declaring `item:` twice:

        - amount: "200 ml"
        - item: "flavourings to taste, like chicken stock cubes, fish sauce..."
          item: coconut cream

    The flavourings line was gone -- not just from the derived ingredient index
    that surfaced it, but from the recipe page itself, for as long as it had
    been there. Nothing could see it: the file parses, the build succeeds, the
    page renders, and every other test in this suite reads the PARSED front
    matter, which by then is missing the line entirely. The only symptom is an
    ingredient that isn't there, on a page nobody re-reads once it is written.

    yaml.safe_load accepts duplicates by specification, so catching this needs
    a loader that refuses them. That is the whole test.
    """
    match = re.match(r"\A---\n(.*?\n)---", recipe.raw, re.S)
    try:
        yaml.load(match.group(1), Loader=_StrictLoader)
    except yaml.constructor.ConstructorError as exc:
        raise AssertionError(
            f"{where(recipe)} has a duplicate key in its front matter: {exc}.\n"
            f"YAML keeps only the last one, so whatever the earlier line said "
            f"has already been thrown away -- check what is missing from the "
            f"rendered page, not just what looks wrong in the file."
        ) from None


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


def test_claude_rewritten_is_a_real_boolean(recipe):
    """`meta.claude_rewritten` is optional and additive (issue #418) -- most
    files won't have it, and that's fine, unlike `rewritten`/`proofread`/
    `cooked_before` this doesn't gate anything today. But a quoted "true"
    would be the same silent trap `awaiting_fix` already had, so it's worth
    catching before anything ever comes to depend on the value being a real
    bool rather than a truthy string.
    """
    meta = recipe.fm.get("meta")
    if not isinstance(meta, dict) or "claude_rewritten" not in meta:
        return
    assert isinstance(meta["claude_rewritten"], bool), (
        f"{where(recipe)} has `meta.claude_rewritten: {meta['claude_rewritten']!r}`, "
        f"not a real boolean. Never quote it."
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


# --- scalar front-matter values are always double-quoted --------------------
# GitHub issue #168, open, picked up 2026-08-12 -- the broader sibling of
# #170 (main_ingredients specifically, test_taxonomy.py) and applied to
# tags there too. Same Sublime-editing convenience, same "formatting, not
# data" safety -- EXCEPT this is deliberately NOT "every value in the
# file": `meta:` booleans are excluded on purpose. Quoting `rewritten: true`
# would silently turn it into the STRING "true", and
# `meta.get("cooked_before") is True` (test_cooked_before_is_true, this
# file) would then read False for every recipe -- checked against the
# actual test code before touching a single meta value, not assumed safe.
# 284 unquoted scalars across 76 recipes fixed 2026-08-12 via a line-by-line
# raw-text substitution restricted to these nine top-level scalar fields
# specifically -- not a YAML dump (CLAUDE.md), and not the nested list/dict
# fields (ingredient items, method steps, notes), which is a larger, separate
# piece of work than this pass covers.
SCALAR_STRING_FIELDS = ["title", "tagline", "source", "prep_time",
                         "cook_time", "star_ingredient", "makes", "serves"]


def test_scalar_fields_are_quoted(recipe):
    match = re.match(r"\A---\n(.*?\n)---", recipe.raw, re.S)
    fm_text = match.group(1)
    bad = []
    for field in SCALAR_STRING_FIELDS:
        m = re.search(rf"^{field}:[ \t]*(.+)$", fm_text, re.M)
        if not m:
            continue
        val = m.group(1).rstrip()
        if val.startswith("[") or val.startswith("{"):
            continue  # a flow sequence/mapping, not a bare scalar
        if not (val.startswith('"') and val.endswith('"')):
            bad.append(f"{field}: {val}")
    assert not bad, (
        f"{where(recipe)} has unquoted scalar front-matter value(s): {bad!r}. "
        f'Wrap each in double quotes, e.g. title: "Beef Wellington".'
    )


# =============================================================================
# PROVENANCE: IF AN AGENT WAS LAST TO TOUCH A RECIPE, IT IS NOT PROOFREAD.
# GitHub issue #367.
# =============================================================================
# Helen is the last human judgement before a recipe publishes. If Claude edited
# a file after she blessed it, the blessing no longer covers what is in the
# file -- so `meta.proofread` must go back to false in the same commit that
# made the edit.
#
# WHY THIS IS A TEST AND NOT ONLY A WRITTEN RULE. A written rule works when the
# agent reads and follows it, which is precisely what failed on 2026-08-18:
# twelve proofread recipes were edited without their flags being touched, and
# nothing anywhere noticed. The flag is the gate the whole publish decision
# hangs off (#331), so it cannot depend on good intentions.
#
# GRANDFATHERED, ON PURPOSE. Everything up to and including the baseline commit
# below is exempt. Helen's call, 2026-08-18: those 34 recipes include the 45
# second-person changes she reviewed one at a time and decided personally, so
# she WAS the last judgement even though an agent's commit wrote the bytes.
# Flipping them would mean re-proofreading work she had just finished. The rule
# applies from the baseline forward.
#
# Ancestry, not dates, decides what is grandfathered -- a rebase rewrites dates
# but not the shape of history.
import pathlib
import subprocess

from conftest import FRONT_MATTER, DRAFTS_PRESENT, ALL_DRAFTS

ROOT = pathlib.Path(__file__).resolve().parent.parent

BASELINE_COMMIT = "9306cef"   # (copy) Helen's proofread of the citation backlog
#
# MOVED 2026-08-20 (second move that day), AND THIS IS THE CASE THE MECHANISM
# WAS BUILT FOR -- the one the failure message describes as "reviewed by Helen
# line by line". She was not told a summary and asked to bless it. She asked to
# be taken through the backlog one recipe at a time, was shown the old line, the
# new line and the reason for each, and answered each individually. Two she
# changed rather than approved. So her proofread describes those files more
# exactly than it describes most of the corpus.
#
# COST, MEASURED BEFORE MOVING, as the entry below insists: the number of
# recipes correctly sitting at proofread:false that this move would release is
# ZERO. The backlog is empty because she just emptied it. The 72 other recipes
# whose newest commit is an agent's are held by INVISIBLE_KEYS instead, not by
# the baseline, and that stays true after the move -- so this does not quietly
# take over their protection either.
#
# The previous entry, kept because its reasoning is the precedent:
#
#   366f392 -- moved 2026-08-20, with Helen's explicit permission, given IN
#   ADVANCE and unprompted: she specified the change and then said, of it, "I
#   trust you to make that change without making others, so no need to flip the
#   proofread flag again." She was the author of that edit in every sense that
#   mattered; the agent only typed it.
#
# WHAT THE MOVE ACTUALLY COVERS, measured rather than assumed. Before moving it,
# the question "which recipes is this rule currently holding to proofread:false?"
# was put to git, and the answer was NONE -- Helen's own c07104a had just
# re-proofread the backlog of eight and set them back to true. So sliding the
# baseline from 9c70675 to 366f392 stops checking exactly nothing. That is the
# check to run before ever touching this line, and the reason the move is
# defensible today when the identical move last week would not have been: a
# baseline says "everything at or before here predates the rule", and moving it
# over recipes that ARE being held quietly asserts something false about all of
# them.
#
# The previous entry, kept because the reasoning is the precedent:
#
#   9c70675 -- moved 2026-08-18, with Helen's explicit permission, asked for
#   before the commit rather than after. The awaiting_fix rename touched all 82
#   recipes, so every one of them has an agent commit as its newest -- and this
#   rule would have demanded proofread: false on all 82.
#
#   That would have been the letter of the rule against its purpose. It exists
#   so her proofread never describes a file she has not read. A key name changing
#   from hyphen to underscore changes no word of any recipe, so her proofread
#   still describes every one of them exactly.
#
# The one before that was dc2a7bf, moved for the same kind of reason: 45
# second-person edits she reviewed one at a time.
#
# ORDERING MATTERS AND IS EASY TO GET BACKWARDS. Move the baseline BEFORE making
# the next batch of agent edits, never after: a baseline moved afterwards sweeps
# those edits up too, which is the exact accident this comment block exists to
# prevent. The citation work of #406 lands after 366f392 for that reason, and is
# still held to proofread: false like anything else.
#
# NEVER MOVE THIS TO MAKE A RED TEST GREEN. It is Helen's to grant, and the
# question to put to her is whether she has read what is now in the files --
# not whether the change felt small.
AGENT_TRAILER = "co-authored-by: claude"

# RECIPES HELEN HAS CLEARED ONE AT A TIME, when the baseline is the wrong tool.
#
# The baseline is a blunt instrument: it grandfathers EVERYTHING at or before a
# commit. That is right when the change was sweeping and content-free (a key
# rename across all 82). It is wrong when a single recipe needs clearing and
# other recipes are being held on purpose -- sliding the baseline forward to
# reach the one would quietly release the others too.
#
# That case arrived on 2026-08-20. Helen asked for slow-cooked-duck-legs-confit
# to go back to proofread: true ("this is an exception"), and the same commit
# had to keep holding beef-wellington and indian-mutton-raan-roast at false,
# because an agent had just rewritten their citation lines. One baseline cannot
# express both. So: name the file, and leave the baseline alone.
#
# THIS HAS THE SAME WEAKNESS AS THE BASELINE and it is worth saying plainly --
# an agent can add an entry here to turn a red test green, exactly as it could
# move a SHA. What makes it better is legibility, not security: a diff that adds
# a filename, a date and a sentence of reason is something Helen can review at a
# glance, where a forty-character SHA changing is not. The protection is her
# eyes on the diff, so make the entry easy to read and never add one she has not
# asked for in words.
HELEN_CLEARED: dict[str, str] = {
    "_food_recipes/slow-cooked-duck-legs-confit.md":
        "2026-08-20 -- the last of the eight-recipe backlog she re-proofread in "
        "c07104a. She cleared the other seven in her own commit and this one by "
        "instruction: 'Duck legs confit can go back to true, please, this is an "
        "exception.'",

    # --- the en-dash pass, 2026-08-21 (issue #413) ---------------------------
    #
    # THIRTEEN ENTRIES FROM ONE SESSION, WHICH IS WORTH EXPLAINING, because a
    # block this size is exactly the shape of an agent quietly clearing its own
    # work. It is not. Helen asked to see the lines individually -- "Show me the
    # lines here one by one, then I can't miss anything, and we can agree
    # together. This means the proofread flag can stay true." -- and then read
    # and confirmed all fourteen, one message at a time, before any edit was
    # made. She was the last judgement on every one of them.
    #
    # WHY NOT MOVE THE BASELINE. It would have been one line instead of
    # thirteen, and it would have been wrong: a baseline grandfathers
    # EVERYTHING at or before a commit, and the citation work of #406 is sitting
    # behind this point being held at proofread: false on purpose. Sliding past
    # it to reach these thirteen would have released those too, silently. That
    # is the case HELEN_CLEARED exists for.
    #
    # WHAT SHE ACTUALLY APPROVED, so this is checkable rather than asserted: one
    # ASCII hyphen became an en dash in a number range, on one line per file
    # (two in roast-beef-fillet). No word changed, in any file. The full list
    # with line numbers is in the commit message.
    #
    # Her ruling on the one that was not prose, cauliflower-cheese's cook_time
    # metadata field: "These still render to the user, so correct to en dash
    # please." The test that followed is scoped by that principle -- what a
    # reader sees -- rather than by whether a field is prose.
    "_food_recipes/beef-wellington.md":
        "2026-08-21 -- en-dash pass, `30-60 seconds` in a method step.",
    "_food_recipes/ben-jerrys-sweet-cream-base-1.md":
        "2026-08-21 -- en-dash pass, `36-40% fat` in an ingredient note.",
    "_food_recipes/ben-jerrys-sweet-cream-base-2.md":
        "2026-08-21 -- en-dash pass, `36-40% fat` in an ingredient note.",
    "_food_recipes/cauliflower-cheese.md":
        "2026-08-21 -- en-dash pass, `20-25 mins` in the cook_time field.",
    "_food_recipes/duck-leg-barley-casserole.md":
        "2026-08-21 -- en-dash pass, `6-9` in an ingredient amount.",
    "_food_recipes/goats-cheese-squash-rosemary-griddle-cakes.md":
        "2026-08-21 -- en-dash pass, `3-4 mins` in a method step.",
    "_food_recipes/indonesian-chicken-curry-gulai-ayam.md":
        "2026-08-21 -- en-dash pass, `12-15 passes` in an ingredient note.",
    "_food_recipes/lemon-meringue-pie.md":
        "2026-08-21 -- en-dash pass, `15-20 mins` in a method step note.",
    "_food_recipes/macarons.md":
        "2026-08-21 -- en-dash pass, `130-140°C` in a method step.",
    "_food_recipes/miso-salmon-veg-traybake.md":
        "2026-08-21 -- en-dash pass, `11-14 mins` in a method step.",
    "_food_recipes/peanut-butter-cookies.md":
        "2026-08-21 -- en-dash pass, `8-12 mins` in a method step.",
    "_food_recipes/roast-beef-fillet.md":
        "2026-08-21 -- en-dash pass, `170-180°C` in two method steps.",
    "_food_recipes/sweet-shortcrust-pastry-mince-pies.md":
        "2026-08-21 -- en-dash pass, `15-20 mins` in a method step.",
}


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          cwd=ROOT).stdout


# =============================================================================
# KEYS THAT CHANGE NOTHING HELEN READS — the general answer, Helen 2026-08-20
# =============================================================================
# "Adding source_type to every recipe doesn't change how they render, so no need
# to flip the proofread flag. Does this sound reasonable? Can we allow for this
# formally so we don't keep asking the same question?"
#
# It is reasonable, and it is a better statement of the rule than the one it
# replaces. Her proofread is of the WORDS ON THE PAGE. An agent editing a recipe
# invalidates it because the words changed -- not because bytes changed. A front
# matter key that no template, plugin or script ever reads renders nothing, so
# the page she proofread is the page that is still there.
#
# This is the same reasoning that moved BASELINE_COMMIT to 9c70675 for the
# awaiting_fix rename; the difference is that this does it by rule instead of by
# asking her again each time, which is what she asked for.
#
# WHY THIS IS NOT THE USUAL "AN AGENT CAN JUST ADD AN ENTRY" HOLE. HELEN_CLEARED
# above is protected only by being legible -- nothing can check whether she
# really cleared a recipe. This list is different: the claim "no template reads
# this key" is a FACT ABOUT THE REPOSITORY, and
# test_invisible_keys_are_really_invisible checks it. A key cannot be added here
# unless it is genuinely unread, and the day someone starts rendering one, that
# test goes red and the entry has to come out. The guard is mechanical, not
# social.
#
# WHAT IT DELIBERATELY DOES NOT COVER: the body text, and any key that IS read.
# A commit qualifies only if every single difference between the two versions of
# the file is confined to these keys and the body is byte-identical. Change one
# word of a method in the same commit and the whole exemption is off.
RENDER_SURFACE = ("_layouts", "_includes", "_plugins", "assets/js", "scripts")

INVISIBLE_KEYS = {
    "source_type": (
        "Classifies a citation (publication / book / website / person / place / "
        "unknown) so the source-shape tests can tell a dateless magazine from a "
        "finished book citation -- `Adapted from Good Food` and `Adapted from "
        "Gordon Ramsay's Ultimate Cookery Course` are the same string shape and "
        "no regex separates them. Read by tests only. Issue #406."
    ),
    "meta.rewritten": (
        "Records that Helen has rewritten the source's wording in her own words, "
        "rather than the draft still carrying the original text. Read by nothing "
        "that builds a page -- the index badge and the publish gate hang off "
        "meta.awaiting_fix and meta.proofread, not this. Listable only since the "
        "scanner below learned to ignore comments: the sole match on the render "
        "surface is an English sentence in assets/js/ingredient-search.js about "
        "ingredient text being rewritten, which has nothing to do with the key. "
        "Issues #418, #428."
    ),
}

# ---------------------------------------------------------------------------
# STRIPPING COMMENTS BEFORE MATCHING. Issue #428.
#
# The scan below used to be `grep -rlw <key>` over RENDER_SURFACE. A word-grep
# cannot tell code from prose, so a key whose name is an ordinary English word
# was reported as rendered the moment anyone used that word in a comment. That
# is what kept `meta.rewritten` off the list above: one comment in
# ingredient-search.js, about ingredient text, not about the key.
#
# THIS IS THE FOURTH TIME PROSE HAS DEFEATED A SOURCE-SCANNING GUARD here
# (HANDOVER §12), and the escalation was already written down after the third:
# strip comments before matching, or parse rather than grep.
#
# STRINGS ARE DELIBERATELY KEPT. The obvious companion move -- strip string
# literals too -- would be a bug, because a string literal is exactly how a key
# gets read: `page["source_type"]`, `data['meta']['rewritten']`. Stripping them
# would turn a real read into a silent miss, which is the one direction this
# guard must never fail in. So strings are tracked (a scanner that did not track
# them would see the `//` in "https://..." as a comment and eat the rest of the
# line, which fails the same dangerous way) but their contents are preserved.
#
# WHAT IT DOES NOT DO: it is not a parser. Liquid comments and HTML comments are
# matched as blocks; a `<!--` inside a Liquid string would confuse it. That has
# never happened, and the 90% is what the previous three instances all needed.
LINE_COMMENT = {".js": "//", ".py": "#", ".rb": "#"}
BLOCK_COMMENT = {".js": ("/*", "*/")}
QUOTES = {".js": "\"'`", ".py": "\"'", ".rb": "\"'"}
LIQUID_COMMENT = re.compile(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}",
                            re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _strip_comments(text, suffix):
    """`text` with its comments blanked out, keeping string literals intact."""
    if suffix in (".html", ".svg", ".md", ".xml"):
        return HTML_COMMENT.sub(" ", LIQUID_COMMENT.sub(" ", text))
    if suffix not in LINE_COMMENT:
        return text

    line, block, quotes = LINE_COMMENT[suffix], BLOCK_COMMENT.get(suffix), QUOTES[suffix]
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in quotes:                     # a string: copy it out verbatim
            out.append(ch)
            i += 1
            while i < n and text[i] != ch:
                if text[i] == "\\":
                    out.append(text[i])
                    i += 1
                    if i >= n:
                        break
                out.append(text[i])
                i += 1
            if i < n:
                out.append(text[i])
                i += 1
        elif text.startswith(line, i):
            i = text.find("\n", i)
            if i == -1:
                break
        elif block and text.startswith(block[0], i):
            end = text.find(block[1], i + len(block[0]))
            i = n if end == -1 else end + len(block[1])
            out.append(" ")
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _render_surface_reads(key):
    """Files on the render surface whose CODE (not comments) names `key`.

    A dotted key is checked by its last segment: `meta.rewritten` is written
    `page.meta.rewritten` in Liquid but reached as `["meta"]["rewritten"]`
    elsewhere, and the leading `meta` is shared by every key under it.
    """
    word = re.compile(r"\b" + re.escape(key.rsplit(".", 1)[-1]) + r"\b")
    hits = []
    for root in RENDER_SURFACE:
        for path in sorted((ROOT / root).rglob("*")):
            if not path.is_file() or path.suffix == ".pyc":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if word.search(_strip_comments(text, path.suffix)):
                hits.append(path.relative_to(ROOT).as_posix())
    return hits


def test_invisible_keys_are_really_invisible():
    """Every key in INVISIBLE_KEYS is read by nothing that builds a page.

    This is the check that makes the exemption safe rather than merely stated.
    If a key on this list is ever rendered, the recipes carrying it stopped
    being unchanged-as-far-as-Helen-is-concerned, and the entry must go.
    """
    rendered = {}
    for key in sorted(INVISIBLE_KEYS):
        hits = _render_surface_reads(key)
        if hits:
            rendered[key] = hits

    assert not rendered, (
        "INVISIBLE_KEYS names front matter key(s) that something actually "
        "reads:\n  "
        + "\n  ".join(f"{k}: {', '.join(v)}" for k, v in rendered.items())
        + "\n\nThe whole basis for exempting these from the proofread rule is "
          "that they render nothing, so a recipe carrying one shows Helen "
          "exactly what she proofread. Once a key is rendered that is false. "
          "Remove it from the list -- do not narrow this test."
    )


# The guard above is only as good as its scanner, and the scanner is the part
# that has now been wrong four times. So the scanner gets tested too, on both
# sides: prose must not register as a read, and a real read must not be lost.
# The second half is the one that matters -- a false negative here would let a
# genuinely rendered key sit on INVISIBLE_KEYS unnoticed. Issue #428.
SCANNER_CASES = [
    (".js", "// main_ingredients text is rewritten in the include", False),
    (".js", "/* rewritten\n   across lines */", False),
    (".js", "const x = 1; // rewritten", False),
    (".js", 'fetch("https://example.com/a"); const y = r.rewritten;', True),
    (".js", 'if (item["rewritten"]) render();', True),
    (".js", 'const s = "not a // comment: rewritten";', True),
    (".py", "# rewritten, but only in a comment", False),
    (".py", 'KEYS = ["rewritten"]', True),
    (".py", '"""A docstring mentioning rewritten."""', True),
    (".rb", "# rewritten in prose", False),
    (".rb", 'data.fetch("rewritten")', True),
    (".html", "{% comment %} rewritten {% endcomment %}", False),
    (".html", "{%- comment -%} rewritten {%- endcomment -%}", False),
    (".html", "<!-- rewritten -->", False),
    (".html", "{% if page.meta.rewritten %}yes{% endif %}", True),
    (".svg", "<!-- rewritten --><title>x</title>", False),
]


@pytest.mark.parametrize("suffix,source,is_read", SCANNER_CASES,
                         ids=[f"{s[1:]}:{t[:38]}" for s, t, _ in SCANNER_CASES])
def test_the_invisible_keys_scanner_tells_code_from_prose(suffix, source, is_read):
    found = re.search(r"\brewritten\b", _strip_comments(source, suffix)) is not None
    assert found is is_read, (
        f"_strip_comments({suffix}) got this backwards:\n    {source!r}\n"
        + ("The key is genuinely read here and the scanner lost it -- a false "
           "negative lets a rendered key sit on INVISIBLE_KEYS unnoticed, which "
           "is the failure this whole mechanism exists to prevent."
           if is_read else
           "That is prose, not a read. Over-reporting is why meta.rewritten "
           "could not be listed before #428.")
    )


# A docstring in .py is a string literal, and strings are kept on purpose -- so
# the case above passes for the right reason but for the WRONG kind of file. A
# Python docstring really is prose. It is left alone because telling a docstring
# from `KEYS = ["rewritten"]` needs the AST, and no key on INVISIBLE_KEYS has
# ever collided with one. If that day comes, the fix is ast.parse, not a regex.


def _file_at(commit, relpath):
    """(front matter mapping, body) for `relpath` at `commit`, or None."""
    result = subprocess.run(["git", "show", f"{commit}:{relpath}"],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    match = FRONT_MATTER.match(result.stdout)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None
    return data, result.stdout[match.end():]


def _only_invisible_keys_changed(commit, relpath):
    """True if this commit touched `relpath` ONLY in keys that render nothing.

    Compares the whole file against its state in the parent commit: every key
    whose value differs must be in INVISIBLE_KEYS, and the body must be
    identical. Anything it cannot read confidently -- a new file, a merge,
    unparseable YAML -- returns False, so the proofread rule still applies.
    """
    after = _file_at(commit, relpath)
    before = _file_at(f"{commit}^", relpath)
    if after is None or before is None:
        return False                      # new file, or nothing to compare with

    (new_data, new_body), (old_data, old_body) = after, before
    if new_body != old_body:
        return False                      # the prose moved; nothing else matters

    changed = {k for k in set(new_data) | set(old_data)
               if new_data.get(k, object()) != old_data.get(k, object())}

    # meta is a nested mapping, so compare it key by key rather than wholesale --
    # otherwise a change to any key under it reads as "meta changed", which no
    # entry in INVISIBLE_KEYS can ever match.
    #
    # EXPANDED UNCONDITIONALLY since 2026-08-21. This used to run only when meta
    # was the SOLE difference, so a commit that set source_type AND flipped
    # meta.rewritten fell through to the flat comparison, saw a bare "meta", and
    # said no. That failed in the safe direction, but for the wrong reason: it
    # was a gap in the comparison, not a judgement about the keys.
    if "meta" in changed:
        new_meta = new_data.get("meta") if isinstance(new_data.get("meta"), dict) else {}
        old_meta = old_data.get("meta") if isinstance(old_data.get("meta"), dict) else {}
        changed.discard("meta")
        changed |= {f"meta.{k}" for k in set(new_meta) | set(old_meta)
                    if new_meta.get(k, object()) != old_meta.get(k, object())}

    # Keys are compared by their FULL DOTTED NAME. INVISIBLE_KEYS lists
    # `meta.rewritten`, not `rewritten`, because the two are different keys and a
    # top-level one must not be exempted by its namesake under meta.
    return bool(changed) and changed <= set(INVISIBLE_KEYS)


def _rewritten_at(repo, rev, relpath):
    """`meta.rewritten` for a file at a revision, or None if unreadable."""
    result = subprocess.run(["git", "show", f"{rev}:{relpath}"],
                            cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    match = FRONT_MATTER.match(result.stdout)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None
    return (data.get("meta") or {}).get("rewritten")


def _agent_claimed_rewrites(repo, pathspec):
    """Commits where an agent flipped `meta.rewritten` from false to true.

    Narrowed with `-G` before doing any real work: only commits whose DIFF
    touches a `rewritten:` line are candidates, so this stays a handful of
    `git show` calls rather than a walk of the whole history.
    """
    shas = subprocess.run(
        ["git", "log", "--format=%H", f"--grep={AGENT_TRAILER}", "-i",
         "-G", r"rewritten:", "--", pathspec],
        cwd=repo, capture_output=True, text=True,
    ).stdout.split()

    offenders = []
    for sha in shas:
        files = subprocess.run(
            ["git", "show", "--name-only", "--format=", sha, "--", pathspec],
            cwd=repo, capture_output=True, text=True,
        ).stdout.split()
        for relpath in files:
            if not relpath.endswith(".md"):
                continue
            before = _rewritten_at(repo, f"{sha}^", relpath)
            after = _rewritten_at(repo, sha, relpath)
            if before is False and after is True:
                offenders.append(f"{sha[:8]}  {relpath}")
    return offenders


def test_no_agent_commit_claims_helens_rewrite():
    """`meta.rewritten` is Helen's claim. An agent must never set it true.

    THE HOLE THIS CLOSES. `meta.claude_rewritten` was added (issue #418) exactly
    so an assisted tidy-up pass -- main_ingredients, ingredient and method
    groups, wording nudged toward her voice -- could be recorded WITHOUT being
    mistaken for Helen's own rewrite. `meta.rewritten` stays the real claim:
    that the prose is genuinely hers.

    Nothing enforced that separation. The tests checked `rewritten` exists and
    is nested under `meta:`, and nothing checked who set it or what it changed
    from. A tidy-up pass could have set it true and the only thing that would
    have caught it was Helen reading the diff. That is a documented convention
    with nothing behind it, which in this repository has a perfect record of
    eventually being broken -- see the destructive-git rule, `awaiting_fix`,
    `proofread`, and the citation spec, all documented at length before anything
    checked them.

    Zero violations existed when this was written, in either repository. It is a
    regression guard, not a backlog.

    WHAT IT DELIBERATELY DOES NOT CATCH, said plainly rather than left to be
    found: a file CREATED by an agent already saying `rewritten: true`. Only a
    false-to-true transition is flagged, because `before` is also None for an
    ordinary rename or a promotion moving a file between collections, and
    failing those would be a false positive on Helen's own normal workflow.
    Narrow and correct beats broad and noisy -- but it does mean a brand-new
    file is on trust.

    BOTH REPOSITORIES, because the drafts are where the risk actually lives:
    tidy-up passes happen on drafts, and 15 of them already say true.
    `_food_drafts/` is a separate private repo with its own history, so it is
    asked separately.

    WHAT A GREEN RUN IN CI MEANS, and it is less than it looks: `_food_drafts/`
    is absent there (issue #378), so CI checks the 82 published recipes and NONE
    of the 314 drafts. This does not skip, because the published half is the
    half that ships and losing it to be honest about the other half would be a
    bad trade -- but the half that matters most is the one CI cannot see. Run
    the suite locally before believing this check has passed. Registered in
    tests/test_suite_hygiene.py's PARTIAL_IN_CI for exactly this reason.
    """
    assert (ROOT / ".git").exists(), "Not a git checkout -- this test cannot run."

    offenders = _agent_claimed_rewrites(ROOT, "_food_recipes/")

    drafts = ROOT / "_food_drafts"
    # Named so tests/test_suite_hygiene.py's registry can see this test reads
    # drafts at all -- it generates its list from ALL_DRAFTS references, and a
    # test reaching drafts by path alone would be invisible to it. That gap is
    # called out in its own docstring; this opts in rather than widening it.
    if DRAFTS_PRESENT and ALL_DRAFTS and (drafts / ".git").exists():
        offenders += [f"_food_drafts/  {line}"
                      for line in _agent_claimed_rewrites(drafts, ".")]

    assert not offenders, (
        "An agent commit set `meta.rewritten: true`, which is Helen's claim "
        "and hers alone:\n  "
        + "\n  ".join(offenders)
        + "\n\n`meta.rewritten` means the prose is genuinely in her voice. An "
          "assisted pass records itself with `meta.claude_rewritten: true` and "
          "leaves `rewritten` alone -- tidying structure and wording is not the "
          "same thing as her rewriting a step (issue #418). If she asked for "
          "this herself, the commit is hers to make, not an agent's."
    )


def test_every_cleared_recipe_still_exists():
    """A HELEN_CLEARED entry naming a file that is gone is a silent hole.

    Renaming a recipe would leave its clearance behind, pointing at nothing --
    and then the new name is held to the rule again with no sign that it was
    ever cleared, or worse, a future recipe reusing the old slug inherits a
    clearance nobody granted it. Cheap to check, so check it.
    """
    missing = sorted(p for p in HELEN_CLEARED if not (ROOT / p).exists())
    assert not missing, (
        "HELEN_CLEARED names recipe(s) that no longer exist:\n  "
        + "\n  ".join(missing)
        + "\n\nIf one was renamed, move its entry to the new path and keep the "
          "reason. If it was deleted, delete the entry -- do not leave it to be "
          "inherited by whatever takes the slug next."
    )


def test_agent_edited_recipes_are_not_marked_proofread():
    """A recipe whose newest commit is an agent's must have proofread: false."""
    assert (ROOT / ".git").exists(), "Not a git checkout -- this test cannot run."
    assert "true" not in _git("rev-parse", "--is-shallow-repository").lower(), (
        "This is a SHALLOW clone, so `git log` cannot see who last touched each "
        "recipe and this test would silently check almost nothing. Fetch full "
        "history (actions/checkout needs `fetch-depth: 0`)."
    )

    # Newest commit per recipe, in one pass.
    last: dict[str, str] = {}
    sha = None
    for line in _git("log", "--format=%H", "--name-only", "--", "_food_recipes/").splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
            sha = line
        elif line.endswith(".md"):
            last.setdefault(line, sha)

    assert last, (
        "No recipe history found at all. This test would pass while checking "
        "nothing, which is the failure mode tests/test_suite_hygiene.py exists "
        "to prevent."
    )

    base = BASELINE_COMMIT
    agent_commit: dict[str, bool] = {}
    offenders, checked = [], 0

    for relpath, commit in sorted(last.items()):
        path = ROOT / relpath
        if not path.exists():
            continue                                  # renamed or deleted since
        # Grandfathered: at or before the baseline.
        if subprocess.run(["git", "merge-base", "--is-ancestor", commit, base],
                          cwd=ROOT, capture_output=True).returncode == 0:
            continue
        if relpath in HELEN_CLEARED:
            continue                                  # cleared by name, see above
        if _only_invisible_keys_changed(commit, relpath):
            continue                                  # renders nothing; see above
        if commit not in agent_commit:
            body = _git("show", "-s", "--format=%B", commit).lower()
            agent_commit[commit] = AGENT_TRAILER in body
        if not agent_commit[commit]:
            continue                                  # Helen's own commit
        checked += 1
        raw = path.read_text(encoding="utf-8")
        match = FRONT_MATTER.match(raw)
        meta = (yaml.safe_load(match.group(1)) or {}).get("meta", {}) or {}
        if meta.get("proofread") is not False:
            offenders.append(f"{relpath} (last touched by {commit[:8]})")

    assert not offenders, (
        "Recipe(s) last edited by an agent but still marked proofread:\n  "
        + "\n  ".join(offenders)
        + "\n\nAn agent editing a recipe invalidates Helen's proofread of it, so "
          "the SAME commit must set `meta.proofread: false` (issue #367).\n\n"
          "There are three ways out, in order of how often they are the right "
          "one:\n"
          "  1. Set proofread: false. Almost always correct.\n"
          "  2. If the commit changed ONLY keys that render nothing, add them to "
          "INVISIBLE_KEYS -- but only if test_invisible_keys_are_really_"
          "invisible still passes, which is the check that keeps this honest.\n"
          "  3. If Helen reviewed the change herself, either name the recipe in "
          "HELEN_CLEARED or, for a sweeping content-free change across many "
          "recipes, move BASELINE_COMMIT forward. Both are hers to grant, and "
          "the commit message must say she did."
    )


# =============================================================================
# THE PUBLISH GATE'S DATA SIDE — GitHub issue #331
# =============================================================================
# _plugins/hide_awaiting_fix.rb reads `meta.awaiting_fix` and drops the document
# when it is exactly `true`. tests/test_site_config.py guards the MECHANISM
# (plugin present, configs disagreeing correctly, workflow still plugin-capable).
# These two guard the DATA the mechanism reads, and both failure modes are
# silent: the page publishes, and nothing anywhere says why.

def test_every_recipe_declares_awaiting_fix():
    """The flag is present on every recipe, so its absence is never the answer.

    An absent key reads as "not flagged" and publishes, which is the right
    DEFAULT but the wrong way to arrive at it: you cannot tell a recipe nobody
    has considered from one deliberately cleared. Helen sets this during
    proofreading, and a recipe that never got the field never went through that.
    """
    missing = []
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta = (yaml.safe_load(FRONT_MATTER.match(raw).group(1)) or {}).get("meta", {}) or {}
        if "awaiting_fix" not in meta:
            missing.append(path.name)
    assert not missing, (
        "Recipe(s) with no `meta.awaiting_fix` key:\n  " + "\n  ".join(missing)
        + "\n\nAdd `awaiting_fix: false`. Absent reads as not-flagged and "
          "publishes, which is the right default reached the wrong way -- it "
          "makes 'nobody considered this' indistinguishable from 'deliberately "
          "cleared'."
    )


def test_awaiting_fix_is_a_real_boolean():
    """`awaiting_fix: "true"` is a STRING and the gate ignores it.

    THIS IS THE SILENT ONE. The plugin drops a document when
    `meta["awaiting_fix"] == true` -- Ruby's `true`, not a truthy value. A
    quoted "true", or YAML's `yes` resolving to a string in some parsers, is not
    equal to it, so the page you flagged publishes and the build stays green.
    You would only find out by looking at the live site.

    Same family as _data/cocktails/taxonomy.yml's `ship_scale`, where a bare
    `yes` parsed as the BOOLEAN True and silently failed every comparison
    against the string "yes" -- the same trap pointing the other way.
    """
    bad = []
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta = (yaml.safe_load(FRONT_MATTER.match(raw).group(1)) or {}).get("meta", {}) or {}
        if "awaiting_fix" in meta and not isinstance(meta["awaiting_fix"], bool):
            bad.append(f"{path.name}: {meta['awaiting_fix']!r} ({type(meta['awaiting_fix']).__name__})")
    assert not bad, (
        "`meta.awaiting_fix` must be an unquoted true/false:\n  " + "\n  ".join(bad)
        + "\n\nThe plugin compares with `== true`, so a string never matches "
          "and the page publishes despite being flagged -- silently, with a "
          "green build. Never quote this value."
    )


def test_no_recipe_uses_the_old_hyphenated_awaiting_fix_key():
    """`awaiting-fix` was renamed to `awaiting_fix` on 2026-08-18. Nothing may
    carry the old spelling, in any file, ever again.

    THE HYPHEN IS A HAZARD, NOT A STYLE PREFERENCE, which is why this is a test
    and not a note. Ruby reads `meta["awaiting-fix"]` happily, so the plugin
    never minded -- but LIQUID PARSES `page.meta.awaiting-fix` AS SUBTRACTION.
    Any template or index filter reading the publish gate through the hyphenated
    name would evaluate it as false, i.e. "not flagged", i.e. publish the page
    that was flagged. The failure is arithmetic silently standing in for a
    boolean.

    A recipe carrying only the old key also has no `awaiting_fix` at all, so the
    plugin's fail-closed rule holds it back -- but silently. This makes it loud,
    and because the suite gates the deploy (#369), loud means the build stops.
    """
    offenders = []
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        if "awaiting-fix" in raw:
            offenders.append(path.name)
    assert not offenders, (
        "Recipe(s) still using the old hyphenated `awaiting-fix` key:\n  "
        + "\n  ".join(offenders)
        + "\n\nRename to `awaiting_fix`. Liquid reads the hyphenated form as a "
          "subtraction, so a template asking whether the page is flagged gets "
          "arithmetic instead of the flag."
    )
