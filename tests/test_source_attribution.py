"""The citation spec, enforced. GitHub issue #406.

`model_instructions/SOURCE_ATTRIBUTION_SPEC.md` is the prose version and the
thing to read first; this is the same contract as assertions.

The rules are enforced over drafts too, deliberately. A draft may be
unfinished, but a citation is either in the house shape or it is not, at any
stage, and a draft that drifts is a promotion that will drift. The two
collections get separate tests, matching conftest's split, so a failure names
which collection it is in.
"""
from __future__ import annotations

import re

import pytest

from conftest import where, where_draft

pytestmark = pytest.mark.food

SPEC = "model_instructions/SOURCE_ATTRIBUTION_SPEC.md"

# `magazine` is the near-miss: it is `publication`.
VALID_TYPES = {
    "publication", "book", "website", "author",
    "person", "place", "joke", "unknown",
}

# Only work published by other people takes the prefix; a bare label must not.
PREFIXED = {"publication", "book", "website", "author"}
BARE = {"person", "place", "joke", "unknown"}

PREFIX = "Adapted from "

# A date is a month and year, or a year on its own, anywhere in the string:
# "Adapted from Good Food 2026 calendar" carries its date inside the title.
DATE = re.compile(
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{4}\b"
    r"|\b(?:19|20)\d{2}\b"
)

# Tells a site-with-author from a book-with-author. `Adapted from X, Y` is a
# book and its author; `Adapted from X, recipe Y` is a site and the person who
# wrote the recipe on it. Without it only `source_type` tells them apart, which
# a reader cannot see.
RECIPE_BY = ", recipe "

# A citation names its source, not who printed it (the spec's rule 5).
TRAILING_BRACKET = re.compile(r"\([^)]*\)\s*$")


def _citation(document):
    """(source, source_type) for a recipe or draft, both as plain strings."""
    return (
        str(document.fm.get("source") or "").strip(),
        document.fm.get("source_type"),
    )


# --- the rules, one function each, shared by both collections ---------------

def _bad_type(source, kind):
    if kind in VALID_TYPES:
        return None
    return (
        f"`source_type: {kind!r}` is not one of the eight.\n"
        f"Use one of: {', '.join(sorted(VALID_TYPES))}.\n"
        f"`magazine` is the near-miss -- it is `publication`. See {SPEC}."
    )


def _bad_prefix(source, kind):
    if kind not in VALID_TYPES:
        return None                              # _bad_type owns this file
    prefixed = source.startswith(PREFIX)
    if kind in PREFIXED and not prefixed:
        return (
            f"`source_type: {kind}` is work published by other people, so its "
            f"source must begin \"{PREFIX}\".\n"
            f"  source: {source!r}\n"
            f"Helen, 2026-08-20: \"Bare labels don't need 'adapted from', only "
            f"work published by other people.\""
        )
    if kind in BARE and prefixed:
        return (
            f"`source_type: {kind}` is a bare label, so its source must NOT "
            f"begin \"{PREFIX}\".\n"
            f"  source: {source!r}\n"
            f"A person, a place, a joke and a QQ are not published works. If "
            f"this really is one, the type is wrong rather than the prefix."
        )
    return None


def _bad_unknown(source, kind):
    # Two strings: `QQ` while the question is open (it blocks the build), and
    # `unknown` once Helen has closed it (the spec's rule 7a). Lowercase and
    # exact: `Unknown` reads like a finished answer typed without thinking,
    # and a blank like nothing to see.
    if kind == "unknown" and source not in ("QQ", "unknown"):
        return (
            f"`source_type: unknown` must have `source: \"QQ\"` (question open, "
            f"blocks the build) or `source: \"unknown\"` (Helen has ruled nobody "
            f"knows), not {source!r}.\n"
            f"QQ is the marker that a citation is genuinely unestablished, and "
            f"it deliberately fails test_no_qq_placeholder so the gap cannot be "
            f"ignored. `Unknown` reads like a finished answer and a blank reads "
            f"like there is nothing to see; neither is true."
        )
    if source == "QQ" and kind != "unknown":
        return (
            f"`source: \"QQ\"` means nobody has established the citation, so "
            f"`source_type` must be `unknown`, not {kind!r}."
        )
    return None


