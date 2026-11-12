"""Food taxonomy, recipe-to-recipe links and ingredient-list conventions.
Run: pytest tests/test_taxonomy.py

Stars and tags are declared in `_data/food/taxonomy.yml`, not derived from
front matter: a typo in a recipe would otherwise mint a new star ingredient
with one recipe under it, silently. The `taxonomy` fixture skips if that file
is absent.
"""
from __future__ import annotations

import re

import pytest
import yaml

from conftest import ALL_RECIPES, ROOT, is_qq, where

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


def test_star_also_names_declared_stars_and_real_ingredients(taxonomy):
    """`star_also` lets a row answer a second star filter (DECISIONS §7).

    Both stars must be declared, or the rule points at a button that does not
    exist; each ingredient must be lowercase, because food/index.html matches it
    against a downcased main_ingredient and a capital would never match.
    """
    declared = set(taxonomy.get("star_ingredients") or [])
    for rule in taxonomy.get("star_also") or []:
        assert rule.get("star") in declared and rule.get("from") in declared, (
            f"star_also rule {rule!r} names a star not in star_ingredients"
        )
        assert rule.get("star") != rule.get("from"), f"star_also rule {rule!r} points at itself"
        words = rule.get("main_ingredients") or []
        assert words, f"star_also rule {rule!r} lists no main_ingredients"
        upper = [w for w in words if w != w.lower()]
        assert not upper, f"star_also rule {rule!r} has non-lowercase entries {upper}"


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

    The rules live in the data layer, so changing one is a YAML edit; the
    reasoning for each is beside it in taxonomy.yml.
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
    """A recipe tagged `no-cook` has `cook_time: "None"`. One-directional.

    `cook_time: "None"` is a fact about the recipe; `no-cook` is a filter that
    answers "can I put this on the table without cooking?". So an uncooked
    base recipe (a spice blend) may leave the tag off.
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
    """Fan oven only, one temperature. "180°C fan" is right and is not a
    conversion. Banned: a second, conventional-oven temperature beside it in
    any form, and gas marks always.

    A conventional temperature left in place is 20 degrees too hot in this
    kitchen.
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


# LINK matches only the well-formed "../slug/)" shape, so a link missing its
# trailing slash is invisible to test_internal_recipe_links_resolve, not a
# failure of it.
MISSING_TRAILING_SLASH = re.compile(r"\]\(\.\./[a-z0-9-]+\)")


def test_internal_links_have_trailing_slash(recipe):
    """Cross-recipe links are `../slug/`, not `../slug` -- MANUAL §4.

    `../slug` 404s but looks correct at a glance, and
    test_internal_recipe_links_resolve cannot see it: that test's regex only
    matches links that already have the slash.
    """
    hits = MISSING_TRAILING_SLASH.findall(recipe.raw)
    assert not hits, (
        f"{where(recipe)} has {len(hits)} internal link(s) missing a "
        f"trailing slash: {hits}.\nCross-recipe links must be "
        f"[text](../slug/), not [text](../slug)."
    )


# "](../" followed by anything up to ")": every internal-link attempt,
# well-formed or not. LINK and MISSING_TRAILING_SLASH only match a slug of
# [a-z0-9-]+, so a stray file extension (`../garam-masala-powder.md`), an
# underscore or a typo is invisible to both.
ANY_RELATIVE_LINK = re.compile(r"\]\(\.\./([^)]+)\)")
_WELL_FORMED_TARGET = re.compile(r"^[a-z0-9-]+/?$")

# A second legitimate shape: a recipe linking out to a reference page,
# `](../../reference/<slug>/)`. ANY_RELATIVE_LINK strips the leading `../`.
# It has to be relative: front matter is never Liquid-templated (MANUAL §4),
# and a root-relative `/food/reference/...` drops the baseurl and 404s in
# production while working on localhost. Narrow on purpose: only `reference/`,
# a slug, a trailing slash and an optional `?protein=` (#243). The timings
# page ignores an unknown protein silently, so a typo there shows no error.
_REFERENCE_TARGET = re.compile(r"^\.\./reference/[a-z0-9-]+/(\?protein=[a-z-]+)?$")

