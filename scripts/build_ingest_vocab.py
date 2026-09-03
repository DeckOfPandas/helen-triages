#!/usr/bin/env python3
"""Render the vocabulary blocks inside the two standalone ingest documents.

    python3 scripts/build_ingest_vocab.py --check    # diff, exit 1 if stale
    python3 scripts/build_ingest_vocab.py --write    # rewrite the blocks

`model_instructions/INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md` are
handed to a Claude with no checkout, so each PRINTS the closed vocabularies as
literal text. That is the only deliberate duplication of data in this
repository -- tests/test_standalone_docs.py's header argues for it at length --
and until now the guard ran in ONE direction: everything printed had to still
be declared, nothing required the document to print everything declared.

WHAT THE ONE-WAY GUARD LET THROUGH, measured 2026-09-02 (INGEST_INBOX_DESIGN
§3): the cocktail document printed 42 of the 48 declared garnishes, and the
food document listed a dozen of the 45 accented words and none of the eight
words that deliberately keep NO accent. Nothing was wrong; the reader was
simply under-served, and an under-served reader "corrects" a valid string to a
near one -- which is a real edit to a real file, made confidently.

SO THE DUPLICATION IS NOW GENERATED, and only the duplication. Each vocabulary
sits between a pair of HTML-comment markers:

    <!-- vocab:garnish start -->
    **Citrus peel:** lemon twist * lemon twist (discarded) * ...
    <!-- vocab:garnish end -->

Everything outside a marker pair is prose -- the "meanings you would not guess"
bullets, the four garnish rules, the worked examples -- and stays hand-written
under the existing one-way tests. INGEST_INBOX_DESIGN §4: the documents' value
is judgement and calibration, and a generator over the prose would preserve the
words and lose the point.

EVERY BLOCK IS SOURCED FROM AN IMPORTED LOADER, NEVER FROM A LIST TYPED HERE.
Same rule as scripts/ingest_preflight.py, and the reason is sharper for a
GENERATOR than for a reporter: a script carrying its own copy of the vocabulary
would write a stale document that then passes the drift check, because the
check would be comparing the copy against itself. If an import here breaks
because a loader moved, that is the mechanism working.

THE FORMATTING IS NOT FREE EITHER. tests/test_standalone_docs.py scrapes these
sections with regexes tuned to the documents' own shapes -- middle-dot
separators, `**Group:**` prefixes, backticked terms, the two-column correction
table. The rendering functions below emit exactly those shapes, and the
existing scrapers are the check that they do. If a scraper stops matching, the
generator's output is what is wrong.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from conftest import SHARED_DATA_DIR                            # noqa: E402
from test_cocktails import (                                    # noqa: E402
    _garnish_vocab, _glasses, _methods, _vocab,
)
from test_source_attribution import VALID_TYPES                 # noqa: E402
from test_standalone_docs import (                              # noqa: E402
    COCKTAIL_DOC, FOOD_DOC, _food_taxonomy,
)
from test_style import _accented_words                          # noqa: E402

WIDTH = 80

MARKER = re.compile(
    r"(?ms)^<!-- vocab:(?P<name>[a-z0-9_:]+) start -->\n"
    r"(?P<body>.*?)"
    r"^<!-- vocab:(?P=name) end -->$"
)


# =============================================================================
# RENDERING -- the shapes the scrapers in test_standalone_docs.py already parse
# =============================================================================

def _wrap(atoms, prefix: str = "") -> str:
    """Hard-wrap at 80, breaking only BETWEEN entries and never inside one.

    textwrap.fill would do this in one line and was the first version. It
    wraps on any space, so it broke the star ingredient "oily fish" across two
    lines in the middle of its backticks. Every entry in these lists is a
    string a reader COPIES into a file, and a term split over a line break gets
    copied with the break in it or retyped from memory. So the unit of wrapping
    is one entry plus its trailing separator -- which is also what the
    hand-written versions of these lists did: they broke after a separator,
    never inside a term.
    """
    lines, line = [], prefix
    for atom in atoms:
        if not line:
            line = atom
        elif len(line) + 1 + len(atom) <= WIDTH:
            line += " " + atom
        else:
            lines.append(line)
            line = atom
    lines.append(line)
    return "\n".join(lines)


def _dots(items, tick: bool = False, prefix: str = "") -> str:
    """`a · b · c`, the middle-dot list both documents already use."""
    items = [f"`{i}`" if tick else str(i) for i in items]
    assert items, "a vocabulary block rendered from an empty list"
    atoms = [i + " ·" for i in items[:-1]] + items[-1:]
    return _wrap(atoms, prefix)


def _commas(items) -> str:
    """`` `a`, `b`, `c` `` -- the food document's own list shape."""
    items = [f"`{i}`" for i in items]
    assert items, "a vocabulary block rendered from an empty list"
    return _wrap([i + "," for i in items[:-1]] + items[-1:])


