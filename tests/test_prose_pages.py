"""House typography on the pages that are NOT recipes. GitHub issue #413.

tests/test_style.py's typography rules are parametrised over the recipe
fixture, so until this file existed the about page, both index pages and the
two reference pages had no typography coverage at all -- and the about page is
the most-read prose on the site after the recipes themselves. #376 found
"But more importantly -- and please hear me when I say this --" sitting three
paragraphs from a real em dash on that page. Nothing failed, because that page
is not a recipe.

WHAT IS PORTED AND WHAT IS NOT. This is a porting exercise with judgement in
it, not a copy of test_style.py. Ported: em dash, Unicode fractions, degree
signs, house spellings, accents, and no ampersand in a title. Deliberately NOT
ported, because they are recipe-shaped and would be wrong here:

  - `mins`/`hours` prose time formats. The reference tables write "3 hrs" and
    "39 min/kg" in compact table cells, where the recipe convention is not the
    house style. 17 hits, every one of them fine as written.
  - fan-oven wording and `Estimated N mins`, which describe a recipe's own
    metadata and have no counterpart on a prose page.
  - markdown link shapes (wikilinks, reversed brackets). These pages link with
    <a href>; the markdown rules have nothing to bite on.

TWO SURFACES, because the pages' words do not all live in the pages. The
reference pages render most of their prose out of _data/food/*.yml -- the
paragraphs around each timing table, the covering instructions, the sourcing
notes. Checking only the .html would have found 0 of the 4 real violations
that were actually there.
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
# DISCOVERED, NOT LISTED. A hard-coded list of pages is exactly how coverage
# stops reaching -- the page nobody adds to the list is the page nobody checks,
# which is the whole complaint behind this issue. Anything the site publishes
# under these roots is checked the day it appears.
#
# _dev/ is excluded because it is a scratch harness that never ships, and
# _site/, _site_prod/ and tmp/ because they are build output and scratch: the
# same words twice over, reported at a path nobody edits.
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
# NAMED RATHER THAN GLOBBED, and this one really does have to be a list. Walking
# every file under _data/ was tried and measured: it reports `category--star`
# from filter_sections.yml as a missing em dash (it is a BEM class name), and 18
# more from the rationale prose in the two taxonomy files, which documents why a
# mood exists and renders nowhere. These two files are different in kind -- they
# are content, every string in them is destined for a page, and walking them
# whole produced no false positives at all.
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
    """The words a reader actually sees, and nothing else.

    THE FRONT MATTER IS DROPPED WHOLE, not comment-stripped. On these pages it
    is pure configuration -- layout, permalink, site_key -- wrapped in long `#`
    comments explaining the configuration, and those comments are written in
    Helen's prose voice, ASCII dashes and all. Scanning them found 11 hits on
    about.html against 2 real ones: a check that is 85% noise is a check people
    learn to ignore. `title:` is pulled back out separately below, because it is
    the one front matter field that reaches the reader.

    Liquid and HTML comments go for the same reason. <script> and <style> go
    because they are code -- and because cooking-methods-and-timings.html
    serialises a 60 KB JSON blob of the data file into a <script>, which would
    otherwise be scanned here AND again as data, reporting everything twice.
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
#
# The en-dash rule is shared with test_style.py rather than restated here, so
# the two surfaces cannot drift into disagreeing about what a range looks like.
# Helen reviewed the recipe backlog line by line on 2026-08-21 and cleared it;
# these pages and the reference data were already clean.
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
    """A discovery bug here reports a confident green having read nothing.

    PAGE_ROOTS and SKIP_DIRS between them could silently exclude everything --
    a renamed directory, a glob that stopped matching -- and every parametrised
    test below would then simply not exist. Pytest does not fail on an empty
    parametrise; it says nothing at all.
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

    EVERY STRING, not a list of prose-bearing keys. A key list is a guess about
    which fields reach a reader, and it was wrong the first time it was tried:
    `covering` (a table cell) held three of the four violations this test found
    on its first run, and would not have been on anyone's list of prose fields.
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