# A third: a recipe linking to a drink, `](../../../cocktails/recipes/<slug>/)`,
# which climbs to the site root and so resolves from a draft and a published
# recipe alike (MANUAL §4, "Cross-recipe links").
DRINK_TARGET = re.compile(r"^\.\./\.\./cocktails/recipes/([a-z0-9-]+)/$")


def drink_slugs_linked(document):
    return [m.group(1) for t in ANY_RELATIVE_LINK.findall(document.raw)
            if (m := DRINK_TARGET.match(t))]


def test_drink_links_are_read_from_their_one_shape():
    from types import SimpleNamespace
    raw = ("[a](../../../cocktails/recipes/cherry-bakewell/)s "
           "[b](../../cocktails/recipes/x/) [c](../../../cocktails/drafts/y/) "
           "[d](../soup/)")
    assert drink_slugs_linked(SimpleNamespace(raw=raw)) == ["cherry-bakewell"]


PUBLISHED_DRINKS = {p.stem for p in (ROOT / "_cocktail_recipes").glob("*.md")}


def test_drink_links_name_a_published_drink(recipe):
    """A published recipe may link only to a published drink: the page is
    public, and a drafts slug would print an unpublished drink's name on it.
    """
    missing = [s for s in drink_slugs_linked(recipe) if s not in PUBLISHED_DRINKS]
    assert not missing, (
        f"{where(recipe)} links to drink(s) {missing}, which are not in "
        f"_cocktail_recipes/. Promote the drink first, or take the link out."
    )


def test_internal_links_are_well_formed(recipe):
    """No `](../...)` link has a target other than a plain `slug`, `slug/`,
    a reference page or a drink: the shapes the two tests above cannot see.
    """
    bad = [t for t in ANY_RELATIVE_LINK.findall(recipe.raw)
           if not _WELL_FORMED_TARGET.match(t) and not _REFERENCE_TARGET.match(t)
           and not DRINK_TARGET.match(t)]
    assert not bad, (
        f"{where(recipe)} has internal link(s) in an unrecognised shape: "
        f"{bad!r}.\nCross-recipe links must be [text](../slug/) -- check "
        f"for a stray file extension or typo."
    )


# A same-page fragment link, e.g. [read to the bottom](#why-hollandaise-is-hard)
# in a tagline (#353). Matches a bare fragment only; a fragment hanging off a
# path belongs to the cross-recipe rules above.
SAME_PAGE_FRAGMENT = re.compile(r"\]\(#([^)]+)\)")

BODY_ID = re.compile(r'id="([^"]+)"')


def _ids_available_to_a_recipe(recipe):
    """Every id a rendered recipe page can offer, which is NOT just its own.

    A body heading's id is a literal in the recipe file (MANUAL §4.1), but
    `#doneness` belongs to _layouts/recipe.html, so the file alone is not
    enough.

    Over-permissive on purpose: every id in the recipe layout chain and in
    _includes/, without resolving which includes the layout reaches. A broken
    fragment can slip through where an unrelated include defines the same id.
    """
    from conftest import ROOT

    ids = set(BODY_ID.findall(recipe.raw))
    for path in [ROOT / "_layouts" / "recipe.html", ROOT / "_layouts" / "default.html"]:
        if path.exists():
            ids |= set(BODY_ID.findall(path.read_text(encoding="utf-8")))
    for path in (ROOT / "_includes").rglob("*.html"):
        ids |= set(BODY_ID.findall(path.read_text(encoding="utf-8")))
    return ids


