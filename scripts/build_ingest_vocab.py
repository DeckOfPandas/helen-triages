#!/usr/bin/env python3
"""Render the vocabulary blocks inside the two standalone ingest documents.

    python3 scripts/build_ingest_vocab.py --check    # diff, exit 1 if stale
    python3 scripts/build_ingest_vocab.py --write    # rewrite the blocks

One of the two flags is required. `--check` prints a unified diff and any
structural problem, and exits 1 if there is either. `--write` rewrites the
blocks in place and exits 1 only on a structural problem. The test in
tests/test_standalone_docs.py calls `check()`, so the flag and the suite
cannot disagree about what stale means.

`model_instructions/INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md` are
read by a Claude with no checkout, so each prints the closed vocabularies as
literal text. That duplication is generated, so that a document cannot print
less than is declared: a reader who cannot see a valid string "corrects" it to
a near one. Each vocabulary sits between a pair of HTML-comment markers:

    <!-- vocab:garnish start -->
    **Citrus peel:** lemon twist · lemon twist (discarded) · ...
    <!-- vocab:garnish end -->

It writes only between marker pairs. Everything outside one is hand-written
prose and stays under the one-way tests in tests/test_standalone_docs.py.
`required_blocks()` says which blocks each document must carry; a marker with
no renderer, or a required block with no marker, is a structural problem.

The rules:

  - Every block is sourced from a loader imported from `tests/`, never from a
    list typed here. A generator carrying its own copy of a vocabulary would
    write a stale document that then passes the drift check. An import that
    breaks because a loader moved is the mechanism working.
  - The rendering functions emit the shapes the scrapers in
    tests/test_standalone_docs.py parse: middle-dot separators, `**Group:**`
    prefixes, backticked terms, the two-column correction table. If a scraper
    stops matching, the generator's output is what is wrong.
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
    _garnish_vocab, _glasses, _methods, _serve_vocab, _sources_data, _vocab,
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


# --- Rendering: the shapes the scrapers in test_standalone_docs.py parse ---

def _wrap(atoms, prefix: str = "") -> str:
    """Hard-wrap at WIDTH, breaking only between entries and never inside one.

    Every entry is a string a reader copies into a file, and `textwrap.fill`
    wraps on any space, so it would split "oily fish" inside its backticks.
    The unit of wrapping is one entry plus its trailing separator.
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

    Derived, not declared: every group key in garnish.yml and methods.yml is
    lowercase words joined by underscores. A group whose display name needs a
    capital in the middle would need a label map in the data file.
    """
    return key.replace("_", " ").capitalize()


def _grouped(groups: dict, tick: bool) -> str:
    """One paragraph per group, `**Label:** a · b · c`, blank line between.

    Group order is the data file's own; alphabetising would churn the document
    the day a group is renamed.
    """
    out = []
    for key, members in groups.items():
        if not isinstance(members, list):
            continue
        out.append(_dots(members, tick=tick, prefix=f"**{_label(key)}:**"))
    return "\n\n".join(out)


# --- The blocks: one function each, every one over an imported loader ---

def _tags(group: str) -> str:
    return _commas(_food_taxonomy()["tags"][group])


def _stars() -> str:
    return _commas(_food_taxonomy()["star_ingredients"])


def _source_types() -> str:
    """The declared citation types, `VALID_TYPES`, sorted because it is a set.

    The block is named `source_types`, plural, and must stay so.
    `test_invisible_keys_are_really_invisible` in test_front_matter.py scans
    every file under `scripts/` for the singular key name, docstrings
    included, and fails if it appears. See SOURCE_ATTRIBUTION_SPEC.md for the
    field itself.
    """
    return _dots(sorted(VALID_TYPES), tick=True)


def _accents() -> str:
    """The curated accented spellings, as the words a reader should type.

    The map is unaccented -> accented and the document wants the right-hand
    side; the left-hand side is a lookup key, not a word anybody writes.
    """
    return _dots(_accented_words().values())


def _no_accents() -> str:
    """The words that deliberately keep no accent.

    Read straight from the data file: the suite's `_accented_words()` returns
    only the `words:` map. `SHARED_DATA_DIR` is imported so the path is stated
    in one place.
    """
    data = yaml.safe_load(
        (SHARED_DATA_DIR / "accented_words.yml").read_text(encoding="utf-8")
    ) or {}
    return _dots(data.get("no_accent") or [])


def _wrong_glass_spellings() -> dict:
    return _glasses().get("canonical_glasses") or {}


def _glass_spellings() -> str:
    """Every glass spelling a drink may write.

    `icons:` maps both canonical names and aliases; `canonical_glasses` maps
    the spellings that get corrected. The block prints the difference: every
    `icons:` key that is not corrected away. An alias absent from
    `canonical_glasses` is undecided, not blessed
    (test_drinks_use_the_canonical_glass_spelling), and is printed because a
    drink writing one passes the suite.
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
    """The literal groups, then the `shapes:` groups with their `<X>` slot
    printed as-is. The prose around the block says what the slot means."""
    spec = _methods()
    literal = _grouped(spec.get("canonical") or {}, tick=True)
    shapes = spec.get("shapes") or {}
    if not shapes:
        return literal
    return literal + "\n\n" + _grouped(
        {f"with_a_slot_{k}": v for k, v in shapes.items()}, tick=True)


