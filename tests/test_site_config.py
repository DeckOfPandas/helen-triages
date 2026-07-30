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
DATA = ROOT / "_data"


def read(*parts) -> str:
    return (ROOT.joinpath(*parts)).read_text(encoding="utf-8")


# --- the family-button threshold --------------------------------------------

def test_family_button_min_chars_is_three():
    """The value itself, asserted once, in the one place it lives."""
    path = DATA / "ingredient_words.yml"
    assert path.exists(), (
        "_data/ingredient_words.yml is missing. It holds the ingredient search "
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
    scratch and landed on 2. It now lives in _data/ingredient_words.yml and
    filters.js reads it by name. If a literal ever reappears, this fails.
    """
    js = read("js", "filters.js")
    literals = re.findall(r"query\.length\s*[<>]=?\s*\d+", js)
    assert not literals, (
        f"js/filters.js contains hardcoded query-length comparison(s): {literals}.\n"
        f"This threshold is defined in _data/ingredient_words.yml as "
        f"`search.family_button_min_chars` and read into FAMILY_BUTTON_MIN_CHARS. "
        f"Use that constant instead of a literal — the literal is exactly the "
        f"thing that kept resetting to 2."
    )
    assert "FAMILY_BUTTON_MIN_CHARS" in js, (
        "js/filters.js no longer references FAMILY_BUTTON_MIN_CHARS. The "
        "threshold should be read from the vocabulary, not inlined."
    )


def test_vocabulary_is_emitted_to_the_page():
    """filters.js can only read the vocabulary if index.html emits it."""
    html = read("index.html")
    assert 'id="ingredient-vocabulary"' in html, (
        'index.html no longer emits the <script type="application/json" '
        'id="ingredient-vocabulary"> block. Without it filters.js falls back to '
        "empty singulars and synonyms — ingredient search still works, but "
        '"cheese" stops returning cheddar and the collapse behaviour is lost.'
    )
    # Match the <script src> tag specifically — the word "filters.js" also
    # appears in a comment above the block, which would give a false failure.
    tag = re.search(r"<script src=[^>]*filters\.js", html)
    assert tag, "index.html no longer loads js/filters.js at all."
    assert html.index('id="ingredient-vocabulary"') < tag.start(), (
        "The ingredient-vocabulary block must appear BEFORE the filters.js "
        "script tag, or the script will run before the data exists."
    )


def test_filters_js_holds_no_ingredient_vocabulary():
    """Singulars and synonyms belong in YAML, not in the JavaScript."""
    js = read("js", "filters.js")
    for name in ("var singularMap = {", "var synonymMap = {"):
        assert name not in js, (
            f"js/filters.js declares `{name}...` inline. The ingredient "
            f"vocabulary lives in _data/ingredient_words.yml and is read from "
            f"the page; adding a word should be a YAML edit, not a code edit."
        )


# --- colour stays in one place ----------------------------------------------

TEMPLATES = ["index.html", "_layouts/recipe.html", "_layouts/default.html",
             "_includes/filter_group.html", "_includes/recipe_badges.html",
             "_includes/heading_with_highlighter.html"]


@pytest.mark.parametrize("relpath", TEMPLATES)
def test_no_inline_highlighter_fill(relpath):
    """Colour is set by class, in _sass/_palette.scss, and nowhere else.

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
        f"`.category--*` / `.search--*` rules in _sass/_palette.scss and makes "
        f"the palette look broken when you edit it. Add a class instead."
    )


@pytest.mark.parametrize("relpath", ["_data/colors.yml", "_data/recipe_sections.yml"])
def test_deleted_data_files_stay_deleted(relpath):
    """Both were removed in July 2026 and should not come back.

    colors.yml duplicated the palette; recipe_sections.yml was entirely dead —
    assigned in recipe.html and never used.
    """
    assert not (ROOT / relpath).exists(), (
        f"{relpath} has reappeared. Colour belongs in _sass/_palette.scss only; "
        f"section shape and texture are chosen in js/highlighter.js."
    )


def test_palette_is_the_only_place_hex_colours_are_written():
    """JS reads the palette from CSS custom properties rather than mirroring it."""
    js = read("js", "colours.js")
    assert "getPropertyValue" in js, (
        "js/colours.js is no longer reading colours from CSS custom properties. "
        "It should call getComputedStyle on :root and read --colour-* values "
        "defined in _sass/_palette.scss, not keep its own hardcoded copies."
    )