def test_same_page_fragment_links_land_somewhere(recipe):
    """A `](#fragment)` link names an id its rendered recipe page has.

    A wrong fragment is not a 404: the page loads and stays at the top, so it
    reads as a scroll that did not work. tests/test_page_links.py scans
    templates, and a tagline lives in front matter, so it never looks here.
    """
    ids = _ids_available_to_a_recipe(recipe)
    assert ids, (
        "No ids found anywhere in the recipe layout chain, which cannot be "
        "right -- and an empty set would fail every fragment link rather than "
        "check them."
    )
    broken = [f for f in SAME_PAGE_FRAGMENT.findall(recipe.raw) if f not in ids]
    assert not broken, (
        f"{where(recipe)} links to fragment(s) {broken!r} that no id in this "
        f"file provides.\n"
        f"Available ids here: {sorted(ids) or 'none at all'}.\n"
        f"Add `id=\"...\"` to the target heading -- body headings are raw HTML "
        f"(MANUAL §4.1), so the id goes on the <h2> itself, which is also what "
        f"gives it .recipe-section-heading's scroll-margin-top. Ids emitted by "
        f"_layouts/recipe.html or an include (`#doneness`, for one) count too."
    )


def test_no_claude_markers_left(recipe):
    """A note addressed to CLAUDE is an instruction for a future session, not
    content ready to publish -- in any form, with or without a `QQ` prefix.
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

    Covers ALL_DRAFTS and the magic bag as well as published recipes: a draft
    carries its spelling with it when it is promoted.

    Partial in CI, knowingly (#378): `_food_drafts/` is a private repo, absent
    there. This does not skip, because the published half is real coverage,
    but a green in CI means "no collisions among the recipes". A new draft
    clashing with a published recipe is caught only by a local run.
    """
    from collections import defaultdict
    from conftest import ALL_RECIPES, ALL_DRAFTS, ALL_MAGIC_BAG

    assert ALL_RECIPES, (
        "No published recipes loaded at all, so this check has nothing to scan "
        "and would pass having examined nothing."
    )

    # The magic bag is in the corpus: its entries render the same filter
    # buttons from main_ingredients.
    forms = defaultdict(set)
    sources = defaultdict(set)
    for r in ALL_RECIPES + ALL_DRAFTS + ALL_MAGIC_BAG:
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


# --- singular and plural: the list's own word, one chip (DECISIONS §6) -------

def _number_twins(word: str) -> set[str]:
    """The other-number spellings of `word`: lime/limes, leaf/leaves."""
    w = word.lower()
    out = {w + "s", w + "es"}
    if w.endswith("ies"):
        out |= {w[:-3] + "y", w[:-2]}
    if w.endswith("ves"):
        out.add(w[:-3] + "f")
    if w.endswith("es"):
        out.add(w[:-2])
    if w.endswith("s"):
        out.add(w[:-1])
    if w.endswith("y"):
        out.add(w[:-1] + "ies")
    if w.endswith("f"):
        out.add(w[:-1] + "ves")
    return out - {w}


def _phrase_in(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(phrase)}(?![\w-])", text) is not None


def main_ingredients_off_the_list(fm) -> list[tuple[str, str]]:
    """`[(entry, the list's word)]` for an entry the ingredient list writes in
    the other number: `lime` beside "2 limes, juiced". An entry found anywhere
    in a line passes; the other number must end a line's name, before its first
    comma, so "walnut halves" leaves `walnuts` alone.
    Whole eggs follow the count instead (`test_main_ingredients_egg_count_agrees`).
    """
    names, lines = [], []
    for group in fm.get("ingredient_groups") or []:
        for it in group.get("items") or []:
            if isinstance(it, dict):
                text = re.sub(r"^QQ\s+", "", str(it.get("item", "")))
                lines.append(text.lower())
                names.append(re.sub(r"\([^)]*\)", " ", text).split(",")[0].strip().lower())
    out = []
    for entry in (str(m) for m in fm.get("main_ingredients") or []):
        low = entry.lower()
        if re.fullmatch(r"eggs?", low) or any(_phrase_in(n, low) for n in lines):
            continue
        for twin in sorted(_number_twins(low)):
            if any(re.search(rf"(?<![\w-]){re.escape(twin)}$", n) for n in names):
                out.append((entry, twin))
                break
    return out


