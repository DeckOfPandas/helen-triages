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

# Suite marker, so `pytest -m food` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.food

def test_star_ingredient_is_declared(recipe, taxonomy):
    star = recipe.fm.get("star_ingredient")
    if star in (None, ""):
        return
    retired = taxonomy.get("retired_star_ingredients") or {}
    if star in retired:
        assert False, (
            f"{where(recipe)} has `star_ingredient: {star!r}`, which was "
            f"retired: {retired[star]}\n"
            f"Blank the field rather than leaving the retired value in place."
        )
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

    That is what lets a base recipe like mixed-spice-powder be honestly uncooked
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
    """Fan oven only, one temperature. "180°C fan" is exactly right --
    Helen: "saying 'fan' isn't a conversion." What's actually banned is a
    SECOND, conventional-oven-equivalent temperature alongside it -- "180°C
    fan (160°C conventional)" in any form, bracketed or not -- and gas
    marks, always, no exceptions.

    A conventional temperature left in place is 20 degrees too hot in this
    kitchen, so a stray conversion is not merely untidy.
    """
    hits = re.findall(r"[^\s]*\s*(?:non-fan|conventional|gas mark \d|gas \d)[^,.\"]{0,10}", recipe.raw, re.I)
    assert not hits, (
        f"{where(recipe)} contains oven conversion(s): {hits}.\n"
        f"This site is fan-oven only, one temperature: '180°C fan', never "
        f"'180°C fan (160°C conventional)' in any form, and never a gas "
        f"mark."
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


# LINK above only matches the well-formed "../slug/)" shape, so a link
# missing its trailing slash is invisible to test_internal_recipe_links_resolve
# rather than failing it -- a gap, not a deliberate exclusion. Real bug,
# 2026-08-09: teriyaki-salmon.md's tagline and its own note both linked to
# "../teriyaki-sauce)" (no slash before the closing paren), the same class
# of "resolves against the wrong base and 404s" bug HANDOVER_v26.md §4
# already documents for a bare `/recipes/slug/` link -- just with the
# trailing slash missing instead of the leading `../`.
MISSING_TRAILING_SLASH = re.compile(r"\]\(\.\./[a-z0-9-]+\)")


def test_internal_links_have_trailing_slash(recipe):
    """Cross-recipe links must be `../slug/`, not `../slug` -- HANDOVER_v26.md
    §4. `../slug` resolves relative to the parent of the current page
    instead of alongside it, so it 404s the same way an unresolved slug
    does, but looks correct at a glance and slips past
    test_internal_recipe_links_resolve entirely, since that test's own
    regex only matches links that already have the slash.
    """
    hits = MISSING_TRAILING_SLASH.findall(recipe.raw)
    assert not hits, (
        f"{where(recipe)} has {len(hits)} internal link(s) missing a "
        f"trailing slash: {hits}.\nCross-recipe links must be "
        f"[text](../slug/), not [text](../slug)."
    )


# Catches "](../" followed by anything up to ")" -- the universe of every
# internal-recipe-link attempt, well-formed or not. LINK and
# MISSING_TRAILING_SLASH above both only match a slug made of [a-z0-9-]+,
# so anything else -- a stray file extension, an underscore, a typo -- is
# invisible to both rather than failing, the same "test that cannot fail
# and not notice" trap as the missing-trailing-slash case. Real bug,
# 2026-08-10: indian-mutton-raan-roast.md's tagline linked to
# ../garam-masala-powder.md), which doesn't quietly 404 -- it's simply not
# a shape either existing test considered at all.
ANY_RELATIVE_LINK = re.compile(r"\]\(\.\./([^)]+)\)")
_WELL_FORMED_TARGET = re.compile(r"^[a-z0-9-]+/?$")

# A SECOND LEGITIMATE SHAPE, added 2026-08-18: a recipe linking OUT of
# _food_recipes/ to a reference page, e.g. `](../../reference/cooking-methods-and-timings/)` from
# the Christmas turkey to the timing calculator. ANY_RELATIVE_LINK strips the
# leading `../`, so what arrives here is `../reference/cooking-methods-and-timings/`.
#
# WHY IT HAS TO BE RELATIVE, rather than the `{{ '/food/reference/cooking-methods-and-timings/' |
# relative_url }}` the reference pages themselves use: front matter is never
# Liquid-templated (HANDOVER §4), and a method step lives in front matter. A
# root-relative `/food/reference/cooking-methods-and-timings/` would drop the `/helen-triages`
# baseurl and 404 in production while working perfectly on localhost -- the
# exact failure test_no_link_in_the_production_build_points_at_a_file_that_isnt_there
# exists to catch. `../../` is baseurl-safe because it never names the root.
#
# Kept narrow on purpose: only `reference/`, only a slug, only with a trailing
# slash. The bug this whole test was written for -- `](../garam-masala-powder.md)`
# -- is still rejected, as is any other freehand path.
_REFERENCE_TARGET = re.compile(r"^\.\./reference/[a-z0-9-]+/$")


def test_internal_links_are_well_formed(recipe):
    """Anything `](../...)` that isn't a plain `slug` or `slug/` -- the two
    shapes test_internal_recipe_links_resolve and
    test_internal_links_have_trailing_slash already check between them.
    """
    bad = [t for t in ANY_RELATIVE_LINK.findall(recipe.raw)
           if not _WELL_FORMED_TARGET.match(t) and not _REFERENCE_TARGET.match(t)]
    assert not bad, (
        f"{where(recipe)} has internal link(s) in an unrecognised shape: "
        f"{bad!r}.\nCross-recipe links must be [text](../slug/) -- check "
        f"for a stray file extension or typo."
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


# --- main_ingredients entries are always double-quoted -----------------------
# GitHub issue #170, open, picked up 2026-08-12. Purely a Sublime-editing
# convenience -- an unquoted YAML flow-sequence scalar and a double-quoted
# one parse identically, so this changes formatting, not data. Checked
# against the raw text of the flow sequence itself (not the parsed value,
# which can't tell you how it was written) -- 125 unquoted entries across 54
# recipes fixed 2026-08-12 via a raw-text substitution on the
# `main_ingredients: [...]` line specifically, not a YAML dump (CLAUDE.md:
# a round-trip through yaml.dump() silently loses quoting style and key
# order across the whole file, correct in a spot check, wrong at scale).
_MAIN_INGREDIENTS_LINE = re.compile(r"^main_ingredients:\s*\[(.*?)\]\s*$", re.M)


def _split_flow_sequence(inner: str) -> list[str]:
    parts, buf, in_quotes = [], "", False
    for ch in inner:
        if ch == '"':
            in_quotes = not in_quotes
            buf += ch
        elif ch == "," and not in_quotes:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts


def test_main_ingredients_entries_are_quoted(recipe):
    match = _MAIN_INGREDIENTS_LINE.search(recipe.raw)
    assert match, f"{where(recipe)} has no single-line `main_ingredients: [...]` to check."
    unquoted = [
        p.strip() for p in _split_flow_sequence(match.group(1))
        if not (p.strip().startswith('"') and p.strip().endswith('"'))
    ]
    assert not unquoted, (
        f"{where(recipe)} has unquoted main_ingredients entries: {unquoted!r}. "
        f'Wrap each in double quotes, e.g. "beef", not beef.'
    )


def test_tags_entries_are_quoted(recipe):
    """GitHub issue #170's own reasoning extends to tags -- same flow
    sequence shape as main_ingredients, same Sublime-editing convenience,
    same "formatting, not data" safety. 94 unquoted entries across 68
    recipes fixed 2026-08-12, same raw-text substitution approach.
    """
    match = re.search(r"^tags:\s*\[(.*?)\]\s*$", recipe.raw, re.M)
    assert match, f"{where(recipe)} has no single-line `tags: [...]` to check."
    unquoted = [
        p.strip() for p in _split_flow_sequence(match.group(1))
        if not (p.strip().startswith('"') and p.strip().endswith('"'))
    ]
    assert not unquoted, (
        f"{where(recipe)} has unquoted tags entries: {unquoted!r}. "
        f'Wrap each in double quotes, e.g. "make-ahead", not make-ahead.'
    )


# --- ingredient note style (GitHub issue #71) --------------------------------

def _first_word(text: str) -> str:
    match = re.match(r"[A-Za-z']+", text.strip())
    return match.group(0) if match else ""


def test_ingredient_notes_are_lowercase_fragments(recipe, taxonomy):
    """One sentence, no trailing full stop, lower case unless the first word
    is `I` or a proper noun declared in taxonomy.yml's `proper_nouns` list.

    Helen: "I'll look at violations myself because I care about tone of
    voice" -- this test only flags, it never rewrites. Whether a capitalised
    first word is a real proper noun or just needs lowercasing is her call,
    made by editing the note text or adding to `proper_nouns`.
    """
    proper_nouns = {p.lower() for p in (taxonomy.get("proper_nouns") or [])}
    problems = []
    for group in recipe.fm.get("ingredient_groups") or []:
        for item in group.get("items") or []:
            if not isinstance(item, dict) or not item.get("note"):
                continue
            text = item["note"].strip()
            label = f"note on '{item.get('item')}'"
            if text.endswith("."):
                problems.append(f"{label}: ends with a full stop -- {text!r}")
            sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.rstrip(".!?")) if s]
            if len(sentences) > 1:
                problems.append(f"{label}: reads as {len(sentences)} sentences -- {text!r}")
            first = _first_word(text)
            if first and first[0].isupper() and first != "I" and first.lower() not in proper_nouns:
                problems.append(
                    f"{label}: starts with capitalised {first!r}, not `I` or a "
                    f"declared proper noun -- {text!r}"
                )
    assert not problems, (
        f"{where(recipe)} ingredient note style:\n  " + "\n  ".join(problems)
    )


