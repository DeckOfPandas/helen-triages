"""The citation spec, enforced. GitHub issue #406.

`model_instructions/SOURCE_ATTRIBUTION_SPEC.md` is the prose version and the
thing to read first; this is the same contract as assertions.

WHY THIS FILE EXISTS AT ALL, given the corpus was clean when it was written.
The spec was settled with Helen on 2026-08-20 and applied by judgement twice --
once by an Opus pass over 82 published recipes, once by a Sonnet pass over 301
drafts -- with nothing checking either. That produced exactly one violation in
396 files, which sounds like an argument that no guard was needed. It is the
opposite. On the same day, having just written the spec down, Helen filled in
two `QQ` citations by hand and one of them came out three ways wrong: a
`source_type` outside the eight (`magazine`), a missing "Adapted from", and a
publication name matching none of the five already in the corpus. A spec three
days old, freshly documented, with its author typing -- and it still drifted.

That is the repository's oldest lesson wearing another hat: a rule that is
written down and not checked is a rule that will be broken by someone who has
read it. See the destructive-git hook, `meta.awaiting_fix`, and `meta.proofread`.

THE RULES ARE ENFORCED OVER DRAFTS TOO, deliberately. A draft is allowed to be
unfinished -- a blank tagline, no method, `QQ` anywhere -- and test_drafts.py is
careful about which published-recipe rules it declines to apply. These are not
in that category. A citation is either in the house shape or it is not, at any
stage, and a draft is simply a published recipe that has not happened yet: 314
of them are waiting, and every one that drifts is a promotion that will drift.
The two collections get separate tests rather than one over a merged list,
matching conftest's deliberate split, so a failure names which collection it is
in without reading the path.
"""
from __future__ import annotations

import re

import pytest

from conftest import where, where_draft

# Suite marker, so `pytest -m food` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.food

SPEC = "model_instructions/SOURCE_ATTRIBUTION_SPEC.md"

# The eight, and nothing else. `magazine` is the near-miss that has already been
# typed once by hand -- it is `publication`.
VALID_TYPES = {
    "publication", "book", "website", "author",
    "person", "place", "joke", "unknown",
}

# Work published by other people. Helen, 2026-08-20: "Bare labels don't need
# 'adapted from', only work published by other people."
PREFIXED = {"publication", "book", "website", "author"}
BARE = {"person", "place", "joke", "unknown"}

PREFIX = "Adapted from "

# A date is Month+Year, or a year on its own. Helen, 2026-08-20: "Online
# magazines don't have a publication schedule like print ones do... a year alone
# is enough." So "Adapted from Good Food, 2025" and "Adapted from Good Food,
# May 2026" are both complete, and "Adapted from Good Food 2026 calendar"
# carries its date inside the title.
DATE = re.compile(
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{4}\b"
    r"|\b(?:19|20)\d{2}\b"
)

# The separator that distinguishes a site-with-author from a book-with-author.
# `Adapted from X, Y` is a book and its author; `Adapted from X, recipe Y` is a
# site and the person who wrote the recipe on it. Without this the two shapes
# are identical and only `source_type` tells them apart -- which is fine for a
# machine and useless for a reader.
RECIPE_BY = ", recipe "

# A citation names its source, not who printed it. Helen's ruling 8, which took
# "(Hodder & Stoughton)" off beef-wellington -- the only one in the corpus.
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
    if kind == "unknown" and source != "QQ":
        return (
            f"`source_type: unknown` must have `source: \"QQ\"`, not {source!r}.\n"
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

    Nothing in a source STRING says whether it is a magazine or a book --
    `Adapted from Good Food` and `Adapted from Gordon Ramsay's Ultimate Cookery
    Course` are the same shape. The date is what separates the print issue from
    the website, and Good Food is genuinely both: 11 drafts cite the October
    2025 issue and 31 cited no date at all.
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
# Added 2026-08-21, after the spec's own gap put two wrong citations live.
#
# TWO SHAPES, BOTH CARRYING THE AUTHOR:
#
#     Adapted from Feed Your Soul, Wagamama        title, then author
#     Adapted from Delia Smith's Book of Cakes     author possessively, then title
#
# The possessive is the MORE COMMON of the two here -- 44 of 89 book citations --
# and it is ordinary English. Requiring a comma everywhere would have produced
# "Delia Smith's Book of Cakes, Delia Smith", which is why this accommodates the
# shape rather than the corpus accommodating the rule.
#
# WHAT IT REPLACES WAS UNFALSIFIABLE. The spec offered the comma form plus an
# "author not recorded" fallback that accepts ANY string, so all 44 possessive
# citations were passing through the fallback and the rule could not reject
# anything at all. `Adapted from Wagamama Feed Your Soul` -- a publisher glued to
# a title, author nowhere -- passed on two published pages until Helen asked why
# it was allowed. A rule that accepts everything is not lenient, it is absent.
#
# THE HEURISTIC FAILS TOWARDS ACCEPTING, deliberately and knowably: a title that
# merely CONTAINS a possessive ("The Baker's Year") would satisfy it without
# naming an author. That is a missed flag, not a false alarm, and a false alarm
# here would be worse -- it would push someone to mangle correct prose.
COMMA_AUTHOR = re.compile(r",\s*\S")
POSSESSIVE_AUTHOR = re.compile(r"\b\w[\w&.\-]*(?:\s+[\w&.\-]+)*'s\s+\S")

# NO BOOK MAY OMIT ITS AUTHOR. There is no exception list, and there was very
# nearly one.
#
# Helen, 2026-08-21: "I can't imagine knowing the name of a book but not its
# author." A single citation appeared to contradict her --
# sweet-potato-chocolate-brownies.md, `Adapted from Healthier Baking` -- and it
# was about to be added to a declared-exceptions set when she recognised it:
# not a book at all, but a one-off section in Good Food magazine. Retyped as a
# dateless `website` (the date discriminator, above), and the exception set was
# deleted before it ever held anything.
#
# THE NEAR-MISS IS THE POINT. An exception list with one entry looks like
# diligence and reads, later, as evidence that the rule has legitimate
# exceptions -- and the next odd case gets added to it rather than questioned.
# The one entry here was a misfiled citation, and asking a person beat
# accommodating it. If a genuine authorless book ever turns up, add the list
# back deliberately, with the recipe named beside it.


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
    """Same rules, same reasons -- see this module's docstring.

    Reached through the `draft` fixture rather than the ALL_DRAFTS list, so
    when `_food_drafts/` is absent (a CI checkout: it is a separate private
    repo, issue #378) this parametrises to nothing and collects zero tests,
    rather than passing and claiming the drafts were checked.
    """
    source, kind = _citation(draft)
    problem = rule(source, kind)
    assert problem is None, f"{where_draft(draft)}\n\n{problem}"
