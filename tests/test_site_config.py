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