@pytest.mark.parametrize("main,items,want", [
    (["lime"], ["limes, juiced"], [("lime", "limes")]),
    (["bay leaves"], ["bay leaf"], [("bay leaves", "bay leaf")]),
    (["red chilli"], ["juice of 2 limes", "red chillies"], [("red chilli", "red chillies")]),
    (["limes"], ["juice of 2 limes"], []),
    (["walnuts"], ["walnut halves"], []),
    (["anchovies"], ["salted anchovy fillets, chopped"], []),
    (["eggs"], ["egg"], []),
    (["egg yolks"], ["egg yolk, plus 2 egg yolks for glazing"], []),
    (["egg yolks"], ["egg yolk"], [("egg yolks", "egg yolk")]),
])
def test_main_ingredients_off_the_list_on_fixtures(main, items, want):
    fm = {"main_ingredients": main,
          "ingredient_groups": [{"items": [{"item": i} for i in items]}]}
    assert main_ingredients_off_the_list(fm) == want


def test_main_ingredients_use_the_lists_own_number():
    """An entry is written as the ingredient list writes it (DECISIONS §6).
    Recipes, drafts and the magic bag, like the collision check above, and
    partial in CI the same way."""
    from conftest import ALL_DRAFTS, ALL_MAGIC_BAG

    assert ALL_RECIPES, "No published recipes loaded, so this checked nothing."
    bad = [f"{r.slug}: {e!r} -> {t!r}"
           for r in ALL_RECIPES + ALL_DRAFTS + ALL_MAGIC_BAG
           for e, t in main_ingredients_off_the_list(r.fm)]
    assert not bad, (
        "main_ingredients entries in the other number from their own "
        "ingredient list:\n  " + "\n  ".join(bad)
        + "\n\nWrite the list's word. The picker merges the two numbers into "
          "one chip through `aliases` in _data/food/ingredient_words.yml."
    )


def _picker_words() -> dict:
    path = ROOT / "_data" / "food" / "ingredient_words.yml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _chips(entry: str, words: dict) -> list[str]:
    """The include picker's chip(s) for one entry: leading modifiers stripped,
    then one alias hop, as `normaliseEntry` and `applyAlias` do in
    assets/js/ingredient-search.js. Entries carry no quantity or measure."""
    mods = {_fold(m) for m in words.get("modifiers") or []}
    parts = entry.split()
    while len(parts) > 1 and _fold(parts[0]) in mods:
        parts = parts[1:]
    stripped = " ".join(parts)
    aliases = {_fold(k): v for k, v in (words.get("aliases") or {}).items()}
    target = aliases.get(_fold(stripped), stripped)
    return [str(t) for t in (target if isinstance(target, list) else [target])]


def _singular_key(chip: str, words: dict) -> str:
    sing = {_fold(k): _fold(v) for k, v in (words.get("singulars") or {}).items()}
    out = []
    for w in _fold(chip).split():
        if w in sing:
            w = sing[w]
        elif w.endswith("ies") and len(w) > 4:
            w = w[:-3] + "y"
        elif re.search(r"(ch|sh|x|o)es$", w):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return " ".join(out)


def number_split_chips(entries: list[str], words: dict) -> list[list[str]]:
    """Groups of two or more chips that differ only by number or case."""
    from collections import defaultdict
    groups = defaultdict(set)
    for entry in entries:
        for chip in _chips(entry, words):
            groups[_singular_key(chip, words)].add(chip)
    return sorted(sorted(g) for g in groups.values() if len(g) > 1)


