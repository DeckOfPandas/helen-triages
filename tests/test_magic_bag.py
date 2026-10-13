"""The magic bag's spec: dishes Helen makes without a recipe.

A magic-bag entry is not a recipe: it answers "does this exist, and roughly
what goes in it?", not "how do I make this?". The required set is small on
purpose, because capturing a dish has to be nearly free. Each rule either makes
an entry findable or stops it quietly turning into a half-recipe.

Deliberately not checked (DECISIONS §4.3): no `source`, no `meta.rewritten`
(test_no_recipe_only_keys rejects both), no completeness rule on `ingredients`,
and none of test_style.py's ingredient-qualification rules.

Every test is parametrised per entry, so an empty collection would collect
nothing and report green (#1201). The `magic_bag` fixture therefore always
includes the committed entry at conftest's MAGIC_BAG_FIXTURE_PATH, and
`test_each_rule_rejects_what_it_exists_to_reject` breaks it once per rule.
Nothing asserts the real collection is non-empty: that would hold `main` red,
and every deploy, until Helen writes a dish.
"""
from __future__ import annotations

import copy
import re
import types

import pytest
import yaml

import conftest
from conftest import MAGIC_BAG_FIXTURE, where
from test_style import ISO_DATE, NUMBER_RANGE, SPELLINGS, TYPOGRAPHY

pytestmark = pytest.mark.food

# What an entry must have. `tagline` is required as a key and may be empty;
# `main_ingredients` is what the index filters and pills read, so it is what
# makes a dish findable; `ingredients` is the jotted list; `meta` is the
# publish gate. `tags` is not required, unlike on a recipe: a dish is found by
# its ingredients, and a taxonomy decision at jot-down time is friction. Tags
# are still validated when present.
REQUIRED = ["title", "tagline", "main_ingredients", "ingredients", "meta"]

# Keys that mean this has stopped being a magic-bag entry. Each is silently
# ignored by _layouts/magic_bag.html, so a dish written up properly here looks
# unchanged on the page while the work vanishes. The failure says "promote
# it", not "delete this".
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
    "internal_temp_ref": "the temperature layer is recipe-only (MANUAL 14)",
    "doneness": "as `internal_temp_ref`",
}

# `meta:` is the publish gate here and nothing else. The gate publishes only
# on `awaiting_fix: false` and `proofread: true` (#667), so a schema that
# forbade `proofread` could never publish: it is required, `false` on a new
# entry and Helen's to flip. There is no source to rewrite from, so no
# `rewritten`. DECISIONS §4.0.
META_KEYS = ["awaiting_fix", "proofread"]


@pytest.mark.parametrize("field", REQUIRED)
def test_required_field_present(magic_bag, field):
    assert field in magic_bag.fm, (
        f"{where(magic_bag)} is missing `{field}:`.\n"
        f"The magic bag's required set is deliberately short — {REQUIRED} — "
        f"because capturing a dish has to be nearly free. All five are here for "
        f"a reason; see this module's docstring."
    )


def test_tagline_key_is_present_even_when_empty(magic_bag):
    """The key is required; the value may be empty.

    The line is always there to fill in, never something to remember to add:
    the convention `method_short: [""]` uses. _layouts/magic_bag.html renders
    nothing for an empty one.
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

    Every key checked here renders nothing in _layouts/magic_bag.html, so the
    work is invisible rather than broken: the page looks fine and the method
    is nowhere.
    """
    found = {k: why for k, why in RECIPE_ONLY.items() if k in magic_bag.fm}
    assert not found, (
        f"{where(magic_bag)} has recipe-only key(s): "
        + "; ".join(f"`{k}` ({why})" for k, why in found.items())
        + ".\n_layouts/magic_bag.html renders none of these, so this content "
          "would be silently invisible. If this dish has genuinely earned a "
          "full write-up, promote it: move the file to _food_drafts/ and give "
          "it the recipe schema (MANUAL 4). That is a good outcome, not an "
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
        f"else — both flags the gate reads, in that order. `rewritten` is a "
        f"recipe flag with no meaning here, and a flag that can only ever hold "
        f"one value is dead weight. A new entry writes `proofread: false`; "
        f"Helen sets it true once she has read the built page."
    )


def test_awaiting_fix_is_a_real_boolean(magic_bag):
    """`awaiting_fix: "false"` is a string, and a string is not `false`.

    _plugins/publish_gate.rb publishes only on an explicit boolean `false`,
    so a quoted value holds the page back: the safe direction, but silently
    (#331).
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

    The list is allowed to be incomplete, which is the collection's premise,
    but not absent.
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

    The quick form has to stay quick. A dict without `item` renders as a
    blank line with no error, and `amount` is not part of this schema.
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

    Invisible on the page: in a list this short a repeat reads as deliberate.
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

    The same `{label, text}` contract test_front_matter.py enforces, because
    the two render through the same markup, where a bare string gets a box
    labelled with the literal word "note" (#141).
    """
    for i, note in enumerate(magic_bag.fm.get("notes") or [], 1):
        assert isinstance(note, dict) and note.get("label") and note.get("text"), (
            f"{where(magic_bag)} note {i} must be `{{label, text}}`, both "
            f"present, not {note!r}."
        )