def _label(key: str) -> str:
    """`citrus_peel` -> `Citrus peel`, the heading a grouped block prints.

    DERIVED RATHER THAN DECLARED, deliberately. Every group key in garnish.yml
    and methods.yml is lowercase words joined by underscores, and this produces
    exactly the six garnish headings and five method headings the documents
    printed by hand before they were generated. A group whose display name
    needs a capital in the middle -- a proper noun -- would need a label map in
    the data file; there is none today and inventing the key for a case that
    does not exist is the encyclopaedia trap (#459).
    """
    return key.replace("_", " ").capitalize()


def _grouped(groups: dict, tick: bool) -> str:
    """One paragraph per group, `**Label:** a * b * c`, blank line between.

    Group ORDER is the data file's own order, which is the order somebody
    thought about when they wrote it -- alphabetising here would put `cherries`
    before `citrus peel` for no reason and churn the document the day a group
    is renamed.
    """
    out = []
    for key, members in groups.items():
        if not isinstance(members, list):
            continue
        out.append(_dots(members, tick=tick, prefix=f"**{_label(key)}:**"))
    return "\n\n".join(out)


# =============================================================================
# THE BLOCKS -- one function each, every one over an imported loader
# =============================================================================

def _tags(group: str) -> str:
    return _commas(_food_taxonomy()["tags"][group])


def _stars() -> str:
    return _commas(_food_taxonomy()["star_ingredients"])


def _source_types() -> str:
    """The eight declared citation types -- `VALID_TYPES`, imported above.

    `VALID_TYPES` is a set, so the order has to come from somewhere: sorted,
    because any other order here would be a preference typed into this script
    and the table below the block already teaches the meaningful grouping
    (published work takes "Adapted from", a bare label does not).

    THE BLOCK IS NAMED `source_types`, PLURAL, AND THAT IS LOAD-BEARING.
    `test_invisible_keys_are_really_invisible` in test_front_matter.py scans
    every file under `scripts/` for the singular key name and fails if one
    appears, because the whole basis for exempting that key from the proofread
    rule is that nothing on the render surface reads it. This script does not
    read it off a recipe -- it renders the list of values a citation may
    declare, from the suite -- but the guard is deliberately blunt and its
    message says not to narrow it. Naming the block in the plural keeps it
    honest without arguing with it. See SOURCE_ATTRIBUTION_SPEC.md for the
    field itself.
    """
    return _dots(sorted(VALID_TYPES), tick=True)


def _accents() -> str:
    """The 45 curated accented spellings, as the words a reader should type.

    The map is unaccented -> accented and the document wants the right-hand
    side; the left-hand side is a lookup key, not a word anybody writes.
    """
    return _dots(_accented_words().values())


def _no_accents() -> str:
    """The words that deliberately keep NO accent.

    Read straight from the data file rather than through a loader because the
    suite has none for this half: test_style.py's `_accented_words()` returns
    only the `words:` map. `SHARED_DATA_DIR` is imported so the path is still
    stated in exactly one place.
    """
    data = yaml.safe_load(
        (SHARED_DATA_DIR / "accented_words.yml").read_text(encoding="utf-8")
    ) or {}
    return _dots(data.get("no_accent") or [])


def _wrong_glass_spellings() -> dict:
    return _glasses().get("canonical_glasses") or {}


def _glass_spellings() -> str:
    """Every glass spelling a drink may WRITE.

    `icons:` maps both canonical names and aliases, because it exists to keep a
    drink rendering whatever it says. `canonical_glasses` is the map of
    spellings that get corrected. So what a document should print is the
    difference: every key that is not corrected away.

    THAT IS WIDER THAN THE 23 THE DOCUMENT USED TO PRINT, by `martini glass`,
    `pineapple` and `coconut`. Those three are aliases that `canonical_glasses`
    does not declare, and test_drinks_use_the_canonical_glass_spelling says
    exactly what that means: "an alias absent from that map is permitted, which
    is why `martini` / `martini glass` does not fail: it is undecided, not
    blessed." Printing them is honest -- a drink writing one passes every test
    in the suite. Deciding they are wrong is Helen's call and would be made in
    `canonical_glasses`, where this block would then follow it.
    """
    wrong = _wrong_glass_spellings()
    icons = _glasses().get("icons") or {}
    return _dots([g for g in icons if g not in wrong], tick=True)


def _glass_corrections() -> str:
    """The wrong-spelling table's data rows, grouped by what they correct to.

    The header row and its `|---|---|` stay outside the markers: they are the
    table's shape, not its content, and the scraper in test_standalone_docs.py
    reads only rows whose second column is bold.
    """
    by_right: dict[str, list[str]] = {}
    for wrong, right in _wrong_glass_spellings().items():
        by_right.setdefault(right, []).append(wrong)
    return "\n".join(
        f"| {', '.join(wrongs)} | **{right}** |"
        for right, wrongs in by_right.items()
    )


def _garnishes() -> str:
    return _grouped(_garnish_vocab().get("canonical") or {}, tick=False)


def _method_steps() -> str:
    return _grouped(_methods().get("canonical") or {}, tick=True)