def test_number_split_chips_on_fixtures():
    words = {"modifiers": ["fresh"], "singulars": {"leaves": "leaf"},
             "aliases": {"limes": "lime"}}
    assert number_split_chips(["bay leaves", "bay leaf"], words) == [["bay leaf", "bay leaves"]]
    assert number_split_chips(["fresh pears", "pear"], words) == [["pear", "pears"]]
    assert number_split_chips(["limes", "lime", "fresh lime"], words) == []
    assert number_split_chips(["Little Gem lettuce", "little gem lettuce"], words)


def test_no_ingredient_is_two_chips_by_number():
    """`lime` and `limes` are one chip: the plural is aliased to the singular
    (Singular wins). Corpus-wide like the collision check above, and partial
    in CI the same way."""
    from conftest import ALL_DRAFTS, ALL_MAGIC_BAG

    words = _picker_words()
    entries = [str(e) for r in ALL_RECIPES + ALL_DRAFTS + ALL_MAGIC_BAG
               for e in r.fm.get("main_ingredients") or []]
    assert entries, "No main_ingredients loaded, so this checked nothing."
    split = number_split_chips(entries, words)
    assert not split, (
        "The ingredient picker shows these as separate chips:\n  "
        + "\n  ".join(" / ".join(g) for g in split)
        + "\n\nAlias the plural to the singular in `aliases` in "
          "_data/food/ingredient_words.yml. Leave the recipes as their lists "
          "write them."
    )


def test_a_number_alias_still_matches_its_plural_recipes():
    """The include side matches a chip against each row's RAW entries, by word
    prefix after `singulars` (#762), so `bay leaf` finds "bay leaves" only
    because `leaves: leaf` is a singular. A plural alias whose singular is not
    a prefix of it would build a chip that misses half its recipes."""
    words = _picker_words()
    sing = {_fold(k): _fold(v) for k, v in (words.get("singulars") or {}).items()}

    def norm(text):
        return [sing.get(w, w) for w in _fold(text).split()]

    bad = []
    for key, target in (words.get("aliases") or {}).items():
        if isinstance(target, list) or _singular_key(key, words) != _singular_key(str(target), words):
            continue
        if not all(any(ew.startswith(kw) for ew in norm(key)) for kw in norm(str(target))):
            bad.append(f"{key} -> {target}")
    assert not bad, (
        "These plural aliases make a chip that does not match the plural "
        "entries it absorbs:\n  " + "\n  ".join(bad)
        + "\nAdd the plural word to `singulars` in _data/food/ingredient_words.yml."
    )


def test_incidental_not_in_main_ingredients(recipe):
    """An item marked `incidental: true` (MANUAL §4) is a cooking fluid or
    tin-and-pan fat, not a recipe component, so it is not also listed in
    `main_ingredients`, which feeds the index's ingredient pills and search.
    """
    main = {_fold(str(m)) for m in (recipe.fm.get("main_ingredients") or [])}
    if not main:
        return

    def named(item):
        return _fold(str(item.get("item", "")).split(",")[0].strip())

    # What the recipe really uses, by name: every line that is not incidental
    # (#1356). A recipe can grease its tin with butter and also put butter in
    # the base, so a main ingredient is an offence only when nothing but an
    # incidental line accounts for it.
    core = {named(item)
            for group in recipe.fm.get("ingredient_groups") or []
            for item in group.get("items") or []
            if isinstance(item, dict) and not item.get("incidental")}

    def accounted_for(m):
        return any(c and (c in m or m in c) for c in core)

    offenders = []
    for group in recipe.fm.get("ingredient_groups") or []:
        for item in group.get("items") or []:
            if not isinstance(item, dict) or not item.get("incidental"):
                continue
            name = named(item)
            hits = [m for m in main
                    if name and (name in m or m in name) and not accounted_for(m)]
            if hits:
                offenders.append((item.get("item"), hits))
    assert not offenders, (
        f"{where(recipe)} marks ingredient(s) `incidental: true` that still "
        f"appear in main_ingredients: {offenders}. An incidental cooking "
        f"fluid shouldn't show up as a recipe-row pill or an ingredient-"
        f"search hit -- remove it from main_ingredients, or drop the "
        f"incidental flag if it's actually core."
    )