# --- the pantry list stays honest -------------------------------------------

def test_pantry_entries_are_actually_used():
    """Every pantry staple should appear somewhere in the collection.

    An entry that matches nothing is either a typo or a leftover, and either way
    it is dead weight in a list whose whole job is to be short and deliberate.
    Matching is exact and lowercase, exactly as index.html does it.
    """
    from conftest import ALL_RECIPES, ALL_DRAFTS
    path = DATA / "common_ingredients.yml"
    if not path.exists():
        pytest.skip("_data/common_ingredients.yml does not exist yet")
    pantry = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("pantry") or []

    used = set()
    for r in ALL_RECIPES + ALL_DRAFTS:
        for entry in (r.fm.get("main_ingredients") or []):
            used.add(str(entry).lower())

    unused = [p for p in pantry if p.lower() not in used]
    assert not unused, (
        f"_data/common_ingredients.yml lists {unused}, which match no "
        f"main_ingredients entry anywhere.\n"
        f"Matching is exact — 'onion' does not demote 'red onions'. Either the "
        f"entry is a typo, or it is aspirational and should come out until "
        f"something actually uses it."
    )


# --- one base URL, one fetch path -------------------------------------------

JS_DIR = ROOT / "js"


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
                                               ROOT / "index.html"]:
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
    html = read("index.html")
    for input_id in ("ingredient-search-box", "name-search-box"):
        assert f'for="{input_id}"' in html, (
            f'#{input_id} has no <label for="{input_id}">. The visible '
            f'[ SEARCH … ] text should BE the label rather than sitting next to '
            f"one — same styling, same position, `span` becomes `label`."
        )


def test_clear_controls_are_buttons():
    """They were <span>s with click handlers: not focusable, not announced."""
    html = read("index.html") + read("_includes", "filter_group.html")
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
    assert "syncAriaPressed" in read("js", "filters.js"), (
        "filters.js no longer syncs aria-pressed. The attribute would then be "
        "stuck at its initial value and would lie about the filter state."
    )


def test_search_results_are_announced():
    """The results pool is populated as you type, so the change needs announcing."""
    html = read("index.html")
    match = re.search(r'id="ingredient-results-pool"[^>]*', html)
    assert match, "#ingredient-results-pool is missing from index.html."
    assert "aria-live" in match.group(0), (
        "#ingredient-results-pool has no aria-live attribute, so a screen "
        'reader user gets no indication that anything happened. aria-live="polite".'
    )


def test_index_has_a_heading():
    """Every recipe page has an h1. The index had none of any level."""
    html = read("index.html")
    assert re.search(r"<h1[^>]*>", html), (
        "index.html has no <h1>. The logo is the visible title, so a "
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
    for relpath in ("_layouts/recipe.html", "_sass/_recipe.scss", "js/method-toggle.js"):
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
                [ROOT / "index.html"]:
        if path.exists() and "index_tags_sections" in path.read_text(encoding="utf-8"):
            offenders.append(path.name)
    assert not offenders, (
        f"{offenders} still reference site.data.index_tags_sections, which no "
        f"longer exists. Jekyll resolves a missing data file to nil silently, so "
        f"the symptom is empty filter groups rather than an error."
    )


# --- SCSS structure ----------------------------------------------------------

SASS_DIR = ROOT / "_sass"


def _top_level_blocks(text: str):
    """Yield (selector, [declared properties]) for every zero-indent rule."""
    depth = 0
    current = None
    props: list[str] = []
    for line in text.split("\n"):
        code = line.split("//")[0]
        if depth == 0:
            match = re.match(r"^([.#%&][^{}/]*?)\s*\{", line)
            if match:
                current = " ".join(match.group(1).split())
                props = []
        elif depth == 1 and current:
            decl = re.match(r"^\s{2}([a-z-]+)\s*:", line)
            if decl:
                props.append(decl.group(1))
        depth += code.count("{") - code.count("}")
        if depth == 0 and current and "}" in code:
            yield current, props
            current = None


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
    for path in sorted(SASS_DIR.glob("*.scss")):
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


def test_spacing_tokens_are_not_used_for_type():
    """$space-* is for margin, padding and gaps — never font-size.

    A padding and a type size that happen to share a value are not the same
    decision. Tying them together means changing one changes the other.
    """
    offenders = []
    for path in sorted(SASS_DIR.glob("*.scss")):
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
    for path in sorted(SASS_DIR.glob("*.scss")):
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
