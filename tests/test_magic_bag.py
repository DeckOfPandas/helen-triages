"""The magic bag's spec: dishes Helen makes without a recipe.

A magic-bag entry is NOT a recipe and this module is not test_front_matter.py
with the hard bits removed. The two schemas answer different questions:

    a recipe          how do I make this?
    a magic-bag entry does this exist, and roughly what goes in it?

So the required set is small on purpose. The whole feature depends on capturing
a dish being nearly free -- if writing one down costs more than remembering it,
Helen won't, and the collection stays empty. Every rule below either makes an
entry FINDABLE (which is the point) or stops it quietly turning into a
half-recipe (which is the failure mode).

WHAT THIS DELIBERATELY DOES NOT CHECK, and why each is a decision rather than an
oversight:

  - no `source`/`source_type`. These are Helen's own dishes out of her own head.
    SOURCE_ATTRIBUTION_SPEC.md has eight shapes and none of them is "I made it
    up", which is the correct answer here rather than a gap in the spec.
  - no `meta.rewritten`. There is nothing to rewrite FROM. See
    test_no_recipe_only_keys below, which actively rejects it.
  - no `meta.proofread`. That flag records Helen being the last judgement before
    someone else's words publish. These words are hers on the way in.
  - no completeness rule on `ingredients`. The list is incomplete BY DEFINITION
    and _layouts/magic_bag.html says so on every page. A test asserting it were
    complete would contradict the collection.
  - no ingredient-QUALIFICATION rules (salted vs unsalted butter, dark vs light
    soy, which sugar). test_style.py holds recipes to those and this module
    deliberately does not, on the friction argument above: they are questions
    for someone about to shop from a list, and nobody shops from this one.
    conftest's `ingredient_items` DOES now see magic-bag ingredients, so the
    day that call is reversed the rules can be pointed at this fixture without
    any other change.
"""
from __future__ import annotations

import re

import pytest
import yaml

from conftest import where
from test_style import ISO_DATE, NUMBER_RANGE, SPELLINGS, TYPOGRAPHY

# Suite marker, so `pytest -m food` runs this half. test_suite_hygiene.py
# asserts every module declares one.
pytestmark = pytest.mark.food

# WHAT AN ENTRY MUST HAVE. Four keys, and each earns its place:
#
#   title             it needs a name to be reminded of
#   tagline           REQUIRED AS A KEY, allowed to be empty -- see below
#   main_ingredients  the curated set the index filters and pills read. This is
#                     the one that makes a dish findable, and findability is the
#                     entire feature.
#   ingredients       the actual jotted list. Helen's own framing: "as a minimum
#                     I should dash off ingredients lists."
#   meta              the publish gate, and only the publish gate.
#
# `tags` is NOT required, unlike on a recipe. A recipe carries tags because the
# index's five filter categories are how you find one; a magic-bag dish is found
# by its ingredients, and forcing a taxonomy decision at jot-down time is
# exactly the friction that stops the note being written. Tags are allowed and
# validated when present (test_taxonomy.py), just not demanded.
REQUIRED = ["title", "tagline", "main_ingredients", "ingredients", "meta"]

# KEYS THAT MEAN THIS HAS STOPPED BEING A MAGIC-BAG ENTRY.
#
# The realistic failure is not someone typing `source_type:` by accident. It is
# Helen starting to write one up properly -- adding a method, then times, then
# groups -- until the file is a recipe living in the wrong collection, rendered
# by a layout that shows none of it. Every key here is silently ignored by
# _layouts/magic_bag.html, so the page would look unchanged while the work
# vanished. The failure message says "promote it" rather than "delete this",
# because wanting to write one up is a good thing that has outgrown the shape.
RECIPE_ONLY = {
    "method": "a magic-bag dish has no method -- that is what makes it one",
    "method_groups": "as `method`",
    "method_short": "there is no method to summarise",
    "ingredient_groups": "the magic bag's list is flat `ingredients:`",
    "source": "these are Helen's own, out of her own head",
    "source_type": "as `source`",
    "prep_time": "a dish you make from memory is not timed",
    "cook_time": "as `prep_time`",
    "serves": "not portioned -- it is however much you make",
    "makes": "as `serves`",
    "internal_temp_ref": "the temperature layer is recipe-only (HANDOVER 14)",
    "doneness": "as `internal_temp_ref`",
}

