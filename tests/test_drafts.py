"""Draft-scoped structural and style checks.

`_food_drafts/` is deliberately unfinished, and most of the recipe suite
(test_front_matter.py, test_style.py, test_taxonomy.py) correctly leaves it
alone: a blank tagline, an absent `method:`, a bare-string note, `meta.
cooked_before: false`, and `QQ`/`PLACEHOLDER` anywhere are all completely
normal here (HANDOVER_v26.md §4/§9/§12) and none of that is tested.

What IS tested below is the narrower set of rules that are wrong at ANY
stage of a recipe's life, draft or published — a key typo, a value that
doesn't parse the way the template expects, a tag or star that doesn't
exist, a formatting convention (a degree sign, an em dash, a terse time
unit) that carries no information either way. These are structural/
formatting bugs, not unfinished content, so a draft has no more excuse for
them than a published recipe does. Every one of these was seeded from a
real bug found by hand in the drafts folder on 2026-08-11 — see the
individual docstrings for which file(s) caught it.

Two tests here were deliberately allowed to start red, the same "standing
checklist, not a guard that's expected to be green" shape
test_oven_temperature_says_fan (test_style.py) used: an undeclared retired
star_ingredient value and a leftover CLAUDE marker both needed Helen's own
judgement to resolve, not a mechanical fix. Both backlogs have since been
worked through and both tests are green — see their own docstrings below.
A checklist that has gone green has become a regression guard: a failure
in either one now is a real problem to investigate, not a known backlog to
wave past. Don't go near a future violation unprompted all the same — the
judgement call that made these unsuitable for a mechanical fix in the
first place is still real, it's just that there's currently nothing
outstanding to apply it to.

Deliberately NOT ported here, and why — don't add these without asking:

- The closed-list ingredient-qualification rules (salted/unsalted butter,
  dark/light soy sauce, chocolate percentage, etc., test_style.py) and
  test_spice_order_within_group (test_taxonomy.py) — real content-judgement
  work that a fresh ingest isn't expected to have done yet (38 spice-order
  violations across 14 files alone, checked by hand 2026-08-11), not a
  structural bug. This is exactly the tidy-up-to-promote work this file
  exists to reduce, not something a raw draft should already satisfy.
- test_ingredient_notes_are_lowercase_fragments, test_ingredient_group_order_matches_
  title (test_taxonomy.py) — both explicitly flag-only even for published
  recipes ("I'll look at violations myself", HANDOVER_v26.md §10), and the
  proper_nouns list they lean on was seeded from the recipe corpus, not the
  much larger draft one, so porting them risks a flood of false positives
  from ordinary draft-only proper nouns rather than real bugs.
- test_no_oven_conversions (test_taxonomy.py) — bans gas marks/conventional-
  oven restatements, which is correct for published house style but would
  fire on exactly the unrewritten `QQ`/`PLACEHOLDER` source text those
  markers exist to protect (checked by hand: 3 current drafts still carry a
  gas mark inside an un-rewritten step). Stripping it there would be editing
  content, not formatting — HANDOVER_v26.md §4's ingest paragraph is about
  rewriting the step, not scrubbing units out of the original source first.
"""
from __future__ import annotations

import re

import pytest

from conftest import where_draft, ALL_RECIPES, ALL_DRAFTS
from test_front_matter import REQUIRED, RETIRED, MISPLACED_META, _StrictLoader
from test_style import TYPOGRAPHY, SPELLINGS
from test_taxonomy import (

    MISSING_TRAILING_SLASH,
    ANY_RELATIVE_LINK,
    _WELL_FORMED_TARGET,
)

# Suite marker, so `pytest -m food` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.food


# --- front matter shape (test_front_matter.py, structural half only) --------

@pytest.mark.parametrize("field", REQUIRED)
def test_required_field_key_present(draft, field):
    """Key presence only — NOT test_tagline_is_not_blank's "and it must be
    written" half, which is deliberately recipe-only. Checked clean across
    every current draft 2026-08-11 after closing a real gap: 19 files were
    missing `tagline:` entirely (not even blank), which is a different,
    worse thing than an empty value — a missing key silently skips
    `recipe.prose`'s tagline entry rather than showing up as blank.
    """
    assert field in draft.fm, (
        f"{where_draft(draft)} is missing the required field `{field}:`. "
        f"A draft can leave it blank/QQ, but the key itself should exist — "
        f"every other draft already has all of: {', '.join(REQUIRED)}."
    )


