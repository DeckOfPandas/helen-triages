"""Architecture regression tests.

These do not test recipes. They test that the single sources of truth stay
single, and that a value with a home does not sprout a copy elsewhere.
"""
from __future__ import annotations

import re
import subprocess
import unicodedata
from pathlib import Path

import pytest
import yaml

# One comment-stripper for the whole suite: comments go, string literals stay.
from test_front_matter import _strip_comments

pytestmark = pytest.mark.shared

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
    """Neither filters.js nor ingredient-search.js compares `query.length`
    against a literal.

    The threshold lives in _data/food/ingredient_words.yml and is read into
    FAMILY_BUTTON_MIN_CHARS in assets/js/ingredient-search.js. A bare literal
    has nothing defining it, so a rewrite of the file re-derives it wrongly.
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


# --- an alias resolves one hop ----------------------------------------------

def _fold_like_the_matcher(text) -> str:
    """`fold(key.toLowerCase())` from assets/js/ingredient-search.js: lower
    case, diacritics stripped, hyphens to spaces. The alias map is keyed on
    this, so two spellings that fold alike are one key to the matcher."""
    decomposed = unicodedata.normalize("NFD", str(text).lower())
    return "".join(c for c in decomposed
                   if not unicodedata.combining(c)).replace("-", " ")


def _alias_chains(aliases) -> list[str]:
    """Every alias whose target is itself an alias key, as `a -> b -> c`.

    An alias naming ITSELF among its targets is not a chain: `applyAlias`
    returns the list as written and never looks the target up again.
    """
    keys = {_fold_like_the_matcher(k): v for k, v in aliases.items()}
    out = []
    for key, becomes in aliases.items():
        for target in (becomes if isinstance(becomes, list) else [becomes]):
            folded = _fold_like_the_matcher(target)
            if folded in keys and folded != _fold_like_the_matcher(key):
                out.append(f"{key} -> {target} -> {keys[folded]}")
    return out


def test_no_food_alias_points_at_another_alias():
    """An alias must name where the chain ENDS, because nothing follows it.

    `applyAlias` in assets/js/ingredient-search.js returns `aliasMap[key]`
    without resolving the result again, so an alias whose target is itself
    aliased stops one hop short and the index grows a second button for one
    ingredient (#1175).
    """
    path = DATA / "ingredient_words.yml"
    aliases = yaml.safe_load(path.read_text(encoding="utf-8")).get("aliases") or {}
    assert aliases, (
        "_data/food/ingredient_words.yml declares no `aliases`, so this check "
        "examined nothing. Either the block was renamed or the file changed "
        "shape."
    )
    chains = _alias_chains(aliases)
    assert not chains, (
        "Alias(es) pointing at a key that is itself aliased:\n  "
        + "\n  ".join(chains)
        + "\n\nThe matcher resolves ONE hop, so the first target is where the "
          "ingredient lands and the index gets two buttons for it. Point the "
          "alias at the last name in its line."
    )


def test_the_alias_chain_check_sees_a_chain():
    """The check above passes on real data, so prove it can fail.

    Three shapes: a chain through a bare name, a chain through a list, and a
    spelling that only matches a key once folded the way the matcher folds it.
    """
    assert _alias_chains({"onions": "onion", "shallots or onions": ["shallots", "onions"]})
    assert _alias_chains({"spring onions": "spring onion",
                          "spring onions in thin strips": "spring onions"})
    assert _alias_chains({"five spice": "spice", "chinese five-spice": "Five-Spice"})

    assert not _alias_chains({"spring onions": "spring onion",
                              "spring onions in thin strips": "spring onion"})
    assert not _alias_chains({"salt and pepper": ["salt and pepper", "pepper"]})


def test_vocabulary_is_emitted_to_the_page():
    """filters.js can only read the vocabulary if index.html emits it."""
    html = read("food", "index.html")
    assert 'id="ingredient-vocabulary"' in html, (
        'food/index.html no longer emits the <script type="application/json" '
        'id="ingredient-vocabulary"> block. Without it filters.js falls back to '
        "empty singulars and synonyms — ingredient search still works, but "
        '"cheese" stops returning cheddar and the collapse behaviour is lost.'
    )
    # The <script src> tag specifically: the template's comments also say
    # "filters.js".
    tag = re.search(r"<script src=[^>]*filters\.js", html)
    assert tag, "food/index.html no longer loads assets/js/filters.js at all."
    assert html.index('id="ingredient-vocabulary"') < tag.start(), (
        "The ingredient-vocabulary block must appear BEFORE the filters.js "
        "script tag, or the script will run before the data exists."
    )


def test_ingredient_search_js_loads_before_filters_js():
    """filters.js calls HTF.ingredientSearch at startup -- it must already exist.

    The matching algorithm lives in ingredient-search.js, and filters.js wires
    it up with `HTF.ingredientSearch.create(...)` as it starts.
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


def test_list_view_js_loads_before_filters_js():
    """filters.js calls HTF.listView at startup -- it must already exist, the
    same trap as ingredient-search.js (#759).
    """
    html = read("food", "index.html")
    list_view_tag = re.search(r"<script src=[^>]*list-view\.js", html)
    filters_tag = re.search(r"<script src=[^>]*filters\.js", html)
    assert list_view_tag, "food/index.html no longer loads assets/js/list-view.js."
    assert filters_tag, "food/index.html no longer loads assets/js/filters.js."
    assert list_view_tag.start() < filters_tag.start(), (
        "list-view.js must load BEFORE filters.js, or "
        "HTF.listView won't exist yet when filters.js runs."
    )


def test_filter_state_js_loads_before_filters_js():
    """filters.js reads HTF.filterState at startup -- it must already exist.

    filters.js applies the badge links' query string through
    HTF.filterState.parseQuery (#40). Loaded the wrong way round, the call
    throws and the whole DOMContentLoaded handler dies with it: `.recipe-list`
    never has its `visibility: hidden` lifted, so the index is blank.
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

    The arithmetic lives in assets/js/cook-schedule.js and cook-timer.js grabs
    it as it starts. Loaded the wrong way round the timings page throws once
    and shows an empty table, with no visible error.
    """
    html = read("food", "reference", "cooking-methods-and-timings.html")
    schedule_tag = re.search(r"<script src=[^>]*cook-schedule\.js", html)
    timer_tag = re.search(r"<script src=[^>]*cook-timer\.js", html)
    assert schedule_tag, (
        "food/reference/cooking-methods-and-timings.html no longer loads assets/js/cook-schedule.js."
    )
    assert timer_tag, (
        "food/reference/cooking-methods-and-timings.html no longer loads assets/js/cook-timer.js."
    )
    assert schedule_tag.start() < timer_tag.start(), (
        "cook-schedule.js must load BEFORE cook-timer.js, or "
        "HTF.cookSchedule won't exist yet when cook-timer.js runs."
    )


def test_the_scaler_scripts_load_in_dependency_order():
    """scale.js reads HTF.shoppingList, and cocktail-scale.js reads HTF.scale.

    The drink scaler (#545) is a chain: the amount parser (shopping-list.js),
    the arithmetic (scale.js) and the wiring (cocktail-scale.js), each grabbing
    the one before it off `HTF` as it parses. Out of order, the drink page
    throws once and the control never appears, while the page still reads
    correctly at x1. The tags live in the layout, so that is what is read.
    """
    html = read("_layouts", "cocktail.html")
    order = ["shopping-list.js", "scale.js", "cocktail-scale.js"]
    found = {}
    for name in order:
        # `scale\.js` would also match `cocktail-scale.js`; the slash pins it to
        # the start of a filename.
        match = re.search(r"<script src=[^>]*/" + re.escape(name), html)
        assert match, f"_layouts/cocktail.html no longer loads assets/js/{name}."
        found[name] = match.start()

    assert found["shopping-list.js"] < found["scale.js"] < found["cocktail-scale.js"], (
        "the scaler's three scripts are out of order in _layouts/cocktail.html. "
        "shopping-list.js defines HTF.shoppingList, which scale.js reads as it "
        "parses; scale.js defines HTF.scale, which cocktail-scale.js reads. Any "
        "other order leaves the scale control hidden with nothing in the console."
    )


def test_the_search_box_searches_for_anything_on_every_site_page():
    """The search box (#1050) is on every page that belongs to a site, on the
    deployed build too, at the top of the page body and not in the header
    (#1288): there it reads as this site's search, not the shared chrome's.
    No config switch gates it. The markup order is the layout: input, then
    glass, then the dropdown, rendered hidden. The include loads
    page-search.js itself, and each site has a search.json kept out of the
    sitemap.
    """
    include = read("_includes", "page-search.html")
    # The include's Liquid comment discusses the markup at length; only the
    # markup after it is asserted on.
    strip = lambda text: re.sub(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", text, flags=re.S)
    body = strip(include)

    assert "show_header_search" not in body, (
        "_includes/page-search.html reads show_header_search again; the box is "
        "live on both sites (#1288) and no switch gates it."
    )
    for config in ("_config.yml", "_config_local.yml"):
        assert not re.search(r"^show_header_search:", read(config), re.M), (
            f"{config} declares show_header_search; the key is retired (#1288)."
        )
    layout = strip(read("_layouts", "default.html"))
    main_at = layout.find("<main>")
    include_at = layout.find("{% include page-search.html %}")
    assert main_at != -1 and include_at > main_at, (
        "_layouts/default.html must include page-search.html inside <main>, "
        "as the page body's first thing: the box is under the door, not in "
        "the header both sites share (#1288)."
    )
    assert "page-search" not in strip(read("_includes", "back-to-index.html")), (
        "_includes/back-to-index.html renders a search box again; that end of "
        "the furniture line holds print and pdf, and the box is default.html's."
    )

    go = re.search(r'<button[^>]*class="page-search-go"[^>]*type="submit"|'
                   r'<button[^>]*type="submit"[^>]*class="page-search-go"', body)
    box = re.search(r'<input[^>]*class="page-search-input"', body)
    panel = re.search(r'<div[^>]*class="page-search-results"[^>]*hidden', body)
    assert go, "the magnifying glass is not a submit button (.page-search-go)."
    assert box, "the box (.page-search-input) is missing."
    assert panel, "the dropdown (.page-search-results) must be rendered, hidden."
    assert box.start() < go.start() < panel.start(), (
        "input, then glass, then dropdown -- #1056 put the glass at the "
        "RIGHT end, and it only stays put if it comes after the input in "
        "the row."
    )
    assert 'placeholder="I know what I want..."' in body, (
        "the placeholder is Helen's exact words, #1096: 'I know what I want...'"
    )
    assert "data-search-index=" in body and "search.json" in body, (
        "the form must say which JSON it searches (data-search-index)."
    )
    assert "icons/search.svg" in body, "the glass is _includes/icons/search.svg."

    # The script ships with the box, so no page loads a script for a box it
    # does not have (a site_neutral page has neither).
    assert body.find("page-search.js") > body.find('class="page-search"'), (
        "_includes/page-search.html must load page-search.js AFTER the form "
        "it wires (the script binds on run, not on DOMContentLoaded)."
    )
    for layout in ("recipe.html", "cocktail.html", "default.html"):
        assert "page-search.js" not in re.sub(
            r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "",
            read("_layouts", layout), flags=re.S,
        ), (
            f"_layouts/{layout} loads page-search.js itself; only "
            f"_includes/page-search.html does, with the box, so no page loads "
            f"a script for a box it lacks."
        )

    for site in ("food", "cocktails"):
        path = ROOT / site / "search.json"
        assert path.exists(), f"{site}/search.json is missing."
        text = path.read_text(encoding="utf-8")
        assert f"permalink: /{site}/search.json" in text
        assert "sitemap: false" in text, (
            f"{site}/search.json is not a page and must stay out of the sitemap."
        )

    # The dropdown's links end in `#results`, and both indexes must carry that
    # id on the line above their list, or the page opens at the top.
    js = (JS_DIR / "page-search.js").read_text(encoding="utf-8")
    assert "var RESULTS_FRAGMENT = '#results';" in js
    for page in ("food", "cocktails"):
        html = read(page, "index.html")
        assert re.search(r'<(div|p)[^>]*\bid="results"', html), (
            f"{page}/index.html has no element with id=\"results\"; the search "
            "dropdown's filtered links end in #results and would land at the top."
        )

    sites = read("_data", "sites.yml")
    assert not re.search(r"^\s+search_placeholder:", sites, re.M), (
        "sites.yml still declares search_placeholder; the placeholder lives in "
        "_includes/page-search.html since #1050 (it says the same words on "
        "both sites, so it no longer says where you are)."
    )


def test_the_recipe_scaler_scripts_load_in_dependency_order():
    """#1005. The recipe page's scaler scripts are each read at parse time by
    the one after it: shopping-list.js, food-shopping-list.js, food-scale.js,
    recipe-scale.js. Out of order the page throws once, silently, and the
    portions box never appears.
    """
    html = read("_layouts", "recipe.html")
    order = ["shopping-list.js", "food-shopping-list.js", "food-scale.js",
             "recipe-scale.js"]
    positions = []
    for name in order:
        match = re.search(r"<script src=[^>]*/" + re.escape(name), html)
        assert match, f"_layouts/recipe.html no longer loads {name}."
        positions.append(match.start())
    assert positions == sorted(positions), (
        "the recipe scaler's four scripts are out of order in "
        "_layouts/recipe.html. Each one reads the one before it off HTF at "
        f"parse time, so the order must be: {', '.join(order)}."
    )


def test_the_recipe_scaler_is_handed_the_half_step_measures():
    """#1125. Which by-eye measures scale in steps is data, and it reaches the
    page by one route.

    _layouts/recipe.html joins the step lists in _data/food/scaling.yml onto
    the scaler control as data attributes, and recipe-scale.js reads them.
    Break either end and nothing errors -- food-scale.js treats a missing list
    as an empty one -- so "1 handful" quietly scales to "1.17 handfuls".
    """
    scaling = yaml.safe_load(read("_data", "food", "scaling.yml"))
    measures = scaling.get("half_step_measures")
    # `handful` is a quarter-step measure, and must be on exactly one list.
    assert measures and "pinch" in measures, (
        "_data/food/scaling.yml has no `half_step_measures` list naming `pinch`."
    )
    assert "handful" in scaling.get("quarter_step_measures", []), (
        "`handful` is on neither step list; the recipe scaler will print "
        "1.17 handfuls again."
    )
    assert "handful" not in measures, (
        "`handful` is back in half_step_measures. Helen, 2026-10-10: 'Recipe "
        "page handfuls and sprigs in 1/4 too please.'"
    )
    assert "pat" not in measures, (
        "`pat` is in half_step_measures. Helen, 2026-10-04: '\"pat\" is a "
        "correct term, and should be scaled linearly as \"pats\"'."
    )
    not_plain = [m for m in measures
                 if not isinstance(m, str) or not re.fullmatch(r"[a-z]+", m)]
    assert not not_plain, (
        f"half_step_measures entries must be one lowercase word each, singular; "
        f"got {not_plain}. The layout joins the list with `|` and "
        f"food-scale.js adds the plural itself."
    )
    sizes = sorted({"large", "medium", "small"} & set(measures))
    assert not sizes, (
        f"{sizes} must never be a half-step measure: Helen ruled that "
        f"'2 large' scales (#1005), and 240 amounts are written that way."
    )

    # `half_step_counts` step in halves too, from their own list.
    html = read("_layouts", "recipe.html")
    wiring = {
        "data-half-step-measures": "site.data.food.scaling.half_step_measures | "
                                   "concat: site.data.food.scaling.half_step_counts",
        "data-quarter-step-measures": "site.data.food.scaling.quarter_step_measures",
        "data-trailing": "site.data.food.ingredient_words.trailing_phrases",
    }
    script = read("assets", "js", "recipe-scale.js")
    for attribute, source in wiring.items():
        assert re.search(
            re.escape(attribute) + r'="\{\{\s*' + re.escape(source) + r"\s*\|\s*join:\s*'\|'",
            html,
        ), (
            f"_layouts/recipe.html no longer emits {attribute} from {source} "
            f"joined with `|`, so recipe-scale.js is handed no list."
        )
        assert f"'{attribute}'" in script, (
            f"assets/js/recipe-scale.js no longer reads {attribute}."
        )


def test_the_food_shopping_scripts_load_in_dependency_order():
    """food-shopping-list.js reads HTF.shoppingList, and filters.js reads both.

    The shopping list (#801) is a chain: the amount parser (shopping-list.js),
    the food arithmetic (food-shopping-list.js) and the wiring (filters.js).
    food-shopping-list.js reads HTF.shoppingList at module scope, so loading
    it first throws as it parses and kills filters.js's whole startup: a blank
    index, not just a missing panel.
    """
    html = read("food", "index.html")
    order = ["shopping-list.js", "food-shopping-list.js", "filters.js"]
    found = {}
    for name in order:
        # `shopping-list\.js` would also match `food-shopping-list.js`; the
        # slash pins the pattern to the start of a filename.
        match = re.search(r"<script src=[^>]*/" + re.escape(name), html)
        assert match, f"food/index.html no longer loads assets/js/{name}."
        found[name] = match.start()

    assert (found["shopping-list.js"] < found["food-shopping-list.js"]
            < found["filters.js"]), (
        "the shopping list's three scripts are out of order in food/index.html. "
        "shopping-list.js defines HTF.shoppingList, which food-shopping-list.js "
        "reads as it parses; that defines HTF.foodShoppingList, which filters.js "
        "calls. Any other order throws once in the console and leaves the whole "
        "index unfiltered."
    )


def test_the_results_pill_loads_after_the_index_script_on_both_indexes():
    """results-bar.js places the results pill (#1448) from what the index
    script paints, so it loads after it.

    The index script adopts the pill's × as its one clear-all, and the pill
    reads that ×'s visibility; both wire on DOMContentLoaded, and listeners
    fire in registration order. Also pinned: both indexes render the pill from
    one include, which ships `hidden`; each marks its filter panel, which the
    pill reads for "top"; the digits carry the shared class on both indexes;
    and both stylesheets import the partial that styles it.
    """
    pill = _strip_comments(read("_includes", "results-pill.html"), ".html")
    assert re.search(r'<div class="results-pill"[^>]*\bhidden\b', pill), (
        "_includes/results-pill.html's `.results-pill` no longer ships `hidden`. "
        "The script reveals it; without JavaScript a pill that is not hidden is "
        "an empty fixed lozenge at the foot of every visit."
    )
    assert "data-results-pill-clear" in pill, (
        "_includes/results-pill.html has no `data-results-pill-clear`: that "
        "button is each index's only clear-all."
    )
    for page, index_script, top in (("food", "filters.js", "filter-star"),
                                    ("cocktails", "cocktail-index.js", "filter-chaos")):
        html = read(page, "index.html")
        index_tag = re.search(r"<script src=[^>]*/" + re.escape(index_script), html)
        bar_tag = re.search(r"<script src=[^>]*/results-bar\.js", html)
        assert index_tag, f"{page}/index.html no longer loads assets/js/{index_script}."
        assert bar_tag, f"{page}/index.html no longer loads assets/js/results-bar.js."
        assert index_tag.start() < bar_tag.start(), (
            f"results-bar.js must load AFTER {index_script} on {page}/index.html: "
            f"it reads the visibility that script sets on the pill's ×, so loaded "
            f"first it reads nothing."
        )
        assert re.search(r"\{%\s*include\s+results-pill\.html\s+top=\"" + top + r"\"\s*%\}", html), (
            f"{page}/index.html no longer renders the results pill with "
            f'`top="{top}"`, the section its "top" returns to.'
        )
        assert re.search(r'<div class="[^"]*"[^>]*\bdata-filter-panel\b', html), (
            f"{page}/index.html's filter panel no longer carries "
            f"`data-filter-panel`, which the pill reads to know when to offer "
            f'"top".'
        )
        assert re.search(r'class="results-count-number"[^>]*id="[a-z]+-count-n"', html), (
            f"{page}/index.html's count number no longer carries "
            f"`.results-count-number`. That class is what gives the digits the "
            f"label face on both indexes (shared/_results-bar.scss)."
        )
        assert '@use "shared/results-bar";' in read("assets", "css", f"{page}.scss"), (
            f"assets/css/{page}.scss does not load shared/results-bar, so "
            f"`.results-count-number` and `.results-pill` have no rule on {page}."
        )


def test_the_card_measurement_passes_are_loaded_in_order():
    """card-name-fit.js, then card-line-budget.js, both from the shared layout.

    cocktail-index.js guards its call with `if (HTF.cardLineBudget)`, so a
    missing tag means the budget pass (#776) silently never runs while every
    JS test stays green. The budget pass reads the ingredient line the name
    pass has just sized, so it loads second.
    """
    html = read("_layouts", "default.html")
    order = ["card-name-fit.js", "card-line-budget.js"]
    found = {}
    for name in order:
        match = re.search(r"<script src=[^>]*/" + re.escape(name), html)
        assert match, (
            f"_layouts/default.html no longer loads assets/js/{name}. A "
            "measurement pass that nothing loads fails silently -- the index "
            "guards the call -- so the tag going missing looks like nothing."
        )
        found[name] = match.start()

    assert found["card-name-fit.js"] < found["card-line-budget.js"], (
        "card-line-budget.js must load after card-name-fit.js: it measures the "
        "ingredient line the name pass has just decided the clamp for."
    )


def test_a_drink_cards_tagline_is_a_reveal_and_never_shown_at_rest():
    """#1292: a card's tagline is a reveal, in the markup and hidden at rest.

    Three things fail quietly on their own: the line's base rule is
    `display: none`, or every card shows it at rest (#512); both card
    templates emit it through the one include (#991); and the shared layout
    loads card-tagline.js, or the `?` stays hidden where there is no hover.
    """
    scss = read("_sass", "cocktails", "_cards.scss")
    base = re.search(r"^\.drink-card-tagline \{(.*?)^\}", scss, re.S | re.M)
    assert base, "_cards.scss has no base `.drink-card-tagline` rule."
    assert re.search(r"^\s*display:\s*none;", base.group(1), re.M), (
        "`.drink-card-tagline` must be `display: none` at rest. Shown by "
        "default it is the tagline back on every index card, which #512 "
        "removed and Helen declined again on 2026-10-04."
    )

    for parts in (("cocktails", "index.html"), ("_layouts", "cocktail.html")):
        html = read(*parts)
        for part in ("line", "mark"):
            assert re.search(
                r'include cocktails/card-tagline\.html doc=\w+ part="' + part + '"', html
            ), (
                f"{'/'.join(parts)} no longer includes cocktails/card-tagline.html "
                f'with part="{part}". The index card and the related card must '
                "both carry the tagline and its mark, through the one include."
            )

    layout = read("_layouts", "default.html")
    assert re.search(r"<script src=[^>]*/card-tagline\.js", layout), (
        "_layouts/default.html no longer loads assets/js/card-tagline.js. The "
        "`?` mark ships `hidden` and only that script un-hides it, so without "
        "the tag a device with no hover cannot see a tagline on a card."
    )


def test_the_shopping_list_reads_the_aisles_from_the_data_file():
    """The aisle headings are emitted from _data/food/aisles.yml, not written out.

    Adding an aisle is a YAML edit and must never need the template touched.
    The keyword table stays off the page: the matching happens at build time
    in _plugins/food_shopping.rb.
    """
    html = read("food", "index.html")
    assert 'id="recipe-aisles"' in html, (
        "food/index.html no longer emits the #recipe-aisles block, so the "
        "shopping list has no headings and no order to put them in."
    )
    assert "site.data.food.aisles.order" in html, (
        "the #recipe-aisles block no longer reads _data/food/aisles.yml's own "
        "`order`. A hand-written copy in the template is a second list to keep "
        "in step, which is the thing this contract exists to prevent."
    )
    # Comments stripped first: the template's prose names what it does not emit.
    assert "aisles.keywords" not in _strip_comments(html, ".html"), (
        "food/index.html looks like it is emitting the aisle KEYWORD table. "
        "That belongs at build time in _plugins/food_shopping.rb -- one "
        "implementation of the matching rule, and 400 keywords off the page."
    )


def test_filters_js_holds_no_aisle_vocabulary():
    """No aisle name is written into the JavaScript.

    A heading spelled in two places means renaming one renames half the page.
    filters.js reads the list off the page and passes it straight through.
    """
    aisles = yaml.safe_load((DATA / "aisles.yml").read_text(encoding="utf-8"))
    source = _strip_comments(
        (ROOT / "assets" / "js" / "filters.js").read_text(encoding="utf-8"), ".js")

    leaked = [a["label"] for a in aisles["order"]
              if f'"{a["label"]}"' in source or f"'{a['label']}'" in source]
    assert not leaked, (
        f"aisle labels are written into assets/js/filters.js: {leaked}. They "
        "belong to _data/food/aisles.yml, which food/index.html emits as "
        "#recipe-aisles for the script to read."
    )


def test_cook_timer_js_holds_no_schedule_arithmetic():
    """The maths lives in cook-schedule.js, where tests/js can reach it.

    cook-timer.js is DOM wiring. A rate multiplication or a minutes-from-
    midnight calculation written there is untested by construction (#221).
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

    The state is one object whose fields, cleared value and "is anything set"
    answers are all derived from FIELD_SPEC in assets/js/filter-state.js. A
    loose variable in filters.js is outside that enumeration, so clearing and
    the clear-all button's predicate can disagree about it (#52). Declarations
    only: the names may still appear in prose.
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

    The block alone, with its {% comment %} blocks removed, because the
    incidental check below searches it for a word the rest of the template,
    and the loop's own comment, are free to use.
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
    """Each index row carries its complete ingredient list, derived from
    ingredient_groups and joined on `|` (#52).

    The exclude filter reads it. main_ingredients is a deliberately partial
    hint: an exclusion answered from it hands back recipes containing the
    thing the cook is avoiding.
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

    # Not the comma data-ingredients uses: these values are free `item:` text,
    # where a comma is common and nothing validates it away.
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

    The flag hides an item from main_ingredients and from the recipe page's
    Ingredients section, but someone avoiding the frying oil still needs it
    excluded (#52). Two halves: the template must not filter the flag out, and
    the collection must still contain an example.
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

    # The Liquid's rule, mirrored: name up to the first comma or open bracket,
    # lowercased. A parallel implementation, not a render of the template: it
    # guards the rule, not the template's fidelity to it.
    for slug, item_text in with_incidentals:
        name = re.split(r"[,(]", item_text)[0].strip().lower()
        assert name, (
            f"_food_recipes/{slug}.md has an incidental item ({item_text!r}) "
            f"that derives to an empty index entry, so it can never be excluded."
        )


# --- a badge is a control, not a caption -------------------------------------

def test_recipe_badges_are_links_carrying_their_own_filter_value():
    """GitHub issue #40. Every taxonomy badge is an <a> with data-tag/data-star.

    A <span> fails quietly three ways: it is unreachable by keyboard;
    filters.js routes a click and paints `.badge--matched` from the data
    attribute; and the href is the whole mechanism on a recipe page, where no
    script intercepts. The href's fragment names the filter section that
    holds the badge (#1059).
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

    # url_encode spells a space as `+`, which parseQuery in
    # assets/js/filter-state.js undoes. No filter at all breaks every taxonomy
    # value containing a space.
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

    # The star badge names one fixed section; a tag badge's section depends
    # on its group, so its fragment is built from `group.name` (#1059).
    assert "#filter-star" in html, (
        '_includes/recipe_badges.html\'s star badge no longer ends its href '
        'in "#filter-star" -- #1059. Clicking the badge on a recipe page must '
        'land on the STAR INGREDIENT section, not the top of the index.'
    )
    assert re.search(r'\?tag=[^"]*#filter-\{\{\s*group\.name\s*\}\}', html), (
        '_includes/recipe_badges.html\'s tag badge no longer ends its href in '
        '"#filter-{{ group.name }}" -- #1059. A tag\'s fragment has to name '
        'whichever section (mood or practicalities) actually holds it, so it '
        'is built from the same group.name the badge\'s class already uses, '
        'not a fixed string.'
    )


def test_filter_sections_carry_the_id_their_badges_and_chips_link_to():
    """#1059: the filter section a chip's or badge's fragment names carries
    that id, or the link lands at the top of the index.

    food/index.html passes each filter_group.html call a `section_id`, which
    the include turns into the wrapper's `id`; cocktails' MOOD and HASSLE
    sections write the literal id.
    """
    filter_group = read("_includes", "filter_group.html")
    assert 'id="{{ include.section_id }}"' in filter_group, (
        "_includes/filter_group.html no longer passes include.section_id "
        "through to the wrapper's id -- #1059. Without it, no filter section "
        "built through this include has a stable id for a badge to link to."
    )

    food_index = read("food", "index.html")
    assert re.search(r'section_id\s*=\s*"filter-star"', food_index), (
        'food/index.html\'s STAR INGREDIENT filter_group.html call no longer '
        'passes section_id="filter-star" -- #1059. The star badge '
        '(recipe_badges.html) links to exactly this fragment.'
    )
    assert re.search(
        r'\{%-?\s*capture\s+group_section_id\s*%\}filter-\{\{\s*group\.name\s*\}\}',
        food_index,
    ), (
        "food/index.html no longer builds a per-tag-group fragment id "
        "(`filter-<group.name>`) for its tag_groups loop -- #1059. MOOD and "
        "PRACTICALITIES must each carry a stable id a tag badge can name."
    )
    assert re.search(r'section_id\s*=\s*group_section_id', food_index), (
        "food/index.html's tag_groups filter_group.html call no longer "
        "passes the captured section_id through -- #1059."
    )

    cocktails_index = read("cocktails", "index.html")
    for group, section_id in (("mood", "filter-mood"), ("hassle", "filter-hassle")):
        assert re.search(
            r'class="drink-filter drink-filter--' + group + r'"\s+id="' + section_id + r'"',
            cocktails_index,
        ), (
            f'cocktails/index.html\'s {group.upper()} section no longer '
            f'carries id="{section_id}" -- #1059. A drink page\'s own {group} '
            f'chips (_layouts/cocktail.html) link to exactly this fragment.'
        )

    cocktail_layout = read("_layouts", "cocktail.html")
    assert re.search(
        r'href="\{\{\s*index_home\s*\|\s*relative_url\s*\}\}\?mood=\{\{\s*m\s*\|\s*'
        r'url_encode\s*\}\}#filter-\{\{\s*chip\s*\}\}"',
        cocktail_layout,
    ), (
        "_layouts/cocktail.html's mood chip no longer ends its href in "
        '"#filter-{{ chip }}" -- #1059. `chip` is already "mood" or "hassle", '
        "the same word cocktails/index.html's two section ids use."
    )


def test_the_see_shortlist_link_lands_on_the_results_list():
    """#1057: "see shortlist" lands on the count line both indexes carry
    id="results" on, not the top of the index.
    """
    page_actions = read("_includes", "page-actions.html")
    assert re.search(r'href="[^"]*\?shortlist=1#results"', page_actions), (
        '_includes/page-actions.html\'s "see shortlist" link no longer ends '
        'in "?shortlist=1#results" -- #1057. It must land on the count line '
        'both indexes carry id="results" on, the same landing a search '
        'result gets.'
    )


def test_filters_js_holds_no_ingredient_vocabulary():
    """Singulars and synonyms belong in YAML, not in the JavaScript."""
    js = read("assets", "js", "filters.js")
    for name in ("var singularMap = {", "var synonymMap = {"):
        assert name not in js, (
            f"assets/js/filters.js declares `{name}...` inline. The ingredient "
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
    """Neither file comes back: colors.yml would be a second copy of the
    palette, and nothing reads recipe_sections.yml.
    """
    assert not (ROOT / relpath).exists(), (
        f"{relpath} has reappeared. Colour belongs in _sass/food/_palette.scss only; "
        f"highlighter shape and texture are chosen in assets/js/decorations.js."
    )


def test_palette_is_the_only_place_hex_colours_are_written():
    """No script under assets/js/ writes a hex colour; the palette is the only source.

    A script that needs a colour reads a CSS custom property at runtime. Both
    comment kinds are stripped first, or `issue #244` in a block comment reads
    as a three-digit colour. `_strip_js_comments` keeps line breaks because the
    failure names `file:lineno`.
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

    An entry that matches nothing is a typo or a leftover. Matching is exact
    and lowercase, as food/index.html does it. Skips when ALL_DRAFTS is empty.
    """
    from conftest import ALL_RECIPES, ALL_DRAFTS
    path = DATA / "pantry.yml"
    if not path.exists():
        pytest.fail("_data/food/pantry.yml is gone. Every test that reads it would skip, not fail, without this line.")
    pantry = yaml.safe_load(path.read_text(encoding="utf-8")) or []

    # Some pantry entries are used only by drafts, and `_food_drafts/` is a
    # private repo a CI checkout lacks. Without ALL_DRAFTS this would fail on
    # correct data, so it skips; test_pantry_entries_are_well_formed is what
    # CI can still check.
    if not ALL_DRAFTS:
        pytest.skip(
            "_food_drafts/ is absent (private, gitignored repo), so the "
            "collection here is the 82 published recipes only. 15 pantry "
            "entries are used exclusively by drafts, so this check cannot be "
            "evaluated -- it would fail on correct data. Runs on a machine "
            "with the drafts checked out."
        )
    assert ALL_RECIPES, (
        "No published recipes found either, so there is no corpus at all and "
        "this test would pass while checking nothing."
    )

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


def test_pantry_entries_are_well_formed():
    """What CI can check about pantry.yml without the private drafts repo.

    food/index.html does a raw `contains` against this list, so a duplicate
    survives an edit that removes the first copy, and an entry with
    surrounding whitespace, or an empty one, never matches anything.
    """
    path = DATA / "pantry.yml"
    if not path.exists():
        pytest.fail("_data/food/pantry.yml is gone. Every test that reads it would skip, not fail, without this line.")
    pantry = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    assert pantry, (
        "_data/food/pantry.yml is empty. Every main_ingredients entry would be "
        "promoted, which is not a state to reach by accident."
    )

    problems = []
    seen = set()
    for entry in pantry:
        text = str(entry)
        if text != text.strip():
            problems.append(f"{text!r} has surrounding whitespace")
        if not text.strip():
            problems.append("an empty entry")
        key = text.strip().lower()
        if key in seen:
            problems.append(f"{text!r} is listed more than once")
        seen.add(key)

    assert not problems, (
        "_data/food/pantry.yml:\n  " + "\n  ".join(problems)
        + "\n\nfood/index.html matches these with a raw `contains` against a "
          "stripped, lowercased ingredient, so any of these is an entry that "
          "silently never fires."
    )


def test_pantry_list_is_lowercase():
    """food/index.html matches `ing | downcase` against this list with a raw
    `contains`, and Liquid does not lowercase the pantry side, so an uppercase
    entry silently never matches anything.
    """
    path = DATA / "pantry.yml"
    if not path.exists():
        pytest.fail("_data/food/pantry.yml is gone. Every test that reads it would skip, not fail, without this line.")
    pantry = yaml.safe_load(path.read_text(encoding="utf-8")) or []

    not_lower = [p for p in pantry if p != p.lower()]
    assert not not_lower, (
        f"_data/food/pantry.yml has non-lowercase entries: {not_lower}.\n"
        f"food/index.html compares `ing | downcase` against this list as-is -- an "
        f"uppercase entry here matches nothing, ever, and nothing will tell you."
    )


def _sink_pantry(main_ingredients, pantry):
    """Python mirror of food/index.html's ordering Liquid (#74, #107):
    non-pantry ingredients first, pantry staples sunk to the end, authored
    order preserved within each half. Exact, lowercase match.

    A parallel implementation, not a render of the template: if the Liquid
    changes, change this to match, or its test checks a rule the page has left.
    """
    lead = [i for i in main_ingredients if str(i).lower() not in pantry]
    tail = [i for i in main_ingredients if str(i).lower() in pantry]
    return lead + tail


def test_main_ingredients_sink_pantry_to_the_end():
    """#74, #107: main_ingredients render in larder order on the index --
    distinctive ingredients first, pantry staples trailing. Checks the rule
    against known cases.
    """
    pantry = {"onion", "butter", "salt", "garlic"}

    # Ordinary split: distinctive ingredients lead, pantry trails.
    assert _sink_pantry(["chicken", "onion", "lemon", "butter"], pantry) == [
        "chicken", "lemon", "onion", "butter",
    ]

    # Exact match only -- a variety naming itself is not demoted (MANUAL §6).
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
    """Only assets.js reads the base-url meta tag.

    Every decorative asset URL is built from this value, and it changes when
    `baseurl` does, so a second reader is a second chance to be wrong on deploy.
    """
    pattern = re.compile(r"""meta\[name=["']base-url["']\]""")
    offenders = []
    scripts = sorted(JS_DIR.glob("*.js"))
    assert any(p.name == "assets.js" for p in scripts), "assets/js/assets.js is gone."
    # The pattern is the CSS selector a reader queries, so default.html's
    # `<meta name="base-url">`, which emits the tag, does not match it.
    for path in scripts + [ROOT / "_layouts" / "default.html",
                           ROOT / "_layouts" / "recipe.html",
                           ROOT / "food" / "index.html"]:
        assert path.exists(), f"{path.relative_to(ROOT)} is gone; scan its successor."
        hits = len(pattern.findall(path.read_text(encoding="utf-8")))
        if hits and path.name != "assets.js":
            offenders.append(f"{path.name} ({hits})")
    assert not offenders, (
        f"base-url is read outside assets/js/assets.js: {offenders}.\n"
        f"Use window.HTF.base or window.HTF.asset(path) instead. assets.js is "
        f"loaded first in default.html precisely so that it can be."
    )


def test_assets_js_loads_before_any_other_script():
    """assets.js defines window.HTF, which every other script calls at parse time.

    "End of <body>" is not first: a page layout's own scripts are emitted
    inside `{{ content }}`, above default.html's closing scripts, and would
    run before it and throw. So assets.js sits in <head>, above
    `{{ content }}`.
    """
    # Liquid comments stripped first: the layout's own comment quotes
    # `{{ content }}`, and find() would locate that mention.
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

    Each stripped block leaves exactly the newlines it held, because callers
    report `file:lineno`. A trailing `//` comment is stripped as well as a
    whole-line one.
    """
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"),
                  text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def test_svg_injection_does_not_assume_a_space_after_the_svg_tag():
    """No script's replace() searches for the literal `'<svg '` with a
    trailing space.

    Inkscape puts each attribute on its own line, so its files open with
    `<svg\\n`. String.replace returns its input unchanged when nothing matches,
    so the artwork renders at its natural size with no error. Match `<svg`
    plus whitespace. Comments are stripped first: they may quote the literal.
    """
    # Only the search argument of a replace: the replacement legitimately
    # contains `<svg `.
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
    """Every SVG under assets/img/ opens with a tag the injection can match.

    Guards the files rather than the regex, so artwork exported with another
    convention fails here instead of rendering at the wrong size.
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

    The usual cause is `--` inside an XML comment, which is illegal: the whole
    document fails to parse and the browser keeps showing its cached copy
    (#241). The build does not parse SVGs. Covers _includes/icons/ too: those
    are inlined into the page, so a malformed one damages the markup round it.
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
    """Only assets.js reads the site-key meta tag.

    Each site keeps its artwork under assets/img/<site>/, so every decorative
    fetch needs the key; assets.js exposes it as HTF.site and HTF.siteAsset().
    A wrong key in a second reader fails only on the site nobody is looking at.
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

    Artwork goes through HTF.siteAsset(), which builds the path from the
    page's site key; `HTF.asset('/assets/img/…')` reaches into one site's set.
    The shared header and footer artwork is no exception: it goes through
    HTF.chromeAsset, so this rule never has to allow HTF.asset for images.
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

    With `.catch(function() {})` a wrong baseurl gives a site with no
    decoration and a clean console. HTF.fetchSvg warns with the URL.
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
        "Direct fetch() call(s) found outside assets/js/assets.js:\n  "
        + "\n  ".join(offenders)
        + "\n\nUse window.HTF.fetchSvg(url, cb) so the call gets caching and a "
          "diagnostic warning on failure."
    )


# --- repo and deployment hygiene --------------------------------------------

def test_gemfile_does_not_pin_jekyll_backwards():
    """The `github-pages` gem would silently downgrade Jekyll 4.3 to 3.9.

    Deployment runs `bundle exec jekyll build` in an Actions workflow, so the
    version in the Gemfile is the one used.
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

    .gitignore matches by directory name, so renaming a drafts collection
    silently stops ignoring it and the drafts become stageable. The names are
    derived from _config.yml, so a collection added later is covered. Git is
    asked too: a pattern ending in `/` does not ignore a symlink (#235).
    """
    config = yaml.safe_load(read("_config.yml"))
    drafts = [name for name in (config.get("collections") or {}) if "draft" in name]
    assert drafts, (
        "_config.yml declares no drafts collection. If drafts were deliberately "
        "removed, delete this test; otherwise the collection name has changed "
        "shape and this check is no longer finding it."
    )
    # Active patterns only: .gitignore's own comments name the directories.
    active = {line.strip() for line in read(".gitignore").splitlines()
              if line.strip() and not line.strip().startswith("#")}
    missing = [f"_{name}/" for name in drafts if f"_{name}/" not in active]
    assert not missing, (
        f".gitignore does not cover {missing}.\n"
        f"These are unpublished drafts and the repo is public. `output: false` "
        f"in _config.yml stops them PUBLISHING; it does nothing to stop the "
        f"source markdown being committed."
    )

    # A written pattern is not an ignored path: `_cocktail_drafts/` matches a
    # directory, and git does not treat a symlink to one as a directory. Only
    # paths on disk are asked about; `check-ignore` on an absent path proves
    # nothing.
    for name in drafts:
        path = ROOT / f"_{name}"
        if not (path.exists() or path.is_symlink()):
            continue
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", f"_{name}"],
            cwd=ROOT, capture_output=True,
        ).returncode == 0
        assert ignored, (
            f"`_{name}` exists here but git does NOT ignore it, even though "
            f".gitignore names it. The usual cause is that it is a SYMLINK: "
            f"`_{name}/` matches a directory and a link to one is not a "
            f"directory. Add the slashless `_{name}` beside it. Until then "
            f"these unpublished drafts are stageable in a public repo."
        )


def test_every_glass_icon_named_in_the_data_exists():
    """Every icon _data/cocktails/glasses.yml names exists under
    _includes/icons/glasses/.

    A glass with no entry renders no icon, by design. An entry naming a file
    that is not there fails the Jekyll build on every drink using that glass:
    `{% include %}` has no file-exists test.
    """
    path = ROOT / "_data" / "cocktails" / "glasses.yml"
    if not path.exists():
        pytest.fail("_data/cocktails/glasses.yml is gone. Every test that reads it would skip, not fail, without this line.")
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


def _png_size(path: Path) -> tuple[int, int]:
    """Width and height from a PNG's IHDR chunk -- bytes 16..24, big-endian."""
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def test_every_link_preview_image_exists_at_the_size_the_layout_claims():
    """The og:image cards (#1086): one per site in sites.yml, rendered by
    scripts/render_social_images.py. A site-neutral page takes its site_key's.

    Every named card exists, its PNG header matches the og:image:width/height
    the layout states, and the layout's numbers match the script's constants.
    """
    sites = yaml.safe_load(read("_data", "sites.yml"))
    cards = {f"sites.yml {key}": s.get("social_image") for key, s in sites.items()}
    missing_key = [where for where, path in cards.items() if not path]
    assert not missing_key, (
        f"No social_image declared for: {missing_key}. Every site names its own "
        f"card; _layouts/default.html falls back to text-only for a page with "
        f"none, which is the state this test exists to end."
    )

    layout = read("_layouts", "default.html")
    width = re.search(r'property="og:image:width" content="(\d+)"', layout)
    height = re.search(r'property="og:image:height" content="(\d+)"', layout)
    assert width and height, "_layouts/default.html no longer states og:image:width/height"
    claimed = (int(width.group(1)), int(height.group(1)))

    script = read("scripts", "render_social_images.py")
    dims = re.search(r"^WIDTH, HEIGHT, SCALE = (\d+), (\d+), (\d+)", script, re.M)
    assert dims, "scripts/render_social_images.py no longer declares WIDTH, HEIGHT, SCALE"
    written = (int(dims.group(1)) * int(dims.group(3)), int(dims.group(2)) * int(dims.group(3)))
    assert claimed == written, (
        f"_layouts/default.html claims og:image is {claimed}, but "
        f"scripts/render_social_images.py writes {written}. Change both together."
    )

    problems = []
    for where, path in cards.items():
        file = ROOT / path.lstrip("/")
        if not file.is_file():
            problems.append(f"{where}: {path} is not in the repo -- run the script")
            continue
        size = _png_size(file)
        if size != claimed:
            problems.append(f"{where}: {path} is {size}, the layout claims {claimed}")
    assert not problems, "\n".join(problems)


def test_every_site_has_each_favicon_the_layout_links():
    """The tab and home-screen icons: _layouts/default.html links
    assets/img/favicon/<site_key>-<size>.png at the sizes its `sizes=`
    attributes state. Every site in sites.yml has every one of those files,
    each a PNG of exactly that size, and no SVG icon is linked, because a
    browser would take it at every size over the PNGs.
    """
    layout = read("_layouts", "default.html")
    linked = re.findall(r'sizes="(\d+)x\1" href="\{\{ icon_base \| append: \'-(\d+)\.png\'', layout)
    assert linked, "_layouts/default.html no longer links the per-site favicons"
    assert all(a == b for a, b in linked), f"a favicon's sizes= and file name disagree: {linked}"
    assert 'type="image/svg+xml"' not in layout, "an SVG icon is linked again; see the comment above the favicon links"

    sites = yaml.safe_load(read("_data", "sites.yml"))
    problems = []
    for key in sites:
        for size, _ in linked:
            file = ROOT / "assets" / "img" / "favicon" / f"{key}-{size}.png"
            if not file.is_file():
                problems.append(f"{file.relative_to(ROOT)} is missing -- run scripts/render_favicons.py "
                                f"(or render_social_images.py for the 180)")
            elif _png_size(file) != (int(size), int(size)):
                problems.append(f"{file.relative_to(ROOT)} is {_png_size(file)}, the layout claims {size}x{size}")
    assert not problems, "\n".join(problems)


# --- accessibility of the interactive layer ----------------------------------

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


def test_the_recipe_title_gap_names_the_furniture_includes_own_wrapper():
    """The gap under the back arrow is a sibling selector naming the include's
    outermost element.

    `_sass/food/_recipe-header.scss` closes the gap with
    `.<wrapper> + .recipe .recipe-title`. Rename or re-wrap the include and
    the rule matches nothing, silently, and the title drops (#1024, #1093).
    """
    include = read("_includes", "back-to-index.html")
    wrapper = re.search(r'^<(\w+) class="([\w-]+)"', _strip_comments(include, ".html"), re.M)
    assert wrapper, "_includes/back-to-index.html has no top-level classed element."
    selector = f".{wrapper.group(2)} + .recipe .recipe-title"
    assert selector in read("_sass", "food", "_recipe-header.scss"), (
        f"The food recipe title's gap under the arrow must be `{selector}`: that is "
        f"the element directly before article.recipe now. A sibling selector naming "
        f"anything else matches nothing, silently, and the title drops to 3rem."
    )


def test_clear_controls_are_buttons():
    """A <span> with a click handler is not focusable and not announced."""
    html = read("food", "index.html") + read("_includes", "filter_group.html")
    offenders = re.findall(r'<span[^>]*class="[^"]*btn-clear-inline', html)
    assert not offenders, (
        f"Found {len(offenders)} clear control(s) rendered as <span>. "
        f"A control with a click handler must be a <button type=\"button\"> or "
        f"it cannot be reached by keyboard. The class is already named btn-*."
    )


def test_filter_buttons_announce_their_state():
    """The filter buttons are toggles, so they need aria-pressed.

    filters.js syncs the value from the .active class in one place,
    syncAriaPressed, rather than at each toggle site.
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
    """The food index has an h1, like every recipe page."""
    html = read("food", "index.html")
    assert re.search(r"<h1[^>]*>", html), (
        "food/index.html has no <h1>. The logo is the visible title, so a "
        '<h1 class="visually-hidden"> is the right shape — it gives assistive '
        "tech and search engines something to anchor to without changing the "
        "design."
    )


# --- one word per concept ----------------------------------------------------

def test_the_method_is_called_method_everywhere():
    """The word `instructions` appears in no code line of the recipe layout or
    method-toggle.js: the data field is `method`, so the class and the JS say
    `method` too.
    """
    offenders = []
    for relpath in ("_layouts/recipe.html", "_sass/food/_recipe-ingredients-method.scss",
                    "assets/js/method-toggle.js"):
        path = ROOT / relpath
        # A missing file would pass by scanning nothing, so a rename must fail here.
        assert path.exists(), f"{relpath} is gone; point this test at its successor."
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            # A comment may use the word.
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
    """The template has no fallback to `instructions:`, so a file using it
    renders no method.

    Partial in CI, knowingly (#378): it reads ALL_DRAFTS as well as recipes,
    and a CI checkout has no drafts. Not skipped there, because the published
    half is the half that ships.
    """
    from conftest import ALL_RECIPES, ALL_DRAFTS
    assert ALL_RECIPES, (
        "No published recipes loaded at all, so this check has nothing to scan "
        "and would pass having examined nothing."
    )
    offenders = [r.slug for r in ALL_RECIPES + ALL_DRAFTS if "instructions" in r.fm]
    assert not offenders, (
        f"These files still use an `instructions:` field: {offenders}.\n"
        f"recipe.html no longer falls back to it, so their method would render "
        f"empty. Rename the field to `method:`."
    )


def test_no_orphaned_data_file_references():
    """No template reads `index_tags_sections`: Jekyll resolves a missing data
    file to nil silently, so the symptom is empty filter groups."""
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

    rglob, not glob: the partials live in subdirectories, and a flat glob
    matches an empty set, so the structural tests pass while checking nothing.
    test_sass_files_are_actually_found asserts this returns something.
    """
    return sorted(SASS_DIR.rglob("*.scss"))


def test_sass_files_are_actually_found():
    """sass_files() finds the partials. If they move somewhere it does not
    reach, this fails instead of the structural tests passing on an empty list.
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

    A rule inside an at-rule counts, and carries the at-rule in its key
    (`@media print .recipe-badges`): a print rule overriding a screen rule
    declares the same property on purpose and must not read as a clash.
    Element selectors (`body`, `h1, h2`) count too. Line-oriented: it assumes
    one opening brace at the end of its line and a closing brace on its own.
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

# The palette variables a shared partial may read: everything
# _sass/shared/_theme.scss declares (#374, #129).
SHARED_PALETTE_CONTRACT = re.findall(
    r"^\$([\w-]+):\s*null !default;",
    (SASS_DIR / "shared" / "_theme.scss").read_text(encoding="utf-8"), re.M)

# Directories holding a _palette.scss: the two sites.
PALETTE_OWNERS = ["food", "cocktails"]


@pytest.mark.parametrize("owner", PALETTE_OWNERS)
def test_every_palette_satisfies_the_shared_contract(owner):
    """Every palette declares each variable shared/_theme.scss lists, and the
    site's entry stylesheet passes each one into the theme.

    The theme stops the build when a value is unset; checked here too so the
    failure names the file and the variable.
    """
    assert SHARED_PALETTE_CONTRACT, "_sass/shared/_theme.scss declares no variables"
    path = SASS_DIR / owner / "_palette.scss"
    assert path.exists(), (
        f"_sass/{owner}/_palette.scss is missing. assets/css/{owner}.scss "
        f"loads it first and fills the shared theme from it."
    )
    text = path.read_text(encoding="utf-8")
    missing = [v for v in SHARED_PALETTE_CONTRACT
               if not re.search(rf"^\${re.escape(v)}\s*:", text, re.M)]
    assert not missing, (
        f"_sass/{owner}/_palette.scss does not declare {missing}, which "
        f"_sass/shared/_theme.scss says every palette owes the shared partials."
    )
    entry = (ROOT / "assets" / "css" / f"{owner}.scss").read_text(encoding="utf-8")
    unpassed = [v for v in SHARED_PALETTE_CONTRACT
                if not re.search(rf"\${re.escape(v)}:\s*palette\.\${re.escape(v)}\b", entry)]
    assert not unpassed, (
        f"assets/css/{owner}.scss does not pass {unpassed} into "
        f"`@use \"shared/theme\" with (...)`. Pass each as "
        f"`$name: palette.$name`."
    )


SHARED_FONT_STACKS = ["font-headings", "font-body"]


@pytest.mark.parametrize("variable", SHARED_FONT_STACKS)
def test_the_two_palettes_declare_the_SAME_font_stack(variable):
    """Both palettes declare the same `$font-headings` and `$font-body` (#686).

    Typography is the family resemblance between the sites; a stack that
    drifts on one leaves neither looking wrong on its own screen. Compared
    for equality rather than hoisted into shared/, so every palette still
    declares each variable in SHARED_PALETTE_CONTRACT by name. An intended
    divergence takes the variable out of SHARED_FONT_STACKS with the reason.
    """
    pattern = rf"^\${re.escape(variable)}\s*:\s*(.+?);"
    declared = {}
    for owner in PALETTE_OWNERS:
        text = (SASS_DIR / owner / "_palette.scss").read_text(encoding="utf-8")
        match = re.search(pattern, text, re.M)
        assert match, (
            f"_sass/{owner}/_palette.scss declares no ${variable}, which "
            f"test_every_palette_satisfies_the_shared_contract should have "
            f"caught first — the build fails without it."
        )
        # Whitespace normalised: the two files align their values in a column.
        declared[owner] = re.sub(r"\s+", " ", match.group(1).strip())

    values = set(declared.values())
    assert len(values) == 1, (
        f"The two sites set ${variable} differently:\n  "
        + "\n  ".join(f"_sass/{o}/_palette.scss: {v}" for o, v in declared.items())
        + f"\n\nTypography is the family resemblance between the two sites, and "
          f"both palettes' comments ask that a change here be a decision rather "
          f"than drift. If the divergence IS the decision, take '{variable}' out "
          f"of SHARED_FONT_STACKS and say why."
    )


def test_shared_scss_never_imports_a_site_partial():
    """The dependency arrow points one way: sites load shared, never back.

    A shared partial reaching into _sass/food/ compiles on the food stylesheet
    and fails on the cocktails one. Sass's own `sass:` modules belong to no
    site, so a shared partial may use them.
    """
    offenders = []
    for path in sorted((SASS_DIR / "shared").glob("*.scss")):
        for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            code = line.split("//")[0]
            match = re.search(r"""@(?:import|use|forward)\s+['"]([^'"]+)""", code)
            if match and not match.group(1).startswith(("shared/", "sass:")):
                offenders.append(f"shared/{path.name}:{i} imports {match.group(1)}")
    assert not offenders, (
        "A shared partial imports something outside shared/:\n  "
        + "\n  ".join(offenders)
        + "\n\nshared/ may not depend on any one site. Move the shared thing "
          "into shared/, or the site-specific thing out of it."
    )


def test_no_stylesheet_uses_a_deprecated_sass_feature():
    """No `@import`, and none of the global functions Dart Sass 3 removes (#129).

    Each one prints a deprecation warning on every build, and a build log full
    of them is where a real error goes unseen. `@use` a module instead:
    `lightness.shift()` (shared/_lightness.scss) for darken()/lighten(),
    `color.mix()`, `list.append()`, an `@if` block for `if()`.
    """
    banned = re.compile(r"@import\b|(?<![\w.$-])(darken|lighten|mix|append|"
                        r"transparentize|opacify|saturate|desaturate|if|percentage|"
                        r"map-get|map-merge|nth|unquote)\(")
    offenders = []
    for path in sorted(list(SASS_DIR.rglob("*.scss")) + list((ROOT / "assets" / "css").glob("*.scss"))):
        for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            code = re.sub(r"//.*$", "", line)
            if banned.search(code):
                offenders.append(f"{path.relative_to(ROOT)}:{i}: {line.strip()}")
    assert not offenders, (
        "Deprecated Sass in use; each warns on every build:\n  " + "\n  ".join(offenders)
    )


def test_shared_scss_names_no_site():
    """No selector or variable in shared/ names one site: both render it.

    Comments are exempt.
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
    """No selector declares the same property in two separate blocks.

    A selector may appear more than once, since a partial groups by concern.
    A repeated property is the hazard: the later block wins and editing the
    earlier one appears to do nothing.
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

def test_a_print_partial_declares_nothing_outside_media_print():
    """Every top-level block in a `_print.scss` is an `@media print` (#538).

    A rule that forgets the wrapper compiles to top level and styles the
    screen, with a clean build. Only blocks are checked: a print partial may
    hold variables, `@use` lines or comments.
    """
    partials = [p for p in sass_files() if p.name.startswith("_print")]
    assert partials, (
        "No _print*.scss partials found under _sass/. There are three "
        "(shared, food, cocktails), so finding none means this scan went stale "
        "and would pass while checking nothing (MANUAL 12)."
    )

    offenders = []
    for path in partials:
        depth = 0
        for i, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            code = raw.split("//")[0]
            if depth == 0 and "{" in code:
                head = code.split("{")[0].strip()
                if not (head.startswith("@media") and "print" in head):
                    # Every print partial is called _print.scss, so the parent
                    # directory is the half that says which one.
                    offenders.append(f"{path.parent.name}/{path.name}:{i} {head}")
            depth += code.count("{") - code.count("}")

    assert not offenders, (
        "Top-level block(s) in a print partial that are not `@media print`:\n  "
        + "\n  ".join(offenders)
        + "\n\nThese compile to top level and apply ON SCREEN, which is issue "
          "#538: cocktails' print rules did exactly this and would have "
          "permanently disabled the `make it` toggle they were written to "
          "override. Wrap them in `@media print { … }`. If a rule genuinely "
          "belongs on screen, it belongs in a partial that is not named "
          "_print.scss."
    )


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
    """Every class the print stylesheet styles is emitted by a template or
    named by a script (#86).

    A print rule that did not follow a rename goes wrong on paper only, with
    no error. Both sides are derived, so a new print rule is covered without
    editing this test. A class with no print rule is the normal case.
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

    # A class a script adds counts: `is-making` comes from
    # assets/js/cocktail-make.js, never a template (#482). Matched as a quoted
    # string, which is how a classList call names one.
    scripts = "\n".join(
        s.read_text(encoding="utf-8") for s in sorted(ROOT.glob("assets/js/*.js")))

    def somewhere(cls):
        if re.search(rf'class="[^"]*\b{re.escape(cls)}\b', markup):
            return True
        return bool(re.search(rf"""['"]{re.escape(cls)}['"]""", scripts))

    missing = sorted({
        f"{where_}: .{cls}" for where_, cls in named if not somewhere(cls)
    })
    assert not missing, (
        "Print rule(s) target a class no template emits:\n  " + "\n  ".join(missing)
        + "\n\nEither the class was renamed and the print stylesheet did not "
          "follow it, or the rule is left over from markup that has gone. A "
          "print rule that matches nothing fails silently and on paper only.\n\n"
          "Templates AND assets/js/*.js are both searched, so a class applied "
          "only by a script counts as emitted."
    )


def test_print_neutralises_the_screen_page_background():
    """Whatever paints the page ground for the screen is overridden in print.

    A screen `body { background }` is still in the cascade inside
    `@media print`, so a print stylesheet that leaves the background
    unmentioned prints the tint over every sheet. Derived from the
    stylesheets, so a new partial painting the ground is asked the same.
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

    # Asserted, not an early return: with nothing found this would pass while
    # checking nothing.
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
    """A list section in the recipe layout is gated on `.size`, never on bare
    truthiness.

    An empty array is truthy in Liquid, so `notes: []` renders the heading
    over nothing, with valid data and a clean build. Any `.size` comparison
    is fine.
    """
    layout = read("_layouts", "recipe.html")
    # Not stripped of comments first: the layout's comments describe the bad
    # pattern in prose, because Liquid parses tags inside a comment.
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
    """The pdf link on a page and the file scripts/generate_pdfs.py writes
    agree on one directory (#86).

    A changed permalink leaves the script working and every link a 404, on a
    green deploy. The permalink, the link and the write path are each read
    from where they live.
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

    # The link is the page's own URL with its trailing slash swapped for
    # `.pdf` (#1005), built in _includes/page-print.html, which the recipe and
    # drink layouts include above their head's rule (#1447). The magic-bag
    # page has no PDF beside it, so its layout must not include it.
    include = read("_includes", "page-print.html")
    assert re.search(
        r"page\.url\s*\|\s*append:\s*'\.pdf'\s*\|\s*replace:\s*'/\.pdf',\s*'\.pdf'",
        include,
    ), (
        "_includes/page-print.html no longer builds the PDF link from "
        "page.url (`page.url | append: '.pdf' | replace: '/.pdf', '.pdf'`). "
        "If it is built another way now, this check needs to follow it -- it "
        "is the only thing tying the link to where the files are written."
    )
    include_print = r"\{%\s*include\s+page-print\.html\s*%\}"
    assert not re.search(include_print, _strip_comments(read("_includes", "back-to-index.html"), ".html")), (
        "_includes/back-to-index.html renders page-print.html again; print and "
        "pdf sit above the head's rule (#1447), not under the search box."
    )
    for layout_name in ("recipe.html", "cocktail.html"):
        assert re.search(include_print, _strip_comments(read("_layouts", layout_name), ".html")), (
            f"_layouts/{layout_name} no longer includes page-print.html, so its "
            f"pages have no pdf link -- or have one built somewhere this test "
            f"does not read."
        )
    assert not re.search(include_print, _strip_comments(read("_layouts", "magic_bag.html"), ".html")), (
        "_layouts/magic_bag.html includes print and pdf, but "
        "scripts/generate_pdfs.py renders no PDF beside a magic-bag page, so the "
        "link would be #86's permanent 404."
    )

    # Read from the script's tuple of directories, not a literal glob (#1005).
    script = read("scripts", "generate_pdfs.py")
    dirs = re.search(r'for collection in \(([^)]*)\):', script)
    assert dirs, (
        "scripts/generate_pdfs.py no longer loops `for collection in (...)` "
        "over the directories it renders, so this check cannot see where it "
        "writes PDFs. Follow the script's new shape here."
    )
    rendered = re.findall(r'"([^"]+)"', dirs.group(1))
    assert expected.strip("/") in rendered, (
        f"scripts/generate_pdfs.py renders {rendered}, which does not include "
        f"{expected.strip('/')!r} -- recipe pages would get no PDF and every "
        f"pdf link on food would 404."
    )
    drinks = ((config.get("collections") or {}).get("cocktail_recipes") or {}).get("permalink")
    assert drinks and drinks.split(":")[0].strip("/") in rendered, (
        f"scripts/generate_pdfs.py renders {rendered}, which does not include "
        f"the cocktail_recipes permalink {drinks!r} -- drink pages get a pdf "
        f"link since #1005, and it would 404."
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
    """No fixed `width` above 320px without a max-width, min() or clamp().

    One unclamped element is enough to scroll a phone sideways. This checks
    elements only; overflow is also a property of the row, which
    `test_a_multi_track_row_can_become_one` covers (#468).
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


# A multi-track grid that never collapses is a bet that its content stays
# narrow: the floor of a `1fr` track is its content's min-content width, which
# nothing static can compute. Each row here is a declared exception with the
# claim it makes. An entry for a row that has a narrow variant fails the test.
MULTI_TRACK_ROWS_WITHOUT_A_NARROW_VARIANT = {
    ".drink-count-block": (
        "`1fr auto` (#1412): the count or the shortlisted pill, beside the ship "
        "legend or `× clear ship`. The widest right cell is `SHIP IT? = ` plus "
        "one card word (`ship_words` keeps every rung to one short word) and "
        "the ship key's (i), about 175px; measured at 360px with no overflow."
    ),
    ".ship-key-list": (
        "`max-content 1fr` (#1440): a ship word beside Helen's line for it. "
        "The first track is the icon and the widest card word (`YES²`), about "
        "75px; the second is wrapping prose inside a dialog capped at the "
        "viewport less 2rem. Measured at 360px with no overflow."
    ),
    ".recipe-pagination": (
        "`1fr auto 1fr`: prev, a page-status label, next. Roughly 26 characters "
        "of Courier all told, so it is believed to fit a 360px phone -- BELIEVED, "
        "not measured, and it is the same shape as the footer row that did not. "
        "The status string is built in filters.js and is the part that could grow."
    ),
    ".cocktail-ingredients": (
        "`max-content 1fr` -- the amount column and the ingredient "
        "name/suggestion text. It was `.cocktail-ingredient-top` with "
        "`$amount-col 1fr` until #1088 (2026-09-20) moved the tracks up to the "
        "list so every row could share one measured column via `subgrid`; the "
        "claim is the same one, and the first track's is now stronger rather "
        "than weaker. `max-content` is bounded by the longest AMOUNT in one "
        "drink -- 13 characters of Plex Mono across the whole live collection "
        "('1 small pinch', about 119px), measured in tmp/amount_widths.py -- "
        "where the old fixed 5.5rem was paid by every drink whether it needed "
        "it or not. The `1fr` track is ordinary wrapping prose, not a nowrap "
        "label or a flat-width image the way the footer's hearts were: its "
        "min-content is the width of its single longest WORD, and every "
        "ingredient name and bottle suggestion in the data is comfortably under "
        "a 360px phone one word at a time. There is no unbroken string here "
        "that could grow past that. Verified at 360 and 390 with shoot.sh, "
        "which reported no element past the viewport."
    ),
    ".tc-row": (
        "`max-content minmax(0, 1fr)` -- a chart row's label and its figure on "
        "one line, the bar in a second grid row spanning both (2026-10-08, "
        "#1327). The first track is a Courier label of at most three words "
        "('DUCK BREAST SEPARATE', about 150px, the widest in the data); the "
        "second is the figure, which WRAPS in whatever is left -- and since "
        "2026-10-09 it is built from the numbers ('70°C+ → ~72–74°C' is the "
        "longest, under 20 characters), not the data's display string, so it "
        "no longer needs to. Verified at 360 and 390 with shoot.sh."
    ),
    ".ct-method": (
        "`minmax(0, 1fr) auto` -- a method's name and its time on one line, "
        "the oven setting and the outcome spanning both beneath (2026-10-08, "
        "#1329). The name is wrapping prose; the time is capped at 10.5rem and "
        "breaks at its dash (.ct-t), so its floor is one half of a range, "
        "'4h50m' at most since the compact format (2026-10-09), about 50px of "
        "Plex Mono. Verified at 360 and 390 with shoot.sh."
    ),
}


def _split_tracks(value: str) -> list[str]:
    """Top-level whitespace split, respecting parentheses."""
    out, depth, cur = [], 0, ""
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch.isspace() and depth == 0:
            if cur:
                out.append(cur)
                cur = ""
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def _track_count(value: str):
    """How many tracks this declares, or None if it sizes itself.

    `repeat(auto-fit, …)` and `repeat(auto-fill, …)` drop to one column on their
    own as the container narrows, which is exactly the collapse this test asks
    for -- so they are exempt by construction rather than by listing.
    """
    if re.search(r"repeat\(\s*auto-(?:fit|fill)", value):
        return None
    total = 0
    for track in _split_tracks(value):
        repeated = re.match(r"repeat\(\s*(\d+)\s*,", track)
        total += int(repeated.group(1)) if repeated else 1
    return total


def _grid_declarations():
    """(selector, value, inside_a_narrow_media_query, file, line) for each one."""
    found = []
    for path in sass_files():
        stack: list[str] = []
        narrow_at: list[int] = []
        for i, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            code = raw.split("//")[0]
            declared = re.search(r"grid-template-columns:\s*([^;]+);", code)
            if declared:
                # A rule written entirely on one line (`.x { grid-…; }`) names
                # its own selector left of the brace; otherwise the open block
                # on the stack does.
                inline = re.match(r"\s*([^{};]+?)\s*\{", code)
                selector = inline.group(1) if inline else (stack[-1] if stack else "?")
                found.append(
                    (selector, declared.group(1).strip(), bool(narrow_at), path.name, i)
                )
            for _ in range(code.count("{")):
                head = code.split("{")[0].strip()
                if head.startswith("@media") and "max-width" in head:
                    narrow_at.append(len(stack))
                stack.append(head)
            for _ in range(code.count("}")):
                if stack:
                    stack.pop()
                if narrow_at and narrow_at[-1] >= len(stack):
                    narrow_at.pop()
    return found


def test_a_multi_track_row_can_become_one():
    """Every grid row of 2+ tracks collapses on a narrow screen, or says why not.

    Issue #468. Overflow is a property of the row: tracks that each pass
    `test_no_element_can_force_horizontal_scroll` can overflow side by side.
    A collapse is asked for, not arithmetic, because a `1fr` track's floor is
    its content's min-content width. `repeat(auto-fit, …)` and
    `repeat(auto-fill, …)` collapse on their own and are exempt.
    """
    declarations = _grid_declarations()
    assert declarations, (
        "No grid-template-columns declarations found under _sass/. Either the "
        "scan went stale or the selector-stack walk is broken -- and a scan that "
        "matches nothing passes while checking nothing (MANUAL 12)."
    )

    collapses = {sel for sel, _v, in_narrow, _f, _l in declarations if in_narrow}
    assert collapses, (
        "No grid row anywhere restates grid-template-columns inside a "
        "`@media (max-width: …)` block. Three do (.drink-searches, .search-pair, "
        ".site-footer-top), so finding none means this walk stopped recognising "
        "media queries and every row below would pass vacuously."
    )

    offenders = []
    for selector, value, in_narrow, fname, line in declarations:
        if in_narrow or selector in collapses:
            continue
        count = _track_count(value)
        if count is None or count < 2:
            continue
        if selector in MULTI_TRACK_ROWS_WITHOUT_A_NARROW_VARIANT:
            continue
        offenders.append(f"{fname}:{line} {selector} -- {value} ({count} tracks)")

    assert not offenders, (
        "Grid row(s) of two or more tracks with no narrow-screen variant:\n  "
        + "\n  ".join(sorted(offenders))
        + "\n\nA `1fr` track will not shrink below its content's min-content "
          "width, so a row like this has a floor nothing in this repo can "
          "compute -- which is how the footer overflowed a phone in issue #468 "
          "with every element in it under 320px. Restate "
          "`grid-template-columns: 1fr` for this selector inside a "
          "`@media (max-width: 600px)` block, or add it to "
          "MULTI_TRACK_ROWS_WITHOUT_A_NARROW_VARIANT with the claim you are "
          "making about its content."
    )

    stale = sorted(set(MULTI_TRACK_ROWS_WITHOUT_A_NARROW_VARIANT) & collapses)
    assert not stale, (
        "Registered as having no narrow-screen variant, and now has one:\n  "
        + "\n  ".join(stale)
        + "\n\nDelete the entry. A registry that keeps naming rows somebody has "
          "already fixed stops being a list of open questions and becomes "
          "furniture -- the same reason methods.yml's proposals are checked "
          "against the live collection."
    )


def test_no_decoration_slot_is_orphaned():
    """Every empty aria-hidden slot in a template is filled by some script.

    A slot whose injector was deleted stays in the markup drawing nothing and
    looking load-bearing. Slots come from the markup and injectors from the
    scripts, so a new slot is covered. The reverse is not checked: scripts
    query classes they create themselves.
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

    # An empty span/div with a class and aria-hidden="true" is the
    # decoration-slot idiom. `[^>]*` spans newlines, so attributes split
    # across lines still match.
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


# --- the publication gate (#331, #667) ---------------------------------------
# A page publishes only with `meta.awaiting_fix: false` and `meta.proofread:
# true`; _plugins/publish_gate.rb removes anything else at :post_read. Every
# way of breaking the gate fails open with a green build: a deleted plugin, a
# flipped config key, a build that ignores plugins. DECISIONS §4.0.

PLUGIN = ROOT / "_plugins" / "publish_gate.rb"


def test_awaiting_fix_plugin_exists_and_checks_the_flag():
    """The gate's implementation is present and still reads both flags."""
    assert PLUGIN.is_file(), (
        f"{PLUGIN.relative_to(ROOT)} is missing. Without it every recipe "
        f"flagged `meta.awaiting_fix: true`, and every unproofread one, "
        f"publishes normally -- silently, because nothing else in the build "
        f"looks at those fields."
    )
    src = PLUGIN.read_text(encoding="utf-8")
    for needle in ("awaiting_fix", "proofread", "show_awaiting_fix", "post_read"):
        assert needle in src, (
            f"{PLUGIN.name} no longer mentions {needle!r}. The gate is either "
            f"reading a different field or hooking a different phase, and it "
            f"fails open either way."
        )
    # Both legs must be compared, not merely mentioned in a comment.
    for needle in ('meta["awaiting_fix"] == false', 'meta["proofread"] == true'):
        assert needle in src, (
            f"{PLUGIN.name} no longer contains `{needle}`. The gate publishes "
            f"only on an explicit pass on BOTH flags (#667); a missing leg "
            f"fails open for every page that leg was holding back."
        )


def test_production_config_hides_awaiting_fix_and_local_shows_it():
    """The two configs must disagree, and in the right direction.

    Production hides flagged pages; local shows them, because locally they are
    the pages being worked on. Setting `show_awaiting_fix: true` in _config.yml
    would disable the gate everywhere while looking like a deliberate choice.
    """
    prod = yaml.safe_load((ROOT / "_config.yml").read_text(encoding="utf-8"))
    local = yaml.safe_load((ROOT / "_config_local.yml").read_text(encoding="utf-8"))
    assert prod.get("show_awaiting_fix") is False, (
        "_config.yml must set `show_awaiting_fix: false`. Production is the "
        "build that must not carry a page you have flagged as wrong; anything "
        "other than an explicit false (including the key being absent, which "
        "reads as nil and happens to work) leaves the gate undeclared."
    )
    assert local.get("show_awaiting_fix") is True, (
        "_config_local.yml must set `show_awaiting_fix: true`. Hiding flagged "
        "recipes locally hides the very pages you are trying to fix."
    )


def test_deploy_workflow_still_runs_a_plugin_capable_build():
    """`bundle exec jekyll build`, never a Pages-native safe-mode build.

    Safe mode ignores _plugins/ without warning, so the gate never runs and
    every flagged recipe publishes from an unchanged, correct repository.
    """
    wf = ROOT / ".github" / "workflows" / "build-and-deploy.yml"
    assert wf.is_file(), f"{wf.relative_to(ROOT)} is missing."
    src = wf.read_text(encoding="utf-8")
    assert "bundle exec jekyll build" in src, (
        "The deploy workflow no longer runs `bundle exec jekyll build`. If it "
        "has moved to a Pages-native build, _plugins/ is silently ignored and "
        "the awaiting_fix gate fails open -- flagged recipes publish with a "
        "completely green build. Keep a full build, or replace the gate."
    )
    assert "--safe" not in src, (
        "The deploy workflow passes --safe, which disables _plugins/ and so "
        "disables the awaiting_fix gate. Remove it, or replace the gate."
    )


def _needs(job) -> list[str]:
    needs = (job or {}).get("needs")
    return [needs] if isinstance(needs, str) else list(needs or [])


# Any of these in a job's `if` replaces the implicit success() check, so the
# job runs even when a job it needs FAILED. `!cancelled()` contains
# `cancelled()`, so it needs no entry of its own.
_STATUS_FUNCTIONS = ("always()", "failure()", "cancelled()")


def _why_a_red_suite_could_deploy(jobs) -> str | None:
    """None if `deploy` can only run after `test` succeeded; else the reason.

    #1271. `test` must be among the jobs `deploy` needs, directly or through
    another job, and no job on that route may have an `if` calling a status
    function: that replaces the implicit success(), so the job runs after a
    failed need.
    """
    if "deploy" not in jobs:
        return "The deploy workflow has no `deploy` job, so this gate is unread."

    # Every chain of `needs` from `deploy` that reaches `test`.
    def chains(name, seen):
        if name == "test":
            return [[name]]
        return [[name] + rest
                for parent in _needs(jobs.get(name)) if parent not in seen
                for rest in chains(parent, seen | {name})]

    routes = chains("deploy", frozenset())
    if not routes:
        return (
            "Nothing `deploy` needs leads back to the `test` job. Without that "
            "the jobs run side by side and a failing suite deploys anyway -- "
            "the test job becomes a report nobody is gated on. `deploy` must "
            "declare `needs: test`, or need a job that does."
        )
    for route in routes:
        for name in route[:-1]:
            condition = str(jobs[name].get("if", ""))
            for fn in _STATUS_FUNCTIONS:
                if fn in condition:
                    return (
                        f"The `{name}` job's `if` calls {fn}, which replaces "
                        "the implicit success() check: it runs even when a job "
                        "it needs has FAILED, so a red suite deploys with "
                        "`needs` intact. Drop the status function."
                    )
    return None


def test_the_deploy_gate_check_refuses_every_way_round_it():
    """The check above is only worth having if the broken shapes fail it."""
    def job(needs=None, cond=None):
        out = {}
        if needs is not None:
            out["needs"] = needs
        if cond is not None:
            out["if"] = cond
        return out

    pr = "github.event_name != 'pull_request'"
    ok = [
        # build waits for test, deploy waits for build
        {"test": job(), "build": job("test", pr), "deploy": job("build", pr)},
        # side by side, and deploy waits for both (#1271)
        {"test": job(), "build": job(cond=pr), "deploy": job(["test", "build"], pr)},
    ]
    broken = [
        # side by side with nothing gating on test
        {"test": job(), "build": job(), "deploy": job("build")},
        {"test": job(), "build": job()},
        # `needs` intact, and a status function that ignores it
        {"test": job(), "build": job(), "deploy": job(["test", "build"], "always()")},
        {"test": job(), "build": job(), "deploy": job(["test", "build"], f"!cancelled() && {pr}")},
        {"test": job(), "build": job("test", "failure() || success()"), "deploy": job("build")},
    ]
    for jobs in ok:
        assert _why_a_red_suite_could_deploy(jobs) is None, jobs
    for jobs in broken:
        assert _why_a_red_suite_could_deploy(jobs) is not None, (
            f"this workflow shape can deploy a red suite and was accepted: {jobs}"
        )


def test_the_deploy_workflow_runs_the_tests_and_gates_on_them():
    """CI runs the suite and cannot deploy while it is red (#369).

    Pinned: a `test` job exists; `deploy` cannot run unless it succeeded
    (`_why_a_red_suite_could_deploy`); `fetch-depth: 0`, or #367's
    history-reading test examines nothing in a shallow clone; and the JS suite
    is invoked with a glob, because `node --test tests/js/` treats the
    directory as one test file.
    """
    wf = ROOT / ".github" / "workflows" / "build-and-deploy.yml"
    src = wf.read_text(encoding="utf-8")
    cfg = yaml.safe_load(src)
    jobs = cfg.get("jobs") or {}

    assert "test" in jobs, (
        "The deploy workflow has no `test` job. Without one, nothing stops a "
        "red suite from deploying -- which was the state this repository was "
        "in until 2026-08-18 (#369)."
    )
    problem = _why_a_red_suite_could_deploy(jobs)
    assert problem is None, problem
    steps = jobs["test"].get("steps") or []
    checkout = [s for s in steps if "actions/checkout" in str(s.get("uses", ""))]
    assert checkout, "The test job never checks the repository out."
    assert checkout[0].get("with", {}).get("fetch-depth") == 0, (
        "The test job's checkout is shallow. actions/checkout defaults to "
        "depth 1, and `git log -- <file>` in a depth-1 clone reports the same "
        "single commit for every file, so test_agent_edited_recipes_are_not_"
        "marked_proofread (#367) would examine nothing and pass. Set "
        "`fetch-depth: 0`."
    )
    assert "python3 -m pytest" in src, "The test job never runs pytest."
    assert "node --test tests/js/*.test.js" in src, (
        "The JS suite must be invoked with the glob. `node --test tests/js/` "
        "treats the directory as a single test file and reports 'tests 1, "
        "fail 1' without running any of the tests inside it."
    )


# --- the shared chrome's own artwork (#374) -----------------------------------

def test_tape_count_matches_the_tape_directory():
    """_data/chrome.yml's tape_count equals the files in assets/img/chrome/tape/.

    A browser cannot list a directory, so decorations.js picks from 1 to the
    count. Too high, and some page loads render no tape; too low, and the
    extra files are never dealt. Neither errors.
    """
    chrome = yaml.safe_load((ROOT / "_data" / "chrome.yml").read_text(encoding="utf-8")) or {}
    declared = chrome.get("tape_count")
    assert isinstance(declared, int) and declared > 0, (
        f"_data/chrome.yml declares tape_count = {declared!r}. It must be a "
        f"positive integer: assets/js/decorations.js parses it off the .tape-bg "
        f"slot and picks a file from 1 to N."
    )

    tape_dir = ROOT / "assets" / "img" / "chrome" / "tape"
    # Sorted by the number, not the name: a lexical sort puts tape-10 before
    # tape-2 and reports a gapless run as broken.
    actual = sorted(tape_dir.glob("tape-*.svg"),
                    key=lambda p: int(p.stem.split("-", 1)[1]))
    assert len(actual) == declared, (
        f"_data/chrome.yml says tape_count: {declared}, but "
        f"assets/img/chrome/tape/ holds {len(actual)} tape-*.svg files "
        f"({[p.name for p in actual]}).\n"
        f"Update the count, or add/remove the file. scripts/generate_tape.py "
        f"makes new ones -- see its docstring, and MANUAL 13.9 for how the "
        f"shipped set was chosen."
    )

    # Named tape-1 .. tape-N with no gaps: decorations.js rolls a number in
    # that range, so a gap satisfies the count above and is an intermittent 404.
    expected = [f"tape-{n}.svg" for n in range(1, declared + 1)]
    assert [p.name for p in actual] == expected, (
        f"assets/img/chrome/tape/ is not a gapless tape-1..tape-{declared} run: "
        f"{[p.name for p in actual]}.\n"
        f"decorations.js picks a random n in that range and builds the filename "
        f"from it, so a gap is an intermittent 404 rather than an error."
    )


def test_no_site_holds_a_copy_of_the_chrome_artwork():
    """The header and footer artwork exists in exactly one place (#374).

    Fails if a site's image directory holds a file named the same as one in
    assets/img/chrome/. By filename, not directory name: a second file with
    the same name is what two directories can disagree about.
    """
    chrome_dir = ROOT / "assets" / "img" / "chrome"
    chrome_names = {p.name for p in chrome_dir.rglob("*.svg")}
    assert chrome_names, (
        f"No SVGs under {chrome_dir.relative_to(ROOT)} -- either the shared "
        f"chrome artwork moved again or this path is stale, and either way "
        f"there is nothing here to compare against, which passes."
    )

    duplicates = []
    for owner in PALETTE_OWNERS:
        for path in (ROOT / "assets" / "img" / owner).rglob("*.svg"):
            if path.name in chrome_names:
                duplicates.append(str(path.relative_to(ROOT)))
    assert not duplicates, (
        "A site's image directory holds a file named the same as one in the "
        "shared chrome set:\n  " + "\n  ".join(sorted(duplicates))
        + "\n\nThe header and the footer are one artefact for the whole repo "
          "(issue #374), so their artwork lives once in assets/img/chrome/ and "
          "is fetched with HTF.chromeAsset. A per-site copy is a second header "
          "or a second footer arriving one file at a time, and the copy that "
          "nobody looks at is the one that goes stale."
    )


def test_both_indexes_filter_chips_wear_the_shared_tape():
    """Both indexes' filter chips wear the shared tape (#1219).

    The tape is a `.tag-shape` slot filled by decorations.js's tagShapes().
    Three things fail without a console message: a chip with no slot, a chip
    class missing from tagShapes()'s host list, and a shape with no file in
    the shared folder.
    """
    cocktails = (ROOT / "cocktails" / "index.html").read_text(encoding="utf-8")
    chips = re.findall(r'<button type="button" class="btn-(?:chaos|mood)"[^>]*>(.*?)</button>', cocktails)
    assert chips, "cocktails/index.html emits no .btn-chaos or .btn-mood buttons."
    bare = [c for c in chips if not c.startswith('<span class="tag-shape" aria-hidden="true"></span>')]
    assert not bare, f"Cocktail filter chips with no .tag-shape slot: {bare}"

    group = (ROOT / "_includes" / "filter_group.html").read_text(encoding="utf-8")
    assert '<span class="tag-shape" aria-hidden="true"></span>{{ item }}' in group, (
        "_includes/filter_group.html no longer puts a .tag-shape slot in food's chips.")

    decorations = (JS_DIR / "decorations.js").read_text(encoding="utf-8")
    hosts = re.search(r"slot\.closest\('(\.badge, [^']+)'\)", decorations)
    assert hosts, "decorations.js's tagShapes() no longer finds a slot's host with closest()."
    for cls in (".btn-tag", ".btn-star", ".btn-chaos", ".btn-mood", ".btn-pool"):
        assert cls in hosts.group(1).split(", "), (
            f"{cls} is not in tagShapes()'s host list, so its slots are skipped.")
    assert "HTF.chromeAsset('/tag-shapes/' + shape + '.svg')" in decorations, (
        "tagShapes() must fetch from the shared set: siteAsset() would look in "
        "assets/img/cocktails/, which holds no shapes.")

    pool = re.search(r"var POOL = \[(.*?)\];", decorations, re.S)
    assert pool, "decorations.js's tagShapes() no longer declares POOL."
    shapes = re.findall(r"'(tag-shape-[^']+)'", pool.group(1))
    missing = [s for s in shapes
               if not (ROOT / "assets" / "img" / "chrome" / "tag-shapes" / f"{s}.svg").is_file()]
    assert shapes and not missing, f"Shapes in POOL with no file in assets/img/chrome/tag-shapes/: {missing}"

    # Helen's picks (#1369) bypass the hash, so nothing at run time notices a
    # typo in a shape (a missing file) or a key no chip says (a pick that
    # silently stops applying when a tag is renamed).
    chosen_block = re.search(r"var CHOSEN = \{(.*?)\};", decorations, re.S)
    assert chosen_block, "decorations.js's tagShapes() no longer declares CHOSEN."
    chosen = dict(re.findall(r"'([^']+)':\s*'([^']+)'", chosen_block.group(1)))
    assert chosen, "CHOSEN declares no picks, or its entries are not 'text': 'shape'."
    stray = {k: v for k, v in chosen.items() if v not in shapes}
    assert not stray, f"CHOSEN names a shape that is not in POOL: {stray}"
    chip_texts = {re.sub(r"<[^>]+>", "", c).replace("&rsquo;", "’").strip().lower()
                  for c in chips}
    moods = yaml.safe_load((ROOT / "_data" / "cocktails" / "taxonomy.yml").read_text(encoding="utf-8"))
    chip_texts |= {str(m).lower() for m in (moods.get("moods") or {})}
    unknown = [k for k in chosen if k not in chip_texts]
    assert not unknown, f"CHOSEN keys that no filter chip says: {unknown}"
    named = re.findall(r'data-tag-shape="([^"]*)"', cocktails + group
                       + (ROOT / "food" / "index.html").read_text(encoding="utf-8"))
    stray_attr = [n for n in named if n not in shapes]
    assert not stray_attr, f"data-tag-shape names a shape that is not in POOL: {stray_attr}"

    for entry in ("food.scss", "cocktails.scss"):
        assert '@use "shared/tag-shape";' in (ROOT / "assets" / "css" / entry).read_text(encoding="utf-8"), (
            f"assets/css/{entry} does not load the tape slot.")


# --- the cocktail index (#579) ------------------------------------------------
# The food index's guards are scoped to `filters.js` by name and do not reach
# cocktails. These are the same guards, aimed at the other page.

def _strip_js_comments(js: str) -> str:
    """Source with comments removed.

    A guard that counts a token in raw source is defeated by a comment naming
    that token.
    """
    return re.sub(r"//.*$", " ", re.sub(r"/\*.*?\*/", " ", js, flags=re.S), flags=re.M)


def test_cocktail_index_js_holds_no_loose_filter_state_variables():
    """The drinks index's filter state lives in filter-state.js, like food's.

    Issue #579. Loose state variables let clear-all empty one set of fields
    while its visibility predicate checks another (#52). Declarations only:
    the names are ordinary English and may appear elsewhere.
    """
    js = _strip_js_comments(read("assets", "js", "cocktail-index.js"))
    for name in ("chosenMoods", "chosenChaos", "wantName", "include", "exclude", "vocabulary"):
        assert not re.search(rf"\bvar\s+{name}\b", js), (
            f"assets/js/cocktail-index.js declares `var {name}`. The drinks "
            f"index's filter state belongs in COCKTAIL_FIELDS in "
            f"assets/js/filter-state.js, where emptyState() and "
            f"hasAnythingToClear() both pick it up at once and "
            f"tests/js/filter-state.test.js generates a case for it."
        )

    assert "HTF.filterState.create(HTF.filterState.COCKTAIL_FIELDS)" in js, (
        "assets/js/cocktail-index.js no longer builds its state from "
        "HTF.filterState. clearAll() must replace the whole state object rather "
        "than empty it field by field, or the clear-all button's predicate can "
        "drift from what it clears -- issue #52's bug, on the other index."
    )


def test_the_cocktail_index_never_matches_an_ingredient_by_substring():
    """Fuzzy to find, exact to filter: the wiring calls cocktail-search.js's rules.

    A substring test over the joined data-ingredients attribute cannot tell
    `gin` from `ginger` and can match across the `|` between two ingredients.
    Checked as "the wiring does not roll its own", not as "`indexOf` never
    appears": it legitimately does, on lists of chips and DOM children.
    """
    js = _strip_js_comments(read("assets", "js", "cocktail-index.js"))

    for fn in ("matchesInclude", "matchesExclude", "matchesName", "entryIsHit"):
        assert f"Search.{fn}(" in js, (
            f"assets/js/cocktail-index.js no longer calls Search.{fn}(). The "
            f"matching rules belong in assets/js/cocktail-search.js, covered by "
            f"tests/js/cocktail-search.test.js -- a rule spelled out here can "
            f"only be checked by opening a browser and typing."
        )

    offenders = re.findall(r"dataset\.ingredients[^;\n]*indexOf", js)
    assert not offenders, (
        "assets/js/cocktail-index.js probes a card's data-ingredients attribute "
        "with indexOf. That is the substring rule this page was fixed of: it "
        "cannot tell `gin` from `ginger`, and it can match across the `|` "
        "between two ingredients. Split the attribute with "
        "HTF.cocktailSearch.splitEntries and ask Search.matchesInclude / "
        "matchesExclude, which are tested.\n  " + "\n  ".join(offenders)
    )


def test_the_cocktail_search_thresholds_are_not_hardcoded():
    """The search thresholds live in the vocabulary, not in the algorithm.

    How much typing earns a pool of candidates is a question about the
    vocabulary, so the answer is a one-line edit to a YAML file (#549).
    """
    path = ROOT / "_data" / "cocktails" / "ingredients.yml"
    vocab = yaml.safe_load(path.read_text(encoding="utf-8"))
    search = vocab.get("search")
    assert isinstance(search, dict), (
        "_data/cocktails/ingredients.yml has no `search:` block. It carries the "
        "drinks index's minimum query length and family-button threshold "
        "(there was a pool cap too, until 2026-10-11); without it "
        "cocktail-search.js falls back to defaults and the "
        "numbers stop being editable."
    )
    for key in ("min_query_chars", "family_button_min_chars"):
        assert isinstance(search.get(key), int), (
            f"_data/cocktails/ingredients.yml's `search:` block is missing an "
            f"integer `{key}`."
        )

    js = _strip_js_comments(read("assets", "js", "cocktail-search.js"))
    for key in ("min_query_chars", "family_button_min_chars"):
        assert re.search(rf"cfg\.{key}\b", js), (
            f"assets/js/cocktail-search.js no longer reads `{key}` from the "
            f"vocabulary it was handed."
        )
    # A literal beside the name, in either case or as an `||` fallback, is the
    # shape of a value that has crept back in.
    for bad in re.findall(r"(min_query_chars|family_button_min_chars)\s*(?:[:=]|\|\|)\s*\d",
                          js, re.I):
        raise AssertionError(
            f"assets/js/cocktail-search.js assigns `{bad}` a number of its own. "
            f"The value belongs in _data/cocktails/ingredients.yml."
        )


def test_the_cocktail_vocabulary_is_emitted_to_the_page():
    """cocktail-search.js can only read the families and the bottles if the
    template emits them, ahead of its script tag (#579).
    """
    html = read("cocktails", "index.html")
    assert 'id="drink-vocabulary"' in html, (
        "cocktails/index.html no longer emits an id=\"drink-vocabulary\" block. "
        "Without it cocktail-search.js falls back to no declared families, so "
        "the (all) buttons vanish and `rum` -- which no drink lists literally -- "
        "becomes unfilterable."
    )
    assert "site.data.cocktails.ingredients | jsonify" in html, (
        "the drink-vocabulary block no longer emits "
        "_data/cocktails/ingredients.yml. Emitting a hand-picked subset means a "
        "key added to the YAML needs this template touched, which is exactly "
        "the coupling #501 values card_names for not having."
    )

    assert 'id="drink-bottles"' in html, (
        "cocktails/index.html no longer emits an id=\"drink-bottles\" block. The "
        "search reads _data/cocktails/bottles.yml for two of Helen's rules: a "
        "bottle keeps ONE identity through its aliases (`wray and nephew` and "
        "`wray & nephew` collapse onto the latter), and the ten strings that "
        "file declares `unresolved_suggestions` are not offered as chips at all."
    )
    assert "site.data.cocktails.bottles | jsonify" in html, (
        "the drink-bottles block no longer emits _data/cocktails/bottles.yml."
    )

    script_at = html.index("assets/js/cocktail-search.js")
    for block in ("drink-vocabulary", "drink-bottles"):
        assert html.index('id="%s"' % block) < script_at, (
            f"The {block} block must appear BEFORE the cocktail-search.js script "
            f"tag, or the JSON is not in the DOM when the module is created."
        )


def test_the_cocktail_index_scripts_load_in_dependency_order():
    """The drinks index's scripts load in dependency order.

    Each reads its dependency at startup, not on first use: cocktail-index.js
    reads HTF.cocktailSearch, HTF.filterState and HTF.shoppingList (to fold
    bottle aliases) as it runs, and cocktail-search.js reads
    HTF.ingredientSearch as it loads.
    """
    html = read("cocktails", "index.html")
    needs = [("ingredient-search.js", "cocktail-search.js"),
             ("filter-state.js", "cocktail-index.js"),
             ("cocktail-search.js", "cocktail-index.js"),
             ("shopping-list.js", "cocktail-index.js")]
    positions = {}
    for name in {n for pair in needs for n in pair}:
        tag = re.search(rf"""<script src=["']?\{{\{{ '/assets/js/{re.escape(name)}'""", html)
        assert tag, f"cocktails/index.html no longer loads assets/js/{name}."
        positions[name] = tag.start()

    for earlier, later in needs:
        assert positions[earlier] < positions[later], (
            f"{earlier} must load BEFORE {later} on cocktails/index.html, or the "
            f"namespace it provides will not exist yet when {later} runs."
        )


def test_the_cocktail_card_ingredient_attribute_is_self_delimiting():
    """`data-ing` is `|`-separated, like every other ingredient attribute here.

    A comma is the commonest character in the values, and a space-separated
    attribute cannot be split back into ingredients. The join and the
    downcasing live in _plugins/cocktail_card_ingredients.rb (#567, #691);
    the template only prints what it is handed.
    """
    html = read("cocktails", "index.html")
    tag = re.search(r'data-ing="\{\{[^"]*"', html)
    assert tag, "cocktails/index.html no longer writes a data-ing attribute."
    assert "ing.search" in tag.group(0), (
        "data-ing no longer emits the plugin's `search` value unchanged. It must "
        "keep its `|` separators: assets/js/cocktail-index.js splits it with "
        "HTF.cocktailSearch.splitEntries so a matched ingredient is found by "
        "the same rule the filter used."
    )

    plugin = ROOT / "_plugins" / "cocktail_card_ingredients.rb"
    assert plugin.exists(), (
        "_plugins/cocktail_card_ingredients.rb is gone, and it is what builds "
        "the `search` value data-ing prints."
    )
    source = plugin.read_text(encoding="utf-8")
    join = re.search(r"def search_key.*?\n  end\n", source, re.S)
    assert join, "the plugin's search_key method is gone or renamed."
    assert '.join("|")' in join.group(0), (
        "search_key no longer joins its values with `|`, so splitEntries cannot "
        "recover the individual ingredients from data-ing."
    )
    assert ".downcase" in join.group(0), (
        "search_key no longer downcases. The template stopped applying "
        "`| downcase` when the join moved here, so this is the only place it "
        "happens -- and cocktail-index.js compares against lowercased chips."
    )


# --- a binding is only asked for what it has ---------------------------------
#
# filter-state.js exports two shapes: `HTF.filterState`, the module, and
# `HTF.filterState.create(SPEC)`, a binding of spec-bound functions and nothing
# else. A name taken off the wrong one is `undefined`, and calling it throws at
# startup. The JS suite asks pure modules questions and cannot see the wiring
# between them; this checks the call sites.


def _js_object_keys(source: str, opener: str) -> set[str]:
    """The keys of the object literal that starts at `opener`, one brace deep.

    Deliberately shallow -- it reads the top level of one literal and stops at
    its closing brace, so a nested object cannot leak its own keys in.
    """
    start = source.index(opener) + len(opener)
    depth = 1
    keys, i = set(), start
    while depth and i < len(source):
        ch = source[i]
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif depth == 1:
            match = re.match(r"\s*([A-Za-z_$][\w$]*)\s*:", source[i:])
            if match:
                keys.add(match.group(1))
        i += 1
    return keys


def test_a_filter_state_binding_is_only_asked_for_what_it_has():
    """Every `X.name` on a filter-state object is a name that object has.

    The fix is usually one word: a spec-bound name comes off the binding
    `create()` returns, a spec-free one off the module.
    """
    fs_source = read("assets", "js", "filter-state.js")
    module_keys = _js_object_keys(fs_source, "var api = {")
    binding_keys = _js_object_keys(fs_source, "return {\n      FIELDS:")

    assert "create" in module_keys and "arrivedByGoingBack" in module_keys, (
        "the module's export block is not where this test thinks it is; "
        "`var api = {` no longer starts it."
    )
    assert "emptyState" in binding_keys and "serialise" in binding_keys, (
        "create()'s return block is not where this test thinks it is."
    )

    # Which shape each consumer holds, read from how it assigns the variable
    # rather than assumed -- if one of them switches, this switches with it.
    consumers = {
        "filters.js": ("var FilterState = HTF.filterState;", module_keys),
        "cocktail-index.js": (
            "var FilterState = HTF.filterState.create(", binding_keys),
    }

    problems = []
    for filename, (assignment, available) in consumers.items():
        raw = read("assets", "js", filename)
        assert assignment in raw, (
            f"{filename} no longer binds FilterState as `{assignment}`, so this "
            f"test is checking its names against the wrong shape. Update the "
            f"table above rather than deleting the case."
        )
        # Comments stripped first, so a name mentioned in prose is not read as
        # a call. `_strip_comments` keeps strings, because a string is how a
        # name gets read (MANUAL §12).
        source = _strip_comments(raw, ".js")
        for name in sorted(set(re.findall(r"\bFilterState\.([A-Za-z_$][\w$]*)", source))):
            if name not in available:
                where = "the binding create() returns" if available is binding_keys \
                    else "the filterState module"
                other = module_keys if available is binding_keys else binding_keys
                hint = " It IS on the other one -- take it off that instead." \
                    if name in other else ""
                problems.append(
                    f"{filename} calls FilterState.{name}, which is not on "
                    f"{where}.{hint}"
                )

    assert not problems, (
        "A filter-state name is read off an object that does not have it, which "
        "is `undefined` at runtime and throws when called:\n  "
        + "\n  ".join(problems)
    )


# --- duplicate YAML keys (#609) ----------------------------------------------
#
# A duplicate key in a YAML mapping is not an error: the parser keeps the last
# and discards the first in silence, which can replace a documented decision
# with a generated placeholder. Front matter is scanned as well as _data/.


class _DuplicateKeyLoader(yaml.SafeLoader):
    """A SafeLoader that collects repeated keys instead of resolving them, so
    one file reports all of its own with the key and the line."""


def _collect_duplicates(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            loader.duplicates.append((key, key_node.start_mark.line + 1))
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_DuplicateKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _collect_duplicates)


def _duplicate_keys(text: str):
    """Every (key, line) that appears twice in one mapping, at any depth."""
    loader = _DuplicateKeyLoader(text)
    loader.duplicates = []
    try:
        loader.get_single_data()
    except yaml.YAMLError:
        # A file that does not parse at all is another test's failure.
        return []
    finally:
        loader.dispose()
    return loader.duplicates


def _yaml_sources():
    """Every (label, path, text) the site reads as YAML: data files and front matter.

    The collections are globbed rather than listed, and absent ones are simply
    absent -- the two drafts directories are private repos that a CI checkout
    does not have.
    """
    sources = []
    for path in sorted(ROOT.glob("_data/**/*.yml")):
        sources.append((f"{path.relative_to(ROOT)}", path, path.read_text(encoding="utf-8")))

    for name in ("_food_recipes", "_food_magic_bag", "_food_drafts",
                 "_cocktail_recipes", "_cocktail_drafts"):
        for path in sorted((ROOT / name).rglob("*.md")) if (ROOT / name).exists() else []:
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue
            sources.append((f"{path.relative_to(ROOT)}", path, parts[1]))
    return sources


_YAML_SOURCES = _yaml_sources()


def test_the_duplicate_key_scan_actually_has_files_to_scan():
    """The duplicate-key corpus is a glob, and a stale glob scans nothing.

    An empty parametrisation reports as a skip. The two floors are what CI
    has: the data files and the published recipes. The drafts are private
    repos, absent there.
    """
    labels = [label for label, _, _ in _YAML_SOURCES]
    assert any(l.startswith("_data/") for l in labels), (
        "No _data/**/*.yml matched. Either the data directory moved or this "
        "glob went stale -- and a stale glob here means the duplicate-key check "
        "silently stopped checking, which is the failure mode it exists for."
    )
    assert any(l.startswith("_food_recipes/") for l in labels), (
        "No _food_recipes/*.md front matter matched, and those are in this "
        "repository, so they are present even in CI."
    )


@pytest.mark.parametrize(
    "label,text",
    [(label, text) for label, _, text in _YAML_SOURCES],
    ids=[label for label, _, _ in _YAML_SOURCES],
)
def test_no_yaml_mapping_has_a_duplicate_key(label, text):
    """No YAML mapping repeats a key: the earlier one is silently discarded.

    Issue #609. In CI this covers the data files and the published collections
    only; the drafts are private repos a CI checkout lacks. The fix is to
    delete one of the two after reading both, since they are not always the
    same text.
    """
    duplicates = _duplicate_keys(text)
    assert not duplicates, (
        f"{label} repeats {len(duplicates)} key(s) in one mapping:\n  "
        + "\n  ".join(f"line {line}: {key!r}" for key, line in duplicates)
        + "\n\nYAML keeps the LAST and discards the first, without complaint, so "
          "whatever the earlier one said is gone. Delete one -- after reading "
          "both, because the two are not always the same text."
    )


# --- a YOLO button that nothing handles (#732) --------------------------------
#
# Pressing a `.btn-chaos` is generic over `state.chaos`; the clause in
# `matches()` is not. A misspelled `data-chaos` value gives a button that
# presses in and filters nothing. Checked as source because `matches()` is
# inside cocktail-index.js's IIFE with no export (#633).

CHAOS_NO_OP = {
    # `open` is a state, not a filter: "I'm open to chaos" includes every
    # drink, so it has no clause on purpose.
    "open",
}


def test_every_yolo_button_value_is_handled_by_the_index_script():
    """Every `.btn-chaos` value is one `matches()` reads, or is in CHAOS_NO_OP.

    A value with no clause still presses in, highlights and clears, because
    those are generic over `state.chaos`, and it filters nothing.
    """
    html = read("cocktails", "index.html")
    script = (ROOT / "assets" / "js" / "cocktail-index.js").read_text(encoding="utf-8")

    values = set(re.findall(r'class="btn-chaos"[^>]*data-chaos="([^"]+)"', html))
    assert values, (
        "cocktails/index.html emits no .btn-chaos buttons. The YOLO section is "
        "gone or its markup has changed shape."
    )

    unhandled = sorted(
        v for v in values - CHAOS_NO_OP
        if f"'{v}'" not in script and f'"{v}"' not in script
    )
    assert not unhandled, (
        "These YOLO buttons emit a `data-chaos` value that "
        "assets/js/cocktail-index.js never names, so each one presses in, "
        "highlights, and filters nothing:\n  " + "\n  ".join(unhandled)
        + "\nAdd a clause in matches(), or add the value to CHAOS_NO_OP here "
        "with the reason it is deliberately inert."
    )


def test_the_card_s_chaos_stamp_comes_from_the_taxonomy_lists():
    """A card's `data-chaos` is read off taxonomy.yml's `chaos` lists (#1413).

    A literal list of rungs here would drift from the taxonomy in silence: a
    rung added to `chaos.good` would never reach `no chaos please`.
    """
    html = read("cocktails", "index.html")
    for name in ("good", "chaos"):
        assert f"taxonomy.chaos.{name} contains ship" in html, (
            f"cocktails/index.html no longer stamps `data-chaos` from "
            f"`taxonomy.chaos.{name}`."
        )


# --- the leopard on the cocktails page ground (#733) --------------------------

def test_the_leopard_picture_is_laid_at_the_fur_tile_s_own_size():
    """_leopard.scss lays the ground picture at the size the fur SVG says it is.

    `background-size` is written by hand. If the tile changes size and the
    stylesheet does not follow, the browser scales the print and nothing
    fails (LEOPARD.md). The tiles are not regenerated and compared here:
    rounded sines can differ by platform, and a red suite stops the deploy.
    """
    scss = (SASS_DIR / "cocktails" / "_leopard.scss").read_text(encoding="utf-8")
    declared = re.search(r"background-size:\s*(\d+)px (\d+)px;", scss)
    assert declared, (
        "_sass/cocktails/_leopard.scss no longer has a one-layer `background-size` "
        "in px. This test reads it to compare with the fur tile's own size; if "
        "the rule changed shape, change the pattern here with it."
    )
    want = [int(n) for n in declared.groups()]
    head = (ROOT / "assets" / "img" / "cocktails" / "leopard-fur.svg").read_text(encoding="utf-8")[:300]
    got = re.search(r'<svg[^>]* width="(\d+)" height="(\d+)"', head)
    assert got and [int(got.group(1)), int(got.group(2))] == want, (
        f"leopard-fur.svg is {got.groups() if got else 'of unknown size'} but "
        f"_leopard.scss lays the picture at {want[0]}px by {want[1]}px. The "
        f"browser will scale the print to fit and nothing will look broken -- "
        f"only wrong-sized. Make `background-size` say the file's own size."
    )


def test_the_leopard_files_the_stylesheet_declares_exist_and_are_never_loaded_by_it():
    """The stylesheet names the two SVGs for ground-print.js and never loads them.

    A name with no file is a 404 the build never makes, and the page has a
    plain ground. A `url()` to the SVG is redrawn for every strip of page
    that scrolls into view, which judders.
    """
    scss = _strip_comments((SASS_DIR / "cocktails" / "_leopard.scss").read_text(encoding="utf-8"), ".scss")
    img = ROOT / "assets" / "img" / "cocktails"
    for prop in ("--ground-print", "--ground-nap"):
        named = re.search(re.escape(prop) + r':\s*"(/[^"]+\.svg)";', scss)
        assert named, (
            f"_sass/cocktails/_leopard.scss does not declare `{prop}` as a quoted "
            f"path under the site's artwork directory. assets/js/ground-print.js "
            f"reads it; without it there is no print (or no nap) and no error."
        )
        assert (img / named.group(1).lstrip("/")).exists(), (
            f"_leopard.scss declares {prop}: \"{named.group(1)}\", and "
            f"assets/img/cocktails{named.group(1)} does not exist. "
            f"`python3 scripts/build_leopard.py --write` regenerates both tiles."
        )
    assert ".svg\")" not in scss and ".svg)" not in scss, (
        "_sass/cocktails/_leopard.scss loads an SVG with url(). The leopard must "
        "reach the page as the picture assets/js/ground-print.js draws once "
        "(`--ground-picture`): as a CSS background the SVG is redrawn on every "
        "scroll, which is the judder of 2026-10-06. See that script's header."
    )


def test_the_leopard_version_is_the_hash_of_the_committed_files():
    """_leopard-version.scss is the hash of the two SVGs as committed.

    A browser keeps the picture it drew under this version, so regenerated
    artwork with a stale version leaves returning visitors on the old leopard.
    `scripts/build_leopard.py --write` writes all three; committed bytes are
    hashed, so the result cannot differ by platform.
    """
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import build_leopard
    finally:
        sys.path.pop(0)
    img = ROOT / "assets" / "img" / "cocktails"
    files = {name: (img / name).read_text(encoding="utf-8")
             for name in ("leopard-fur.svg", "leopard-nap.svg")}
    want = build_leopard.version_scss(build_leopard.version_of(files))
    got = (SASS_DIR / "cocktails" / "_leopard-version.scss").read_text(encoding="utf-8")
    assert got == want, (
        "_sass/cocktails/_leopard-version.scss is not the hash of the two "
        "leopard SVGs as committed. Browsers that have already kept a picture "
        "will go on showing the old artwork. Run "
        "`python3 scripts/build_leopard.py --write` and commit all three files."
    )


def test_the_index_shopping_list_is_handed_the_by_eye_measures():
    """The by-eye measures reach the index's shopping list (#1297).

    food/index.html joins `half_step_measures` and `half_step_counts` onto
    the panel as `data-whole-measures`; filters.js reads the attribute and
    hands it to `build()` as `wholeMeasures`. Break a link and nothing
    errors: the list prints "1.17 handfuls".
    """
    index = read("food", "index.html")
    assert re.search(
        r'id="shopping-list"[^>]*data-whole-measures="\{\{\s*'
        r'site\.data\.food\.scaling\.half_step_measures\s*\|\s*concat:\s*'
        r'site\.data\.food\.scaling\.half_step_counts\s*\|\s*join:\s*\',\'',
        index), (
        "food/index.html no longer joins half_step_measures and "
        "half_step_counts onto #shopping-list as data-whole-measures."
    )
    filters = read("assets", "js", "filters.js")
    assert "getAttribute('data-whole-measures')" in filters, (
        "filters.js no longer reads data-whole-measures off the panel."
    )
    assert "wholeMeasures: WHOLE_MEASURES" in filters, (
        "filters.js reads the by-eye measures and does not hand them to "
        "HTF.foodShoppingList.build(), so no total is rounded."
    )


def test_the_whole_fruit_vocabulary_is_the_shape_the_plugin_reads():
    """`whole_fruit:` in _data/food/scaling.yml has the shape
    _plugins/food_shopping.rb reads (#1297).

    It lets "zest of 1 lemon" and "juice of 1 lemon" total as one lemon. With
    `fruits` or `parts` missing the plugin marks nothing and the list
    silently stops combining.
    """
    vocab = yaml.safe_load(read("_data", "food", "scaling.yml")).get("whole_fruit")
    assert isinstance(vocab, dict), "_data/food/scaling.yml has no `whole_fruit:`."
    for key in ("fruits", "preparations", "sizes", "pointers"):
        words = vocab.get(key)
        assert words and all(isinstance(w, str) and w == w.lower() for w in words), (
            f"whole_fruit.{key} must be a list of lowercase strings; got {words!r}"
        )
    assert {"lemon", "lime", "orange"} <= set(vocab["fruits"])
    parts = vocab.get("parts")
    assert isinstance(parts, dict) and {"juice", "zest"} <= set(parts), (
        f"whole_fruit.parts must name at least juice and zest; got {parts!r}"
    )
    plural = [f for f in vocab["fruits"] if f.endswith("s")]
    assert not plural, (
        f"whole_fruit.fruits are singular -- the plugin adds the plural: {plural}"
    )


def test_the_index_shopping_list_is_handed_the_count_nouns():
    """`count_nouns` reaches the index's shopping list, and holds only nouns
    with a plain plural (#1297).

    The list is joined onto #shopping-list as `data-count-nouns`, read by
    filters.js and handed to build() as `countNouns`; break a link and the
    list says "2 lemon". `unitLabel` adds `s` or `es`, so a word whose plural
    is anything else must not be listed.
    """
    nouns = yaml.safe_load(read("_data", "food", "scaling.yml")).get("count_nouns")
    assert nouns and {"lemon", "onion", "egg"} <= set(nouns), (
        "_data/food/scaling.yml has no `count_nouns` list naming lemon, onion "
        "and egg."
    )
    not_plain = [n for n in nouns
                 if not isinstance(n, str) or not re.fullmatch(r"[a-z]+", n)]
    assert not not_plain, (
        f"count_nouns entries are one lowercase word each, singular: {not_plain}"
    )
    irregular = sorted(
        n for n in nouns
        if n.endswith(("y", "i", "f", "s"))
        or n in {"tomato", "potato", "mango", "goose", "fish", "thyme",
                 "butter", "garlic", "anise", "bread", "bacon"})
    assert not irregular, (
        f"these take no plain plural, or are not bought by count: {irregular}. "
        "The list is for words where adding an `s` is always right."
    )

    index = read("food", "index.html")
    assert re.search(
        r'id="shopping-list"[^>]*data-count-nouns="\{\{\s*'
        r'site\.data\.food\.scaling\.count_nouns\s*\|\s*join:\s*\',\'', index), (
        "food/index.html no longer joins site.data.food.scaling.count_nouns "
        "onto #shopping-list as data-count-nouns."
    )
    filters = read("assets", "js", "filters.js")
    assert "getAttribute('data-count-nouns')" in filters
    assert "countNouns: COUNT_NOUNS" in filters, (
        "filters.js reads the count nouns and does not hand them to build()."
    )
    assert 'class="shopping-list-note"' in index, (
        "food/index.html has lost the `(Not scaled: ...)` line's element; "
        "filters.js fills it and says nothing when it is missing."
    )


def test_the_quarter_step_measures_reach_both_scalers():
    """`quarter_step_measures` reaches the recipe page and the index's
    shopping list (#1297).

    food/index.html joins it onto the panel as `data-quarter-measures` and
    filters.js hands it to build(). Lose it and the page prints
    "1.17 sprigs" with nothing failing. The recipe page's route is checked by
    `test_the_recipe_scaler_is_handed_the_half_step_measures`.
    """
    scaling = yaml.safe_load(read("_data", "food", "scaling.yml"))
    quarter = scaling.get("quarter_step_measures")
    assert quarter and "sprig" in quarter, (
        "_data/food/scaling.yml has no `quarter_step_measures` naming `sprig`."
    )
    assert all(isinstance(m, str) and re.fullmatch(r"[a-z]+", m) for m in quarter), quarter
    both = sorted(set(quarter) & set(scaling["half_step_measures"]))
    assert not both, (
        f"{both} are in both step lists; the half-step rule would win and "
        "the quarter never apply."
    )
    counts = scaling.get("half_step_counts")
    assert counts == ["drop", "twist", "lot", "pat"], (
        "half_step_counts should be drop, twist, lot, pat -- Helen, "
        f"2026-10-10: 'please round to the nearest 1/2'. Got {counts!r}."
    )
    misplaced = sorted(set(counts) & (set(quarter) | set(scaling["half_step_measures"])))
    assert not misplaced, (
        f"{misplaced} must stay OUT of half_step_measures and "
        "quarter_step_measures. The half-recipe judge is handed "
        "half_step_measures and lets those halve always; '1 lot' of another "
        "recipe must go on refusing a half recipe ('Neither mince pies nor "
        "sweet cream base halve')."
    )
    # The judge's own list is the half-step measures plus `by_eye_also`. A
    # handful halves always; a sprig is a count and an odd one refuses.
    also = scaling["half_recipe"].get("by_eye_also")
    assert also == ["handful"], (
        f"half_recipe.by_eye_also should be just `handful`; got {also!r}. "
        "Without it an odd handful refuses a half recipe; with `sprig` in it "
        "an odd sprig stops refusing."
    )
    # The judge adds `by_eye_also` itself, so its two callers (the build and
    # scripts/food_yield.rb) cannot disagree about it.
    assert 'vocab["by_eye_also"]' in read("_plugins", "food_half_recipe.rb")
    plugin = read("_plugins", "food_shopping.rb")
    assert 'dig("food", "scaling", "half_step_measures")' in plugin
    assert "half_step_counts" not in plugin, (
        "_plugins/food_shopping.rb now hands half_step_counts to the "
        "half-recipe judge, which would let an odd count of pats or lots halve."
    )
    index = read("food", "index.html")
    assert re.search(
        r'data-quarter-measures="\{\{\s*site\.data\.food\.scaling\.'
        r'quarter_step_measures\s*\|\s*join:\s*\',\'', index), (
        "food/index.html no longer joins quarter_step_measures onto the panel."
    )
    filters = read("assets", "js", "filters.js")
    assert "getAttribute('data-quarter-measures')" in filters
    assert "quarterMeasures: QUARTER_MEASURES" in filters