# --- tin-and-pan fats and flour are incidental (#1356) ------------------------
# The words are data, `_data/food/incidentals.yml`; `incidental_verdict` is the
# one reading of them, and scripts/tidy_drafts.py imports it to apply them.

_INCIDENTALS = yaml.safe_load(
    (ROOT / "_data" / "food" / "incidentals.yml").read_text(encoding="utf-8"))


def _any_word(words):
    return re.compile(r"\b(?:" + "|".join(map(re.escape, words)) + r")\b", re.I)


_FAT_OR_FLOUR = _any_word(_INCIDENTALS["fats_and_flours"])
_USE = _any_word(_INCIDENTALS["uses"])
_NOT_INCIDENTAL = _any_word(_INCIDENTALS["not_incidental"])
_BRACKETED = re.compile(r"\([^)]*\)")
_DEEP_FRY = re.compile(r"\bdeep[- ]?fr(?:y|ying|ied)\b", re.I)
DEEP_FRYING = ", for deep frying"
_PLUS_TAIL = re.compile(r",?\s+plus\b[^,]*$", re.I)
_USE_CLAUSE = re.compile(r"(?:,\s*|\s+)(?:extra,\s*)?(?=(?:for|to)\b)", re.I)


def incidental_verdict(text):
    """("flag", None), ("trim", the item without its tail), ("deep", the item
    as it should read), or (None, None).

    "flag": the line names a fat or flour and is only for the tin or the pan
    ("butter, for greasing"). "trim": a real line with that use tacked on after
    "plus" ("175 g butter, softened, plus extra for the tin"). "deep": a fat
    for deep frying, which stays on the list with no amount, since the pan
    decides the volume, and reads "vegetable oil, for deep frying". A bracket
    is not read: "olive oil (a little for frying, the rest for the dressing)"
    is one real line. A source line (`QQ`) is judged like any other; whether
    it may be edited is the caller's question.
    """
    text = str(text or "")
    plain = _BRACKETED.sub("", text)
    deep = _USE_CLAUSE.search(text)
    if (deep and "plus" not in text.lower()
            and _DEEP_FRY.search(text[deep.end():])
            and _FAT_OR_FLOUR.search(text[:deep.start()])):
        return "deep", text[:deep.start()] + DEEP_FRYING
    plus = _PLUS_TAIL.search(plain)
    if plus:
        use = plus.group(0)
        if (_USE.search(use) and not _NOT_INCIDENTAL.search(use)
                and _FAT_OR_FLOUR.search(plain.split(",")[0])):
            cut = _PLUS_TAIL.search(text)
            return ("trim", text[:cut.start()]) if cut else (None, None)
        return None, None
    clause = _USE_CLAUSE.search(plain)
    if not clause:
        return None, None
    use = plain[clause.end():]
    if (_USE.search(use) and not _NOT_INCIDENTAL.search(use)
            and _FAT_OR_FLOUR.search(plain[:clause.start()])):
        return "flag", None
    return None, None


def _items(recipe):
    for group in recipe.fm.get("ingredient_groups") or []:
        for item in (group or {}).get("items") or []:
            if isinstance(item, dict):
                yield item