def test_front_matter_has_no_duplicate_keys(draft):
    """Same rule as the recipe version, and worth having here specifically
    because a draft carries its front matter with it when it is promoted --
    the same reasoning as test_no_main_ingredient_spelling_collisions. A key
    silently discarded in a draft becomes a line silently missing from a
    published recipe, and by then the evidence is gone: every other test
    reads the PARSED front matter, which no longer contains it.

    Clean across all 254 drafts when this was written, so it is a regression
    guard rather than a checklist.
    """
    import re as _re
    import yaml as _yaml
    match = _re.match(r"\A---\n(.*?\n)---", draft.raw, _re.S)
    try:
        _yaml.load(match.group(1), Loader=_StrictLoader)
    except _yaml.constructor.ConstructorError as exc:
        raise AssertionError(
            f"{where_draft(draft)} has a duplicate key in its front matter: "
            f"{exc}.\nYAML keeps only the last one, so the earlier line's "
            f"content is already gone -- fix it here, before promotion turns "
            f"it into a missing ingredient on a live page."
        ) from None


def test_no_retired_fields(draft):
    found = {f: why for f, why in RETIRED.items() if f in draft.fm}
    assert not found, (
        f"{where_draft(draft)} still has retired field(s): "
        + "; ".join(f"`{f}` ({why})" for f, why in found.items())
    )


def test_meta_fields_are_nested_not_top_level(draft):
    stray = [f for f in MISPLACED_META if f in draft.fm]
    assert not stray, (
        f"{where_draft(draft)} has {stray} at the top level. "
        f"These belong inside the `meta:` block."
    )


def test_meta_block_complete(draft):
    meta = draft.fm.get("meta")
    assert isinstance(meta, dict), (
        f"{where_draft(draft)} has no `meta:` block, or it is not a mapping."
    )
    missing = [f for f in ("rewritten", "proofread", "cooked_before") if f not in meta]
    assert not missing, (
        f"{where_draft(draft)} `meta:` is missing {missing}."
    )


def test_serves_xor_makes(draft):
    """Draft version of the recipe rule keeps the same "exactly one, never
    both" bar — checked 2026-08-11: every current draft already has one or
    the other, so there's no legitimate "neither yet" state to carve out.
    """
    has_serves = "serves" in draft.fm
    has_makes = "makes" in draft.fm
    assert has_serves != has_makes, (
        f"{where_draft(draft)} has "
        + ("neither `serves:` nor `makes:`" if not (has_serves or has_makes)
           else "both `serves:` and `makes:`")
        + ". Exactly one, never both."
    )


def test_method_xor_method_groups(draft):
    """Unlike the recipe version, "neither present" is fine here — a draft
    can legitimately have ingredients transcribed and no method yet. Only
    "both present" (the second silently dropped by the template) is a bug.
    """
    has_flat = "method" in draft.fm
    has_groups = "method_groups" in draft.fm
    assert not (has_flat and has_groups), (
        f"{where_draft(draft)} has both `method:` and `method_groups:`. "
        f"They are mutually exclusive; the recipe layout renders one or the "
        f"other, and having both means the second is silently dropped."
    )


def test_method_groups_have_name_and_steps(draft):
    """Same key-typo trap as the recipe version — caught for real on
    garam-masala-powder.md (a _food_recipes/ file, not a draft, but the
    exact `step:`-singular-with-no-`name:` shape is just as silent here).
    """
    for i, group in enumerate(draft.fm.get("method_groups") or []):
        assert group.get("name"), (
            f"{where_draft(draft)} method_groups entry {i} has no `name`."
        )
        assert group.get("steps"), (
            f"{where_draft(draft)} method_groups entry {i} "
            f"({group.get('name')!r}) has no `steps` -- check for a "
            f"`step:` (singular) typo."
        )


def test_method_produces_actual_steps(draft):
    """Only fires when method/method_groups is DECLARED but produces zero
    steps — a structural bug (a key typo, an empty `method:` with nothing
    after it), not "hasn't been written yet" (which just omits the key
    entirely and isn't tested). Caught for real on pizza-dough.md: `method:`
    present with nothing after it because the source docx had quantities
    only, no method — fixed with a QQ placeholder step, not left bare,
    precisely so this stays a reliable guard against the typo case too.
    """
    if "method" not in draft.fm and "method_groups" not in draft.fm:
        return
    assert draft.method_steps, (
        f"{where_draft(draft)} declares method/method_groups but produces "
        f"zero actual steps. If there's genuinely no method to transcribe "
        f"yet, use a QQ placeholder step rather than leaving `method:` bare "
        f"-- an empty method is indistinguishable from this exact bug."
    )