# `meta:` IS ONE FLAG HERE, NOT THREE. The publish gate and nothing else.
#
# test_front_matter.py's META_ORDER is `rewritten -> awaiting_fix -> proofread`
# because that is the order a RECIPE moves through them. A magic-bag entry moves
# through none of it: there is no source to rewrite from and no proofread to
# grant, so two of the three would be permanently false and meaningless -- and a
# flag that can only hold one value is the thing test_front_matter.py's own
# `cooked_before` tombstone warns about.
#
# awaiting_fix stays because the collection is `output: true` and the gate is
# about what the world sees, which is as true of a four-line dish as of a
# recipe.
META_KEYS = ["awaiting_fix"]


@pytest.mark.parametrize("field", REQUIRED)
def test_required_field_present(magic_bag, field):
    assert field in magic_bag.fm, (
        f"{where(magic_bag)} is missing `{field}:`.\n"
        f"The magic bag's required set is deliberately short — {REQUIRED} — "
        f"because capturing a dish has to be nearly free. All five are here for "
        f"a reason; see this module's docstring."
    )


def test_tagline_key_is_present_even_when_empty(magic_bag):
    """The KEY is required; the VALUE may be empty.

    Helen's ask, 2026-08-26: "Optional. Always add the line to file front matter
    so I don't have to remember to add it." So the line is always there to fill
    in or ignore, and never something to remember to add — which is the same
    convention `method_short: [""]` already uses, where an empty string means
    "not written" rather than "written, and blank".

    This is the mechanical half of that promise. Without it the key is merely
    conventional, and a convention is what fails on the day you are in a hurry.
    _layouts/magic_bag.html renders nothing at all for an empty one.
    """
    assert "tagline" in magic_bag.fm, (
        f"{where(magic_bag)} has no `tagline:` line at all. Write `tagline: \"\"` "
        f"— the key is always present so there is a line to fill in later; the "
        f"value is genuinely optional and renders nothing when empty."
    )
    assert isinstance(magic_bag.fm["tagline"], str), (
        f"{where(magic_bag)} has `tagline: {magic_bag.fm['tagline']!r}`, which is "
        f"not a string. Empty is fine — `tagline: \"\"` — but it is always a string."
    )


def test_no_recipe_only_keys(magic_bag):
    """A magic-bag entry that grows a method has become a recipe.

    Every key checked here renders NOTHING in _layouts/magic_bag.html, so the
    work would be invisible rather than broken — the page looks fine and the
    method you just wrote is nowhere. That is the silent-failure shape this
    repository keeps finding (HANDOVER 12), so it fails loudly instead.
    """
    found = {k: why for k, why in RECIPE_ONLY.items() if k in magic_bag.fm}
    assert not found, (
        f"{where(magic_bag)} has recipe-only key(s): "
        + "; ".join(f"`{k}` ({why})" for k, why in found.items())
        + ".\n_layouts/magic_bag.html renders none of these, so this content "
          "would be silently invisible. If this dish has genuinely earned a "
          "full write-up, promote it: move the file to _food_drafts/ and give "
          "it the recipe schema (HANDOVER 4). That is a good outcome, not an "
          "error — it just cannot live here."
    )


def test_meta_is_exactly_the_publish_gate(magic_bag):
    meta = magic_bag.fm.get("meta")
    assert isinstance(meta, dict), (
        f"{where(magic_bag)} has no `meta:` block, or it is not a mapping."
    )
    assert list(meta) == META_KEYS, (
        f"{where(magic_bag)} `meta:` is {list(meta)}, expected exactly "
        f"{META_KEYS}.\nA magic-bag entry carries the publish gate and nothing "
        f"else — `rewritten` and `proofread` are recipe flags with no meaning "
        f"here, and a flag that can only ever hold one value is dead weight."
    )


def test_awaiting_fix_is_a_real_boolean(magic_bag):
    """`awaiting_fix: "false"` is a string, and a string is not `false`.

    _plugins/hide_awaiting_fix.rb publishes only on an explicit boolean `false`,
    so a quoted value holds the page back — which fails in the SAFE direction,
    but silently, and you would be left wondering where your dish went. The
    recipe side has the identical guard for the identical reason (#331).
    """
    value = magic_bag.fm.get("meta", {}).get("awaiting_fix")
    assert isinstance(value, bool), (
        f"{where(magic_bag)} has `meta.awaiting_fix: {value!r}`, not a real "
        f"boolean. Never quote it — the publish gate compares against Ruby's "
        f"`false` and a string never equals it, so this entry would be held "
        f"back from the live site with no error anywhere."
    )