def test_tin_and_pan_fats_are_flagged_incidental(recipe):
    """#1356, DECISIONS §4: "butter, for greasing" carries `incidental: true`,
    which hides it from the ingredients and the shopping list and keeps it
    visible to the exclusion filter. `/tidy-drafts` adds the flag."""
    unflagged = [item.get("item") for item in _items(recipe)
                 if incidental_verdict(item.get("item"))[0] == "flag"
                 and item.get("incidental") is not True]
    assert not unflagged, (
        f"{where(recipe)} lists a fat or flour only for the tin or the pan "
        f"without `incidental: true`: {unflagged}. Add the flag (`python3 "
        f"scripts/tidy_drafts.py --only incidentals --apply` does it on a "
        f"draft), or, if the line is not a tin-and-pan use, narrow the words in "
        f"_data/food/incidentals.yml."
    )


def test_no_real_line_carries_its_tin_and_pan_extra(recipe):
    """#1356: ", plus extra for the tin" on a fat or flour is trimmed; the cook
    greases a tin without being told. A source line (`QQ`) is left for Helen's
    rewrite, so it is not held here."""
    tails = [item.get("item") for item in _items(recipe)
             if not is_qq(item.get("item"))
             and incidental_verdict(item.get("item"))[0] == "trim"]
    assert not tails, (
        f"{where(recipe)} still carries a tin-and-pan extra on a real line: "
        f"{tails}. Trim it (`python3 scripts/tidy_drafts.py --only incidentals "
        f"--apply` does it on a draft)."
    )


def test_deep_frying_oil_is_listed_without_an_amount(recipe):
    """#1356, DECISIONS §4: deep-frying oil stays on the list, unquantified,
    as "<oil>, for deep frying": the pan decides how much. A `QQ` line keeps
    its words for Helen's rewrite, but not its amount."""
    wrong = []
    for item in _items(recipe):
        verdict, should = incidental_verdict(item.get("item"))
        if verdict != "deep":
            continue
        if item.get("amount") not in (None, ""):
            wrong.append(f"{item.get('item')!r} has amount {item.get('amount')!r}")
        elif not is_qq(item.get("item")) and item.get("item") != should:
            wrong.append(f"{item.get('item')!r} should read {should!r}")
        elif item.get("incidental"):
            wrong.append(f"{item.get('item')!r} is flagged incidental, which hides it")
    assert not wrong, (
        f"{where(recipe)}: deep-frying oil is listed with no amount, as "
        f"\"<oil>{DEEP_FRYING}\", and not incidental: {wrong}. "
        f"`python3 scripts/tidy_drafts.py --only incidentals --apply` fixes "
        f"the first two on a draft."
    )


# --- main_ingredients entries are always double-quoted -----------------------
# #170. An editing convenience: a quoted and an unquoted flow-sequence scalar
# parse identically, so this is checked against the raw text of the line, not
# the parsed value. Fix it by raw-text substitution, never a yaml.dump() round
# trip, which loses quoting and key order (MANUAL §12).
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
    """#170. `tags` entries are double-quoted, as main_ingredients entries
    are: the same flow-sequence shape, checked against the raw line.
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

    #71. This test only flags, and nothing rewrites a note to pass it: tone
    of voice is Helen's. Whether a capitalised first word is a proper noun or
    needs lowercasing is her call, made by editing the note or adding to
    `proper_nouns` (MANUAL §10.1).
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
    Chicken Curry". The whole title would match accompaniments and asides.
    """
    head = re.split(r"\bwith\b", title, flags=re.I)[0]
    head = re.sub(r"\([^)]*\)", "", head)
    return head.strip().lower()


def _group_matches_title(title_head: str, group_name: str) -> bool:
    """Whether group_name names the dish itself, not just any word overlap.

    English puts modifiers before the head noun, so "matches" means "is the
    head clause's tail": 'turkey' matches "Christmas Roast Turkey", and
    'meringue' does not match "Lemon Meringue Pie".
    """
    name = (group_name or "").strip().lower()
    return bool(name) and title_head.endswith(name)