# --- ingredient group order (GitHub issue #69) -------------------------------

def _title_head_clause(title: str) -> str:
    """The part of a title naming the dish itself, before any "with ..."
    clause and any parenthetical translation/aside.

    "Christmas Roast Turkey with Lemon, Parsley and Garlic" -> "Christmas
    Roast Turkey". "Indonesian Chicken Curry (Gulai Ayam)" -> "Indonesian
    Chicken Curry". Matching a group's name against this narrower clause,
    rather than the whole title, is what keeps this test from flagging
    lemon-meringue-pie ("meringue" is a real word in the title, but it's a
    modifier of "pie", not the dish's own head noun -- the pastry-then-
    filling-then-meringue build order is correct as it stands) or
    miso-salmon-veg-traybake ("miso" describes the salmon, it doesn't mean
    the marinade group belongs first).
    """
    head = re.split(r"\bwith\b", title, flags=re.I)[0]
    head = re.sub(r"\([^)]*\)", "", head)
    return head.strip().lower()


def _group_matches_title(title_head: str, group_name: str) -> bool:
    """Whether group_name names the dish itself, not just any word overlap.

    English noun phrases put modifiers before the head noun, so "matches"
    means "is the head clause's own tail", not "appears anywhere in it" --
    that distinction is exactly what keeps "Lemon Meringue Pie" from
    matching a group called 'meringue' (a modifier of 'pie', not the head
    noun) while still matching 'turkey' against "Christmas Roast Turkey".
    """
    name = (group_name or "").strip().lower()
    return bool(name) and title_head.endswith(name)