def test_ingredients_is_a_non_empty_list(magic_bag):
    """An entry with no ingredients is just a title in a list.

    Helen's own minimum. The list is explicitly allowed to be INCOMPLETE — that
    is the collection's whole premise and the layout says so on every page — but
    "incomplete" and "absent" are different things, and only one of them is a
    reminder of how the dish goes.
    """
    items = magic_bag.fm.get("ingredients")
    assert isinstance(items, list) and items, (
        f"{where(magic_bag)} has `ingredients:` as "
        f"{type(items).__name__ if items is not None else 'nothing'}"
        f"{' (empty)' if items == [] else ''}, not a non-empty list.\n"
        f"The list may be as partial as you like — that is the point — but "
        f"there has to be one."
    )


def test_ingredient_items_are_strings_or_labelled_dicts(magic_bag):
    """Bare string, or `{item, note}` with `item` present.

    The same string-or-dict polymorphism `method:`, `notes:` and recipe
    ingredient items already use, for the same reason: the quick form has to
    stay quick. A dict WITHOUT `item` is the shape that renders as a blank line
    — _layouts/magic_bag.html falls through to printing the raw value, and
    Liquid stringifies a hash rather than admitting there is nothing there.
    That is exactly the bug the index's derived-ingredient comment records on
    indonesian-chicken-curry-gulai-ayam.md, caught here before it can happen.
    """
    for i, item in enumerate(magic_bag.fm.get("ingredients") or [], 1):
        if isinstance(item, str):
            assert item.strip(), (
                f"{where(magic_bag)} ingredient {i} is an empty string."
            )
            continue
        assert isinstance(item, dict) and item.get("item"), (
            f"{where(magic_bag)} ingredient {i} is {item!r}.\nAn ingredient is "
            f"either a bare string, or a dict with `item:` present (and "
            f"optionally `note:`). A dict with no `item:` renders as a blank "
            f"line on the page, with no error."
        )
        stray = set(item) - {"item", "note"}
        assert not stray, (
            f"{where(magic_bag)} ingredient {i} has unexpected key(s) {sorted(stray)}. "
            f"Only `item` and `note` are read. `amount:` in particular is "
            f"deliberately absent from this schema — a quantity is precisely "
            f"what you do not remember about a dish you make by eye."
        )


def test_no_duplicate_ingredient_lines(magic_bag):
    """Two identical lines in a list this short is a copy-paste slip.

    Cheap to catch and invisible on the page — the list is short enough that a
    repeat reads as deliberate emphasis rather than a mistake.
    """
    names = [i if isinstance(i, str) else i.get("item") for i in
             magic_bag.fm.get("ingredients") or []]
    lowered = [n.strip().lower() for n in names if n]
    dupes = sorted({n for n in lowered if lowered.count(n) > 1})
    assert not dupes, (
        f"{where(magic_bag)} lists {dupes} more than once."
    )


def test_notes_are_labelled_dicts(magic_bag):
    """Optional, but shaped exactly as a recipe's `notes:` when present.

    Same `{label, text}` contract as test_front_matter.py enforces, because the
    two render through identical markup — a bare string falls back to a box
    labelled with the literal word "note", which is the unlabelled state issue
    #141 removed from published recipes.
    """
    for i, note in enumerate(magic_bag.fm.get("notes") or [], 1):
        assert isinstance(note, dict) and note.get("label") and note.get("text"), (
            f"{where(magic_bag)} note {i} must be `{{label, text}}`, both "
            f"present, not {note!r}."
        )


def test_main_ingredients_is_a_non_empty_list(magic_bag):
    """This is the field that makes the dish findable, so it cannot be empty.

    `ingredients` is the jotted list; `main_ingredients` is the curated set the
    index's pills and ingredient search read. They are different jobs and an
    entry needs both — a dish nobody can find is a dish still lost in the bag,
    which is the exact problem this collection exists to fix.
    """
    mains = magic_bag.fm.get("main_ingredients")
    assert isinstance(mains, list) and mains, (
        f"{where(magic_bag)} has no usable `main_ingredients:`. This is what the "
        f"index filters and the ingredient pills read — without it the dish is "
        f"in the collection but unfindable, which defeats the point of it."
    )


# --- the shared vocabulary applies unchanged ---------------------------------
# `tags` and `star_ingredient` are OPTIONAL on a magic-bag entry (see REQUIRED
# above) but they are not FREE-FORM. The three-layer rule is what is at stake:
# _data/food/taxonomy.yml is the only place food's vocabulary is declared, and
# an undeclared term renders nowhere at all — no badge, no filter button — with
# no error. A dish tagged with a word nobody declared is a dish you cannot find,
# which is the one thing this collection must never be.