def test_ingredient_group_order_matches_title(recipe):
    """A group named for the dish itself leads; a group named for a
    component the title doesn't call out (dressing, marinade, glaze) does not
    come first (#69).

    Conservative on purpose: it only flags a non-matching group sitting
    before a matching one. Two groups that both match, or both don't, are
    never compared. Call order within a group (#68) is not tested.
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

# #172. Compared on _title_head_clause, not the whole title: a "with ..."
# clause is a deliberate difference, since the slug is the dish alone.
# Apostrophes are stripped before splitting, so "Grandma's" folds to
# "grandmas" as the slug does, not to "grandma" plus a stray "s".
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
# #112. A rename can update a link's slug and leave its display text
# describing the old name. Every significant word of the link text must be in
# the target's title; a legitimate extra word is a declared exception below,
# not a looser rule. A link whose slug is not in PUBLISHED is
# test_internal_recipe_links_resolve's to report.
LINK_WITH_TEXT = re.compile(r"\[([^\]]+)\]\(\.\./([a-z0-9-]+)/\)")
_LINK_TEXT_EXTRA_WORD_EXCEPTIONS = {
    ("chinese five-spice powder", "five-spice-powder"): {"chinese"},
    ("garam masala powder", "garam-masala-powder"): {"powder"},
    ("stella and henry's version", "stella-henrys-christmas-pudding"): {"version"},
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
# A fixed sequence checked against a declared list: the base spices in this
# order among themselves, then any warm spice in any order, always after the
# base spices. Not #68, call order within a group, which is not tested.
_SPICE_BASE_ORDER = ["coriander", "cumin", "turmeric", "fennel"]
_SPICE_WARM = {"cinnamon", "cloves", "nutmeg", "cardamom", "star anise", "ajwain", "mace"}
# "garlic cloves" is not the spice cloves.
_SPICE_GARLIC_EXCLUDE = re.compile(r"\bgarlic\b", re.I)
# "coriander" alone is ambiguous: the dried spice this rule is about, or the
# fresh herb used as a garnish, which is exempt from the order rule.
_CORIANDER_HERB_SIGNAL = re.compile(r"\b(fresh|handful|leaves|garnish|to serve)\b", re.I)
# Recipes for a named spice blend state the blend's own component list, so
# the order convention does not apply to them.
_SPICE_BLEND_RECIPES = {
    "chai-spice-powder", "five-spice-powder", "mixed-spice-powder",
    "garam-masala-powder",
}


def _spice_rank(name: str, herb_context: str = None):
    """None if `name` is not a tracked spice. Base spices rank by their
    required order; every warm spice ties at the next rank, since order among
    them is not enforced.

    `herb_context`, when given, is what the coriander herb-or-spice signal is
    read from: a measure word such as "handful" lives in `amount:`, not in
    `item:` (#982).
    """
    if _SPICE_GARLIC_EXCLUDE.search(name):
        return None
    context = name if herb_context is None else herb_context
    for i, word in enumerate(_SPICE_BASE_ORDER):
        if word == "coriander" and _CORIANDER_HERB_SIGNAL.search(context):
            continue
        if re.search(rf"\b{word}\b", name, re.I):
            return i
    for word in _SPICE_WARM:
        if re.search(rf"\b{re.escape(word)}\b", name, re.I):
            return len(_SPICE_BASE_ORDER)
    return None


def test_spice_order_within_group(recipe):
    """Helen's cooking convention: within one ingredient group, coriander,
    cumin, turmeric, fennel in that order among themselves, then whichever of
    the warm spices are used, in any order, always after the base spices.
    Recipes for a named spice blend are exempt: that order is the blend's own.
    """
    if recipe.slug in _SPICE_BLEND_RECIPES:
        return
    problems = []
    for group in recipe.fm.get("ingredient_groups") or []:
        ranked = []
        for it in group.get("items") or []:
            text = it.get("item", "") if isinstance(it, dict) else str(it)
            amount = it.get("amount", "") if isinstance(it, dict) else ""
            name = re.split(r"[,(]", text)[0].strip()
            rank = _spice_rank(name, f"{amount} {text}")
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
