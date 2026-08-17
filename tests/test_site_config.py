"""Architecture regression tests.

These do not test recipes. They test that the structure we built stays built —
that the single sources of truth stay single, and that values which now have a
home do not silently sprout copies elsewhere.

Everything here exists because it went wrong at least once.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data" / "food"


def read(*parts) -> str:
    return (ROOT.joinpath(*parts)).read_text(encoding="utf-8")


# --- the family-button threshold --------------------------------------------

def test_family_button_min_chars_is_three():
    """The value itself, asserted once, in the one place it lives."""
    path = DATA / "ingredient_words.yml"
    assert path.exists(), (
        "_data/food/ingredient_words.yml is missing. It holds the ingredient search "
        "vocabulary and the family-button threshold; without it, filters.js "
        "falls back to defaults and search loses its synonyms."
    )
    vocab = yaml.safe_load(path.read_text(encoding="utf-8"))
    actual = (vocab.get("search") or {}).get("family_button_min_chars")
    assert actual == 3, (
        f"family_button_min_chars is {actual!r}, should be 3.\n"
        f"Two is too permissive — with a two-character query nearly every "
        f"ingredient matches something and the family buttons become noise "
        f"rather than a shortcut."
    )


def test_filters_js_holds_no_literal_threshold():
    """The regression guard, and the point of the whole exercise.

    For months this value lived as a bare `query.length >= 3` in filters.js with
    nothing defining it, so every rewrite of that file re-derived it from
    scratch and landed on 2. It now lives in _data/food/ingredient_words.yml, read
    into FAMILY_BUTTON_MIN_CHARS in assets/js/ingredient-search.js (the
    matching algorithm moved there so it could be tested directly with
    Node — see tests/js/ingredient-search.test.js — filters.js is DOM wiring
    only now). If a literal ever reappears in either file, this fails.
    """
    js = read("assets", "js", "filters.js")
    search_js = read("assets", "js", "ingredient-search.js")
    literals = re.findall(r"query\.length\s*[<>]=?\s*\d+", js + search_js)
    assert not literals, (
        f"Hardcoded query-length comparison(s) found: {literals}.\n"
        f"This threshold is defined in _data/food/ingredient_words.yml as "
        f"`search.family_button_min_chars` and read into FAMILY_BUTTON_MIN_CHARS "
        f"in ingredient-search.js. Use that constant instead of a literal — the "
        f"literal is exactly the thing that kept resetting to 2."
    )
    assert "FAMILY_BUTTON_MIN_CHARS" in search_js, (
        "assets/js/ingredient-search.js no longer references "
        "FAMILY_BUTTON_MIN_CHARS. The threshold should be read from the "
        "vocabulary, not inlined."
    )


def test_vocabulary_is_emitted_to_the_page():
    """filters.js can only read the vocabulary if index.html emits it."""
    html = read("food", "index.html")
    assert 'id="ingredient-vocabulary"' in html, (
        'food/index.html no longer emits the <script type="application/json" '
        'id="ingredient-vocabulary"> block. Without it filters.js falls back to '
        "empty singulars and synonyms — ingredient search still works, but "
        '"cheese" stops returning cheddar and the collapse behaviour is lost.'
    )
    # Match the <script src> tag specifically — the word "filters.js" also
    # appears in a comment above the block, which would give a false failure.
    tag = re.search(r"<script src=[^>]*filters\.js", html)
    assert tag, "food/index.html no longer loads js/filters.js at all."
    assert html.index('id="ingredient-vocabulary"') < tag.start(), (
        "The ingredient-vocabulary block must appear BEFORE the filters.js "
        "script tag, or the script will run before the data exists."
    )


def test_ingredient_search_js_loads_before_filters_js():
    """filters.js calls HTF.ingredientSearch at startup -- it must already exist.

    Same shape as assets.js needing to load before everything else: the
    matching algorithm lives in ingredient-search.js (see
    model_instructions/DEV_JOBS_v22.md §3.4), and filters.js wires it up
    with `HTF.ingredientSearch.create(...)` in its very first few lines.
    """
    html = read("food", "index.html")
    search_tag = re.search(r"<script src=[^>]*ingredient-search\.js", html)
    filters_tag = re.search(r"<script src=[^>]*filters\.js", html)
    assert search_tag, "food/index.html no longer loads assets/js/ingredient-search.js."
    assert filters_tag, "food/index.html no longer loads assets/js/filters.js."
    assert search_tag.start() < filters_tag.start(), (
        "ingredient-search.js must load BEFORE filters.js, or "
        "HTF.ingredientSearch won't exist yet when filters.js runs."
    )


def test_recipe_list_js_loads_before_filters_js():
    """filters.js calls HTF.recipeList at startup (shuffleRecipeList, update's
    pagination) -- it must already exist, same trap as ingredient-search.js.
    """
    html = read("food", "index.html")
    recipe_list_tag = re.search(r"<script src=[^>]*recipe-list\.js", html)
    filters_tag = re.search(r"<script src=[^>]*filters\.js", html)
    assert recipe_list_tag, "food/index.html no longer loads assets/js/recipe-list.js."
    assert filters_tag, "food/index.html no longer loads assets/js/filters.js."
    assert recipe_list_tag.start() < filters_tag.start(), (
        "recipe-list.js must load BEFORE filters.js, or "
        "HTF.recipeList won't exist yet when filters.js runs."
    )


def test_filter_state_js_loads_before_filters_js():
    """filters.js reads HTF.filterState at startup -- it must already exist.

    Same trap as ingredient-search.js and recipe-list.js above, and worth
    stating again because of how it fails rather than because the shape is
    new. GitHub issue #40 made every taxonomy badge a link into
    `/food/?star=…&tag=…`, and filters.js applies that query string in its
    last few lines via HTF.filterState.parseQuery. Loaded the wrong way round,
    the call throws once and the whole DOMContentLoaded handler dies with it:
    no shuffle, no filter buttons, and `.recipe-list` never has its
    `visibility: hidden` lifted -- a blank page, with the only evidence in a
    console nobody has open.
    """
    html = read("food", "index.html")
    filter_state_tag = re.search(r"<script src=[^>]*filter-state\.js", html)
    filters_tag = re.search(r"<script src=[^>]*filters\.js", html)
    assert filter_state_tag, "food/index.html no longer loads assets/js/filter-state.js."
    assert filters_tag, "food/index.html no longer loads assets/js/filters.js."
    assert filter_state_tag.start() < filters_tag.start(), (
        "filter-state.js must load BEFORE filters.js, or "
        "HTF.filterState won't exist yet when filters.js runs."
    )


def test_cook_schedule_js_loads_before_cook_timer_js():
    """cook-timer.js reads HTF.cookSchedule at startup -- it must already exist.

    Third of the same trap as ingredient-search.js and recipe-list.js above:
    the arithmetic (resolving a method to minutes, the backwards-from-the-plate
    clock maths, the rounding) lives in assets/js/cook-schedule.js, and
    cook-timer.js grabs it into `CS` in its first few lines. Loaded the wrong
    way round the timings page throws once, silently, and shows nothing but an
    empty table -- there is no visible error to notice.
    """
    html = read("food", "reference", "timings.html")
    schedule_tag = re.search(r"<script src=[^>]*cook-schedule\.js", html)
    timer_tag = re.search(r"<script src=[^>]*cook-timer\.js", html)
    assert schedule_tag, (
        "food/reference/timings.html no longer loads assets/js/cook-schedule.js."
    )
    assert timer_tag, (
        "food/reference/timings.html no longer loads assets/js/cook-timer.js."
    )
    assert schedule_tag.start() < timer_tag.start(), (
        "cook-schedule.js must load BEFORE cook-timer.js, or "
        "HTF.cookSchedule won't exist yet when cook-timer.js runs."
    )


def test_cook_timer_js_holds_no_schedule_arithmetic():
    """The maths lives in cook-schedule.js, where tests/js can reach it.

    cook-timer.js is DOM wiring. If a rate multiplication or a minutes-from-
    midnight calculation reappears here it is, by construction, untested again --
    which is the state GitHub issue #221 existed to end.
    """
    js = read("assets", "js", "cook-timer.js")
    for fragment in ("rate_min", "* 1440", "+= 1440", "Math.round(mins / 5)"):
        assert fragment not in js, (
            f"assets/js/cook-timer.js contains `{fragment}`. Schedule arithmetic "
            f"belongs in assets/js/cook-schedule.js (HTF.cookSchedule), covered by "
            f"tests/js/cook-schedule.test.js."
        )


def test_filters_js_holds_no_loose_filter_state_variables():
    """The filter state lives in filter-state.js, where tests/js can reach it.

    Same spirit as test_cook_timer_js_holds_no_schedule_arithmetic above, and
    for a sharper reason. GitHub issue #52, step one: filters.js used to hold
    its filter state as six loose variables inside 900 lines of DOM wiring, and
    three times in two days the same bug shipped -- clearAllFilters() emptied
    N of them while the clear-all button's visibility predicate checked N-1, so
    the button hid while it still had work to do. Each was found by eye.

    The state is now ONE object whose fields, cleared value and both "is
    anything set" answers are all derived by iterating FIELD_SPEC in
    assets/js/filter-state.js, covered by the generated per-field cases in
    tests/js/filter-state.test.js. If a loose variable reappears here it is, by
    construction, outside that enumeration again -- and the generated test
    cannot see it, because it generates from FIELDS.

    Declarations only. The names are still perfectly good English and may well
    appear in prose in a comment; what must not come back is filters.js owning
    the value.
    """
    js = read("assets", "js", "filters.js")
    for name in (
        "activeTags",
        "activeStar",
        "activeIngredient",
        "activeMetaFilters",
        "nameQuery",
        "isSearching",
    ):
        assert not re.search(rf"\bvar\s+{name}\b", js), (
            f"assets/js/filters.js declares `var {name}`. The index's filter "
            f"state belongs in assets/js/filter-state.js -- add the field to "
            f"FIELD_SPEC there, where emptyState(), hasAnythingToClear() and "
            f"hasNarrowingFilter() all pick it up at once and "
            f"tests/js/filter-state.test.js generates a case for it."
        )

    assert "FilterState.emptyState()" in js, (
        "assets/js/filters.js no longer builds its state from "
        "HTF.filterState.emptyState(). clearAllFilters() must replace the "
        "whole state object rather than empty it field by field, or the "
        "clear-all button's predicate can drift from it again (issue #52)."
    )


# --- the derived ingredient index (the "they hate peas" filter) --------------

def _derivation_block(html: str) -> str:
    """The Liquid that builds `_all_ing` in food/index.html, on its own.

    Grabbing the block rather than the whole file matters for the incidental
    check below: the word "incidental" is free to appear anywhere else in the
    template, and only its appearance INSIDE this loop would change what the
    index contains. {% comment %} blocks come out for the same reason one step
    down: the loop's own comment has to be able to say the word "incidental" in
    order to explain why the code never says it.
    """
    start = html.find('{% assign _all_ing = "|" %}')
    assert start != -1, (
        'food/index.html no longer builds `_all_ing`. The derived ingredient '
        'index is what the exclude filter matches against (GitHub issue #52) — '
        'without it, "show me everything without peas" has nothing to read.'
    )
    end = html.find("data-all-ingredients", start)
    assert end != -1, "the `_all_ing` accumulator is built but never emitted."
    return re.sub(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", html[start:end], flags=re.S)


def test_index_emits_the_derived_ingredient_index():
    """GitHub issue #52: "they hate peas, show me everything without peas".

    Answering that needs each row's COMPLETE ingredient list, not
    main_ingredients. main_ingredients is a deliberately partial hint — fine to
    include ON, dangerous to exclude BY. Nine recipes list an olive oil in
    ingredient_groups and not one of them names it in main_ingredients, so an
    exclusion answered from main_ingredients would hand back nine recipes
    containing the thing the cook is avoiding; coriander is 3 against 8,
    mushrooms 3 against 4. Hence a second, derived attribute rather than a
    reuse of the first.
    """
    html = read("food", "index.html")
    assert "data-all-ingredients=" in html, (
        "food/index.html no longer emits data-all-ingredients on its recipe "
        "rows. filters.js builds both the exclude picker's vocabulary and every "
        "row's own entry set from that attribute, so without it the dislike "
        "navigator offers nothing and excludes nothing."
    )

    block = _derivation_block(html)
    assert "ingredient_groups" in block, (
        "the derived index is no longer built from recipe.ingredient_groups. "
        "That is the complete, required ingredient list; anything else "
        "(main_ingredients above all) is a partial one, and a partial list is "
        "precisely what makes an exclusion filter lie."
    )

    # The separator, and why it is not the comma data-ingredients uses. That
    # attribute joins main_ingredients, a curated vocabulary the taxonomy tests
    # already keep comma-free. These values are arbitrary `item:` free text
    # where the comma is the commonest character there is, and it is kept out of
    # the value only by the truncation in the same expression — a separator
    # whose safety depends on another rule staying exactly as it is.
    assert re.search(r'data-all-ingredients="\{\{\s*_all_ing', html), (
        "data-all-ingredients is no longer emitting the `_all_ing` accumulator."
    )
    assert '| append: "|"' in block or "| append: '|'" in block, (
        "the derived index is no longer joined on `|`.\n"
        "Do not join it on commas: unlike main_ingredients, these values are "
        "arbitrary `item:` free text (1,393 of the 3,751 item strings across "
        "recipes and drafts contain a comma), and nothing validates them. Pick "
        "a separator that cannot appear in the value rather than one that "
        "happens not to today."
    )


def test_the_derived_ingredient_index_counts_incidental_items():
    """`incidental: true` items are IN the index, deliberately.

    The flag hides an item from main_ingredients and from the recipe page's own
    Ingredients section, which is right for "what is this dish made of" — but
    "we didn't itemise the frying oil" is not an answer to someone avoiding it.
    Helen's call, GitHub issue #52.

    Two halves, because either alone can go quiet: the template must not filter
    the flag out, and the collection must still contain an example for that to
    mean anything.
    """
    from conftest import ALL_RECIPES

    block = _derivation_block(read("food", "index.html"))
    assert "incidental" not in block, (
        "food/index.html's derived ingredient index now skips `incidental: "
        "true` items. Put them back: they are hidden from main_ingredients and "
        "from the rendered ingredient list on purpose, but an exclusion filter "
        'that quietly ignores the frying oil tells someone avoiding it "no '
        'oil listed" about a recipe that fries in it.'
    )

    with_incidentals = [
        (r.slug, item["item"])
        for r in ALL_RECIPES
        for group in (r.fm.get("ingredient_groups") or [])
        for item in (group.get("items") or [])
        if isinstance(item, dict) and item.get("incidental") and item.get("item")
    ]
    assert with_incidentals, (
        "no recipe in _food_recipes/ uses `incidental: true` any more, so the "
        "half of this test that checks real data is now checking nothing.\n"
        "As of 2026-08-16 the live example was "
        "vietnamese-spiced-braised-venison-haunch.md's 'neutral oil'. If it has "
        "genuinely gone, point this at another one, or delete this half "
        "deliberately — do not leave it passing over an empty list."
    )

    # The Liquid's own rule, mirrored: name up to the first comma or open
    # bracket, lowercased. A PARALLEL implementation, not a render of the real
    # template (same caveat as _sink_pantry above) — it guards the rule, not the
    # template's fidelity to it.
    for slug, item_text in with_incidentals:
        name = re.split(r"[,(]", item_text)[0].strip().lower()
        assert name, (
            f"_food_recipes/{slug}.md has an incidental item ({item_text!r}) "
            f"that derives to an empty index entry, so it can never be excluded."
        )


# --- a badge is a control, not a caption -------------------------------------

def test_recipe_badges_are_links_carrying_their_own_filter_value():
    """GitHub issue #40. Every taxonomy badge is an <a> with data-tag/data-star.

    Three separate things all rest on this one line of markup, and none of
    them fails loudly if it regresses to a <span>:

      1. KEYBOARD REACH. A <span> with a click handler is invisible to the tab
         key and to a screen reader's link list. An <a href> is focusable and
         announced for free, with no roles or tabindex to remember.
      2. THE HANDLER'S INPUT. filters.js reads `badge.dataset.tag` /
         `badge.dataset.star` -- both to route a click and to decide which
         badges get `.badge--matched`. It used to match on the badge's TEXT,
         which could not tell a mood badge from a star one.
      3. THE FALLBACK. The href is what makes middle-click, open-in-new-tab
         and copy-link-address work, and it is the entire mechanism on a
         recipe page, where no script intercepts anything.

    Asserted against the template rather than the built site so it holds
    without a build, and covers both include sites at once -- food/index.html
    and _layouts/recipe.html share this one partial.
    """
    html = read("_includes", "recipe_badges.html")

    assert "<span class=\"badge" not in html, (
        "_includes/recipe_badges.html emits a taxonomy badge as a <span> "
        "again. It must be an <a>: a span is unreachable by keyboard and "
        "carries no href for middle-click or open-in-new-tab to use."
    )

    for attr, kind in (("data-star", "star ingredient"), ("data-tag", "tag")):
        tag_match = re.search(
            r'<a\s[^>]*class="badge[^"]*"[^>]*\b' + attr + r'="[^"]*"[^>]*href="[^"]*"',
            html,
        )
        assert tag_match, (
            f"_includes/recipe_badges.html no longer emits an <a class=\"badge…\" "
            f"{attr}=\"…\" href=\"…\"> for the {kind}.\n"
            f"filters.js routes a badge click by reading {attr} off the element "
            f"it was clicked on, and paints .badge--matched from the same "
            f"attribute. Without it a badge is a caption again."
        )

    # The query grammar's own shape, at the one place it is written into a URL.
    # url_encode specifically: it is Ruby's CGI.escape, so it spells a space as
    # `+`, and assets/js/filter-state.js's parseQuery is written to undo that.
    # Swapping it for a filter that emits %20 would work; swapping it for no
    # filter at all would break `oily fish` and five other real values.
    assert "url_encode" in html, (
        "_includes/recipe_badges.html builds a badge href without url_encode. "
        "Six taxonomy values contain a space (oily fish, root veg, carbs "
        "party, hot snack, ice cream, one-handed food) and would produce a "
        "URL with a raw space in it."
    )
    for param in ("?star=", "?tag="):
        assert param in html, (
            f"_includes/recipe_badges.html no longer emits `{param}` in a badge "
            f"href. The query grammar is documented in "
            f"assets/js/filter-state.js's header -- one parameter per filter "
            f"KIND -- and filters.js only knows how to read that one."
        )


def test_filters_js_holds_no_ingredient_vocabulary():
    """Singulars and synonyms belong in YAML, not in the JavaScript."""
    js = read("assets", "js", "filters.js")
    for name in ("var singularMap = {", "var synonymMap = {"):
        assert name not in js, (
            f"js/filters.js declares `{name}...` inline. The ingredient "
            f"vocabulary lives in _data/food/ingredient_words.yml and is read from "
            f"the page; adding a word should be a YAML edit, not a code edit."
        )


# --- colour stays in one place ----------------------------------------------

TEMPLATES = ["food/index.html", "_layouts/recipe.html", "_layouts/default.html",
             "_includes/filter_group.html", "_includes/recipe_badges.html"]


@pytest.mark.parametrize("relpath", TEMPLATES)
def test_no_inline_highlighter_fill(relpath):
    """Colour is set by class, in _sass/food/_palette.scss, and nowhere else.

    Inline styles beat stylesheet rules, so a single inline fill silently
    overrides the palette and makes editing the palette appear to do nothing.
    """
    path = ROOT / relpath
    if not path.exists():
        pytest.skip(f"{relpath} does not exist")
    text = path.read_text(encoding="utf-8")
    assert "--highlighter-fill" not in text, (
        f"{relpath} sets --highlighter-fill inline.\n"
        f"Inline styles win over the stylesheet, so this overrides the "
        f"`.category--*` / `.search--*` rules in _sass/food/_palette.scss and makes "
        f"the palette look broken when you edit it. Add a class instead."
    )


@pytest.mark.parametrize("relpath", ["_data/colors.yml", "_data/recipe_sections.yml"])
def test_deleted_data_files_stay_deleted(relpath):
    """Both were removed in July 2026 and should not come back.

    colors.yml duplicated the palette; recipe_sections.yml was entirely dead —
    assigned in recipe.html and never used.
    """
    assert not (ROOT / relpath).exists(), (
        f"{relpath} has reappeared. Colour belongs in _sass/food/_palette.scss only; "
        f"section shape and texture are chosen in js/highlighter.js."
    )


def test_palette_is_the_only_place_hex_colours_are_written():
    """No script writes a colour down. The palette is the only source.

    This used to assert that assets/js/colours.js called getPropertyValue — it
    read food's --colour-* custom properties off :root so JS-injected SVG could
    be recoloured without a second copy of the palette. The 2026-07-31 recipe
    redesign removed the last decoration that needed a colour in JavaScript, so
    colours.js and the :root block both went, and that assertion had nothing
    left to read.

    Checking every script for a hex literal is what the old test was reaching
    for anyway, and it is stronger: it covers files colours.js never did, and it
    keeps biting now that the bridge it guarded no longer exists. If a script
    ever needs a colour again, the answer is a CSS custom property read at
    runtime, not a literal here.

    COMMENTS ARE STRIPPED FIRST -- BOTH KINDS, as of 2026-08-16. This used to
    strip only `//` (`line.split("//")[0]`), which is every comment in most of
    these scripts and almost none of the comments in cook-timer.js, where the
    prose is written in `/* */` blocks. So `issue #244` in a block comment was
    reported as a three-digit colour, and the same false positive was waiting
    for every three- and six-digit issue number anyone might cite that way:
    #139, #204, #221, #227, #241 are all live references in this codebase and
    all read as hex.

    That is not a cosmetic complaint. A check that cries wolf on correct code
    gets switched off, or -- worse here -- gets worked around by writing the
    reference wrongly, and the guard ends up shaping the prose instead of
    guarding the palette. Same reasoning test_notes_are_not_damaged in
    tests/test_reference_data.py gives for keeping its own checks exact rather
    than heuristic, and it applies to the code this suite reads as much as to
    the data.

    _strip_js_comments (defined below, with the SVG guards) is line-preserving
    for exactly this test's sake: the failure names `file:lineno`, so blanking a
    block comment must leave its newlines behind.
    """
    js_files = sorted((ROOT / "assets" / "js").glob("*.js"))
    assert js_files, "No scripts found — this test would pass while checking nothing."

    offenders = []
    for path in js_files:
        code = _strip_js_comments(path.read_text(encoding="utf-8"))
        for i, line in enumerate(code.split("\n"), 1):
            for match in re.finditer(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b", line):
                offenders.append(f"{path.name}:{i} {match.group(0)}")

    assert not offenders, (
        "Hex colour(s) written into JavaScript:\n  " + "\n  ".join(offenders)
        + "\n\nColour lives in _sass/food/_palette.scss and nowhere else. A "
          "script that needs one should read a CSS custom property at runtime, "
          "so editing the palette actually changes the page."
    )


# --- the pantry list stays honest -------------------------------------------

def test_pantry_entries_are_actually_used():
    """Every pantry staple should appear somewhere in the collection.

    An entry that matches nothing is either a typo or a leftover, and either way
    it is dead weight in a list whose whole job is to be short and deliberate.
    Matching is exact and lowercase, exactly as index.html does it.
    """
    from conftest import ALL_RECIPES, ALL_DRAFTS
    path = DATA / "pantry.yml"
    if not path.exists():
        pytest.skip("_data/food/pantry.yml does not exist yet")
    pantry = yaml.safe_load(path.read_text(encoding="utf-8")) or []

    used = set()
    for r in ALL_RECIPES + ALL_DRAFTS:
        for entry in (r.fm.get("main_ingredients") or []):
            used.add(str(entry).lower())

    unused = [p for p in pantry if p.lower() not in used]
    assert not unused, (
        f"_data/food/pantry.yml lists {unused}, which match no "
        f"main_ingredients entry anywhere.\n"
        f"Matching is exact — 'onion' does not demote 'red onions'. Either the "
        f"entry is a typo, or it is aspirational and should come out until "
        f"something actually uses it."
    )


def test_pantry_list_is_lowercase():
    """The match in food/index.html is `ing | downcase` against a raw `contains`
    check on this list -- an uppercase entry here would silently never match
    anything (Liquid does not lowercase the pantry side), the exact "test that
    cannot fail and not notice" failure mode HANDOVER_v26.md §12 warns about:
    green, no error, just an entry that's dead weight forever.
    """
    path = DATA / "pantry.yml"
    if not path.exists():
        pytest.skip("_data/food/pantry.yml does not exist yet")
    pantry = yaml.safe_load(path.read_text(encoding="utf-8")) or []

    not_lower = [p for p in pantry if p != p.lower()]
    assert not not_lower, (
        f"_data/food/pantry.yml has non-lowercase entries: {not_lower}.\n"
        f"food/index.html compares `ing | downcase` against this list as-is -- an "
        f"uppercase entry here matches nothing, ever, and nothing will tell you."
    )


def _sink_pantry(main_ingredients, pantry):
    """Python mirror of food/index.html's ordering Liquid (issue #107/#74):
    non-pantry ingredients first, pantry staples sunk to the end, authored
    order preserved within each half. Exact, lowercase match.

    This is a *parallel* implementation, not a render of the real template --
    it cannot catch food/index.html drifting from this rule, only regressions
    in the rule itself. If the Liquid there changes, update this to match, or
    this test will pass green while checking something the page no longer does.
    """
    lead = [i for i in main_ingredients if str(i).lower() not in pantry]
    tail = [i for i in main_ingredients if str(i).lower() in pantry]
    return lead + tail


def test_main_ingredients_sink_pantry_to_the_end():
    """GitHub issue #74/#107: main_ingredients render in "larder order" on the
    index page -- distinctive ingredients first, pantry staples trailing, so
    the eye meets what makes the dish itself before the things every kitchen
    already has. Checks the rule against known cases, not just that it runs.
    """
    pantry = {"onion", "butter", "salt", "garlic"}

    # Ordinary split: distinctive ingredients lead, pantry trails.
    assert _sink_pantry(["chicken", "onion", "lemon", "butter"], pantry) == [
        "chicken", "lemon", "onion", "butter",
    ]

    # Exact match only -- a variety naming itself is not demoted (§6/pantry.yml).
    assert _sink_pantry(["red onions", "onion"], pantry) == ["red onions", "onion"]

    # Case-insensitive: `ing | downcase` in the template.
    assert _sink_pantry(["Onion", "Chicken"], pantry) == ["Chicken", "Onion"]

    # Authored order is preserved within each half, not re-sorted.
    assert _sink_pantry(["butter", "salt", "lemon", "chicken"], pantry) == [
        "lemon", "chicken", "butter", "salt",
    ]

    # Nothing pantry: no reordering at all.
    assert _sink_pantry(["lemon", "chicken"], pantry) == ["lemon", "chicken"]


# --- one base URL, one fetch path -------------------------------------------

JS_DIR = ROOT / "assets" / "js"


def test_base_url_is_derived_in_exactly_one_place():
    """The base URL used to be copy-pasted four times, and the copies drifted.

    Every decorative asset URL is built from this value, and the value changes
    when `baseurl` changes — so a second copy is a second chance to be subtly
    wrong on the day you deploy.
    """
    pattern = re.compile(r"""meta\[name=["']base-url["']\]""")
    offenders = []
    for path in sorted(JS_DIR.glob("*.js")) + [ROOT / "_layouts" / "default.html",
                                               ROOT / "_layouts" / "recipe.html",
                                               ROOT / "food" / "index.html"]:
        if not path.exists():
            continue
        hits = len(pattern.findall(path.read_text(encoding="utf-8")))
        # default.html legitimately EMITS the meta tag once; that is not a read.
        if path.name == "default.html":
            hits = max(0, hits)
        if hits and path.name != "assets.js":
            offenders.append(f"{path.name} ({hits})")
    assert not offenders, (
        f"base-url is read outside js/assets.js: {offenders}.\n"
        f"Use window.HTF.base or window.HTF.asset(path) instead. assets.js is "
        f"loaded first in default.html precisely so that it can be."
    )


def test_assets_js_loads_before_any_other_script():
    """assets.js defines window.HTF, which every other script calls at parse time.

    It has to load first, and "end of <body>" is NOT first here. A page
    layout's own scripts are emitted inside `{{ content }}`, which default.html
    renders into <main> — ABOVE its own closing scripts. So recipe.html's
    section-rule.js (now heading-underline.js, renamed when the redesign cut
    four of its five jobs) ran before assets.js and threw
    `Cannot read properties of undefined (reading 'makeShuffledPicker')` on its
    first line, silently removing the section rules, the ingredient bullets and
    the section-heading doodles. They were missing for weeks.

    The fix is assets.js at the end of <head>, above `{{ content }}`. It reads
    only the two meta tags above it and touches no body element at parse time.
    """
    # Strip Liquid comments FIRST. The comment above assets.js explains the
    # rule by quoting `{{ content }}`, and a naive find() locates that mention
    # rather than the real render — which is the same read-a-comment-as-code
    # mistake this file's other guards were bitten by.
    html = re.sub(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", "",
                  read("_layouts", "default.html"), flags=re.S)

    tags = list(re.finditer(r"<script\s[^>]*src=[^>]*>", html))
    assert tags, "_layouts/default.html loads no scripts at all."

    first = tags[0]
    assert "assets.js" in first.group(0), (
        f"The first script in _layouts/default.html is {first.group(0)!r}, not "
        f"assets.js.\nEverything else calls window.HTF at parse time, so "
        f"assets.js must come first or the page throws before it draws."
    )

    content = html.find("{{ content }}")
    assert content != -1, (
        "_layouts/default.html no longer renders {{ content }}. If the marker "
        "was renamed, this check needs updating — it exists to prove assets.js "
        "sits ABOVE the point where a page layout injects its own scripts."
    )
    assert first.start() < content, (
        "assets.js is emitted BELOW {{ content }} in _layouts/default.html.\n"
        "A page layout's scripts land inside content, so they would run first "
        "and find window.HTF undefined. Move assets.js into <head>."
    )


IMG_DIR = ROOT / "assets" / "img"


def _strip_js_comments(text: str) -> str:
    """Blank // and /* */ comments so a guard cannot match its own explanation.

    LINE NUMBERS SURVIVE, and that is the whole reason this replaces the comment
    rather than deleting it: every caller reports `file:lineno`, and a block
    comment removed outright takes its newlines with it, so every line number
    after the first `/* */` in the file comes out short by however many lines
    that comment ran to. A guard that names the wrong line is worse than one
    that names none. Each stripped block leaves exactly the newlines it held.

    Trailing `//` is stripped as well as a whole-line one -- a hex literal in an
    end-of-line comment is a comment, wherever it sits on the line.
    """
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"),
                  text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def test_svg_injection_does_not_assume_a_space_after_the_svg_tag():
    """`'<svg '` with a trailing space is a trap, and it cost weeks.

    decorations.js rewrites each decorative SVG as it injects it — stripping the
    mm dimensions and adding `position:absolute` so the wash sits BEHIND its
    label. Every one of those rewrites matched the literal `'<svg '`.

    Inkscape puts each attribute on its own line, so all 100 files under
    backgrounds-headers/ open with `<svg\\n   width="…mm"`. Not one replace
    matched. String.replace returns the input unchanged when it does not match,
    so there was no error anywhere — the wash simply rendered at its natural
    14mm × 4mm, inline, to the left of the label text.

    Match `<svg` plus whitespace instead. Comments are stripped first, because
    the comment in decorations.js explaining this rule quotes the bad literal.
    """
    # Only the SEARCH argument of a replace, never the replacement. The
    # replacement legitimately contains `<svg ` — it is what gets written back
    # — so a bare search for the literal flags every correct call as a fault.
    # First version of this test did exactly that and failed on the fix.
    search_arg = re.compile(
        r"""\.replace\(\s*(?:(['"])<svg |/[^/\n]*<svg )"""
    )
    offenders = []
    for path in sorted(JS_DIR.glob("*.js")):
        code = _strip_js_comments(path.read_text(encoding="utf-8"))
        for match in re.finditer(search_arg, code):
            line = code[:match.start()].count("\n") + 1
            offenders.append(f"{path.name}:{line} {match.group(0).strip()!r}")
    assert not offenders, (
        "SVG rewriting assumes a space after `<svg`:\n  " + "\n  ".join(offenders)
        + "\n\nUse /<svg(?=[\\s>])/ or /(<svg\\s[^>]*?)…/. Inkscape-exported "
          "files put every attribute on its own line, and a replace that does "
          "not match fails silently."
    )


def test_every_shipped_svg_is_matched_by_the_injection_pattern():
    """The other half: assets must be matchable, not just the code tolerant.

    Guards the actual files rather than the regex, so dropping in artwork
    exported by something with yet another convention fails here — loudly, once
    — instead of rendering wrong on a page nobody reloads for a fortnight.
    """
    pattern = re.compile(r"<svg(?=[\s>])")
    svgs = sorted(IMG_DIR.rglob("*.svg"))
    assert svgs, f"No SVGs found under {IMG_DIR} — has the artwork moved?"
    offenders = [
        str(p.relative_to(ROOT)) for p in svgs
        if not pattern.search(p.read_text(encoding="utf-8", errors="replace"))
    ]
    assert not offenders, (
        f"{len(offenders)} SVG(s) have an opening tag the injection cannot "
        f"match:\n  " + "\n  ".join(offenders[:10])
        + "\n\nThe rewrite would leave them at their natural size and position."
    )


def test_every_shipped_svg_actually_parses():
    """An SVG is XML, and a browser that cannot parse it renders NOTHING.

    GitHub issue #241, and it is a good demonstration of why "the file looks
    right" is not the same as "the file works". The favicon was changed to a
    black H on the brand magenta, and the fill values were correct -- but the
    comment explaining the choice used ` -- ` as a dash, the way a commit
    message here does. A double hyphen is illegal inside an XML comment, so
    the whole document failed to parse, every browser silently kept showing
    the previously cached icon, and the change appeared simply not to have
    happened. It was diagnosed only when Helen opened the .svg directly and
    got a parser error page.

    Nothing else could have caught it. The build does not parse SVGs, and
    test_every_shipped_svg_is_matched_by_the_injection_pattern above reads
    each file as TEXT, looking for an opening tag -- which a malformed file
    still has.

    HOUSE STYLE POINT worth keeping with the test: prose in this repo uses an
    em dash (HANDOVER §5). The ASCII `--` exception is for COMMIT MESSAGES
    specifically. Inside an SVG comment it is not merely off-style, it is a
    parse error.

    Covers _includes/icons/ as well as assets/img/: those partials are
    inlined straight into the page by default.html, so a malformed one takes
    the surrounding markup with it rather than just failing to draw.
    """
    import xml.dom.minidom

    svgs = sorted(IMG_DIR.rglob("*.svg")) + sorted((ROOT / "_includes" / "icons").rglob("*.svg"))
    assert svgs, (
        f"No SVGs found under {IMG_DIR} or _includes/icons/ — either the "
        f"artwork has moved, or this scan has stopped finding it, and a scan "
        f"that finds nothing passes."
    )

    broken = []
    for path in svgs:
        try:
            xml.dom.minidom.parse(str(path))
        except Exception as exc:
            broken.append(f"{path.relative_to(ROOT)}: {exc}")

    assert not broken, (
        "SVG(s) that are not well-formed XML, so a browser will render "
        "nothing at all for them:\n  " + "\n  ".join(broken)
        + "\n\nThe usual cause is `--` inside a <!-- comment -->, which is "
          "illegal in XML. Use an em dash — in artwork comments; the ASCII "
          "double hyphen is a commit-message convention only."
    )


def test_site_key_is_derived_in_exactly_one_place():
    """Same discipline as the base URL, for the same reason.

    Food and cocktails keep separate artwork under assets/img/<site>/, so every
    decorative fetch needs the site key. It is emitted once by default.html and
    read once by assets.js, which exposes HTF.site and HTF.siteAsset(). A second
    reader is a second thing to forget when a third site appears — and unlike
    the base URL, a wrong site key fails only on the site nobody was looking at.
    """
    pattern = re.compile(r"""meta\[name=["']site-key["']\]""")
    offenders = []
    for path in sorted(JS_DIR.glob("*.js")):
        if path.name == "assets.js":
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(path.name)
    assert not offenders, (
        f"site-key is read outside assets.js: {offenders}.\n"
        f"Use window.HTF.site, or window.HTF.siteAsset(path) to build an "
        f"artwork URL. assets.js loads first in default.html so that it can be."
    )


def test_artwork_fetches_go_through_site_asset():
    """No script may hardcode which site's artwork it is loading.

    `HTF.asset('/assets/img/…')` reaches into a specific site's set from code
    that should not know which site it is on — it is how tape-food-N.svg came to
    be named in decorations.js. Artwork goes through HTF.siteAsset(), which
    builds the path from the page's site key.

    assets/img/favicon.svg is the one genuinely shared image and is referenced
    from the template, not from JS, so nothing here needs an exception.
    """
    pattern = re.compile(r"""HTF\.asset\(\s*['"]/assets/img/""")
    offenders = []
    for path in sorted(JS_DIR.glob("*.js")):
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.name}: {match.group(0)}…")
    assert not offenders, (
        "Artwork fetched through HTF.asset() rather than HTF.siteAsset():\n  "
        + "\n  ".join(offenders)
        + "\n\nHTF.asset() is for genuinely shared files. Anything under a "
          "site's own image directory must go through HTF.siteAsset(path), "
          "which returns null on a page with no site so the caller can skip it."
    )


def test_no_silently_swallowed_fetch_errors():
    """An empty catch on an asset fetch is worse than no catch.

    All five decorative SVG fetches used to end in `.catch(function() {})`, so a
    wrong baseurl produced a site with no decoration and a completely clean
    console. Fetching now goes through HTF.fetchSvg, which warns with the URL
    and names the likely cause.
    """
    empty_catch = re.compile(r"\.catch\(\s*function\s*\(\s*\)\s*\{\s*\}\s*\)")
    offenders = []
    for path in sorted(JS_DIR.glob("*.js")) + list((ROOT / "_layouts").glob("*.html")):
        text = path.read_text(encoding="utf-8")
        if empty_catch.search(text):
            offenders.append(path.name)
    assert not offenders, (
        f"Empty catch block(s) found in {offenders}. Report the failure — an "
        f"asset that silently does not load is indistinguishable from an asset "
        f"that was never meant to be there."
    )


def test_svg_fetching_goes_through_the_shared_helper():
    """No direct fetch() for assets outside assets.js."""
    offenders = []
    for path in sorted(JS_DIR.glob("*.js")) + list((ROOT / "_layouts").glob("*.html")):
        if path.name == "assets.js":
            continue
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"(?<!HTF\.)\bfetch\(", text):
            snippet = text[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
            offenders.append(f"{path.name}: …{snippet}…")
    assert not offenders, (
        "Direct fetch() call(s) found outside js/assets.js:\n  "
        + "\n  ".join(offenders)
        + "\n\nUse window.HTF.fetchSvg(url, cb) so the call gets caching and a "
          "diagnostic warning on failure."
    )


# --- repo and deployment hygiene --------------------------------------------

def test_gemfile_does_not_pin_jekyll_backwards():
    """The `github-pages` gem would silently downgrade Jekyll 4.3 to 3.9.

    It is only needed for GitHub Pages' classic branch-based build. Deployment
    here runs `bundle exec jekyll build` in an Actions workflow, so the version
    in the Gemfile is the one actually used.
    """
    lines = read("Gemfile").splitlines()
    active = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    offenders = [l.strip() for l in active if "github-pages" in l]
    assert not offenders, (
        f"Gemfile has an active github-pages gem: {offenders}.\n"
        f"This pins Jekyll to 3.9. Remove it — the Actions workflow builds with "
        f"whatever `gem \"jekyll\"` says, and that should stay at ~> 4.3."
    )


def test_gitignore_covers_build_output():
    """Both build directories, or one of them ends up committed."""
    path = ROOT / ".gitignore"
    assert path.exists(), ".gitignore is missing from the repo root."
    text = path.read_text(encoding="utf-8")
    required = ["_site/", "_site_prod/", ".jekyll-cache/"]
    missing = [r for r in required if r not in text]
    assert not missing, (
        f".gitignore does not cover {missing}.\n"
        f"`_site_prod/` is the newer one — it is where the production preview "
        f"server builds, and it is easy to forget because it postdates the "
        f"original .gitignore."
    )


def test_every_drafts_collection_is_gitignored():
    """Unpublished drafts must not reach a public repo.

    .gitignore matches by directory NAME, so renaming a drafts collection
    silently stops ignoring it — no error, no warning, just 221 unpublished
    recipes newly stageable. That is exactly what happened when `_drafts/`
    became `_food_drafts/` in the mono-repo migration.

    Derived from _config.yml rather than hardcoded, so a drafts collection added
    later is covered the day it is declared.
    """
    config = yaml.safe_load(read("_config.yml"))
    drafts = [name for name in (config.get("collections") or {}) if "draft" in name]
    assert drafts, (
        "_config.yml declares no drafts collection. If drafts were deliberately "
        "removed, delete this test; otherwise the collection name has changed "
        "shape and this check is no longer finding it."
    )
    # Active patterns only. A substring match over the whole file would count a
    # commented-out `# _food_drafts/` as coverage — and the explanatory comment
    # directly above the entries names them, so a naive check passes even with
    # every pattern deleted.
    active = {line.strip() for line in read(".gitignore").splitlines()
              if line.strip() and not line.strip().startswith("#")}
    missing = [f"_{name}/" for name in drafts if f"_{name}/" not in active]
    assert not missing, (
        f".gitignore does not cover {missing}.\n"
        f"These are unpublished drafts and the repo is public. `output: false` "
        f"in _config.yml stops them PUBLISHING; it does nothing to stop the "
        f"source markdown being committed."
    )


def test_every_glass_icon_named_in_the_data_exists():
    """_data/cocktails/glasses.yml maps a drink's `glass:` to an SVG partial,
    and _layouts/cocktail.html inlines it with `{% include %}`.

    THE TWO FAILURE MODES ARE OPPOSITE AND ONLY ONE IS LOUD. A glass with no
    entry in the map renders no icon, silently and correctly -- that is the
    designed absent-means-nothing path, and it is the NORMAL case today, since
    `coupe` is the commonest glass in the collection and has no artwork yet. But
    an entry naming a file that is not there is a Jekyll build failure on every
    drink using that glass, which is a bad way to find out you typed
    `nick-and-nora` as `nick-and-norah`.

    So the map is checked against the directory rather than the template being
    made defensive: Liquid has no file-exists test, and adding one would mean
    the layout silently swallowing a real mistake in the data.
    """
    path = ROOT / "_data" / "cocktails" / "glasses.yml"
    if not path.exists():
        pytest.skip("_data/cocktails/glasses.yml does not exist yet")
    icons = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("icons") or {}
    assert icons, (
        "_data/cocktails/glasses.yml declares no `icons:` map, so this check "
        "has nothing to verify. Either the file changed shape or the key was "
        "renamed -- an empty map would make every glass iconless while looking "
        "configured."
    )

    icon_dir = ROOT / "_includes" / "icons" / "glasses"
    available = {p.stem for p in icon_dir.glob("*.svg")}
    assert available, (
        f"No SVGs found in {icon_dir.relative_to(ROOT)}, so every name in the "
        f"map would fail. Has the artwork moved?"
    )

    missing = sorted({f"{glass!r} -> {icon}.svg" for glass, icon in icons.items()
                      if icon not in available})
    assert not missing, (
        "glasses.yml names glass icon(s) that do not exist:\n  "
        + "\n  ".join(missing)
        + f"\n\nAvailable: {', '.join(sorted(available))}.\n"
          "Jekyll's {% include %} fails the whole build on a missing partial, "
          "so this would take down every drink using that glass."
    )


def test_page_has_a_description_and_link_preview():
    """A pasted recipe URL should show a title and a description, not a bare link."""
    html = read("_layouts", "default.html")
    required = {
        'name="description"': "search engines and link previews",
        'property="og:title"': "the title on a shared link",
        'property="og:description"': "the description on a shared link",
        'property="og:url"': "the canonical URL on a shared link",
    }
    missing = [f"{tag} ({why})" for tag, why in required.items() if tag not in html]
    assert not missing, (
        "_layouts/default.html is missing meta tag(s):\n  " + "\n  ".join(missing)
        + "\n\nWithout these, pasting a recipe link into a chat shows the URL "
          "and nothing else."
    )


# --- accessibility of the interactive layer ----------------------------------
# The decorative layer is already sound: every ornamental SVG carries
# aria-hidden. These guard the controls, which is where the gaps were.

def test_search_inputs_have_a_label():
    """A <span> beside an input is not a label.

    Without <label for>, a screen reader announces these as "edit text, blank".
    Placeholder text is not an accessible name and vanishes as soon as you type.
    """
    html = read("food", "index.html")
    for input_id in ("ingredient-search-box", "name-search-box"):
        assert f'for="{input_id}"' in html, (
            f'#{input_id} has no <label for="{input_id}">. The visible '
            f'[ SEARCH … ] text should BE the label rather than sitting next to '
            f"one — same styling, same position, `span` becomes `label`."
        )


def test_clear_controls_are_buttons():
    """They were <span>s with click handlers: not focusable, not announced."""
    html = read("food", "index.html") + read("_includes", "filter_group.html")
    offenders = re.findall(r'<span[^>]*class="[^"]*btn-clear-inline', html)
    assert not offenders, (
        f"Found {len(offenders)} clear control(s) rendered as <span>. "
        f"A control with a click handler must be a <button type=\"button\"> or "
        f"it cannot be reached by keyboard. The class is already named btn-*."
    )


def test_filter_buttons_announce_their_state():
    """The filter buttons are toggles, so they need aria-pressed.

    filters.js syncs the value from the .active class inside update(), in one
    place rather than at each of the fifteen toggle sites.
    """
    assert 'aria-pressed="false"' in read("_includes", "filter_group.html"), (
        "Filter buttons in filter_group.html have no aria-pressed attribute. "
        "Visually the active state is obvious; programmatically it is invisible."
    )
    assert "syncAriaPressed" in read("assets", "js", "filters.js"), (
        "filters.js no longer syncs aria-pressed. The attribute would then be "
        "stuck at its initial value and would lie about the filter state."
    )


def test_search_results_are_announced():
    """The results pool is populated as you type, so the change needs announcing."""
    html = read("food", "index.html")
    match = re.search(r'id="ingredient-results-pool"[^>]*', html)
    assert match, "#ingredient-results-pool is missing from food/index.html."
    assert "aria-live" in match.group(0), (
        "#ingredient-results-pool has no aria-live attribute, so a screen "
        'reader user gets no indication that anything happened. aria-live="polite".'
    )


def test_index_has_a_heading():
    """Every recipe page has an h1. The index had none of any level."""
    html = read("food", "index.html")
    assert re.search(r"<h1[^>]*>", html), (
        "food/index.html has no <h1>. The logo is the visible title, so a "
        '<h1 class="visually-hidden"> is the right shape — it gives assistive '
        "tech and search engines something to anchor to without changing the "
        "design."
    )


# --- one word per concept ----------------------------------------------------

def test_the_method_is_called_method_everywhere():
    """It used to be `instructions` in CSS, `method` in the data, and
    `method-full` in JS — one concept, two words, three places.

    `recipe.html` also carried a `page.method | default: page.instructions`
    fallback to a front matter field that no file has used since June.
    """
    offenders = []
    for relpath in ("_layouts/recipe.html", "_sass/food/_recipe.scss", "assets/js/method-toggle.js"):
        path = ROOT / relpath
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            # comments may mention the old name to explain the history
            if stripped.startswith(("//", "/*", "*", "#", "{%- comment", "{% comment")):
                continue
            if "instructions" in line:
                offenders.append(f"{relpath}: {stripped[:70]}")
    assert not offenders, (
        "The retired word `instructions` is still in use:\n  " + "\n  ".join(offenders)
        + "\n\nThe data field is `method`, so the class is .method-full and the "
          "JS looks for .method-full. One word per concept."
    )


def test_no_recipe_uses_the_retired_instructions_field():
    """The template fallback is gone, so a file using it would render no method."""
    from conftest import ALL_RECIPES, ALL_DRAFTS
    offenders = [r.slug for r in ALL_RECIPES + ALL_DRAFTS if "instructions" in r.fm]
    assert not offenders, (
        f"These files still use an `instructions:` field: {offenders}.\n"
        f"recipe.html no longer falls back to it, so their method would render "
        f"empty. Rename the field to `method:`."
    )


def test_no_orphaned_data_file_references():
    """_data/index_tags_sections.yml was renamed to filter_sections.yml."""
    offenders = []
    for path in list((ROOT / "_layouts").glob("*.html")) + \
                list((ROOT / "_includes").glob("*.html")) + \
                [ROOT / "food" / "index.html"]:
        if path.exists() and "index_tags_sections" in path.read_text(encoding="utf-8"):
            offenders.append(path.name)
    assert not offenders, (
        f"{offenders} still reference site.data.index_tags_sections, which no "
        f"longer exists. Jekyll resolves a missing data file to nil silently, so "
        f"the symptom is empty filter groups rather than an error."
    )


# --- SCSS structure ----------------------------------------------------------

SASS_DIR = ROOT / "_sass"


def sass_files() -> list[Path]:
    """Every partial, at any depth under _sass/.

    rglob, NOT glob. The partials used to sit flat in _sass/ and the three
    structural tests below globbed "*.scss"; the mono-repo split moved every one
    of them into _sass/shared/, _sass/food/ and _sass/cocktails/ (there used
    also to be a _sass/root/, for the landing page's own styles — deleted by
    GitHub issue #204 along with the landing page itself), which would have
    left that pattern matching an empty set. The tests would have gone on
    PASSING while checking nothing at all.

    That is not hypothetical. The same failure had already happened once in this
    file: JS_DIR pointed at _sass's sibling `js/` after the scripts moved to
    `assets/js/`, and three guards silently passed over an empty directory until
    it was noticed. A test that cannot fail is worse than no test, because it
    reads as coverage.

    test_sass_files_are_actually_found below asserts this returns something.
    """
    return sorted(SASS_DIR.rglob("*.scss"))


def test_sass_files_are_actually_found():
    """The guard on the guards — see sass_files() above.

    If a future reorganisation moves the partials somewhere this does not reach,
    this fails loudly instead of the three structural tests quietly passing on
    an empty list.
    """
    found = sass_files()
    assert len(found) >= 5, (
        f"sass_files() found {len(found)} .scss file(s) under {SASS_DIR}. "
        f"The structural SCSS tests iterate this list, so an empty or truncated "
        f"result means they are checking nothing while still reporting green. "
        f"Check whether the partials have moved."
    )


def _top_level_blocks(text: str):
    """Yield (selector, [declared properties]) for every un-nested rule.

    "Un-nested" rather than "zero-indent" since 2026-08-14: a rule sitting
    inside an at-rule counts too, and carries that at-rule in its key --
    `@media print .recipe-badges`, not `.recipe-badges`.

    ELEMENT SELECTORS COUNT TOO, also 2026-08-14. The pattern used to require
    a leading `.#%&`, so `body`, `a`, `main` and `h1, h2, h3` -- every bare
    element rule in shared/_base.scss and shared/_layout.scss -- were simply
    not seen. That was invisible until a test built on this helper needed to
    ask "does anything paint the page ground", got back nothing, and passed
    while checking nothing at all.

    THIS USED TO SEE NOTHING INSIDE AN @media BLOCK, and that mattered the
    moment the site got its first one. The old version matched a selector
    only at zero indent, so every rule the print stylesheet declares
    (_sass/shared/_print.scss and _sass/food/_print.scss, GitHub issue #86)
    was invisible to test_no_selector_declares_the_same_property_twice below
    while it went on reporting green -- the exact "test that cannot fail and
    not notice" shape HANDOVER_v26.md §12 warns about, arriving with a
    feature rather than with a file move.

    THE AT-RULE HAS TO STAY IN THE KEY, not be folded away. A print rule and
    the screen rule it overrides declare the same property for the same
    selector deliberately -- that is what an override IS -- so keying both as
    `.recipe-badges` would report every correct print rule as a clash. Only
    two print rules fighting each other, or two screen rules, are a bug.

    Line-oriented, like the version it replaces: it assumes this codebase's
    own formatting, one opening brace at the end of its line and a closing
    brace on a line of its own.
    """
    depth = 0
    at_rule = None          # the @media/@supports we are inside, if any
    at_depth = None
    current = None
    current_depth = None
    props: list[str] = []

    for line in text.split("\n"):
        code = line.split("//")[0]
        stripped = code.strip()

        if current is None:
            at_match = re.match(r"^(@[a-z-][^{}/]*?)\s*\{", stripped)
            sel_match = re.match(r"^([.#%&a-zA-Z][^{}/]*?)\s*\{", stripped)
            if at_match and at_rule is None:
                at_rule = " ".join(at_match.group(1).split())
                at_depth = depth
            elif sel_match and (depth == 0
                                or (at_rule is not None and depth == at_depth + 1)):
                current = " ".join(sel_match.group(1).split())
                if at_rule is not None:
                    current = f"{at_rule} {current}"
                current_depth = depth
                props = []
        elif depth == current_depth + 1:
            # Declarations of THIS rule only -- anything deeper belongs to a
            # nested block (`&:hover`, a descendant selector) and is not a
            # clash with its parent.
            decl = re.match(r"^([a-z-]+)\s*:", stripped)
            if decl:
                props.append(decl.group(1))

        depth += code.count("{") - code.count("}")

        if current is not None and depth == current_depth:
            yield current, props
            current = None
            current_depth = None
        if at_rule is not None and current is None and depth == at_depth:
            at_rule = None
            at_depth = None


# --- the shared/forked SCSS boundary -----------------------------------------

# Every variable _sass/shared/_base.scss and _sass/shared/_layout.scss use but
# do not define. Each site palette owes all of them.
SHARED_PALETTE_CONTRACT = [
    "color-bg", "color-border", "color-clear-text", "color-mood-root",
    "color-surface", "color-text", "color-white",
    "font-body", "font-headings",
]

# Directories holding a _palette.scss: the two sites. There used to be a
# third, "root", for the landing page — which belonged to neither site but
# rendered the same shared chrome and so needed the same nine variables. The
# landing page and its palette were deleted by GitHub issue #204 in favour of
# a bare redirect from the root to food/, which needs no palette at all.
PALETTE_OWNERS = ["food", "cocktails"]


@pytest.mark.parametrize("owner", PALETTE_OWNERS)
def test_every_palette_satisfies_the_shared_contract(owner):
    """A shared partial names palette variables it does not define.

    That is what makes it shareable — but it means a palette that omits one
    fails at BUILD time, with an "Undefined variable" pointing at a line in
    _sass/shared/, not at the palette that actually forgot it. Worse, it only
    breaks the site whose palette is short, so food can be perfectly fine while
    cocktails will not compile.

    Checked here so the failure names the file and the variable instead.
    """
    path = SASS_DIR / owner / "_palette.scss"
    assert path.exists(), (
        f"_sass/{owner}/_palette.scss is missing. assets/css/{owner}.scss "
        f"imports it before the shared partials, which need the variables it "
        f"declares."
    )
    text = path.read_text(encoding="utf-8")
    missing = [v for v in SHARED_PALETTE_CONTRACT
               if not re.search(rf"^\${re.escape(v)}\s*:", text, re.M)]
    assert not missing, (
        f"_sass/{owner}/_palette.scss does not declare {missing}.\n"
        f"_sass/shared/_base.scss and _sass/shared/_layout.scss use these by "
        f"name. Without them the build fails with an error pointing at the "
        f"shared file rather than at this one."
    )


def test_shared_scss_never_imports_a_site_partial():
    """The dependency arrow points one way: sites import shared, never back.

    A shared partial reaching into _sass/food/ would compile perfectly well on
    the food stylesheet and fail on the cocktails one, which is the most
    annoying possible version of this bug — it looks fine everywhere you tend
    to look.
    """
    offenders = []
    for path in sorted((SASS_DIR / "shared").glob("*.scss")):
        for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            code = line.split("//")[0]
            match = re.search(r"""@(?:import|use)\s+['"]([^'"]+)""", code)
            if match and not match.group(1).startswith("shared/"):
                offenders.append(f"shared/{path.name}:{i} imports {match.group(1)}")
    assert not offenders, (
        "A shared partial imports something outside shared/:\n  "
        + "\n  ".join(offenders)
        + "\n\nshared/ may not depend on any one site. Move the shared thing "
          "into shared/, or the site-specific thing out of it."
    )


def test_shared_scss_names_no_site():
    """No selector or variable in shared/ may name one site.

    `.site-logo-food` lived in the layout that both sites now render. The word
    in the brackets comes from _data/sites.yml, so the class cannot assume it —
    it is `.site-logo-word`. Comments are exempt: they explain the history.
    """
    offenders = []
    for path in sorted((SASS_DIR / "shared").glob("*.scss")):
        for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            code = line.split("//")[0]
            if re.search(r"[.$%#-](food|cocktail)s?\b", code, re.I):
                offenders.append(f"shared/{path.name}:{i} {code.strip()[:60]}")
    assert not offenders, (
        "A shared SCSS partial names a specific site:\n  " + "\n  ".join(offenders)
        + "\n\nshared/ is rendered by both sites. If the rule is genuinely "
          "site-specific it belongs in _sass/<site>/; if it is not, the name "
          "should not say so."
    )


def test_no_selector_declares_the_same_property_twice():
    """A selector may legitimately appear more than once.

    `_layout.scss` groups by concern — the clip-path SHAPES for .btn-star sit
    with the badges, its appearance sits with the buttons. That is a deliberate
    structure and merging the blocks would flatten it.

    What is never safe is the same PROPERTY declared for the same selector in
    two blocks, because then the later one silently wins and editing the earlier
    one appears to do nothing. That is the actual hazard, so that is what this
    tests — not mere repetition.
    """
    from collections import defaultdict
    problems = []
    for path in sass_files():
        seen = defaultdict(lambda: defaultdict(int))
        for selector, props in _top_level_blocks(path.read_text(encoding="utf-8")):
            for prop in set(props):
                seen[selector][prop] += 1
        for selector, counts in seen.items():
            clashes = sorted(p for p, n in counts.items() if n > 1)
            if clashes:
                problems.append(f"{path.name}: `{selector}` declares {clashes} in more than one block")
    assert not problems, (
        "The same property is declared for one selector in two separate blocks:\n  "
        + "\n  ".join(problems)
        + "\n\nThe later block wins, so editing the earlier one does nothing. "
          "Merge them, or move the property to whichever block owns that concern."
    )


# --- the print stylesheet keeps pointing at real markup ----------------------

def _print_block_classes() -> list[tuple[str, str]]:
    """(file, class) for every class named inside an `@media print` block."""
    out = []
    for path in sass_files():
        text = path.read_text(encoding="utf-8")
        for selector, _ in _top_level_blocks(text):
            if not selector.startswith("@media print"):
                continue
            # Attribute selectors carry no class of their own, and a stray
            # `[hidden]` would otherwise be parsed as part of the name.
            bare = re.sub(r"\[[^\]]*\]", "", selector)
            for cls in re.findall(r"\.([a-zA-Z][\w-]*)", bare):
                out.append((path.name, cls))
    return out


def test_print_rules_target_classes_that_exist():
    """GitHub issue #86. Every class the print stylesheet styles is emitted by
    some template.

    THE FAILURE THIS PREVENTS IS INVISIBLE BY CONSTRUCTION. Rename a class and
    the screen rule that follows it goes wrong in front of you; the print rule
    that did not follow it goes wrong on paper, which nobody looks at in
    review, and which has no console, no layout shift and no error. A printout
    that quietly regains the site header, or loses its page breaks, would
    survive indefinitely.

    Derived from both sides -- the classes come from whatever is currently
    inside an `@media print` block, the markup from whatever the templates
    currently emit -- so a print rule added tomorrow is covered tomorrow,
    without this test being edited.

    Not the reverse direction: a class with no print rule is the normal case,
    since most of the page needs no different treatment on paper.
    """
    named = _print_block_classes()
    assert named, (
        "No classes found inside any `@media print` block. Either the print "
        "stylesheet has gone (in which case delete this test and its helper) "
        "or _top_level_blocks has stopped seeing into at-rules again -- and an "
        "empty check passes."
    )

    html_files = (
        sorted(ROOT.glob("_layouts/*.html"))
        + sorted(ROOT.glob("_includes/**/*.html"))
        + sorted(ROOT.glob("food/**/*.html"))
        + sorted(ROOT.glob("cocktails/**/*.html"))
        + [ROOT / "index.html"]
    )
    markup = "\n".join(p.read_text(encoding="utf-8") for p in html_files if p.exists())

    missing = sorted({
        f"{where_}: .{cls}" for where_, cls in named
        if not re.search(rf'class="[^"]*\b{re.escape(cls)}\b', markup)
    })
    assert not missing, (
        "Print rule(s) target a class no template emits:\n  " + "\n  ".join(missing)
        + "\n\nEither the class was renamed and the print stylesheet did not "
          "follow it, or the rule is left over from markup that has gone. A "
          "print rule that matches nothing fails silently and on paper only."
    )


def test_print_neutralises_the_screen_page_background():
    """Whatever paints the page ground for the screen must be overridden in
    print, not merely left unmentioned there.

    THIS IS THE BUG IT CAME FROM, and it is worth stating plainly because the
    mistake is so easy to repeat. Asked to stop printing a page-wide tint, I
    deleted the print stylesheet's own `background: $color-bg` line -- and
    nothing changed, because shared/_base.scss sets `body { background:
    $color-bg }` for the screen and that rule is still in the cascade inside
    @media print. Removing an override is not the same as overriding.
    $color-bg is a tint rather than white, so the symptom was every sheet
    flooded with ink, and the only thing that caught it was Helen looking at
    another print preview.

    Derived from the stylesheets rather than hardcoded: if a future partial
    starts painting the ground somewhere else, this asks for that to be
    answered in print too.
    """
    paints_ground = []
    print_override = False
    for path in sass_files():
        for selector, props in _top_level_blocks(path.read_text(encoding="utf-8")):
            names = {s.strip() for s in selector.replace("@media print", "").split(",")}
            if not ({"body", "html"} & names):
                continue
            if "background" not in props:
                continue
            if selector.startswith("@media print"):
                print_override = True
            else:
                paints_ground.append(f"{path.name}: `{selector}`")

    # NOT `if not paints_ground: return`. That was the first version, and it
    # is how this test passed while checking nothing -- see the docstring.
    # If one day genuinely nothing paints a ground, that is a real change to
    # know about, not a reason to fall silent.
    assert paints_ground, (
        "Nothing in _sass/ paints a background on html or body, so this test "
        "has nothing to check. Either the shared base stopped setting the page "
        "ground (in which case delete this test with it) or the scan has "
        "stopped finding it -- and a scan that finds nothing passes."
    )
    assert print_override, (
        f"{paints_ground} paints the page ground for the screen, and no "
        f"`@media print` rule sets a background on html/body to replace it.\n"
        f"A print stylesheet has to SAY what it wants -- deleting its own "
        f"declaration just leaves the screen rule in force, and if that "
        f"colour is not white it prints as a flat wash over every sheet."
    )


def test_list_sections_are_conditioned_on_size_not_truthiness():
    """An empty array is TRUTHY in Liquid, so a section guarded by a bare
    truth test renders its heading with nothing underneath it.

    Only nil and false are falsy. `notes: []` therefore drew the NOTES
    heading and an empty grid on 49 drafts, unnoticed until Helen looked at
    one while checking the print layout -- and the pages it affects are
    exactly the ones nobody scrutinises, because a draft looking unfinished
    is not a surprise.

    Nothing else can catch this: the data is valid, the template is valid,
    the build is clean, and the only symptom is a heading over blank space
    on whichever files happen to hold an empty list today.

    Scoped to the fields that are lists and that gate a whole section --
    `.size > 0` is the fix, `.size > 1` and `.size == 1` are fine too since
    they are already asking about length rather than existence.
    """
    layout = read("_layouts", "recipe.html")
    # The comment blocks in this layout describe the bad pattern in prose
    # rather than quoting it, precisely because Liquid parses tag delimiters
    # inside a comment -- so there is nothing here to strip first.
    bare = re.findall(
        r"\{%-?\s*if\s+page\.(notes|ingredient_groups|method_short|tags|main_ingredients)"
        r"\s*(?:%\}|-%\})",
        layout,
    )
    assert not bare, (
        f"_layouts/recipe.html gates a section on the bare truthiness of "
        f"{sorted(set(bare))}. An empty array is truthy in Liquid, so that "
        f"renders the section's heading over nothing whenever the list is "
        f"empty. Test the length instead: `page.notes.size > 0`."
    )


def test_pdf_link_points_where_the_pdfs_are_written():
    """GitHub issue #86. The "pdf" link on a recipe page and the file
    scripts/generate_pdfs.py writes have to agree on one directory, and
    nothing at either end would notice if they stopped.

    Almost everything else about this feature fails loudly: no browser, a
    crashed render, a build with no recipe pages in it all exit the workflow
    non-zero. This one does not. Change the collection's permalink and the
    script keeps working perfectly -- it globs whatever the build produced --
    while every link in the markup goes on pointing at the old path. The
    result is a deploy that succeeds, a site that looks right, and a link that
    404s on every recipe.

    So all three are read from where they actually live rather than restated
    here: the permalink from _config.yml, the link from the layout, and the
    write path from the script.
    """
    config = yaml.safe_load(read("_config.yml"))
    permalink = ((config.get("collections") or {}).get("food_recipes") or {}).get("permalink")
    assert permalink, (
        "_config.yml declares no permalink for the food_recipes collection. "
        "If the collection was renamed, this check no longer knows where "
        "recipe pages live."
    )
    # "/food/recipes/:path/" -> "/food/recipes/"
    expected = permalink.split(":")[0]

    layout = read("_layouts", "recipe.html")
    link = re.search(r"\{\{\s*'([^']+)'\s*\|\s*append:\s*page\.slug\s*\|\s*append:\s*'\.pdf'", layout)
    assert link, (
        "_layouts/recipe.html no longer builds the PDF link as "
        "`'<dir>' | append: page.slug | append: '.pdf'`. If the link is built "
        "another way now, this check needs to follow it -- it is the only "
        "thing tying the link to where the files are written."
    )
    assert link.group(1) == expected, (
        f"The PDF link points at {link.group(1)!r} but recipe pages are "
        f"published under {expected!r} (from _config.yml's permalink), which "
        f"is where scripts/generate_pdfs.py writes each PDF -- it puts "
        f"<slug>.pdf beside the recipe's own output directory. One of the two "
        f"has moved and the other has not."
    )

    script = read("scripts", "generate_pdfs.py")
    assert 'glob("food/recipes/*/index.html")' in script, (
        "scripts/generate_pdfs.py no longer globs food/recipes/*/index.html, "
        "so it may be writing PDFs somewhere other than beside the recipe "
        "pages this link points at."
    )


def test_spacing_tokens_are_not_used_for_type():
    """$space-* is for margin, padding and gaps — never font-size.

    A padding and a type size that happen to share a value are not the same
    decision. Tying them together means changing one changes the other.
    """
    offenders = []
    for path in sass_files():
        for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if re.search(r"(font-size|line-height|letter-spacing)\s*:.*\$space-", line):
                offenders.append(f"{path.name}:{i} {line.strip()[:60]}")
    assert not offenders, (
        "A spacing token is being used for typography:\n  " + "\n  ".join(offenders)
        + "\n\nUse the $font-size-* scale, or a literal if the value is a one-off."
    )


def test_no_element_can_force_horizontal_scroll():
    """A fixed width wider than a phone viewport, with nothing clamping it.

    Horizontal scroll is the most visible mobile failure there is, and it takes
    exactly one unclamped element to cause it. The site has no media queries and
    does not need any — everything else is fluid or wraps — so this one check
    stands in for a responsive test suite.

    A `width: Npx` above 320 is fine as long as a max-width, min() or clamp()
    sits with it.
    """
    offenders = []
    for path in sass_files():
        lines = path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            match = re.match(r"^\s*width:\s*(\d+)px", line)
            if not match or int(match.group(1)) <= 320:
                continue
            context = "\n".join(lines[max(0, i - 4):i + 5])
            if not re.search(r"max-width|min\(|clamp\(", context):
                offenders.append(f"{path.name}:{i + 1} {line.strip()}")
    assert not offenders, (
        "Fixed width(s) wider than a small phone with nothing clamping them:\n  "
        + "\n  ".join(offenders)
        + "\n\nUse `width: min(Npx, 92vw)` or add a max-width. 92 rather than 100 "
          "if the element is rotated, since the rendered box is wider than the "
          "declared width."
    )


def test_no_decoration_slot_is_orphaned():
    """Every empty aria-hidden slot in a template is filled by some script.

    A decoration slot is an empty `<span class="…-slot" aria-hidden="true">`
    that exists only for JavaScript to inject an SVG into. If the injection is
    deleted and the slot is not, the slot stays in the markup forever, drawing
    nothing, looking load-bearing to whoever reads the template next. That is
    exactly how `--annotation-gutter: 200px` became a declaration nobody dared
    remove — see DEV_JOBS_v23.md §4.

    It nearly happened again in the 2026-07-31 recipe-page redesign, which cut
    four of the five decorations `section-rule.js` drew (the section rules, the
    violet asterisk bullets, the pink section-heading doodles and the meta-label
    underlines) and left six `.section-heading-sparkle` spans, four
    `.meta-label-underline` spans and every `.ingredient-bullet` in the layout
    to be removed by hand.

    Derived, not listed: the slots come from the markup and the injectors from
    the scripts, so a new slot is covered the day it is written.

    The reverse direction — a script querying a slot no template emits — is NOT
    checked here, because several classes filters.js queries are ones it creates
    itself and no template ever contains. `decorations.js` used to carry a
    `doodles()` function in exactly that shape, querying `data-index-doodle`
    for a slot no template had emitted in as long as git remembered — GitHub
    issue #228 deleted it (and the function was already the only thing in the
    file referencing that attribute, so nothing else needed to change). Recorded
    here as history rather than as a live caveat, since there is no longer any
    dead code of this kind for this test's coverage gap to be hiding.
    """
    html_files = (
        sorted(ROOT.glob("_layouts/*.html"))
        + sorted(ROOT.glob("_includes/*.html"))
        + sorted(ROOT.glob("food/*.html"))
        + sorted(ROOT.glob("cocktails/*.html"))
        + [ROOT / "index.html"]
    )
    assert html_files, "No templates found — this test would pass while checking nothing."

    js_files = sorted((ROOT / "assets" / "js").glob("*.js"))
    assert js_files, "No scripts found — this test would pass while checking nothing."
    js_blob = "\n".join(p.read_text(encoding="utf-8") for p in js_files)

    # An empty span/div carrying a class and aria-hidden="true" is this repo's
    # decoration-slot idiom. `[^>]*` spans newlines, so a slot whose attributes
    # are split across lines (.tape-bg) is still matched.
    slot_pattern = re.compile(
        r'<(span|div)\s+class="([^"]*)"[^>]*aria-hidden="true"[^>]*>\s*</\1>'
    )

    orphans = []
    found_any = False
    for path in html_files:
        for match in slot_pattern.finditer(path.read_text(encoding="utf-8")):
            for cls in match.group(2).split():
                if "{{" in cls or "{%" in cls:
                    continue   # a Liquid-built class name is not checkable here
                found_any = True
                if f"'.{cls}'" not in js_blob and f'".{cls}"' not in js_blob:
                    orphans.append(f"{path.relative_to(ROOT)}: .{cls}")

    assert found_any, (
        "No decoration slots were matched at all. Either the idiom changed or "
        "the pattern above stopped matching — and an empty check passes."
    )
    assert not orphans, (
        "Decoration slot(s) with nothing to fill them:\n  "
        + "\n  ".join(sorted(set(orphans)))
        + "\n\nEither a script should inject into it, or the slot should come "
          "out of the template. An empty aria-hidden span that no script names "
          "renders nothing and misleads the next person to read the file."
    )