def test_star_ingredient_is_declared(magic_bag, taxonomy):
    star = magic_bag.fm.get("star_ingredient")
    if star in (None, ""):
        return
    retired = taxonomy.get("retired_star_ingredients") or {}
    assert star not in retired, (
        f"{where(magic_bag)} has `star_ingredient: {star!r}`, which was "
        f"retired: {retired.get(star)}\nBlank the field rather than leaving the "
        f"retired value in place."
    )
    declared = taxonomy.get("star_ingredients") or []
    assert star in declared, (
        f"{where(magic_bag)} has `star_ingredient: {star!r}`, which is not "
        f"declared in _data/food/taxonomy.yml.\nDeclared stars are: "
        f"{', '.join(declared)}."
    )


def test_tags_are_declared(magic_bag, taxonomy):
    declared = set()
    for group in (taxonomy.get("tags") or {}).values():
        declared.update(group)
    unknown = [t for t in (magic_bag.fm.get("tags") or []) if t not in declared]
    assert not unknown, (
        f"{where(magic_bag)} uses undeclared tag(s) {unknown}.\n"
        f"A tag that is not in _data/food/taxonomy.yml renders NOWHERE — not as "
        f"a badge and not as a filter button. Declared tags: "
        f"{', '.join(sorted(declared))}."
    )


def test_front_matter_has_no_duplicate_keys(magic_bag):
    """Duplicate YAML keys are silent data loss: the last one wins, quietly.

    The recipe side has the identical guard, and it earned it — a duplicated key
    on indonesian-chicken-curry-gulai-ayam.md swallowed an ingredient's name
    entirely and left a dict with an amount and nothing to call it.
    """
    class _Strict(yaml.SafeLoader):
        pass

    def _no_duplicates(loader, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in seen:
                raise AssertionError(
                    f"{where(magic_bag)} front matter defines `{key}` twice. "
                    f"YAML keeps the last one silently."
                )
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)

    _Strict.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)
    match = re.match(r"\A---\n(.*?)\n---", magic_bag.raw, re.S)
    yaml.load(match.group(1), Loader=_Strict)


# --- house style reaches the magic bag ---------------------------------------
# These entries are short, informal and dashed off, and NONE of that is a reason
# to exempt them: they render to the same page, in the same fonts, next to the
# recipes. HANDOVER 5's scoping rule is by what a READER SEES, not by whether a
# field feels like prose — which is exactly why the rule reached `cook_time` and
# the prose pages. Reused from test_style.py rather than restated, so the two
# cannot drift apart.
#
# The `QQ` exemption (issue #426) does NOT apply here and there is no need for
# it. A `QQ` line is the SOURCE's wording awaiting a rewrite; a magic-bag entry
# has no source and every word in it is already Helen's own.


@pytest.mark.parametrize("name,pattern,fix",
                         [(n, p, f) for n, p, f in TYPOGRAPHY if p])
def test_typography(magic_bag, name, pattern, fix):
    hits = re.findall(pattern, magic_bag.raw)
    assert not hits, (
        f"{where(magic_bag)} contains {len(hits)} instance(s) of {name}: "
        f"{sorted(set(h if isinstance(h, str) else h[0] for h in hits))[:5]}. "
        f"Fix: {fix}."
    )


def test_number_ranges_use_en_dashes(magic_bag):
    hits = NUMBER_RANGE.findall(ISO_DATE.sub(" ", magic_bag.raw))
    assert not hits, (
        f"{where(magic_bag)} writes {len(hits)} number range(s) with a hyphen: "
        f"{sorted(set(hits))[:5]}. Ranges take an en dash — 3–4 mins, 170–180°C."
    )


def test_spellings(magic_bag):
    """SPELLINGS keys are already `\\b`-anchored patterns, not bare words —
    used exactly as test_style.py uses them so the two cannot drift.
    """
    problems = []
    for pattern, correct in SPELLINGS.items():
        if re.search(pattern, magic_bag.raw, re.I):
            problems.append(f"{pattern.strip(chr(92) + 'b')} -> {correct}")
    assert not problems, (
        f"{where(magic_bag)} uses non-house spellings: " + "; ".join(problems)
    )


def test_temperatures_use_degree_c(magic_bag):
    bad = re.findall(r"\b(\d{2,3})\s*(?:oC|C\b)(?!\w)", magic_bag.raw)
    assert not bad, (
        f"{where(magic_bag)} writes temperature(s) {bad} without the degree "
        f"sign. Always °C, e.g. 200°C."
    )