def test_notes_is_a_list(draft):
    """Caught for real, 2026-08-11: 20 drafts had bare `notes:` with nothing
    after it, which YAML parses as null, not a list -- easy to write by
    accident (it's what you get from deleting every note but leaving the
    key), easy to miss reading the file, since it looks like an intentional
    "no notes yet" the same way `notes: []` does.
    """
    if "notes" not in draft.fm:
        return
    assert isinstance(draft.fm["notes"], list), (
        f"{where_draft(draft)} has `notes:` as a "
        f"{type(draft.fm['notes']).__name__}, not a list. Use `notes: []` "
        f"for none, or a real list."
    )


def test_note_dicts_have_label_and_text_when_dict(draft):
    """Deliberately looser than the recipe version: a bare string note is
    still allowed here (HANDOVER_v26.md §4) -- what's never fine is a note
    that LOOKS like the dict form but is missing a key, which renders blank
    or unlabelled with no error anywhere. Caught for real, 2026-08-11, in
    six *-rewrite.md files: a `note:` key typo instead of `text:` in two of
    them, and four bare strings sitting in a file whose sibling notes were
    already `{label, text}` (not itself a bug, but the typo was).
    """
    for i, note in enumerate(draft.fm.get("notes") or [], 1):
        if isinstance(note, str):
            continue
        assert isinstance(note, dict) and note.get("label") and note.get("text"), (
            f"{where_draft(draft)} note {i} is a dict but missing `label` "
            f"and/or `text` (check for a key typo, e.g. `note:` instead of "
            f"`text:`) -- {note!r}."
        )


def test_method_short_is_a_list(draft):
    ms = draft.fm.get("method_short")
    if ms is None:
        return
    assert isinstance(ms, list), (
        f"{where_draft(draft)} has `method_short:` as a "
        f"{type(ms).__name__}, not a list."
    )


def test_method_short_uses_current_placeholder(draft):
    ms = draft.fm.get("method_short") or []
    retired = [s for s in ms if s in ("QQ", "none")]
    assert not retired, (
        f"{where_draft(draft)} uses retired method_short placeholder(s) "
        f"{retired}. The current convention is a single empty string: "
        f'method_short: [""]'
    )


def test_ingredient_groups_named_when_there_is_more_than_one(draft):
    """Caught for real, 2026-08-11, in 4 files: a second/third named group
    (dressing, marinade, sauce) alongside a first group with no `name:` at
    all -- renders as an unlabelled block followed by labelled ones.
    """
    groups = draft.fm.get("ingredient_groups") or []
    if len(groups) < 2:
        return
    unnamed = [i for i, g in enumerate(groups) if not (isinstance(g, dict) and g.get("name"))]
    assert not unnamed, (
        f"{where_draft(draft)} has {len(groups)} ingredient groups but "
        f"group(s) {unnamed} have no `name:`."
    )


def test_group_names_omit_leading_article(draft):
    offenders = []
    for key in ("ingredient_groups", "method_groups"):
        for group in draft.fm.get(key) or []:
            name = group.get("name") if isinstance(group, dict) else None
            if name and re.match(r"^(for the |for |the )", name, re.I):
                offenders.append(f"{key}: {name!r}")
    assert not offenders, (
        f"{where_draft(draft)} has group name(s) with a leading article: "
        f"{offenders}. The template supplies \"For the \" itself."
    )


# --- house style (test_style.py) ---------------------------------------------

@pytest.mark.parametrize("name,pattern,fix",
                         [(n, p, f) for n, p, f in TYPOGRAPHY if p])
def test_typography(draft, name, pattern, fix):
    hits = re.findall(pattern, draft.raw)
    assert not hits, (
        f"{where_draft(draft)} contains {len(hits)} instance(s) of {name}: "
        f"{sorted(set(h if isinstance(h, str) else h[0] for h in hits))[:5]}. "
        f"Fix: {fix}."
    )


def test_no_ampersand_in_title(draft, taxonomy):
    """Same declared-exception shape as the recipe version -- see
    ampersand_proper_nouns in _data/food/taxonomy.yml. Currently red on
    two *-rewrite.md files (Ben & Jerry's Base No. 2/3) left for Helen: her
    call whether to spell it "and" (like Base No. 1) or declare the phrase.
    `short_name` used to be checked here too; retired 2026-08-12, GitHub
    issue #169.
    """
    allowed = taxonomy.get("ampersand_proper_nouns") or []
    value = str(draft.fm.get("title", ""))
    if "&" in value:
        remainder = value
        for phrase in allowed:
            remainder = remainder.replace(phrase, "")
        assert "&" not in remainder, (
            f"{where_draft(draft)} `title: {value!r}` contains an "
            f"ampersand that isn't part of a declared proper noun. Titles "
            f"use the word 'and' -- if this is a real brand/proper name, "
            f"add the exact phrase to ampersand_proper_nouns in "
            f"_data/food/taxonomy.yml."
        )