def test_main_ingredients_is_a_non_empty_list(magic_bag):
    """This is the field that makes the dish findable, so it cannot be empty.

    `ingredients` is the jotted list; `main_ingredients` is the curated set
    the index's pills and ingredient search read. An entry needs both.
    """
    mains = magic_bag.fm.get("main_ingredients")
    assert isinstance(mains, list) and mains, (
        f"{where(magic_bag)} has no usable `main_ingredients:`. This is what the "
        f"index filters and the ingredient pills read — without it the dish is "
        f"in the collection but unfindable, which defeats the point of it."
    )


# --- the shared vocabulary applies unchanged ---------------------------------
# `tags` and `star_ingredient` are optional here but not free-form:
# _data/food/taxonomy.yml is the only place food's vocabulary is declared, and
# an undeclared term renders nowhere -- no badge, no filter button, no error.


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

    yaml.safe_load accepts them, so this loads with a loader that refuses
    them, as the recipe side does.
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
# Short and informal is no exemption: house style is scoped by what a reader
# sees (MANUAL §5). The patterns are test_style.py's own, imported so the two
# cannot drift. The `QQ` exemption (#426) does not apply: a `QQ` line is a
# source's wording, and a magic-bag entry has no source.


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


# ---- The spec cannot test nothing, #1201 ----
# Everything above takes the `magic_bag` argument and so runs against the
# committed fixture entry as well as every real one. What follows proves what
# a green run of the above cannot: that each rule can fail, and that the run
# says so when the real collection is empty.


def _broken(fm=None, raw=None):
    """The fixture entry with one thing wrong with it.

    `fm` mutates a deep copy of the parsed front matter; `raw` rewrites the
    file's text. A stand-in rather than a Recipe, because a Recipe is read from
    disk and none of these states may ever be written to one.
    """
    data = copy.deepcopy(MAGIC_BAG_FIXTURE.fm)
    if fm is not None:
        fm(data)
    text = MAGIC_BAG_FIXTURE.raw if raw is None else raw(MAGIC_BAG_FIXTURE.raw)
    return types.SimpleNamespace(
        fm=data, raw=text, path=MAGIC_BAG_FIXTURE.path,
        slug=MAGIC_BAG_FIXTURE.slug)


def _meta(**changes):
    def mutate(fm):
        fm["meta"] = changes
    return mutate