def _measures() -> str:
    """The units an amount may carry that are NOT converted to millilitres.

    Straight from `measures.non_volumetric` in ingredients.yml, so the day
    `to top` or `to rinse` is declared the document teaches it. The prose the
    document had before this block listed `1 barspoon`, `1 whole egg`,
    `1 sugar cube` and `top` -- three of which are undeclared units that
    test_every_amount_is_readable_as_a_quantity rejects outright. That is the
    exact failure the one-way guard could not see: the document was not stale,
    it was inventing.
    """
    measures = (_vocab().get("measures") or {})
    return _dots(measures.get("non_volumetric") or [], tick=True)


def renderers() -> dict:
    """Block name -> the function that renders it.

    THE TAG BLOCKS ARE BUILT FROM THE TAXONOMY'S OWN GROUPS, not named here.
    The food document glosses each group in prose ("what you feel like eating,
    a craving"), so the groups cannot live inside one block -- and a group
    added to taxonomy.yml must still be loud rather than silently missing, so
    `required_blocks()` below asks for one block per declared group.
    """
    out = {
        "stars": _stars,
        "source_types": _source_types,
        "accents": _accents,
        "no_accent": _no_accents,
        "glass": _glass_spellings,
        "glass_corrections": _glass_corrections,
        "garnish": _garnishes,
        "method": _method_steps,
        "measures": _measures,
    }
    for group in _food_taxonomy()["tags"]:
        out[f"tags:{group}"] = (lambda g: lambda: _tags(g))(group)
    return out


def required_blocks() -> dict:
    """Which blocks each document must carry.

    A manifest, not a vocabulary: it says where a block belongs, and every
    block's CONTENT still comes from the loaders above. The tag groups are
    derived so that declaring a third group in taxonomy.yml fails this until
    the food document has a section for it -- the one direction the old guard
    could not point in.
    """
    tags = {f"tags:{group}" for group in _food_taxonomy()["tags"]}
    return {
        FOOD_DOC: tags | {"stars", "source_types", "accents", "no_accent"},
        COCKTAIL_DOC: {
            "glass", "glass_corrections", "garnish", "method", "measures",
            "accents",
        },
    }


# =============================================================================
# THE PASS ITSELF
# =============================================================================

def render(path: Path) -> tuple[str, list[str]]:
    """(the document with every block re-rendered, problems found).

    A problem is structural -- an unknown block name, or a required block the
    document does not carry. Content differences are not problems here; they
    are what the caller diffs.
    """
    text = path.read_text(encoding="utf-8")
    known = renderers()
    problems = []
    seen = set()

    def replace(match):
        name = match.group("name")
        seen.add(name)
        if name not in known:
            problems.append(
                f"{path.name}: no renderer for block `vocab:{name}`. Either "
                f"the marker is a typo or the block wants a function in "
                f"scripts/build_ingest_vocab.py."
            )
            return match.group(0)
        body = known[name]().rstrip("\n")
        return (f"<!-- vocab:{name} start -->\n{body}\n"
                f"<!-- vocab:{name} end -->")

    out = MARKER.sub(replace, text)

    for name in sorted(required_blocks()[path] - seen):
        problems.append(
            f"{path.name}: required block `vocab:{name}` is missing. Add the "
            f"marker pair where that vocabulary belongs; the generator fills "
            f"it in."
        )
    return out, problems


def diff(path: Path) -> tuple[str, list[str]]:
    """(a unified diff of what --write would do, problems)."""
    current = path.read_text(encoding="utf-8")
    wanted, problems = render(path)
    if current == wanted:
        return "", problems
    rel = str(path.relative_to(ROOT))
    return "".join(difflib.unified_diff(
        current.splitlines(keepends=True),
        wanted.splitlines(keepends=True),
        fromfile=f"a/{rel}", tofile=f"b/{rel}",
    )), problems


def check() -> tuple[str, list[str]]:
    """(every document's diff, every document's problems).

    The test in test_standalone_docs.py runs exactly this, so `--check` and the
    suite cannot disagree about what stale means.
    """
    diffs, problems = [], []
    for path in required_blocks():
        d, p = diff(path)
        diffs.append(d)
        problems += p
    return "".join(diffs), problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="print a diff and exit 1 if any block is stale")
    mode.add_argument("--write", action="store_true",
                      help="rewrite every block in place")
    args = parser.parse_args(argv)

    if args.check:
        text, problems = check()
        for problem in problems:
            print(problem)
        if text:
            print(text, end="")
        if text or problems:
            print("\nStale. Run: python3 scripts/build_ingest_vocab.py --write")
            return 1
        print("Every vocabulary block matches its generator.")
        return 0

    changed, problems = [], []
    for path in required_blocks():
        wanted, p = render(path)
        problems += p
        if wanted != path.read_text(encoding="utf-8"):
            path.write_text(wanted, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))
    for problem in problems:
        print(problem)
    print("Rewrote: " + (", ".join(changed) if changed else "nothing"))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
