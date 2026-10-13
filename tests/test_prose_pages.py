"""House typography on the pages that are NOT recipes. GitHub issue #413.

tests/test_style.py's typography rules are parametrised over the recipe
fixture, so without this file the about page, the index pages and the
reference pages have no typography coverage.

Ported from test_style.py: em dash, Unicode fractions, degree signs, house
spellings, accents, and no ampersand in a title. Not ported, because they are
recipe-shaped: `mins`/`hours` time formats (the reference tables write
"3 hrs" and "39 min/kg" in compact cells), fan-oven wording and `Estimated N
mins`, and markdown link shapes (these pages link with <a href>).

Two surfaces are checked, because the reference pages render most of their
prose out of _data/food/*.yml and not out of the .html.
"""
import re

import pytest
import yaml

from conftest import ROOT

# `shared`, not `food`: the pages here span both sites (cocktails/index.html)
# and the about page belongs to neither by design (#374, #395).
pytestmark = pytest.mark.shared

# --- what counts as a prose page ---------------------------------------------
#
# Discovered, not listed: the page nobody adds to a list is the page nobody
# checks. _dev/ is excluded because it never ships; _site/, _site_prod/ and
# tmp/ because they are the same words again at a path nobody edits.
PAGE_ROOTS = (".", "food", "cocktails")
SKIP_DIRS = {"_site", "_site_prod", "tmp", "_dev", "node_modules", ".git",
             "_food_recipes", "_food_drafts", "_cocktail_drafts"}


def _prose_pages():
    seen = []
    for root in PAGE_ROOTS:
        base = ROOT / root
        pattern = "*.html" if root == "." else "**/*.html"
        for path in sorted(base.glob(pattern)):
            if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
                continue
            seen.append(path)
    return seen


PROSE_PAGES = _prose_pages()

# The reference pages' own words, which live in data rather than in the page.
#
# Named rather than globbed, and this one has to be a list: walking all of
# _data/ reports BEM class names (`category--star`) as missing em dashes, and
# rationale prose that renders nowhere. Every string in these two files is
# destined for a page.
REFERENCE_DATA = ("food/cooking_methods.yml", "food/internal_temperatures.yml")

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LIQUID_COMMENT = re.compile(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}",
                            re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
SCRIPT_OR_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
LIQUID_TAG = re.compile(r"\{%.*?%\}|\{\{.*?\}\}", re.S)
HTML_TAG = re.compile(r"<[^>]+>", re.S)
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def visible_text(raw: str) -> str:
    """The words a reader sees, and nothing else.

    The front matter is dropped whole: on these pages it is configuration and
    `#` comments with ASCII dashes, which would all be false hits. `title:`,
    the one field that reaches the reader, is read by `page_title`. Liquid and
    HTML comments go for the same reason; <script> and <style> are code, and a
    reference page's <script> holds the data file again as JSON.
    """
    raw = FRONT_MATTER.sub("", raw)
    for pattern in (LIQUID_COMMENT, HTML_COMMENT, SCRIPT_OR_STYLE):
        raw = pattern.sub(" ", raw)
    return HTML_TAG.sub(" ", LIQUID_TAG.sub(" ", raw))


def page_title(raw: str) -> str:
    match = FRONT_MATTER.match(raw)
    if not match:
        return ""
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return ""
    return str(data.get("title") or "")


# --- the rules ---------------------------------------------------------------
TYPOGRAPHY = [
    ("slash fractions",
     r"(?<![\d/])(?:1/2|1/4|3/4|1/3|2/3|1/8|3/8|5/8|7/8)(?![\d/])",
     "use Unicode fractions: ½ ¼ ¾ ⅓ ⅔ ⅛ ⅜ ⅝ ⅞"),
    ("double hyphen", r"(?<!-)--(?!-)", "use an em dash —"),
    ("ASCII arrow", r"->", "use →"),
    ("degree-less temperature", r"\b\d{2,3}\s*(?:oC|C)\b(?!\w)",
     "always °C, e.g. 200°C"),
]