def test_spellings(draft):
    problems = []
    for pattern, correct in SPELLINGS.items():
        if re.search(pattern, draft.raw, re.I):
            problems.append(f"{pattern.strip(chr(92) + 'b')} -> {correct}")
    assert not problems, (
        f"{where_draft(draft)} uses non-house spellings: " + "; ".join(problems)
    )


def test_temperatures_use_degree_c(draft):
    """Pure formatting, no information lost either way -- safe to enforce
    even inside an un-rewritten `QQ`/`PLACEHOLDER` step, unlike
    test_no_oven_conversions (see module docstring). Caught for real,
    2026-08-11: 14 drafts wrote e.g. "180C" instead of "180°C".
    """
    bad = re.findall(r"\b(\d{2,3})\s*(?:oC|C\b)(?!\w)", draft.raw)
    assert not bad, (
        f"{where_draft(draft)} writes temperature(s) {bad} without the "
        f"degree sign. Always °C, e.g. 200°C."
    )


def test_metadata_time_format(draft):
    """Same terse-forms rule as the recipe version, both fields at once
    rather than parametrized -- caught for real, 2026-08-11: 7 drafts wrote
    e.g. "2 hours" or "15 minutes" in prep_time/cook_time, which want the
    terse "2 hrs"/"15 mins" metadata form (HANDOVER_v26.md §5).
    """
    problems = []
    for field in ("prep_time", "cook_time"):
        value = draft.fm.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        if value.strip() in ("QQ", "None", "Until done"):
            continue
        bad_units = re.findall(r"(?<=[0-9])\s*(minutes?|hours?|h)\b", value)
        if bad_units:
            problems.append(f"{field}: {value!r} uses {sorted(set(bad_units))}")
    assert not problems, (
        f"{where_draft(draft)} uses spelled-out time units in metadata: "
        + "; ".join(problems)
        + ". Metadata fields use the terse forms `mins`/`hrs`."
    )


def test_prose_abbreviates_minutes_only(draft):
    """Caught for real, 2026-08-11: 3 *-rewrite.md files wrote "N minutes"
    in a method step or note where prose wants "N mins".
    """
    problems = []
    for location, text in draft.prose:
        for match in re.finditer(r"(?<=[0-9])\s*(minutes?|hrs?|secs?)\b", text):
            word = match.group(1)
            wanted = {"minute": "min", "minutes": "mins",
                      "hr": "hour", "hrs": "hours",
                      "sec": "second", "secs": "seconds"}[word.lower()]
            snippet = text[max(0, match.start() - 25):match.end() + 10]
            problems.append(f"{location}: …{snippet}… — use '{wanted}'")
    assert not problems, (
        f"{where_draft(draft)} breaks the prose time convention:\n  "
        + "\n  ".join(problems)
    )


# --- taxonomy and links (test_taxonomy.py) -----------------------------------

def test_tags_are_declared(draft, taxonomy):
    declared = set()
    for group in (taxonomy.get("tags") or {}).values():
        declared.update(group)
    unknown = [t for t in (draft.fm.get("tags") or []) if t not in declared]
    assert not unknown, (
        f"{where_draft(draft)} uses undeclared tag(s) {unknown}. "
        f"Declared tags: {', '.join(sorted(declared))}."
    )


def test_star_ingredient_is_declared(draft, taxonomy):
    """Was deliberately allowed to start red -- see module docstring. Used to
    fail on 8 drafts using the retired `eggs` value; Helen chose 2026-08-11
    to review that list herself rather than have it fixed for her (a genuine
    egg-forward dish would earn the star back, which isn't a call to make
    mechanically). That backlog is now cleared and this test is green -- a
    failure here is a real regression to investigate, not a known gap. Don't
    touch a future violation unprompted; it still needs Helen's own call.

    The other retired value, `something unusual`, doesn't get this same
    standing-checklist treatment: Helen confirmed 2026-08-12 there's nothing
    to reconsider there, so _data/food/taxonomy.yml's retired_star_
    ingredients dict is checked FIRST and fails loudly with the retirement
    reason rather than folding into the generic "not declared" message --
    five drafts were still carrying it three days after retirement, only
    found by reading test output rather than trusting a green run.
    """
    star = draft.fm.get("star_ingredient")
    if star in (None, ""):
        return
    retired = taxonomy.get("retired_star_ingredients") or {}
    if star in retired:
        assert False, (
            f"{where_draft(draft)} has `star_ingredient: {star!r}`, which "
            f"was retired: {retired[star]}\n"
            f"Blank the field rather than leaving the retired value in place."
        )
    declared = taxonomy.get("star_ingredients") or []
    assert star in declared, (
        f"{where_draft(draft)} has `star_ingredient: {star!r}`, which is "
        f"not declared in _data/food/taxonomy.yml. Declared stars are: "
        f"{', '.join(declared)}."
    )


