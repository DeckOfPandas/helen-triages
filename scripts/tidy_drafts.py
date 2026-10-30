#!/usr/bin/env python3
"""Tidy `_food_drafts/` and `_cocktail_drafts/` -- the mechanical half only.

Run it through `/tidy-drafts`: `.claude/commands/tidy-drafts.md` is the
procedure (branch the drafts repo, report, apply, run pytest, commit there).
This file is the engine, and each rule's exact behaviour is in the docstring
of its `fix_*` function.

    python3 scripts/tidy_drafts.py                  # report, change nothing
    python3 scripts/tidy_drafts.py --apply          # write the fixes
    python3 scripts/tidy_drafts.py --only quoting,meta
    python3 scripts/tidy_drafts.py --site cocktails # one collection only
    python3 scripts/tidy_drafts.py --apply --allow-dirty
    python3 scripts/tidy_drafts.py --drafts-dir <copy> --site food

`--only` takes a comma-separated subset of RULE_NAMES: `notes`, `quoting`,
`dashes`, `typography`, `units`, `accents` and `order` run on both collections,
`meta`, `size` and `incidentals` on food alone, `titles` on cocktails alone.

It reads every `.md` with front matter under the two drafts folders (a file
without front matter, such as a README, is named and skipped),
`_data/accented_words.yml`, and the rule definitions in `tests/`. It writes
only with `--apply`, in place, and never through a YAML dumper: a dumper loses
comment placement, key order and the `[""]` shape `method_short` depends on.
`--apply` refuses while a drafts repo has uncommitted changes unless
`--allow-dirty` is given, so that the diff afterwards is this script's work
alone. An absent drafts repo is announced and skipped; both absent is a
refusal. `--drafts-dir` points one collection's rules at another directory (a
copy to prove a pass on) and needs `--site`.

Every rule is imported from the suite, never re-typed, so the script cannot
tidy a file into a shape the tests reject.

WHAT IT DOES

On both collections:

  - quotes the scalar string fields, and never a `meta:` boolean: a quoted
    flag is the STRING "true", which the publish gate holds back;
  - `3-4` -> an en dash, `--` -> an em dash, `->` -> an arrow;
  - `15ml` -> `15 ml`, imperial units included, never a temperature;
  - accents from `_data/accented_words.yml`;
  - an empty `notes:` becomes one empty label/text pair, and a note with text
    and an empty label is labelled `QQ` (#1258).

On food alone: `main_ingredients` and `tags` flow quoting, the quoting of a
group's `- name:`, the #429 `meta:` block (retired keys dropped, flags in
`META_ORDER`), the #577 size word (`2` / `large onions` -> `2 large` /
`onions`), and the #1356 tin-and-pan incidentals ("butter, for greasing" gains
`incidental: true`; ", plus extra for the tin" is trimmed off a real line),
and the `meta:` block moved whole to directly under `title:`.

On cocktails alone: Title Case for `title` (#1089: capitals only, nothing is
lowered, a qualifier in brackets is left as written) and top-level keys in
page order (#1213: whole blocks move and no line is edited).

WHAT IT WILL NOT DO

  - Reword a `QQ` line: that is the source's wording awaiting Helen's
    rewrite. On food the four formatting rules (dashes, typography, units,
    accents) do reach it, so she rewrites from text already in house style;
    no other rule does (MANUAL §5). A `QQ Claude` line is ours and is tidied
    like any other prose.
  - Touch `source:`: a citation is spelled as the publication spells itself,
    so "Cafe Delites" is correct and accenting it is a misquote.
  - Touch a slug or filename, rename a file, or retitle one. A draft's title
    disagreeing with its slug is not reported either: the title is still the
    source's while the slug is already the dish
    (`test_title_and_slug_dont_diverge` in test_drafts.py's NOT_FOR_DRAFTS).
  - Resolve a content judgement: which milk, which flour, which mustard,
    whether an oven figure is the fan one, whether a note's first word is a
    proper noun. Those rules are listed in NOT_FOR_DRAFTS and each needs Helen
    or her source material.
  - Invent a missing `meta:` flag. It is reported.

A COCKTAIL'S BOUNDARY IS NARROWER

Most of a drink's front matter is a closed vocabulary, somebody else's words,
or a number. Every rule except `notes` and `order` reaches only Helen's own
prose (`title`, `tagline`, `snippet`, `to_serve`, a `notes` entry's label and
text, an ingredient's `note`) and fixes there only what
`tests/test_cocktails.py` demands. On a cocktail it never touches:

  - a `QQ` line, by the suite's predicate (`conftest.checkable_text`), which
    sees a marker behind a key (`tagline: "QQ ..."`). See `drink_editable`.
  - `suggestion`, `source` or `source_url`: somebody else's words
    (`test_cocktails.VERBATIM_KEYS`), which the drinks suite blanks too. The
    one exception is quoting a bare `source:` or `source_url:`, which changes
    no word and which `test_drink_scalar_fields_are_quoted` requires.
  - `glass`, `garnish`, `mood`, `generic` or `character`: closed vocabularies
    declared in `_data/cocktails/`. A dash or an accent written into one is a
    change to the vocabulary, which is a question for `_data/`.
  - a `method` step: `_data/cocktails/methods.yml` holds the canonical steps
    and a `proposals` mechanism for changing one, so editing a step in a drink
    file de-canonicalises it.
  - an `amount`: a `QQ` note may quote the amount back verbatim
    (`amount: "Top (30-45) ml"`), and en-dashing the amount desynchronises the
    note from the value. The drinks suite does check amounts, so a range in
    one is reported and left; see `report_drink_faults_left_alone`.
  - a drink's `meta:` block, which is a different list in a different order
    (`test_cocktails.META_KEYS_IN_ORDER`).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from functools import partial
from pathlib import Path
from types import SimpleNamespace

# Read-only, and only by `fix_key_order`, to PARSE both sides of a reorder and
# compare them. Nothing here is ever written through a dumper.
import yaml

ROOT = Path(__file__).resolve().parent.parent
FOOD_DRAFTS = ROOT / "_food_drafts"
COCKTAIL_DRAFTS = ROOT / "_cocktail_drafts"
ACCENTS = ROOT / "_data" / "accented_words.yml"

FRONT_MATTER = re.compile(r"\A(---\n)(.*?\n)(---\n?)", re.S)

# --- Every rule is imported from the suite, never re-typed here ---
# A fixer carrying its own copy of the contract can tidy files into a shape the
# tests reject while its own report stays green. Importing also keeps the
# INVISIBLE_KEYS names out of this file, which
# test_invisible_keys_are_really_invisible scans `scripts/` for.
sys.path.insert(0, str(ROOT / "tests"))
from test_front_matter import (  # noqa: E402
    META_ORDER, RETIRED, SCALAR_STRING_FIELDS,
)
# `_checkable` is private to the drinks suite and imported on purpose: it is
# the suite's definition of which lines of a drink these rules look at. A copy
# that disagreed would report a collection clean while the suite failed on it.
from conftest import (  # noqa: E402
    checkable_text, degreeless_temperatures, spelling_problems,
)
from test_cocktails import (  # noqa: E402
    DRINK_SCALAR_FIELDS, TOP_LEVEL_KEYS_IN_ORDER, VERBATIM_KEYS,
    _checkable as drink_suite_scope, keys_out_of_page_order, title_cased,
)
# The size-word pattern is the recipe rule's own (#149, #577).
from test_style import _LEADING_SIZE_WORD  # noqa: E402
# The tin-and-pan incidentals predicate (#1356) and its word list in data.
from test_taxonomy import incidental_verdict  # noqa: E402

FLOW_FIELDS = ["main_ingredients", "tags"]

# The retired keys that live under `meta:`, derived from the suite's RETIRED.
# Anything retired at the top level is a different rule and not this script's.
META_RETIRED = [k for k in RETIRED if k not in META_ORDER]

# Optional and additive, and legitimate on a draft alongside the three (#418).
# The recipe-side rule forbids it outright, which is why it is named here and
# not in META_ORDER.
META_OPTIONAL = ["claude_rewritten"]

ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER_RANGE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)(?![\d.])")
# A QQ line is somebody else's wording: on food only the formatting rules
# reach it, and on a drink none does (MANUAL §5). A key may sit in front of the
# marker (`text: "QQ - ..."`, `tagline: "QQ ..."`). `QQ Claude` is excluded:
# that line is our paraphrase. Mirrors `_QQ_LINE` in tests/conftest.py.
QQ_LINE = re.compile(r"^\s*(-\s*)?(?:[a-z_]+:\s*)?[\"']?QQ\b(?!\s+Claude\b)")


# --- Reading the corpus ---

def load_drafts(root):
    """One collection's drafts and its skipped files; `(None, [])` if absent.

    Absent and empty are different answers. One absent root is not fatal: the
    two collections are separate private repos and a worktree often has only
    one, so `main()` refuses when neither is here. A present root with no
    `.md`, or none with front matter, exits instead of reporting an empty
    corpus clean. A `.md` with no front matter (a README) is not a draft and
    is returned as skipped, so that no fixer rewrites its prose.
    """
    if not root.is_dir():
        return None, []
    md = sorted(root.rglob("*.md"))
    if not md:
        sys.exit(
            f"{root.name}/ exists but holds no .md files. That is not the "
            f"absent-repo case, so either the checkout is broken or this glob "
            f"has gone stale. Refusing to report success over an empty corpus."
        )
    files = [p for p in md if has_front_matter(p.read_text(encoding="utf-8"))]
    skipped = [p for p in md if p not in files]
    if not files:
        sys.exit(
            f"{root.name}/ holds {len(md)} .md file(s) and not one has front "
            f"matter. A whole collection of prose is not the shape this script "
            f"reads; refusing rather than reporting {len(md)} files clean."
        )
    return files, skipped


def split_front_matter(text):
    m = FRONT_MATTER.match(text)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3), text[m.end():]


def is_qq(line):
    return bool(QQ_LINE.match(line))


def has_front_matter(text):
    return FRONT_MATTER.match(text) is not None


# --- Which lines of a drink this script may rewrite ---
# The module docstring gives the reason for each key. The alternation is sorted
# longest first because `source` and `source_url` share a prefix and Python's
# alternation takes the first match, not the longest.
DRINK_VOCABULARY_KEYS = ("glass", "garnish", "mood", "generic", "character")
DRINK_NEVER_EDIT = tuple(VERBATIM_KEYS) + DRINK_VOCABULARY_KEYS \
                   + ("amount", "method")
DRINK_NEVER_EDIT_LINE = re.compile(
    r"^(?:-\s*)?(?:"
    + "|".join(sorted(DRINK_NEVER_EDIT, key=len, reverse=True))
    + r"):(?P<value>.*)$"
)


def drink_editable(text):
    """One bool per line: may this script rewrite it?

    The QQ test is the suite's: `conftest.checkable_text` is asked which lines
    it blanked, so a marker behind a key (`tagline: "QQ"`) is seen. `QQ_LINE`
    above is not consulted here.

    A never-edit key with an empty value opens a block, and the indented lines
    under it go too (`method:`, `glass:`, a two-bottle `suggestion:`).
    Matching the key line alone would leave the values under it in scope.
    """
    lines = text.split("\n")
    blanked = checkable_text(text).split("\n")
    editable, block_indent = [], None
    for raw, checked in zip(lines, blanked):
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        if block_indent is not None:
            if not stripped or indent > block_indent:
                editable.append(False)
                continue
            block_indent = None
        if raw and not checked:
            editable.append(False)          # a QQ line, by the suite's predicate
            continue
        match = DRINK_NEVER_EDIT_LINE.match(stripped)
        if match:
            editable.append(False)
            if not match.group("value").strip():
                block_indent = indent
            continue
        editable.append(True)
    return editable


def not_qq(text):
    """One bool per line: not a `QQ` line, by the suite's predicate. Quoting a
    verbatim value (`source:`) changes none of its words, so this is the mask
    for that one rule."""
    return [not (raw and not checked) for raw, checked in
            zip(text.split("\n"), checkable_text(text).split("\n"))]


def only_where_editable(fixer, mask=drink_editable):
    """Wrap a line-wise fixer so it sees, and answers for, the lines `mask`
    allows (by default `drink_editable`'s).

    The rest are blanked, not dropped, so a line's index survives; the fixer's
    answer is taken where the line was editable and the original elsewhere.
    Only a line-wise fixer may be wrapped. One that changes the line count
    would be spliced against the wrong lines into a file that still parses,
    so that raises.
    """
    def run(text, path):
        editable = mask(text)
        lines = text.split("\n")
        masked = "\n".join(l if ok else "" for l, ok in zip(lines, editable))
        out, notes = fixer(masked, path)
        fixed = out.split("\n")
        if len(fixed) != len(lines):
            raise AssertionError(
                f"{getattr(fixer, 'func', fixer).__name__} changed the line "
                f"count of {path} ({len(lines)} -> {len(fixed)}). Only a "
                f"line-wise fixer may be wrapped; see only_where_editable."
            )
        return ("\n".join(f if ok else o
                          for o, f, ok in zip(lines, fixed, editable)), notes)
    return run


# --- Fixers: (text, path) -> (new_text, [what changed]) ---

def fix_scalar_quoting(text, path, fields=None):
    """Quote the collection's scalar string fields; `fields` is imported.

    Food's is `test_front_matter.SCALAR_STRING_FIELDS`, a drink's is
    `test_cocktails.DRINK_SCALAR_FIELDS`. Neither may contain a boolean:
    quoting a `meta:` flag makes it the STRING "true", which the publish gate
    reads as neither true nor false, so the page is held back. A value
    containing a double quote is reported, not escaped.
    """
    fields = SCALAR_STRING_FIELDS if fields is None else fields
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    changed, out = [], []
    for line in fm.split("\n"):
        m = re.match(rf"^({'|'.join(fields)}):([ \t]*)(.+)$", line)
        if m:
            field, gap, val = m.group(1), m.group(2), m.group(3).rstrip()
            trailing = m.group(3)[len(val):]
            if val and not val.startswith(("[", "{", '"')):
                # A value containing a double quote would need escaping, which
                # is a judgement about the text rather than about its quoting.
                if '"' in val:
                    changed.append(f"SKIPPED {field}: contains a double quote")
                else:
                    line = f"{field}:{gap}\"{val}\"{trailing}"
                    changed.append(f"{field}: {val} -> \"{val}\"")
        out.append(line)
    return open_ + "\n".join(out) + close + body, changed


def fix_group_name_quoting(text, path):
    """A food group's `- name:` is quoted, like every other string in the file.

    `- name:` at the start of a list item is a group and nothing else in a
    food file. A value already quoted either way is left alone, and one
    containing a double quote is reported, not escaped. DECISIONS §4.
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    changed, out = [], []
    for line in fm.split("\n"):
        m = re.match(r"^([ \t]*- name:)([ \t]*)(.+)$", line)
        if m:
            val = m.group(3).rstrip()
            trailing = m.group(3)[len(val):]
            if val and not val.startswith(('"', "'")):
                if '"' in val:
                    changed.append(f"SKIPPED group name: contains a double quote: {val}")
                else:
                    line = f"{m.group(1)}{m.group(2)}\"{val}\"{trailing}"
                    changed.append(f"group name: {val} -> \"{val}\"")
        out.append(line)
    return open_ + "\n".join(out) + close + body, changed


def _split_flow(inner):
    """Split a flow sequence on commas that are not inside quotes."""
    parts, buf, quote = [], "", None
    for ch in inner:
        if quote:
            if ch == quote:
                quote = None
            buf += ch
        elif ch in "\"'":
            quote, buf = ch, buf + ch
        elif ch == ",":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts


def fix_flow_quoting(text, path):
    """Quote every entry of food's `main_ingredients` and `tags` flow lists."""
    changed = text
    notes = []
    for field in FLOW_FIELDS:
        m = re.search(rf"^{field}:\s*\[(.*?)\]\s*$", changed, re.M)
        if not m:
            continue
        entries = _split_flow(m.group(1))
        rebuilt, touched = [], []
        for raw in entries:
            e = raw.strip()
            if not e:
                continue
            if e.startswith('"') and e.endswith('"'):
                rebuilt.append(e)
            elif '"' in e:
                rebuilt.append(e)
                touched.append(f"SKIPPED {field} entry with a quote: {e}")
            else:
                rebuilt.append(f'"{e}"')
                touched.append(f"{field}: {e} -> \"{e}\"")
        if touched:
            changed = changed[:m.start()] + f"{field}: [{', '.join(rebuilt)}]" \
                      + changed[m.end():]
            notes += touched
    return changed, notes


def fix_en_dashes(text, path, skip_qq=True):
    """`3-4 mins` -> `3–4 mins`, skipping ISO dates, and QQ lines unless
    `skip_qq` is off, as it is on food (MANUAL §5).
    """
    out, changed = [], []
    for line in text.split("\n"):
        if skip_qq and is_qq(line):
            out.append(line)
            continue
        blanked = ISO_DATE.sub(lambda m: "\x00" * len(m.group()), line)
        hits = list(NUMBER_RANGE.finditer(blanked))
        if hits:
            new = line
            for m in reversed(hits):
                new = new[:m.start()] + f"{m.group(1)}–{m.group(2)}" + new[m.end():]
            changed.append(f"{line.strip()[:60]} -> en dash")
            line = new
        out.append(line)
    return "\n".join(out), changed


TYPOGRAPHY_FIXES = [
    (re.compile(r"(?<!-)--(?!-)"), "—", "double hyphen -> em dash"),
    (re.compile(r"->"), "→", "ASCII arrow -> →"),
]


def fix_typography(text, path, skip_qq=True):
    """`--` -> an em dash and `->` -> an arrow; QQ lines as `fix_en_dashes`."""
    out, changed = [], []
    for line in text.split("\n"):
        if skip_qq and is_qq(line):
            out.append(line)
            continue
        for pattern, replacement, label in TYPOGRAPHY_FIXES:
            if pattern.search(line):
                line = pattern.sub(replacement, line)
                changed.append(f"{label} in: {line.strip()[:60]}")
        out.append(line)
    return "\n".join(out), changed


# A number and its unit take a space, imperial included (DECISIONS §5). The
# alternation is sorted longest first in code: a short-first list turns `2kg`
# into `2k g`, which parses and reads almost right. Deliberately absent: a
# bare `l` (`1ltr` would be mangled), `mins` (a duration is not a measure),
# and temperatures, where `180C` wants a degree sign and is a reported rule.
UNITS = [
    # metric
    "kg", "g", "ml", "cl", "cm", "mm",
    # imperial
    "inches", "inch", "in", "lbs", "lb", "fl oz", "oz", "pts", "pt",
    # spoons
    "tbsp", "tbs", "tsp",
]
UNIT_SPACE = re.compile(
    r"(?<=\d)(" + "|".join(sorted(UNITS, key=len, reverse=True)) + r")\b")


def fix_unit_spacing(text, path, skip_qq=True):
    """`15ml` -> `15 ml`; QQ lines as `fix_en_dashes`.

    On a drink this runs through `only_where_editable`, so a cocktail's
    `amount` is never touched; the module docstring says why. Food's amounts
    are fixed.
    """
    out, changed = [], []
    for line in text.split("\n"):
        if skip_qq and is_qq(line):
            out.append(line)
            continue
        if UNIT_SPACE.search(line):
            new = UNIT_SPACE.sub(r" \1", line)
            changed.append(f"unit space in: {line.strip()[:60]}")
            line = new
        out.append(line)
    return "\n".join(out), changed


def _accent_map():
    """The curated unaccented->accented map, and the words that keep no accent.

    Read as text, not through a YAML parser: the file is a flat two-block
    mapping, `words:` and `no_accent:`.
    """
    words, no_accent, section = {}, set(), None
    for line in ACCENTS.read_text(encoding="utf-8").split("\n"):
        if re.match(r"^words:", line):
            section = "words"
            continue
        if re.match(r"^no_accent:", line):
            section = "no"
            continue
        if re.match(r"^\S", line):
            section = None
            continue
        body = line.split("#")[0].strip()
        if not body:
            continue
        if section == "words":
            m = re.match(r"^([\w'-]+):\s*(\S+)", body)
            if m:
                words[m.group(1)] = m.group(2)
        elif section == "no" and body.startswith("- "):
            no_accent.add(body[2:].strip())
    if not words:
        sys.exit(
            "accented_words.yml yielded no `words:` entries. Refusing to run "
            "the accent pass over an empty reference set -- that would report "
            "every draft clean while checking nothing."
        )
    return words, no_accent


def fix_accents(text, path, skip_qq=True, _cache={}):
    """Prose only. Never `source:` or a slug; QQ lines as `fix_en_dashes`."""
    if "map" not in _cache:
        _cache["map"] = _accent_map()
    words, no_accent = _cache["map"]

    out, changed = [], []
    for line in text.split("\n"):
        if (skip_qq and is_qq(line)) or re.match(r"^source(_url)?:", line):
            out.append(line)
            continue
        for plain, accented in words.items():
            if plain in no_accent:
                continue
            pattern = re.compile(rf"\b{re.escape(plain)}\b", re.I)
            if pattern.search(line):
                def keep_case(m):
                    return accented.capitalize() if m.group()[:1].isupper() else accented
                line = pattern.sub(keep_case, line)
                changed.append(f"{plain} -> {accented}")
        out.append(line)
    return "\n".join(out), changed


def fix_meta_block(text, path):
    """The #429 migration: drop the retired keys, put the flags in order.

    The order is `test_front_matter.META_ORDER`, asserted by
    test_meta_block_is_exactly_the_three_flags_in_order. An optional
    `claude_rewritten` sits after the first flag.

    A missing flag is reported, never invented. `awaiting_fix` fails closed,
    so writing `false` in asserts the recipe is fit to publish, which is
    Helen's to say. An unrecognised key leaves the whole block alone.
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    lines = fm.split("\n")

    start = next((i for i, l in enumerate(lines) if l.rstrip() == "meta:"), None)
    if start is None:
        return text, []
    # `^  \S`, not "indented or blank". Splitting the front matter on "\n"
    # leaves a trailing "", and a scan that accepts blanks swallows it: the
    # rebuilt block eats the final newline and the file ends
    # `proofread: false---`, which no longer parses as front matter.
    end = start + 1
    while end < len(lines) and re.match(r"^  \S", lines[end]):
        end += 1

    block = {}
    for line in lines[start + 1:end]:
        m = re.match(r"^  ([a-z_]+):(.*)$", line)
        if m:
            block[m.group(1)] = line

    unknown = set(block) - set(META_ORDER) - set(META_RETIRED) - set(META_OPTIONAL)
    if unknown:
        return text, [f"SKIPPED: unrecognised meta key(s) {sorted(unknown)} -- "
                      f"left alone rather than guessed at"]

    changed = []
    for key in META_RETIRED:
        if key in block:
            changed.append(f"dropped meta.{key}")

    missing = [k for k in META_ORDER if k not in block]
    if missing:
        changed.append(
            f"REPORT ONLY: meta.{'/'.join(missing)} absent -- not invented, see "
            f"the docstring. The rest of the block was still tidied."
        )

    order = [META_ORDER[0]] + [k for k in META_OPTIONAL if k in block] \
            + META_ORDER[1:]
    rebuilt = [block[k] for k in order if k in block]
    if rebuilt != [block[k] for k in block]:
        changed.append("reordered to " + " -> ".join(META_ORDER))

    if not changed:
        return text, []

    lines[start + 1:end] = rebuilt
    return open_ + "\n".join(lines) + close + body, changed


# --- The size word, #577 ---
# The predicate is the test's, both halves: `_LEADING_SIZE_WORD` is imported,
# and BARE_COUNT spells the `re.fullmatch(r"\d+", amount)` that
# test_size_word_is_with_the_count_not_the_item has inline. Two lines change
# per hit, each keeping its indentation, gap and quote style;
# `tests/test_tidy_drafts.py` proves the rest of the file byte for byte.
BARE_COUNT = re.compile(r"\d+")
KEYED_LINE = re.compile(
    r"^(?P<lead>\s*(?:-\s+)?)(?P<key>amount|item):(?P<gap>[ \t]*)"
    r"(?P<value>.*?)(?P<trail>[ \t]*)$"
)
LIST_ENTRY = re.compile(r"^(?P<dash>\s*-\s+)\S")
# What a bare (unquoted) scalar may not start with -- the YAML indicators.
YAML_INDICATORS = set("-?:,[]{}#&*!|>'\"%@`")


def _ingredient_pairs(lines):
    """(item line index, amount line index or None) for every list entry that
    carries an `item:` key of its own.

    An entry is a `- ` line plus the lines indented deeper than its dash; its
    own keys sit at the column the dash line's key starts in. That is what
    stops an `ingredient_groups:` group entry, which spans every item under
    it, from claiming the first item's lines.
    """
    for i, line in enumerate(lines):
        m = LIST_ENTRY.match(line)
        if not m:
            continue
        indent = len(m.group("dash")) - len(m.group("dash").lstrip())
        col = len(m.group("dash"))
        found = {}
        j = i
        while j < len(lines):
            probe = lines[j]
            if j > i and probe.strip() and len(probe) - len(probe.lstrip()) <= indent:
                break
            keyed = KEYED_LINE.match(probe)
            if keyed and len(keyed.group("lead")) == col:
                found.setdefault(keyed.group("key"), j)
            j += 1
        if "item" in found:
            yield found["item"], found.get("amount")


def _unwrap(value):
    """(inner text, quote char or '') -- or None when rewrapping is not safe."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        if value[0] in inner or "\\" in inner:
            return None
        return inner, value[0]
    if value[:1] in ("\"", "'") or " #" in value:
        return None
    return value, ""


def _rebuild(keyed, value):
    return (keyed.group("lead") + keyed.group("key") + ":" + keyed.group("gap")
            + value + keyed.group("trail"))


def fix_size_words(text, path):
    """`amount: "2"` + `item: "large onions"` -> `amount: "2 large"` + `item: "onions"`.

    Only where the suite's predicate fires: a bare integer count beside an
    item starting with a size word. A weight or a fraction is not moved.
    Refused, each named SKIPPED in the report:

      - a remainder starting `or` (`1` / `large or 2 small onions`): a second
        count sits inside the item;
      - `baby`, which is a kind as often as a size (DECISIONS §6);
      - an escape or inner quote in either value, or a bare remainder starting
        with a YAML indicator: rewrapping is a judgement about the text.

    No `amount:`, or an empty one, is `report_size_words_with_no_count`'s.
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    lines = fm.split("\n")
    changed = []
    for item_i, amount_i in _ingredient_pairs(lines):
        item_line = lines[item_i]
        if is_qq(item_line):
            continue
        item_m = KEYED_LINE.match(item_line)
        if not _LEADING_SIZE_WORD.match(item_m.group("value").lstrip("\"'")):
            continue
        if amount_i is None or is_qq(lines[amount_i]):
            continue                    # the reporter's, not a fix
        amount_m = KEYED_LINE.match(lines[amount_i])
        amount = _unwrap(amount_m.group("value"))
        if amount is not None and not amount[0].strip():
            continue                    # empty: the reporter's, not a fix
        if amount is None or not BARE_COUNT.fullmatch(amount[0]):
            if amount is None:
                changed.append(f"SKIPPED: amount cannot be rewrapped safely: "
                               f"{amount_m.group('value')[:40]}")
            continue                    # a weight, a fraction: not this bug
        item = _unwrap(item_m.group("value"))
        if item is None:
            changed.append(f"SKIPPED: item cannot be rewrapped safely: "
                           f"{item_m.group('value')[:50]}")
            continue
        inner, quote = item
        m = _LEADING_SIZE_WORD.match(inner)
        size, rest = m.group(1), inner[m.end():]
        if size.lower() == "baby":
            changed.append(f"SKIPPED: `baby` is a kind as often as a size "
                           f"(DECISIONS §6), needs an eye: {inner[:50]}")
            continue
        if rest.lower().startswith("or "):
            changed.append(f"SKIPPED: a second count inside the item, needs "
                           f"an eye: {amount[0]} / {inner[:50]}")
            continue
        if not rest or (not quote and rest[0] in YAML_INDICATORS):
            changed.append(f"SKIPPED: the remainder is not a safe bare "
                           f"scalar: {inner[:50]}")
            continue
        new_amount = f"{amount[0]} {size}"
        lines[amount_i] = _rebuild(amount_m, f"{amount[1]}{new_amount}{amount[1]}")
        lines[item_i] = _rebuild(item_m, f"{quote}{rest}{quote}")
        changed.append(f"{amount[0]} / {inner[:40]} -> \"{new_amount}\" / "
                       f"\"{rest[:40]}\"")
    if not any(not c.startswith("SKIPPED") for c in changed):
        return text, changed
    return open_ + "\n".join(lines) + close + body, changed


ENTRY_KEY = re.compile(r"^(?P<lead>\s*(?:-\s+)?)(?P<key>[a-z_]+):")


def fix_incidentals(text, path):
    """Tin-and-pan fats and flour (#1356), by `incidental_verdict`:

      - "butter, for greasing" gains `incidental: true` as the entry's last
        key, at its keys' indentation;
      - "175 g butter, softened, plus extra for the tin" loses its ", plus ..."
        tail, keeping the item's quote style;
      - deep-frying oil loses its amount and reads "<oil>, for deep frying".

    The flag is added to a `QQ` line too, since it changes none of the source's
    words; a `QQ` line's text is never trimmed. An item that cannot be
    rewrapped safely is SKIPPED in the report.
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    lines = fm.split("\n")
    changed = []
    inserts, drops = [], []
    for item_i, amount_i in _ingredient_pairs(lines):
        item_m = KEYED_LINE.match(lines[item_i])
        col = len(item_m.group("lead"))
        start = item_i
        while start > 0 and not LIST_ENTRY.match(lines[start]):
            start -= 1
        indent = len(lines[start]) - len(lines[start].lstrip())
        end, keys = start, set()
        for j in range(start, len(lines)):
            probe = lines[j]
            if j > start and probe.strip() and len(probe) - len(probe.lstrip()) <= indent:
                break
            keyed = ENTRY_KEY.match(probe)
            if keyed and len(keyed.group("lead")) == col:
                keys.add(keyed.group("key"))
            if probe.strip():
                end = j
        item = _unwrap(item_m.group("value"))
        if item is None:
            continue
        verdict, trimmed = incidental_verdict(item[0])
        if verdict == "flag" and "incidental" not in keys:
            inserts.append((end, " " * col + "incidental: true"))
            changed.append(f"flagged incidental: {item[0][:60]}")
        elif verdict == "trim" and not is_qq(lines[item_i]):
            lines[item_i] = _rebuild(item_m, f"{item[1]}{trimmed}{item[1]}")
            changed.append(f"trimmed: {item[0][:70]} -> {trimmed[:50]}")
        elif verdict == "deep":
            if not is_qq(lines[item_i]) and item[0] != trimmed:
                quote = item[1] or '"'
                lines[item_i] = _rebuild(item_m, f"{quote}{trimmed}{quote}")
                changed.append(f"deep frying: {item[0][:60]} -> {trimmed[:60]}")
            if amount_i is not None and not is_qq(lines[amount_i]):
                amount_m = KEYED_LINE.match(lines[amount_i])
                if amount_m.group("lead").strip() == "-":
                    # The amount holds the entry's dash: the item takes it.
                    lines[amount_i] = amount_m.group("lead") + lines[item_i].lstrip()
                    drops.append(item_i)
                else:
                    drops.append(amount_i)
                changed.append(f"deep frying, amount dropped: "
                               f"{amount_m.group('value')[:30]} / {trimmed[:50]}")
    # Bottom up, so no edit moves a line another edit has yet to reach.
    edits = [(end + 1, line) for end, line in inserts] + [(i, None) for i in drops]
    for at, line in sorted(edits, key=lambda e: e[0], reverse=True):
        if line is None:
            del lines[at]
        else:
            lines.insert(at, line)
    if not changed:
        return text, changed
    return open_ + "\n".join(lines) + close + body, changed


def report_size_words_with_no_count(path, text):
    """A size word on an item with no `amount:` to carry it. Surfaced, never moved.

    `small handful of ...` is the amount, not a stray adjective. It is
    reported so that a reader of the pass's diff does not take it for a miss.
    """
    parts = split_front_matter(text)
    if not parts:
        return []
    lines = parts[1].split("\n")
    found = []
    for item_i, amount_i in _ingredient_pairs(lines):
        if is_qq(lines[item_i]):
            continue
        value = KEYED_LINE.match(lines[item_i]).group("value")
        if not _LEADING_SIZE_WORD.match(value.lstrip("\"'")):
            continue
        amount = "" if amount_i is None else \
            KEYED_LINE.match(lines[amount_i]).group("value").strip("\"' ")
        if amount:
            continue
        found.append(f"size word with no count to carry it, left in the "
                     f"item: {value.strip(chr(34))[:60]}")
    return found


# --- The notes slot, #1258 ---
# A published recipe never passes through here, so `notes: []` stays the right
# spelling for a finished page with no notes.
NOTES_KEY = re.compile(r"^notes:[ \t]*(?P<value>\[\s*\])?[ \t]*$")
NOTE_EMPTY_LABEL = re.compile(
    r"^(?P<lead>\s*(?:-\s+)?)label:[ \t]*(?:\"\"|'')?[ \t]*$")
NOTE_TEXT = re.compile(r"^\s*(?:-\s+)?text:[ \t]*(?P<value>.*?)[ \t]*$")
NOTES_PLACEHOLDER = ['notes:', '  - label: ""', '    text: ""']


def fix_notes_slot(text, path):
    """Give a draft a notes slot, and label imported note text `QQ`.

    An empty `notes:` (or `notes: []`) becomes one empty label/text pair,
    which renders as nothing. A note with text and an empty label is labelled
    `QQ`: a published recipe may not contain `QQ`, so the label stops imported
    text publishing unread. A note's text is never touched. DECISIONS §4.
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    lines = fm.split("\n")

    start = next((i for i, l in enumerate(lines) if NOTES_KEY.match(l)), None)
    if start is None:
        return text, []
    # The block is every following line that is indented or a list dash; the
    # next top-level key ends it, and so does the trailing "" that split leaves.
    end = start + 1
    while end < len(lines) and re.match(r"^(\s+\S|-\s)", lines[end]):
        end += 1

    if end == start + 1:
        lines[start:end] = NOTES_PLACEHOLDER
        return (open_ + "\n".join(lines) + close + body,
                ["empty `notes:` -> an empty {label, text} pair to type into"])
    if NOTES_KEY.match(lines[start]).group("value"):
        return text, ["SKIPPED: `notes: []` with lines under it -- left alone "
                      "rather than guessed at"]

    # One note at a time: a list dash opens it, the next dash or the end of the
    # block closes it.
    opens = [i for i in range(start + 1, end)
             if re.match(r"^\s*-\s", lines[i])] + [end]
    changed = []
    for a, b in zip(opens, opens[1:]):
        label_i = next((i for i in range(a, b)
                        if NOTE_EMPTY_LABEL.match(lines[i])), None)
        text_m = next((m for m in map(NOTE_TEXT.match, lines[a:b]) if m), None)
        if label_i is None or text_m is None:
            continue
        if text_m.group("value") in ("", '""', "''"):
            continue                    # the empty pair: a slot, not a note
        lead = NOTE_EMPTY_LABEL.match(lines[label_i]).group("lead")
        lines[label_i] = f'{lead}label: "QQ"'
        changed.append(f"unlabelled note -> label \"QQ\": "
                       f"{text_m.group('value').strip(chr(34))[:50]}")
    if not changed:
        return text, []
    return open_ + "\n".join(lines) + close + body, changed


# --- Key order, #1213: a drink's keys in the order the page prints them ---
TOP_LEVEL_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]|$)")


def _top_level_blocks(lines):
    """`[(key, [lines])]` in file order, or a string saying why not."""
    blocks = []
    for line in lines:
        key = TOP_LEVEL_KEY.match(line)
        if key:
            blocks.append((key.group(1), [line]))
        elif line[:1] in (" ", "\t") or (line.startswith("- ") and blocks) \
                or not line.strip():
            if not blocks:
                if line.strip():
                    return "an indented line before the first key"
                return "a blank line before the first key"
            blocks[-1][1].append(line)
        else:
            return (f"a column-0 line that is not a key, which belongs to no "
                    f"block: {line[:50]}")
    return blocks


def fix_key_order(text, path):
    """Deal a cocktail draft's top-level keys into page order (DECISIONS §9).

    The order is `test_cocktails.TOP_LEVEL_KEYS_IN_ORDER`. A key's block is
    its own line and every line under it up to the next top-level key; blocks
    move whole and are written back byte for byte. Before returning it raises
    unless the lines are the same multiset, the parsed data is equal and the
    declared order is reached: a reorder that breaks a file can still look
    plausible in a diff.

    Refused, each named SKIPPED: an undeclared key, the same key twice, and a
    column-0 line that is not a key (a comment there belongs to no block).
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    # `fm` always ends in a newline (the pattern demands it), so the last
    # element of the split is "" and is not a line. Dropping it here and
    # restoring the newline below is what keeps it out of the final block.
    lines = fm.split("\n")[:-1]
    blocks = _top_level_blocks(lines)
    if isinstance(blocks, str):
        return text, [f"SKIPPED: {blocks}"]

    keys = [k for k, _ in blocks]
    unknown = [k for k in keys if k not in TOP_LEVEL_KEYS_IN_ORDER]
    if unknown:
        return text, [f"SKIPPED: undeclared key(s) {unknown} have no place in "
                      f"the order -- left alone rather than guessed at"]
    if len(set(keys)) != len(keys):
        return text, ["SKIPPED: a top-level key appears twice"]
    problem = keys_out_of_page_order(keys)
    if not problem:
        return text, []

    by_key = dict(blocks)
    new_lines = [l for k in problem[1] for l in by_key[k]]
    new_fm = "\n".join(new_lines) + "\n"

    if sorted(new_lines) != sorted(lines):
        raise AssertionError(f"fix_key_order changed a line of {path}")
    if yaml.safe_load(new_fm) != yaml.safe_load(fm):
        raise AssertionError(
            f"fix_key_order changed what {path} parses to. Nothing was "
            f"written. A block boundary has been drawn in the wrong place."
        )
    if list(yaml.safe_load(new_fm)) != problem[1]:
        raise AssertionError(f"fix_key_order did not reach the declared "
                             f"order in {path}")
    return (open_ + new_fm + close + body,
            [f"top-level keys reordered, no line edited: "
             f"{' '.join(problem[0])} -> {' '.join(problem[1])}"])


def fix_food_meta_first(text, path):
    """Move a food draft's `meta:` block to directly under `title:` (DECISIONS §4).

    Helen reads the flags as soon as she opens a file. The block moves whole
    and is written back byte for byte, under the same three checks as
    `fix_key_order`. No other key moves. A file with no `title` or no `meta`
    is another test's to report and is left alone.

    Refused, each named SKIPPED: `title` or `meta` twice, and a column-0 line
    that is not a key.
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    lines = fm.split("\n")[:-1]                  # as in fix_key_order
    blocks = _top_level_blocks(lines)
    if isinstance(blocks, str):
        return text, [f"SKIPPED: {blocks}"]

    keys = [k for k, _ in blocks]
    if "title" not in keys or "meta" not in keys:
        return text, []
    if keys.count("title") > 1 or keys.count("meta") > 1:
        return text, ["SKIPPED: `title` or `meta` appears twice"]
    if keys.index("meta") == keys.index("title") + 1:
        return text, []

    meta = blocks.pop(keys.index("meta"))
    blocks.insert([k for k, _ in blocks].index("title") + 1, meta)
    new_lines = [l for _, block in blocks for l in block]
    new_fm = "\n".join(new_lines) + "\n"

    if sorted(new_lines) != sorted(lines):
        raise AssertionError(f"fix_food_meta_first changed a line of {path}")
    if yaml.safe_load(new_fm) != yaml.safe_load(fm):
        raise AssertionError(
            f"fix_food_meta_first changed what {path} parses to. Nothing was "
            f"written. A block boundary has been drawn in the wrong place."
        )
    order = list(yaml.safe_load(new_fm))
    if order[order.index("title") + 1] != "meta":
        raise AssertionError(f"fix_food_meta_first did not put meta under "
                             f"the title in {path}")
    return (open_ + new_fm + close + body,
            ["meta moved under the title, no line edited"])


# --- Title case, cocktails only, #1089 ---
TITLE_LINE = re.compile(r'^(?P<head>title:[ \t]*")(?P<title>[^"]*)(?P<tail>"[ \t]*)$')


def fix_title_case(text, path):
    """Title Case for a cocktail draft's `title`, by the suite's `title_cased`.

    It raises the first letter of a word outside brackets and never lowers
    one, so capitals change and words do not. Line-wise, and wrapped: a
    `title: "QQ ..."` line never reaches it. A food title stays the source's.
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    changed, out = [], []
    for line in fm.split("\n"):
        m = TITLE_LINE.match(line)
        if m and title_cased(m.group("title")) != m.group("title"):
            new = title_cased(m.group("title"))
            changed.append(f"title: {m.group('title')} -> {new}")
            line = m.group("head") + new + m.group("tail")
        out.append(line)
    return open_ + "\n".join(out) + close + body, changed


FOOD_FIXERS = [
    ("notes", fix_notes_slot),
    ("quoting", fix_scalar_quoting),
    ("quoting", fix_flow_quoting),
    ("quoting", fix_group_name_quoting),
    # Formatting reaches a food QQ line, so Helen rewrites from text already
    # in house style (DECISIONS §5). A drink's QQ lines stay as written.
    ("dashes", partial(fix_en_dashes, skip_qq=False)),
    ("typography", partial(fix_typography, skip_qq=False)),
    ("units", partial(fix_unit_spacing, skip_qq=False)),
    ("accents", partial(fix_accents, skip_qq=False)),
    ("meta", fix_meta_block),
    ("size", fix_size_words),
    ("incidentals", fix_incidentals),
    # LAST, for the reason the drinks table gives.
    ("order", fix_food_meta_first),
]

# Two tables, not one with a site test inside each fixer. A drink has no
# `main_ingredients` or `tags` for `fix_flow_quoting`, its `meta:` is not
# food's, and `fix_size_words` would rewrite an `amount`.
# `units` is in both: unwrapped on food, so `amount: "40g"` is fixed; wrapped
# on a drink, so it reaches only Helen's prose.
# `notes` is unwrapped on a drink: it changes the line count, which
# `only_where_editable` refuses, and it must see a `text: "QQ - ..."` line to
# know the note has text. It writes only a `label:` line or an empty pair.
DRINK_FIXERS = [
    ("notes", fix_notes_slot),
    ("quoting", only_where_editable(
        partial(fix_scalar_quoting, fields=DRINK_SCALAR_FIELDS))),
    # `source` and `source_url` are verbatim, so the mask above blanks them;
    # quotes change no word, so they get their own pass that spares only QQ.
    ("quoting", only_where_editable(
        partial(fix_scalar_quoting, fields=["source", "source_url"]), mask=not_qq)),
    ("dashes", only_where_editable(fix_en_dashes)),
    ("typography", only_where_editable(fix_typography)),
    ("units", only_where_editable(fix_unit_spacing)),
    ("accents", only_where_editable(fix_accents)),
    # After `quoting`, which is what gives an unquoted title the quotes
    # TITLE_LINE looks for.
    ("titles", only_where_editable(fix_title_case)),
    # LAST, and unwrapped: it moves blocks and edits no line, so there is
    # nothing for `only_where_editable` to protect, and running after `notes`
    # means the slot that rule writes is dealt into place with the rest.
    ("order", fix_key_order),
]

RULE_NAMES = sorted({n for n, _ in FOOD_FIXERS} | {n for n, _ in DRINK_FIXERS})


# --- Reporters: never fixed, always surfaced ---

# Case-sensitive on purpose: `QQ Claude ...` is the interleaved-rewrite
# convention (MANUAL §5), not an instruction left for Claude.
CLAUDE_MARKER = re.compile(r"[^\"\n]{0,10}\bCLAUDE\b[^\"\n]{0,40}")


def report_claude_markers(path, text):
    return [f"instruction left for Claude: {h.strip()[:70]}"
            for h in CLAUDE_MARKER.findall(text)]


def report_drink_faults_left_alone(path, text):
    """Mechanical faults the drinks suite names that this script will not fix.

    The suite checks an `amount`, a `generic`, a `glass` and a method step;
    this script edits none of them. Naming them here lets a fault the pass
    declined be told from one it missed when pytest fails. A non-house
    spelling and a temperature without its degree sign are reported for the
    same reason and are fixed on neither collection.
    """
    scope = drink_suite_scope(SimpleNamespace(raw=text))
    editable = drink_editable(text)
    found = []
    for raw, seen, ok in zip(text.split("\n"), scope.split("\n"), editable):
        if ok or not seen.strip():
            continue
        if NUMBER_RANGE.search(ISO_DATE.sub(" ", raw)):
            found.append(f"hyphenated number range, not this pass's to fix: "
                         f"{raw.strip()[:70]}")
        for pattern, _, label in TYPOGRAPHY_FIXES:
            if pattern.search(raw):
                found.append(f"{label}, not this pass's to fix: "
                             f"{raw.strip()[:70]}")
    found += [f"non-house spelling, never auto-fixed: {p}"
              for p in spelling_problems(scope)]
    found += [f"temperature without a degree sign: {t}"
              for t in degreeless_temperatures(scope)]
    return found


FOOD_REPORTERS = [report_claude_markers, report_size_words_with_no_count]
DRINK_REPORTERS = [report_claude_markers, report_drink_faults_left_alone]


# =============================================================================

def dirty_drafts(root):
    r = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                       capture_output=True, text=True)
    return [l for l in r.stdout.split("\n") if l.strip()]


# One row per private repo. The name is what `--site` takes.
SITES = {
    "food": (FOOD_DRAFTS, FOOD_FIXERS, FOOD_REPORTERS,
             "helen-triages-food-private"),
    "cocktails": (COCKTAIL_DRAFTS, DRINK_FIXERS, DRINK_REPORTERS,
                  "helen-triages-cocktails-private"),
}


def tidy_one(root, fixers, reporters, wanted, apply):
    """Report on (and optionally write) one collection. Returns the counts."""
    files, skipped = load_drafts(root)
    fixed, reports, total = {}, {}, 0
    for path in files:
        text = original = path.read_text(encoding="utf-8")
        notes = []
        for name, fn in fixers:
            if wanted and name not in wanted:
                continue
            text, said = fn(text, path)
            notes += [f"[{name}] {s}" for s in said]
        found = []
        for reporter in reporters:
            found += reporter(path, original)

        rel = path.relative_to(ROOT).as_posix()
        if notes:
            fixed[rel] = notes
            total += len([n for n in notes if "REPORT ONLY" not in n
                          and "SKIPPED" not in n])
        if found:
            reports[rel] = found
        if apply and text != original:
            path.write_text(text, encoding="utf-8")
    return files, skipped, fixed, reports, total


def print_collection(root, verb, files, skipped, fixed, reports, total):
    print(f"\n{'=' * 70}\n{root.name}/ -- {len(files)} draft(s) scanned")
    if skipped:
        print(f"  ({len(skipped)} .md file(s) with no front matter, not "
              f"drafts, not looked at: "
              + ", ".join(p.name for p in skipped) + ")")
    print(f"\n=== {verb} {total} mechanical change(s) across {len(fixed)} file(s)")
    for rel, notes in sorted(fixed.items()):
        print(f"\n  {rel}")
        for n in notes[:12]:
            print(f"    {n}")
        if len(notes) > 12:
            print(f"    ... and {len(notes) - 12} more")

    print(f"\n=== reported, never changed: {len(reports)} file(s)")
    for rel, found in sorted(reports.items()):
        print(f"\n  {rel}")
        for f in found[:6]:
            print(f"    {f}")
        if len(found) > 6:
            print(f"    ... and {len(found) - 6} more")


def main(argv=None):
    # `argv` is for tests/test_tidy_drafts.py, which calls this in its own
    # process (#1271). None means the command line.
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write the fixes; without it nothing is changed")
    ap.add_argument("--only", default="",
                    help="comma-separated subset of: " + ",".join(RULE_NAMES)
                         + " (meta and size are food's alone, titles is "
                           "cocktails' alone)")
    ap.add_argument("--site", choices=sorted(SITES), default=None,
                    help="one collection only; the default is both")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="run even though a drafts repo has uncommitted changes")
    ap.add_argument("--drafts-dir", default=None,
                    help="operate on a different directory. Exists so this can "
                         "be proved against a COPY before it is ever pointed "
                         "at Helen's real drafts -- see the command doc. "
                         "Needs --site, because a directory does not say "
                         "which collection's rules it wants.")
    args = ap.parse_args(argv)

    sites = [args.site] if args.site else sorted(SITES)
    if args.drafts_dir and not args.site:
        sys.exit(
            "--drafts-dir needs --site. There are two collections with two "
            "different rule sets now, and a bare path does not say which one "
            "it holds -- guessing from the filenames would mean running food's "
            "`meta:` migration over a drink, or a drink's key exclusions over a "
            "recipe, and both are silent."
        )

    wanted = {s.strip() for s in args.only.split(",") if s.strip()}
    unknown = wanted - set(RULE_NAMES)
    if unknown:
        sys.exit(f"--only names no such rule: {sorted(unknown)}")

    plan = []
    for site in sites:
        root, fixers, reporters, repo = SITES[site]
        if args.drafts_dir:
            root = Path(args.drafts_dir).resolve()
        if root.is_dir():
            plan.append((site, root, fixers, reporters))
        else:
            print(f"{root.name}/ is not here -- it is a separate private repo "
                  f"({repo}), gitignored from this one, so a clean checkout "
                  f"does not have it. Skipped.")
    if not plan:
        sys.exit(
            "Neither drafts repo is present. Nothing to tidy; nothing done. "
            "Absent is a legitimate state -- both are private and gitignored -- "
            "but it is not a clean report, so this refuses rather than printing "
            "one."
        )

    if args.apply and not args.allow_dirty:
        for _, root, _, _ in plan:
            dirt = dirty_drafts(root)
            if dirt:
                sys.exit(
                    f"{root.name}/ has {len(dirt)} uncommitted change(s):\n  "
                    + "\n  ".join(dirt[:10])
                    + "\n\nRefusing to write on top of them, because the whole "
                      "safety story here is that you can read the diff "
                      "afterwards and see exactly what this script did. Mixed "
                      "in with your own edits you cannot. Commit or stash them "
                      "first, or pass --allow-dirty if you know they are "
                      "unrelated."
                )

    verb = "applied" if args.apply else "would apply"
    for _, root, fixers, reporters in plan:
        print_collection(root, verb,
                         *tidy_one(root, fixers, reporters, wanted, args.apply))

    print("\n=== NOT looked at, and deliberately")
    print("  FOOD: content judgement -- which milk, which flour, which "
          "mustard, whether\n  an oven figure is the fan one, whether a note's "
          "first word is a proper noun.\n  ~25 rules, listed with counts in "
          "tests/test_drafts.py's NOT_FOR_DRAFTS.\n  Every one needs Helen or "
          "her source material. Run pytest to see them.")
    print("\n  DRINKS: everything that is not Helen's own prose. An `amount`, "
          "a `method`\n  step, a `glass`/`garnish`/`mood`/`generic`/"
          "`character` (closed vocabularies\n  declared in _data/cocktails/), "
          "a `suggestion` or a `source` (somebody else's\n  words, though a bare "
          "`source:` is quoted), and every `QQ` line. A dash or an\n  accent "
          "inside one of those is a question for the vocabulary or for the "
          "source,\n  not a formatting fix -- see the module docstring, and the "
          "reported-never-changed\n  section above for the ones the drinks "
          "suite will still fail on.")
    if not args.apply:
        print("\nNothing was written. Re-run with --apply to write the fixes.")


if __name__ == "__main__":
    main()