def test_ingredient_group_order_matches_title(recipe):
    """A group named for the dish itself leads; a group named for a
    component the title doesn't call out (dressing, marinade, glaze, to
    serve...) doesn't get to come first just because it happens to be
    listed first in the file.

    Helen: title-relevance for group order (this test), call order for
    ingredients within a group (GitHub issue #68 -- not automatable
    reliably enough to test; see the commit that added this test for why).

    Deliberately conservative: only flags a group whose name doesn't
    appear in the title's own head clause sitting before one that does.
    Two groups that both match, or both don't, are never compared against
    each other -- there's no title signal to arbitrate between them, so
    guessing would just trade a real problem for a noisy one.
    """
    groups = recipe.fm.get("ingredient_groups") or []
    if len(groups) < 2:
        return
    title_head = _title_head_clause(recipe.fm.get("title") or "")
    names = [g.get("name") for g in groups]
    matches = [_group_matches_title(title_head, n) for n in names]
    if not any(matches):
        return
    problems = []
    for i in range(len(groups)):
        if matches[i]:
            continue
        for j in range(i + 1, len(groups)):
            if matches[j]:
                problems.append(
                    f"{names[i]!r} (no title match) is listed before "
                    f"{names[j]!r} (matches the title)"
                )
    assert not problems, (
        f"{where(recipe)} ingredient_groups order:\n  " + "\n  ".join(problems)
        + f"\n\ntitle head clause checked against: {title_head!r}"
    )


# --- title and slug shouldn't diverge -----------------------------------