# Shared with test_style.py's recipe rules rather than restated, so the two can
# never drift into disagreeing about how a word is spelled or a range written.
from test_style import (  # noqa: E402
    NUMBER_RANGE, SPELLINGS, _accent_problems, _accented_words,
)

TYPOGRAPHY.append(
    ("hyphenated number range", NUMBER_RANGE.pattern,
     "ranges take an en dash — 3–4 mins, 170–180°C")
)


def _relative(path):
    return path.relative_to(ROOT).as_posix()


def _typography_problems(text):
    problems = []
    for name, pattern, fix in TYPOGRAPHY:
        hits = re.findall(pattern, ISO_DATE.sub(" ", text))
        if hits:
            problems.append(f"{len(hits)} × {name} ({sorted(set(hits))[:4]}) — {fix}")
    for pattern, correct in SPELLINGS.items():
        if re.search(pattern, text, re.I):
            problems.append(f"non-house spelling — {pattern.strip(chr(92) + 'b')} "
                            f"should be '{correct}'")
    return problems


def test_there_are_prose_pages_to_check():
    """A discovery bug would report green having read nothing.

    If PAGE_ROOTS and SKIP_DIRS between them exclude everything, every
    parametrised test below does not exist, and pytest does not fail on an
    empty parametrise.
    """
    assert len(PROSE_PAGES) >= 6, (
        f"only found {len(PROSE_PAGES)} prose page(s): "
        f"{[_relative(p) for p in PROSE_PAGES]}. There should be at least the "
        f"about page, three index pages and two reference pages. Check "
        f"PAGE_ROOTS and SKIP_DIRS -- an over-eager exclusion here turns every "
        f"test in this file green by giving it nothing to read."
    )


@pytest.mark.parametrize("page", PROSE_PAGES, ids=lambda p: _relative(p))
def test_prose_page_typography(page):
    problems = _typography_problems(visible_text(page.read_text(encoding="utf-8")))
    assert not problems, (
        f"{_relative(page)} breaks house typography:\n  " + "\n  ".join(problems)
    )


@pytest.mark.parametrize("page", PROSE_PAGES, ids=lambda p: _relative(p))
def test_prose_page_accents(page):
    """Same curated list as recipes, same reason -- see test_accents_in_prose."""
    words = _accented_words()
    assert words, "_data/accented_words.yml has no `words:` map."
    text = visible_text(page.read_text(encoding="utf-8"))
    problems = _accent_problems([("body", text)], words)
    assert not problems, (
        f"{_relative(page)} uses unaccented spelling(s):\n  " + "\n  ".join(problems)
        + "\n\nIf the word genuinely takes no accent, add it to the `no_accent` "
          "list in _data/accented_words.yml."
    )


@pytest.mark.parametrize("page", PROSE_PAGES, ids=lambda p: _relative(p))
def test_prose_page_title_has_no_ampersand(page):
    """Titles use 'and'. No proper-noun allow-list here, unlike recipes: a page
    title is Helen's own words, never a reproduced brand name, so the escape
    hatch that test_no_ampersand_in_title needs has nothing to protect."""
    title = page_title(page.read_text(encoding="utf-8"))
    assert "&" not in title, (
        f"{_relative(page)} `title: {title!r}` contains an ampersand. Page "
        f"titles use the word 'and'."
    )


def _data_strings(node, path=""):
    """Every string in a data file, with a dotted path to where it lives."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _data_strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _data_strings(value, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path.lstrip("."), node


@pytest.mark.parametrize("name", REFERENCE_DATA)
def test_reference_data_prose_typography(name):
    """The reference pages' words mostly live in _data, so check them there.

    Every string, not a list of prose-bearing keys: a key list is a guess
    about which fields reach a reader, and a table cell such as `covering`
    would not be on it.
    """
    path = ROOT / "_data" / name
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    problems = []
    for location, text in _data_strings(data):
        for problem in _typography_problems(HTML_TAG.sub(" ", text)):
            problems.append(f"{location}: {problem}")
    assert not problems, (
        f"_data/{name} breaks house typography, and it renders on a reference "
        f"page:\n  " + "\n  ".join(problems)
    )