def test_co_tag_rules(draft, taxonomy):
    tags = draft.fm.get("tags") or []
    problems = []
    for trigger, required in (taxonomy.get("co_tags") or {}).items():
        if trigger not in tags:
            continue
        missing = [t for t in required if t not in tags]
        if missing:
            problems.append(f"tagged `{trigger}` but missing {missing}")
    assert not problems, (
        f"{where_draft(draft)} breaks co-tag rule(s):\n  " + "\n  ".join(problems)
    )


def test_no_cook_tag_implies_no_cook_time(draft):
    if "no-cook" not in (draft.fm.get("tags") or []):
        return
    cook = draft.fm.get("cook_time")
    declared_none = isinstance(cook, str) and cook.strip().lower() == "none"
    assert declared_none, (
        f"{where_draft(draft)} is tagged `no-cook` but has "
        f"`cook_time: {cook!r}`. Anything advertised as no-cook must say so "
        f'in the data: cook_time: "None".'
    )


def test_no_claude_markers_left(draft):
    """Was deliberately allowed to start red -- see module docstring. Used to
    fail on schmaltzy-lentils-chicken-lemon.md, which asked Helen to verify
    a chicken breasts-vs-thighs discrepancy before the note was deleted. That
    has since been resolved and this test is green -- a failure here now is
    a real regression to investigate, not a known gap. A future marker still
    isn't something to action or remove unprompted.
    """
    markers = re.findall(r"[^\"\n]{0,10}\bCLAUDE\b[^\"\n]{0,40}", draft.raw)
    assert not markers, (
        f"{where_draft(draft)} still contains marker(s) {markers}."
    )


def test_incidental_not_in_main_ingredients(draft):
    from test_taxonomy import _fold
    main = {_fold(str(m)) for m in (draft.fm.get("main_ingredients") or [])}
    if not main:
        return
    offenders = []
    for group in draft.fm.get("ingredient_groups") or []:
        for item in group.get("items") or []:
            if not isinstance(item, dict) or not item.get("incidental"):
                continue
            name = _fold(str(item.get("item", "")).split(",")[0].strip())
            hits = [m for m in main if name and (name in m or m in name)]
            if hits:
                offenders.append((item.get("item"), hits))
    assert not offenders, (
        f"{where_draft(draft)} marks ingredient(s) `incidental: true` that "
        f"still appear in main_ingredients: {offenders}."
    )


def test_internal_links_have_trailing_slash(draft):
    hits = MISSING_TRAILING_SLASH.findall(draft.raw)
    assert not hits, (
        f"{where_draft(draft)} has {len(hits)} internal link(s) missing a "
        f"trailing slash: {hits}. Cross-recipe links must be "
        f"[text](../slug/), not [text](../slug)."
    )


def test_internal_links_are_well_formed(draft):
    bad = [t for t in ANY_RELATIVE_LINK.findall(draft.raw) if not _WELL_FORMED_TARGET.match(t)]
    assert not bad, (
        f"{where_draft(draft)} has internal link(s) in an unrecognised "
        f"shape: {bad!r}. Check for a stray file extension or typo."
    )


_ALL_SLUGS = {r.slug for r in ALL_RECIPES} | {d.slug for d in ALL_DRAFTS}
_LINK = re.compile(r"\]\(\.\./([a-z0-9-]+)/\)")


def test_internal_recipe_links_resolve_in_drafts(draft):
    """Deliberately checked against recipes AND drafts combined, unlike the
    recipe version (which only checks ALL_RECIPES) -- a draft linking to
    another not-yet-promoted draft is completely normal (chicken-satay.md
    links to peanut-sauce.md, both drafts) and isn't a bug. What's still a
    bug either way is a slug that resolves to nothing at all -- a typo or a
    renamed file the link was never updated for.
    """
    broken = [slug for slug in _LINK.findall(draft.raw) if slug not in _ALL_SLUGS]
    assert not broken, (
        f"{where_draft(draft)} links to recipe slug(s) {broken}, which "
        f"exist in neither _food_recipes/ nor _food_drafts/."
    )