# GitHub issue #172, open, picked up 2026-08-12 -- the "add a test" successor
# to #81's manual spot check. Reuses _title_head_clause (above) rather than
# the whole title, for the same reason the group-order test does: a "with
# ..." clause is a real, deliberate difference (the slug is the dish, the
# clause is what accompanies it), not divergence. Apostrophes are stripped
# before splitting into words -- "Grandma's" must fold to the single token
# "grandmas" the way the slug itself does, not split into "grandma" + "s",
# which is a real trap: a naive non-alphanumeric split treats the "s" after
# an apostrophe as its own word, and that word will never appear in any
# slug. Calibrated against the whole collection 2026-08-12: every recipe
# scored a clean match except ridiculously-good-oxtail-stew.md, whose title
# was "Sticky Oxtail Stew" -- agreeing with its own tagline ("Six hours in
# the oven breaks oxtail down into sticky heaven"), reading as the title
# having been deliberately changed at some point without the filename
# following. Resolved 2026-08-12, Helen's call: renamed the file to
# sticky-oxtail-stew.md rather than reverting the title.
_STOPWORDS = {"a", "an", "and", "the", "with", "for", "of", "in", "on", "to", "no"}


def _head_clause_words(title: str) -> set[str]:
    text = title.replace("’", "").replace("'", "")
    folded = _fold(_title_head_clause(text))
    return {w for w in re.findall(r"[a-z0-9]+", folded) if w not in _STOPWORDS}


def test_title_and_slug_dont_diverge(recipe):
    head_words = _head_clause_words(recipe.fm.get("title") or "")
    if not head_words:
        return
    slug_words = set(re.findall(r"[a-z0-9]+", recipe.slug))
    missing = head_words - slug_words
    assert not missing, (
        f"{where(recipe)} has title word(s) {sorted(missing)} that don't "
        f"appear anywhere in the slug -- title head clause was "
        f"{_title_head_clause(recipe.fm.get('title') or '')!r}. Either the "
        f"title changed without a rename, or the rename never happened; "
        f"confirm which before touching the filename."
    )


# --- internal link text stays honest about its target -----------------------
# GitHub issue #112. A rename is easy to get half-done: update the slug
# everywhere it's linked (test_internal_recipe_links_resolve already catches
# a stale slug) but leave a link's own display TEXT still describing the old
# name. Real near-miss, 2026-08-12: renaming tomato-tarragon-dressing.md to
# ...-salad.md left roast-beef-fillet.md's own link reading "tomato and
# tarragon dressing" until caught by hand while doing exactly that rename.
#
# Deliberately loose, not a strict word-subset check: calibrated against
# every real internal link in the collection 2026-08-12, a strict "every
# link word must appear in the target's title" rule false-positived on two
# legitimate, non-stale links -- "Chinese five-spice powder" (a real
# descriptive word; the target is just titled "Five-Spice Powder") and
# "garam masala powder" (target is "Garam Masala" -- garam masala already
# means a powder blend, "powder" isn't wrong, just redundant). Both are
# hardcoded exceptions below rather than loosening the rule generally, the
# same pattern _data/food/ingredient_words.yml's family_exceptions uses for
# a single word excluded from an otherwise-sound rule. A link entirely
# missing from PUBLISHED is test_internal_recipe_links_resolve's job, not
# this test's -- skipped here rather than double-reported.
LINK_WITH_TEXT = re.compile(r"\[([^\]]+)\]\(\.\./([a-z0-9-]+)/\)")
_LINK_TEXT_EXTRA_WORD_EXCEPTIONS = {
    ("chinese five-spice powder", "five-spice-powder"): {"chinese"},
    ("garam masala powder", "garam-masala-powder"): {"powder"},
}


def _significant_words(text: str) -> set[str]:
    folded = _fold(text.replace("’", "").replace("'", ""))
    return {w for w in re.findall(r"[a-z0-9]+", folded) if w not in _STOPWORDS}


_TITLE_WORDS_BY_SLUG = {r.slug: _significant_words(r.fm.get("title") or "") for r in ALL_RECIPES}
_TITLE_BY_SLUG = {r.slug: (r.fm.get("title") or "") for r in ALL_RECIPES}


def test_internal_link_text_matches_target_title(recipe):
    problems = []
    for text, slug in LINK_WITH_TEXT.findall(recipe.raw):
        if slug not in PUBLISHED:
            continue
        extra = _significant_words(text) - _TITLE_WORDS_BY_SLUG.get(slug, set())
        extra -= _LINK_TEXT_EXTRA_WORD_EXCEPTIONS.get((text.lower(), slug), set())
        if extra:
            problems.append(f"{text!r} -> ../{slug}/ (title {_TITLE_BY_SLUG.get(slug, '')!r}): {sorted(extra)}")
    assert not problems, (
        f"{where(recipe)} has internal link text that doesn't match its "
        f"target's current title:\n  " + "\n  ".join(problems) + "\n\n"
        f"Either the link text is stale from a rename the text side never "
        f"caught up with, or -- if it's a legitimate descriptive word -- add "
        f"a calibrated exception to _LINK_TEXT_EXTRA_WORD_EXCEPTIONS above."
    )