def _measures() -> str:
    """The units an amount may carry that are not converted to millilitres.

    Straight from `measures.non_volumetric` in ingredients.yml. A unit not
    declared there is rejected by test_every_amount_is_readable_as_a_quantity,
    so the document must not teach one.
    """
    measures = (_vocab().get("measures") or {})
    return _dots(measures.get("non_volumetric") or [], tick=True)


def _serve_ice() -> str:
    """The `serve.ice` vocabulary, with what each value means.

    The glosses come from the data: each value's note in serve.yml opens with
    a sentence that is its definition, and that first sentence is what prints.
    """
    ice = (_serve_vocab().get("ice") or {})
    rows = []
    for value, note in ice.items():
        first = re.split(r"(?<=[.!?])\s", str(note).strip())[0]
        rows.append(f"`{value}` — {first}")
    return "\n".join(f"- {r}" for r in rows)


def _to_serve() -> str:
    """The `to_serve` items, grouped as serve.yml groups them (#1256)."""
    return _grouped(_serve_vocab().get("to_serve") or {}, tick=True)


def _sources() -> str:
    """The publications a drink's `source` names, and their canonical spelling.

    Not a closed vocabulary, and it must not become one: a drink's `source` is
    optional, and an empty one is correct. This block fixes spelling only
    (`Difford's`, not `Difford's Guide`): a canonical name and its known
    aliases, as `bottles.yml` does for bottles. A compound attribution naming
    two sources, or free text, is not a variant and is not listed.
    """
    sources = _sources_data().get("publications") or {}
    rows = []
    for name, entry in sources.items():
        aliases = (entry or {}).get("aliases") or []
        tail = f" (also seen as {', '.join(aliases)})" if aliases else ""
        rows.append(f"`{name}`{tail}")
    return "\n".join(f"- {r}" for r in rows)


def _generics() -> str:
    """Every declared generic, grouped by the list that declares it.

    Derived from the file's own shape as `_declared_generics` in
    tests/test_cocktails.py does it: a `<family>_characters` list is
    characters, not generics, and `NOT_GENERIC_LISTS` names the lists that
    refer to the vocabulary. Both tests are imported, not restated.

    `hers_to_apply` is a mapping, so it is skipped, and must be: a style Helen
    has reserved for herself must not be offered to a session
    (`test_no_drink_uses_a_generic_that_is_helens_to_apply`).
    """
    from test_cocktails import NOT_GENERIC_LISTS, _is_character_list

    vocab = _vocab()
    groups = {
        key: value for key, value in vocab.items()
        if isinstance(value, list) and value
        and key not in NOT_GENERIC_LISTS
        and not _is_character_list(key)
        and not key.startswith("retired_")
    }
    return _grouped(groups, tick=True)


def renderers() -> dict:
    """Block name -> the function that renders it.

    The tag blocks are built from the taxonomy's own groups, one block per
    group, because the food document glosses each group in prose.
    `required_blocks()` asks for each, so a new group cannot go missing
    silently.
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
        "generics": _generics,
        "serve_ice": _serve_ice,
        "to_serve": _to_serve,
        "sources": _sources,
    }
    for group in _food_taxonomy()["tags"]:
        out[f"tags:{group}"] = (lambda g: lambda: _tags(g))(group)
    return out


def required_blocks() -> dict:
    """Which blocks each document must carry.

    A manifest, not a vocabulary: every block's content still comes from the
    loaders above. The tag groups are derived, so declaring another group in
    taxonomy.yml fails `--check` until the food document has a section for it.
    """
    tags = {f"tags:{group}" for group in _food_taxonomy()["tags"]}
    return {
        FOOD_DOC: tags | {"stars", "source_types", "accents", "no_accent"},
        COCKTAIL_DOC: {
            "glass", "glass_corrections", "garnish", "method", "measures",
            "accents", "generics", "serve_ice", "to_serve", "sources",
        },
    }


# --- The pass itself ---

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