# id -> (how the fixture is broken, the rule that must refuse it). The rule is
# called with the broken entry and the real taxonomy.
BREAKAGES = {
    "no title": (
        _broken(fm=lambda fm: fm.pop("title")),
        lambda e, t: test_required_field_present(e, "title")),
    "no tagline line": (
        _broken(fm=lambda fm: fm.pop("tagline")),
        lambda e, t: test_tagline_key_is_present_even_when_empty(e)),
    "a tagline that is not a string": (
        _broken(fm=lambda fm: fm.update(tagline=None)),
        lambda e, t: test_tagline_key_is_present_even_when_empty(e)),
    "a method": (
        _broken(fm=lambda fm: fm.update(method=["Fry it."])),
        lambda e, t: test_no_recipe_only_keys(e)),
    "a source": (
        _broken(fm=lambda fm: fm.update(source="a book")),
        lambda e, t: test_no_recipe_only_keys(e)),
    "meta with rewritten": (
        _broken(fm=_meta(rewritten=True, awaiting_fix=False, proofread=False)),
        lambda e, t: test_meta_is_exactly_the_publish_gate(e)),
    "meta without proofread": (
        _broken(fm=_meta(awaiting_fix=False)),
        lambda e, t: test_meta_is_exactly_the_publish_gate(e)),
    "meta in the wrong order": (
        _broken(fm=_meta(proofread=False, awaiting_fix=False)),
        lambda e, t: test_meta_is_exactly_the_publish_gate(e)),
    "a quoted awaiting_fix": (
        _broken(fm=_meta(awaiting_fix="false", proofread=False)),
        lambda e, t: test_awaiting_fix_is_a_real_boolean(e)),
    "an empty ingredients list": (
        _broken(fm=lambda fm: fm.update(ingredients=[])),
        lambda e, t: test_ingredients_is_a_non_empty_list(e)),
    "an ingredient dict with no item": (
        _broken(fm=lambda fm: fm["ingredients"].append({"note": "which one?"})),
        lambda e, t: test_ingredient_items_are_strings_or_labelled_dicts(e)),
    "an ingredient with an amount": (
        _broken(fm=lambda fm: fm["ingredients"].append(
            {"item": "butter", "amount": "50 g"})),
        lambda e, t: test_ingredient_items_are_strings_or_labelled_dicts(e)),
    "the same ingredient twice": (
        _broken(fm=lambda fm: fm["ingredients"].append("Cold cooked rice")),
        lambda e, t: test_no_duplicate_ingredient_lines(e)),
    "a bare-string note": (
        _broken(fm=lambda fm: fm.update(notes=["Has to be cold."])),
        lambda e, t: test_notes_are_labelled_dicts(e)),
    "no main ingredients": (
        _broken(fm=lambda fm: fm.update(main_ingredients=[])),
        lambda e, t: test_main_ingredients_is_a_non_empty_list(e)),
    "an undeclared star": (
        _broken(fm=lambda fm: fm.update(star_ingredient="zzz-not-a-star")),
        lambda e, t: test_star_ingredient_is_declared(e, t)),
    "an undeclared tag": (
        _broken(fm=lambda fm: fm.update(tags=["zzz-not-a-tag"])),
        lambda e, t: test_tags_are_declared(e, t)),
    "a duplicated key": (
        _broken(raw=lambda raw: raw.replace(
            "\nmeta:", '\ntitle: "Again"\nmeta:', 1)),
        lambda e, t: test_front_matter_has_no_duplicate_keys(e)),
    "a hyphenated number range": (
        _broken(raw=lambda raw: raw.replace(
            "cold cooked rice", "cold cooked rice, 3-4 handfuls", 1)),
        lambda e, t: test_number_ranges_use_en_dashes(e)),
    "a temperature with no degree sign": (
        _broken(raw=lambda raw: raw.replace(
            "cold cooked rice", "rice, baked at 200C", 1)),
        lambda e, t: test_temperatures_use_degree_c(e)),
}


@pytest.mark.parametrize("case", BREAKAGES)
def test_each_rule_rejects_what_it_exists_to_reject(case, taxonomy):
    """Break the fixture one way; the rule for that breakage must fail.

    Running every rule against one well-formed entry shows the rules execute,
    not that any of them can say no (#1201). Typography and spellings are not
    broken here: their patterns are test_style.py's own, and that module
    holds the cases that prove them.
    """
    entry, rule = BREAKAGES[case]
    with pytest.raises(AssertionError):
        rule(entry, taxonomy)


def test_the_fixture_entry_is_always_among_the_cases():
    """The fixture is parametrised in, and is not counted as a real dish.

    Out of the parametrisation, this module collects nothing while the
    collection is empty. Inside ALL_MAGIC_BAG, the cross-collection sweeps and
    the empty-collection report treat a test file as one of Helen's dishes.
    """
    class _Metafunc:
        fixturenames = ["magic_bag"]

        def parametrize(self, name, values, ids):
            self.name, self.values, self.ids = name, values, ids

    metafunc = _Metafunc()
    conftest.pytest_generate_tests(metafunc)
    assert metafunc.values and metafunc.values[0] is MAGIC_BAG_FIXTURE, (
        "conftest no longer parametrises `magic_bag` with the fixture entry "
        "first, so an empty _food_magic_bag/ means this whole module collects "
        "zero cases and reports green. That is #1201."
    )
    assert len(metafunc.values) == len(metafunc.ids)
    assert MAGIC_BAG_FIXTURE not in conftest.ALL_MAGIC_BAG, (
        "The fixture entry is in ALL_MAGIC_BAG, so it is being counted and "
        "swept as a real dish."
    )
    assert conftest.MAGIC_BAG_DIR not in MAGIC_BAG_FIXTURE.path.parents, (
        "The fixture entry lives inside _food_magic_bag/, where Jekyll would "
        "build it into a page on the live site."
    )


def test_an_empty_magic_bag_is_reported_and_a_filled_one_is_not():
    """The run says when it was not evidence about a real dish, and only then.

    It must speak while the collection is empty and be silent once it is not:
    a caveat printed on every run is noise. It never fails the run.
    """
    lines = []

    def write(text, **_):
        lines.append(text)

    conftest._report_empty_magic_bag(write, entries=[])
    said = "\n".join(lines)
    assert "Not evidence about the magic bag" in said
    assert "tests/fixtures/magic_bag/" in said

    lines.clear()
    conftest._report_empty_magic_bag(write, entries=[MAGIC_BAG_FIXTURE])
    assert lines == [], (
        "The empty-magic-bag caveat printed for a collection that has an entry."
    )