# --- spice order within a group (Helen's own cooking convention) -----------
# NOT GitHub issue #68 (within-group order matched against method-text call
# order) -- that one is explicitly documented as not automatable reliably
# enough to test (see test_ingredient_group_order_matches_title's own
# docstring above, and scripts/find_ingredient_order_candidates.py, which
# found real word-collision false positives -- "chicken breast" vs "chicken
# stock" both matching "chicken"). This is a different, much safer thing:
# a small, fixed sequence Helen actually cooks by, checked against a
# declared list rather than fuzzy-matched against free-form prose, so
# there's no word-collision risk the same way. Confirmed with Helen
# 2026-08-10: base spices in this exact order among themselves, then any of
# the warm/whole spices in any order, but always after the base spices.
_SPICE_BASE_ORDER = ["coriander", "cumin", "turmeric", "fennel"]
_SPICE_WARM = {"cinnamon", "cloves", "nutmeg", "cardamom", "star anise", "ajwain", "mace"}
# "garlic cloves" isn't the spice cloves -- same shape of collision as
# butter beans/garlic cloves elsewhere in tests/test_style.py.
_SPICE_GARLIC_EXCLUDE = re.compile(r"\bgarlic\b", re.I)
# "coriander" alone is genuinely ambiguous -- the dried seed/ground spice
# this rule is about, or the fresh leaf herb used as a garnish (never as
# part of a "spices added together" step, so exempt from the order rule
# entirely). Real false positives caught running this for real: "handful
# coriander, torn (optional)" and "a large handful of fresh coriander, to
# serve" -- both share "handful", only one says "fresh".
_CORIANDER_HERB_SIGNAL = re.compile(r"\b(fresh|handful|leaves|garnish|to serve)\b", re.I)
# Recipes for a named spice blend itself -- the whole point is stating that
# blend's own fixed component list, not spices added together mid-cook, so
# Helen's order convention doesn't apply to these (confirmed 2026-08-10).
_SPICE_BLEND_RECIPES = {
    "chai-spice-powder", "five-spice-powder", "mixed-spice-powder",
    "garam-masala-powder",
}


def _spice_rank(name: str):
    """None if `name` isn't one of the tracked spices at all -- most
    ingredients aren't, and that's not a signal either way. Base spices
    rank 0..3 by their required order; every warm spice ties at rank 4,
    since order among them is deliberately not enforced.
    """
    if _SPICE_GARLIC_EXCLUDE.search(name):
        return None
    for i, word in enumerate(_SPICE_BASE_ORDER):
        if word == "coriander" and _CORIANDER_HERB_SIGNAL.search(name):
            continue
        if re.search(rf"\b{word}\b", name, re.I):
            return i
    for word in _SPICE_WARM:
        if re.search(rf"\b{re.escape(word)}\b", name, re.I):
            return len(_SPICE_BASE_ORDER)
    return None


def test_spice_order_within_group(recipe):
    """Helen's own cooking convention (confirmed 2026-08-10, prompted by
    indian-mutton-raan-roast.md): within one ingredient group, coriander,
    cumin, turmeric, fennel (seeds) in that order among themselves, then
    whichever of cinnamon/cloves/nutmeg/cardamom/star anise/ajwain/mace are
    used, in any order, but always after the base spices. Exempts recipes
    for a named spice blend itself (chai-spice-powder.md etc.) -- that
    list's order is the blend's own, not a "spices added together" step.
    """
    if recipe.slug in _SPICE_BLEND_RECIPES:
        return
    problems = []
    for group in recipe.fm.get("ingredient_groups") or []:
        ranked = []
        for it in group.get("items") or []:
            text = it.get("item", "") if isinstance(it, dict) else str(it)
            name = re.split(r"[,(]", text)[0].strip()
            rank = _spice_rank(name)
            if rank is not None:
                ranked.append((rank, text))
        for i in range(len(ranked)):
            for j in range(i + 1, len(ranked)):
                if ranked[i][0] > ranked[j][0]:
                    problems.append(
                        f"{ranked[i][1]!r} is listed before {ranked[j][1]!r} "
                        f"in group {group.get('name') or '(unnamed)'!r}"
                    )
    assert not problems, (
        f"{where(recipe)} spice order:\n  " + "\n  ".join(problems)
        + "\n\nOrder: coriander, cumin, turmeric, fennel, then any of "
          "cinnamon/cloves/nutmeg/cardamom/star anise/ajwain/mace."
    )