def _bad_date(source, kind):
    """The discriminator, both ways round.

    The date is what separates a print issue from the website of the same
    name, and Good Food is both: a `publication` carries one and a `website`
    does not.
    """
    if kind == "publication" and not DATE.search(source):
        return (
            f"`source_type: publication` must carry a date -- a month and year, "
            f"or a year alone.\n"
            f"  source: {source!r}\n"
            f"If there is no date, this is the website rather than an issue: "
            f"set `source_type: website`. That is the rule Helen settled on "
            f"2026-08-20, and it is why 64 drafts were retyped."
        )
    if kind == "website" and DATE.search(source):
        return (
            f"`source_type: website` must NOT carry a date.\n"
            f"  source: {source!r}\n"
            f"A dated citation is a print issue: use `source_type: "
            f"publication`. An online magazine has no publication schedule to "
            f"cite, which is exactly why the date is the discriminator."
        )
    return None


def _bad_author_separator(source, kind):
    if kind == "website" and "," in source and RECIPE_BY not in source:
        return (
            f"A `website` naming an author separates it with \"{RECIPE_BY}\".\n"
            f"  source: {source!r}\n"
            f"  wanted: Adapted from <site>, recipe <Firstname Lastname>\n"
            f"Without `recipe` this is indistinguishable from a book and its "
            f"author, which is a different shape entirely."
        )
    if kind == "book" and RECIPE_BY in source:
        return (
            f"A `book` names its author with a plain comma, not "
            f"\"{RECIPE_BY}\".\n"
            f"  source: {source!r}\n"
            f"  wanted: Adapted from <title>, <Firstname Lastname>\n"
            f"`recipe` is the website shape's separator."
        )
    return None


def _bad_publisher(source, kind):
    if TRAILING_BRACKET.search(source):
        return (
            f"A citation names its source, not its publisher.\n"
            f"  source: {source!r}\n"
            f"Helen's ruling 8, 2026-08-20. The bracket comes off. If the "
            f"bracket is part of the actual title rather than a publisher, say "
            f"so in {SPEC} and narrow this rule deliberately."
        )
    return None


# --- a book names its author, in one shape or the other ----------------------
#
#     Adapted from Feed Your Soul, Wagamama        title, then author
#     Adapted from Delia Smith's Book of Cakes     author possessively, then title
#
# The heuristic fails towards accepting, on purpose: a title that merely
# contains a possessive ("The Baker's Year") satisfies it without naming an
# author. A false alarm would push someone to mangle correct prose.
#
# There is no exception list (DECISIONS §4, #406). If a book seems to have no
# author, check first that it is a book, then ask Helen.
COMMA_AUTHOR = re.compile(r",\s*\S")
POSSESSIVE_AUTHOR = re.compile(r"\b\w[\w&.\-]*(?:\s+[\w&.\-]+)*'s\s+\S")


def _bad_book_author(source, kind):
    if kind != "book":
        return None
    body = source[len(PREFIX):] if source.startswith(PREFIX) else source
    if COMMA_AUTHOR.search(body) or POSSESSIVE_AUTHOR.search(body):
        return None
    return (
        f"A `book` names its author, and this one names nobody.\n"
        f"  source: {source!r}\n"
        f"Two shapes are accepted: `Adapted from <title>, <Author>` or "
        f"`Adapted from <Author>'s <title>`. Prefer whichever reads as English "
        f"-- `Delia Smith's Book of Cakes`, not `Book of Cakes, Delia Smith`.\n"
        f"If you believe a book genuinely has no findable author, check first "
        f"that it is a book -- the one candidate this rule ever had turned out "
        f"to be a magazine section. See {SPEC}."
    )


RULES = [
    ("source_type is one of the eight", _bad_type),
    ("published work says 'Adapted from'", _bad_prefix),
    ("unknown means QQ", _bad_unknown),
    ("a publication is dated and a website is not", _bad_date),
    ("a website names its author with 'recipe'", _bad_author_separator),
    ("no publisher in a citation", _bad_publisher),
    ("a book names its author", _bad_book_author),
]

RULE_IDS = [name for name, _ in RULES]
RULE_FUNCS = [func for _, func in RULES]


@pytest.mark.parametrize("rule", RULE_FUNCS, ids=RULE_IDS)
def test_recipe_citation_follows_the_spec(recipe, rule):
    source, kind = _citation(recipe)
    problem = rule(source, kind)
    assert problem is None, f"{where(recipe)}\n\n{problem}"


@pytest.mark.parametrize("rule", RULE_FUNCS, ids=RULE_IDS)
def test_draft_citation_follows_the_spec(draft, rule):
    """The same rules on drafts: see this module's docstring.

    Reached through the `draft` fixture rather than the ALL_DRAFTS list, so
    where `_food_drafts/` is absent (CI: it is a private repo, #378) this
    collects no tests instead of passing and claiming the drafts were checked.
    """
    source, kind = _citation(draft)
    problem = rule(source, kind)
    assert problem is None, f"{where_draft(draft)}\n\n{problem}"
