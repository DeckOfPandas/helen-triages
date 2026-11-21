"""Regression guards for named shortlists (#1521). MANUAL §8.9.

The behaviour is tested in tests/js/shortlists-store.test.js; these hold the
source to the rules a behaviour test cannot see.
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.shared

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "assets/js/shortlists-store.js"
SOURCES = [p for d in ("assets/js", "_includes", "_layouts", "food", "cocktails")
           for p in (ROOT / d).rglob("*") if p.suffix in (".js", ".html")]

FOOD_OLD_KEYS = [
    "htf-shortlist-food-v1", "htf-shortlist-glasses-food-v1",
    "htf-shortlist-portions-food-v1", "htf-shortlist-portions-food-v2",
    "htf-shortlist-batches-food-v1", "htf-shortlist-ticked-food-v1",
    "htf-shortlists-food-v1",
]


def test_the_storage_key_is_named_in_one_place():
    assert SOURCES, "found no source files to scan: the paths above are wrong"
    naming = sorted(str(p.relative_to(ROOT)) for p in SOURCES
                    if "'htf-lists-'" in p.read_text(encoding="utf-8"))
    assert naming == ["assets/js/shortlists-store.js"], (
        "The shortlists key must be built in shortlists-store.js and nowhere "
        f"else, so there is one place to change it; found it in {naming}")


def test_nothing_calls_localstorage_clear():
    offenders = sorted(str(p.relative_to(ROOT)) for p in SOURCES
                       if re.search(r"localStorage\s*\.\s*clear\s*\(", p.read_text(encoding="utf-8")))
    assert not offenders, (
        "localStorage.clear() empties every deckofpandas.github.io site on the "
        f"origin, Is It Rhubarb Yet included: {offenders}")


def test_foods_old_keys_are_removed_by_name_and_no_cocktail_key_is():
    text = STORE.read_text(encoding="utf-8")
    block = re.search(r"var OLD_KEYS = \{(.*?)\};", text, re.S)
    assert block, "shortlists-store.js has no OLD_KEYS map: the old keys are not being removed"
    named = re.findall(r"'([^']+)'", block.group(1))
    missing = [k for k in FOOD_OLD_KEYS if k not in named]
    assert not missing, f"food's old keys must each be removed by name; missing {missing}"
    cocktail = [k for k in named if "cocktail" in k]
    assert not cocktail, f"cocktails' shortlist is still live and must not be removed: {cocktail}"
    assert "removeItem" in text, "the old keys are listed but never removed"


PAGE = ROOT / "food/shortlists.html"
PAGE_JS = ROOT / "assets/js/shortlists-page.js"
PICKER = ROOT / "_includes/shortlist-picker.html"
INDEX = ROOT / "food/index.html"


def test_the_shortlists_page_exists_and_says_what_it_needs_without_javascript():
    text = PAGE.read_text(encoding="utf-8")
    assert "permalink: /food/shortlists/" in text, "food/shortlists.html must be served at /food/shortlists/"
    noscript = re.search(r"<noscript>(.*?)</noscript>", text, re.S)
    assert noscript and "JavaScript" in noscript.group(1) and "browser" in noscript.group(1), (
        "with scripts off the page must say plainly that shortlists live in this "
        "browser and need JavaScript")
    assert re.search(r"<div[^>]*data-shortlists[^>]*\bhidden\b", text), (
        "the page's own markup must ship hidden, so a reader with scripts off "
        "sees the no-JavaScript line and nothing half-built")


def test_the_tabs_are_real_tabs():
    text = PAGE.read_text(encoding="utf-8")
    js = PAGE_JS.read_text(encoding="utf-8")
    assert re.search(r'role="tablist"[^>]*aria-label=', text), "the tab row needs role=tablist and a name"
    assert 'role="tabpanel"' in text, "the tabs need a tabpanel to control"
    for attribute in ('role="tab"', "aria-selected=", 'aria-controls="shortlists-panel"', "tabindex="):
        assert attribute in js, f"shortlists-page.js must draw each tab with {attribute}"
    for key in ("ArrowRight", "ArrowLeft", "Home", "End"):
        assert key in js, f"the tabs must move with {key}"
    assert "aria-labelledby" in js, "the panel must be named by its selected tab"


def test_every_input_on_the_page_has_a_label():
    sources = {"food/shortlists.html": PAGE.read_text(encoding="utf-8"),
               "assets/js/shortlists-page.js": PAGE_JS.read_text(encoding="utf-8"),
               "_includes/shortlist-picker.html": PICKER.read_text(encoding="utf-8")}
    unlabelled = []
    for name, text in sources.items():
        labelled = set(re.findall(r"""<label[^>]*\bfor=["']([\w-]+)""", text))
        for tag in re.findall(r"<input\b[^>]*>", text):
            if 'type="checkbox"' in tag or "aria-label" in tag:
                continue
            ident = re.search(r"""\bid=["']([\w-]+)""", tag)
            if not ident or ident.group(1) not in labelled:
                unlabelled.append(f"{name}: {tag[:80]}")
    assert not unlabelled, (
        "every text input needs a <label for> naming it (a tick box sits inside "
        f"its row's label; food-shopping-rows.js gives a number box aria-label): {unlabelled}")
    assert sum(len(re.findall(r"<input\b", t)) for t in sources.values()) >= 3, (
        "found fewer inputs than the page has: the scan above is reading the wrong files")


def test_the_food_index_only_browses():
    text = INDEX.read_text(encoding="utf-8")
    left = [marker for marker in ('id="shortlist-only"', 'id="shopping-list"', "data-shared-shortlist",
                                  "data-shortlist-export-panel", "recipe-data.html", "shortlist-export.js")
            if marker in text]
    assert not left, (
        "the food index is for browsing; its lists, their shopping and sharing "
        f"live on food/shortlists.html (#1521). Back on the index: {left}")
    assert re.search(r'<a class="shortlists-link" href="\{\{ \'/food/shortlists/\' \| relative_url \}\}" '
                     r'data-shortlists-link>', text), (
        "the index must link to the shortlists page, as a link that counts lists")


FOOD_BUTTONS = ["food/index.html", "_includes/food/recipe-row.html", "_includes/page-actions.html"]


@pytest.mark.parametrize("source", FOOD_BUTTONS)
def test_every_food_shortlist_button_says_what_it_is_and_where_it_starts(source):
    text = (ROOT / source).read_text(encoding="utf-8")
    if source.endswith("page-actions.html"):
        text = text.split('{% if page.site_key == "food" %}')[1].split("{% else %}")[0]
    buttons = re.findall(r'<button[^>]*class="btn-shortlist"[^>]*>', text, re.S)
    assert buttons, f"{source} has no shortlist button: the scan is reading the wrong place"
    for button in buttons:
        for attribute in ("data-shortlist-key=", "data-shortlist-title=", "data-portions=", "hidden"):
            assert attribute in button, (
                f"{source}'s shortlist button has no {attribute}: the picker needs the "
                "recipe's key, its name and the portions it starts at, and the button "
                "ships hidden until the script that works it has run")
