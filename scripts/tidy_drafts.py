#!/usr/bin/env python3
"""Tidy `_food_drafts/` and `_cocktail_drafts/` -- the mechanical half only.

RUN IT THROUGH `/tidy-drafts`, not by hand, unless you know why you are here.
`.claude/commands/tidy-drafts.md` is the procedure: branch the drafts repo,
report, apply, run pytest, commit there. This file is only the engine.

    python3 scripts/tidy_drafts.py                  # report, change nothing
    python3 scripts/tidy_drafts.py --apply          # write the fixes
    python3 scripts/tidy_drafts.py --only quoting,meta
    python3 scripts/tidy_drafts.py --only size      # #577's pass, food only
    python3 scripts/tidy_drafts.py --site cocktails # one collection only

WHY A SCRIPT AND NOT AN AGENT EDITING 340 FILES. Three of these rules have a
trap in them that is easy to state and easy to forget on the hundredth file:
`meta:` booleans must never be quoted (quoting a flag's `true` makes it the
STRING "true" and every `is True` check in the suite silently reads False);
house style stops at a `QQ` line, because that is the source's wording awaiting
a rewrite and correcting its dash edits someone else's words; and no edit here
may go through a YAML dumper, which would lose comment placement, key order and
the exact `[""]` shape `method_short` depends on. Encoded once beats remembered
340 times.

WHAT IT WILL NOT DO, AND THIS IS THE LOAD-BEARING HALF.

  - It never touches a `QQ` line. MANUAL §5, issue #426.
  - It never touches `source:` -- a citation is reproduced as the publication
    spells it, so "Cafe Delites" is correct and accenting it is a misquote.
  - It never touches a slug or filename, which must stay ASCII.
  - It never resolves a CONTENT judgement. Which milk, which flour, which
    mustard, whether an oven figure is the fan one, whether a note's first word
    is a proper noun -- ~25 rules and 600-odd hits across the corpus, listed in
    test_drafts.py's NOT_FOR_DRAFTS, every one of which needs Helen or her
    source material. They are reported and left alone.
  - It never renames a file, and never retitles one, and as of 2026-09-01 it no
    longer even reports the two disagreeing. Helen ruled the class out for
    drafts: a draft's title is still the SOURCE's title while the slug is
    already the dish, so the divergence is the ingest working. See
    test_title_and_slug_dont_diverge in test_drafts.py's NOT_FOR_DRAFTS.
  - It never runs a YAML dumper over a draft.

SCOPE SETTLED WITH HELEN, 2026-08-29: pure formatting, plus the #429 `meta:`
migration. It also reported title/slug divergence until 2026-09-01, when she
ruled that out; the entry above says why. Size words (108 drafts, moving a word
between `amount:` and `item:`) were considered and excluded that day --
mechanical in shape, but it rewrites two fields per hit and the precedent
records real fixes that needed an eye. THEY JOINED ON 2026-09-24, as #577's
option 1 -- "Script it with a hand-review of the diff, one commit, before
promotion" -- Helen's call. The `size` rule below does the move only where the
suite's own predicate fires, refuses the shapes that needed the eye, and the
diff of the one commit is the review.

COCKTAIL DRAFTS JOINED THE PASS ON 2026-09-05, at Helen's request: *"Widen
please -- cocktail drafts passing will save me a lot of time."* They were out
while the drink schema was mid-migration (#544, #571, #573), on the grounds that
tidying a shape about to change is work done twice; #571 and #573 have landed
and #544's mechanical half is spent, so the reason had expired.

WHAT THE PASS DOES ON A DRINK, and the boundary is narrower than food's because
a drink's front matter is mostly NOT prose. Four fifths of its lines are a
closed vocabulary, somebody else's words, or a number.

  - It fixes only what `tests/test_cocktails.py` already demands and calls
    mechanical: the quoted scalars (`test_drink_scalar_fields_are_quoted`),
    hyphenated number ranges (`test_drink_number_ranges_use_en_dashes`), `--`
    and `->` (`test_drink_typography`), and accents from the curated list
    (`test_drink_accents`). Nothing the drinks suite would not ask for.
  - It fixes them only in Helen's OWN prose: `title`, `tagline`, `to_serve`, a
    `notes` entry's label and text, an ingredient's `note`.
  - It never touches a `QQ` line -- by the SUITE's predicate, not the food one
    twenty lines below. On a drink the marker sits behind a key
    (`tagline: "QQ ..."`, `text: "QQ - ..."`) and the food pattern, which allows
    only a list dash and a quote before it, matches none of them. See
    `drink_editable`.
  - It never touches `item`, `suggestion`, `source` or `source_url`. Those are
    somebody else's words -- test_cocktails.VERBATIM_KEYS, imported below rather
    than re-listed -- and the drinks suite blanks them before it looks, so it
    does not ask for them either.
  - It never touches `glass`, `garnish`, `mood`, `generic` or `character`. Each
    is a closed vocabulary declared in `_data/cocktails/` and enforced against
    that declaration; an accent or an em dash written into one is a change to
    the VOCABULARY, which is a question for `_data/`, not a formatting fix.
  - It never touches a `method` step. `_data/cocktails/methods.yml` holds the
    canonical steps and a `proposals` mechanism for changing one, so editing a
    step in a drink file quietly de-canonicalises it.
  - **It never touches an `amount`, and that one is a RECORDED HARM rather than
    a principle.** anitas-attitude-adjuster said `amount: "Top (30-45) ml"` with
    a `QQ` note quoting that string back verbatim; en-dashing the amount would
    have desynchronised the note from the value it describes. The drinks suite
    checks amounts and is right to -- they render -- so this script REPORTS a
    range in one and leaves it, which is what the section below is for.

Food's own rules stay food's: `main_ingredients` and `tags` flow quoting, and
the #429 `meta:` migration, run on `_food_drafts/` and on nothing else. A drink's
`meta:` block is a different list in a different order (test_cocktails.
META_KEYS_IN_ORDER) and migrating it was never asked for.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from functools import partial
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
FOOD_DRAFTS = ROOT / "_food_drafts"
COCKTAIL_DRAFTS = ROOT / "_cocktail_drafts"
ACCENTS = ROOT / "_data" / "accented_words.yml"

FRONT_MATTER = re.compile(r"\A(---\n)(.*?\n)(---\n?)", re.S)

# =============================================================================
# EVERY RULE IS IMPORTED FROM THE SUITE, NEVER RE-TYPED HERE
# =============================================================================
# A fixer that carries its own copy of the contract is a fixer that will one day
# tidy files INTO a shape the tests reject, which is worse than not tidying them
# -- and it fails in the direction nobody checks, because the script is green by
# construction. So: one definition, and the tests own it.
#
# THIS ALSO RESOLVED A GUARD I TRIPPED, and the resolution is the interesting
# part rather than the trip. The first draft of this file hardcoded
# `["cooked_before", "date_last_edited"]`, and
# test_invisible_keys_are_really_invisible failed: `scripts` is deliberately in
# its RENDER_SURFACE, and those keys are on INVISIBLE_KEYS precisely because
# nothing -- "no layout, include, plugin or script" -- reads them. The test's
# own message says "do not narrow this test", and it is right.
#
# The tempting fixes were all bad: narrow the guard, drop the keys from
# INVISIBLE_KEYS (which would make a future source_type-only commit invalidate
# every proofread), or spell the names so the scanner misses them, which is
# routing around a safety rail. Importing is none of those. The literals are
# gone because they were duplication, the guard is untouched, and the script can
# no longer drift from the contract it enforces.
sys.path.insert(0, str(ROOT / "tests"))
from test_front_matter import (  # noqa: E402
    META_ORDER, RETIRED, SCALAR_STRING_FIELDS,
)
# THE DRINKS HALF IMPORTS THE SAME WAY, and the private name is deliberate.
# `_checkable` is the drinks suite's own definition of "the part of a drink file
# these rules look at" -- QQ lines and verbatim-key lines blanked, including the
# indented block a bare `suggestion:` opens. Re-typing it here is exactly the
# drift this section's heading forbids, and it is the one function whose
# disagreement with the suite would be invisible: the script would report a
# collection clean while the suite failed on it.
from conftest import (  # noqa: E402
    checkable_text, degreeless_temperatures, spelling_problems,
)
from test_cocktails import (  # noqa: E402
    DRINK_SCALAR_FIELDS, VERBATIM_KEYS, _checkable as drink_suite_scope,
)
# The size-word pattern is the recipe rule's own (#149, #577). The 2026-09-01
# re-measurement on #577 already imported it rather than retyping it, for the
# reason this section's heading gives; the fixer does the same.
from test_style import _LEADING_SIZE_WORD  # noqa: E402

FLOW_FIELDS = ["main_ingredients", "tags"]

# The retired keys that live under `meta:` -- derived from the suite's own
# authoritative RETIRED dict (MANUAL §4 calls it that), not listed again.
# Anything retired at the TOP level is a different rule and not this script's.
META_RETIRED = [k for k in RETIRED if k not in META_ORDER]

# Optional and additive, and legitimate on a DRAFT alongside the three
# (MANUAL §4, issue #418). The recipe-side rule forbids it outright, which is
# why it is named here and not in META_ORDER.
META_OPTIONAL = ["claude_rewritten"]

ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER_RANGE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)(?![\d.])")
# `QQ Claude` IS EXCLUDED, and deliberately -- see the long note on `_QQ_LINE`
# in tests/conftest.py, which this mirrors. The marker protects SOMEBODY ELSE'S
# wording; a `QQ Claude` line is the paraphrase written here, and MANUAL §4
# holds it to normal house style like any other prose. Fifteen hyphenated
# number ranges were hiding behind the old pattern on 2026-09-01.
#
# IT NOW ALLOWS A KEY IN FRONT OF THE MARKER, AND THIS WAS A REAL HOLE -- fixed
# 2026-09-22. The pattern permitted an optional list dash and an optional quote
# and nothing else, so `- "QQ original ..."` was skipped and
# `text: "QQ - ..."`, `tagline: "QQ ..."` and `prep_time: "QQ"` were NOT. A
# marker behind a key was invisible to the food pass, which then "corrected"
# somebody else's words -- the exact harm MANUAL §5 exists to prevent.
#
# THE DRINKS HALF NEVER HAD THE BUG, which is what makes this a copy that
# drifted rather than an oversight. `drink_editable` below asks
# `conftest.checkable_text` precisely because "a drink puts the source's own
# wording behind a key", and its docstring says using this pattern there "would
# have left every QQ tagline in the collection open to editing while the report
# claimed the rule was applied". Every word of that was true of FOOD as well and
# nobody checked.
#
# MEASURED BEFORE AND AFTER, because the exposure is not the same as the damage.
# 534 lines in `_food_drafts/` are QQ lines the old pattern could not see, 248
# of them taglines added on 2026-09-21; of those, five in four files actually
# carried a fault the pass would have rewritten (`QQ - pulled out as its own
# recipe from ...` notes, an en dash and four em dashes). A latent hole that one
# day's work quadrupled.
#
# THE KEY PATTERN IS conftest's, CHARACTER FOR CHARACTER: `[a-z_]+:` and a
# single optional space, so `main_ingredients:` and `text:` match and a
# capitalised or dotted key does not. Keeping the two literally identical is the
# point -- this file already carries one copy of a rule that drifted from its
# original, and a second spelling would be a third thing to keep in step.
QQ_LINE = re.compile(r"^\s*(-\s*)?(?:[a-z_]+:\s*)?[\"']?QQ\b(?!\s+Claude\b)")


# =============================================================================
# Reading the corpus
# =============================================================================

def load_drafts(root):
    """One collection's drafts, `None` if that private repo is simply absent.

    #537's lesson, and it cost the glass icons twice in two days: a script whose
    input is legitimately empty most of the time must check BEFORE it acts, not
    report `0 files ->` as though that were a result.

    ABSENT AND EMPTY ARE STILL DIFFERENT ANSWERS; what changed on 2026-09-05 is
    that ONE absent root is no longer fatal, because there are now two and they
    are two separate private repos. A worktree routinely has one and not the
    other. `main()` makes the loud refusal when NEITHER is here -- the same
    three-way answer `tests/test_cocktails.py`'s header settles at length: skip
    when neither collection is present, assert non-empty when one is.

    A `.md` WITH NO FRONT MATTER IS NOT A DRAFT and is named, not silently
    dropped. `_cocktail_drafts/README.md` is the live case, and the fixers that
    do not parse front matter (dashes, typography, accents) would happily have
    em-dashed a README's prose.
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


# =============================================================================
# WHICH LINES OF A DRINK THIS SCRIPT MAY REWRITE
# =============================================================================
# The module docstring argues each entry; this is only the list. Two of the
# three groups are imported rather than named:
#
#   VERBATIM_KEYS          somebody else's words (test_cocktails)
#   the closed vocabularies declared in `_data/cocktails/`
#   `amount`               the recorded harm, see the docstring
#   `method`               methods.yml's canonical steps
#
# LONGEST FIRST IN THE ALTERNATION. `source` and `source_url` share a prefix,
# and Python's alternation is first-match-then-backtrack rather than
# longest-match, so the order is doing real work the moment a trailing group
# stops forcing the backtrack. Sorting removes the dependency on that rather
# than relying on it, which is worth one call to `sorted` at import time.
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

    THE QQ TEST IS THE SUITE'S, NOT THE ONE AT THE TOP OF THIS FILE, and the
    difference is not cosmetic. `QQ_LINE` above allows an optional list dash and
    an optional quote before the marker, which is every shape a FOOD draft uses.
    A drink puts the source's own wording behind a key -- `tagline: "QQ"`,
    `text: "QQ - generic values INFERRED"` -- and the food pattern matches none
    of those. Using it here would have left every QQ tagline in the collection
    open to editing while the report claimed the rule was applied, which is the
    shape of exclusion that looks right in the file and does nothing.
    `conftest.checkable_text` is the pattern that knows about the key, and
    asking it which lines it blanked is the same rule rather than a second copy.

    A NEVER-EDIT KEY WITH AN EMPTY VALUE OPENS A BLOCK and the indented lines
    under it go too. `method:`, `glass:`, `garnish:` and `mood:` are always that
    shape, and `suggestion:` is that shape on the couple of dozen drinks that
    name two bottles. Matching the key line alone would blank the header and
    leave the values under it in scope -- the bug `test_cocktails._checkable`'s
    own docstring records, avoided here by copying its algorithm rather than its
    key list.
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


def only_where_editable(fixer):
    """Wrap a LINE-WISE fixer so it sees, and answers for, the editable lines.

    Blank the rest, run the fixer over that, then take its answer line by line
    where the line was editable and the ORIGINAL everywhere else. Blanking
    rather than dropping is what makes the splice possible at all: the index of
    a line has to survive, which is the same reason `conftest.checkable_text`
    blanks and the reason it says so in its own docstring.

    THE LENGTH CHECK IS NOT PARANOIA. Every fixer wrapped here is line-wise
    today; `fix_meta_block` is not, and is food's alone. Wrapping a
    line-count-changing fixer would splice its output against the wrong lines
    and write a plausible-looking, wrong file to 125 drinks in one pass -- the
    exact failure this script's `meta:` bug already produced once, caught then
    only because the result stopped parsing. Here it would still parse.
    """
    def run(text, path):
        editable = drink_editable(text)
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


# =============================================================================
# FIXERS -- each takes the whole file text and returns (new_text, [what changed])
# =============================================================================

def fix_scalar_quoting(text, path, fields=None):
    """`fields` is the collection's own list, imported, never re-typed here.

    Food's is `test_front_matter.SCALAR_STRING_FIELDS`, a drink's is
    `test_cocktails.DRINK_SCALAR_FIELDS`. Neither contains a boolean, and that
    is load-bearing rather than incidental: quoting a `meta:` flag makes it the
    STRING "true", which the publish gate reads as neither true nor false and
    which holds the page back for ever.
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


def fix_en_dashes(text, path):
    """`3-4 mins` -> `3–4 mins`, skipping QQ lines and ISO dates.

    The QQ skip is why this is worth a script. Two thirds of the corpus-wide
    hits for this rule sit inside source wording awaiting a rewrite -- 86 of 130,
    measured 2026-08-29 -- and MANUAL §5 says in as many words that
    correcting a dash there is editing someone else's text.
    """
    out, changed = [], []
    for line in text.split("\n"):
        if is_qq(line):
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


def fix_typography(text, path):
    out, changed = [], []
    for line in text.split("\n"):
        if is_qq(line):
            out.append(line)
            continue
        for pattern, replacement, label in TYPOGRAPHY_FIXES:
            if pattern.search(line):
                line = pattern.sub(replacement, line)
                changed.append(f"{label} in: {line.strip()[:60]}")
        out.append(line)
    return "\n".join(out), changed


def _accent_map():
    """The curated unaccented->accented map, and the words that keep no accent.

    Read as text rather than through a YAML parser so this script has no
    dependency the test suite does not already carry; the file is a flat
    two-block mapping and has been since it was written.
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


def fix_accents(text, path, _cache={}):
    """Prose only. Never `source:`, never a QQ line, never a slug."""
    if "map" not in _cache:
        _cache["map"] = _accent_map()
    words, no_accent = _cache["map"]

    out, changed = [], []
    for line in text.split("\n"):
        if is_qq(line) or re.match(r"^source(_url)?:", line):
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
    """The #429 migration: drop two retired keys, put the three in order.

    THE ORDER IS test_front_matter.META_ORDER, taken from there rather than
    named again here. It is the order a recipe moves through the flags, and
    it is asserted rather than merely preferred
    (test_meta_block_is_exactly_the_three_flags_in_order).

    A MISSING `awaiting_fix` IS REPORTED, NEVER INVENTED. The flag fails closed:
    `false` is the only value that publishes a page, so writing one in is
    asserting the recipe is fit to publish, which is Helen's to say and not a
    formatting fix. Two drafts are in this state.
    """
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    lines = fm.split("\n")

    start = next((i for i, l in enumerate(lines) if l.rstrip() == "meta:"), None)
    if start is None:
        return text, []
    # `^  \S`, NOT "indented or blank". Splitting the front matter on "\n" leaves
    # a trailing "" (the text ends with a newline), and an "or blank" scan
    # swallowed it -- so the rebuilt block absorbed the final newline and every
    # file came out ending `proofread: false---`. 341 of 342 drafts, silently,
    # and the front-matter regex then matched none of them. Caught by parsing
    # the output rather than by reading the diff, which is the only reason this
    # comment is here and not a git history entry.
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


# =============================================================================
# THE SIZE WORD, #577 -- excluded 2026-08-29, scripted 2026-09-24
# =============================================================================
# `amount: "2"` / `item: "large onions"` renders the "2" highlighted and the
# "large" as part of the ingredient's name; the recipe rule
# (test_style.test_size_word_is_with_the_count_not_the_item, issue #149) wants
# `amount: "2 large"` / `item: "onions"`. The 2026-08-29 tidy left it out
# because it rewrites two fields per hit and #149's own fix needed an eye on
# five of them. On 2026-09-24 Helen chose the issue's option 1: script it, hand-
# review the diff, one commit, before promotion. So the script is deliberately
# CONSERVATIVE: every shape that ever needed the eye is refused and named, and
# the diff the reviewer reads holds only the moves nobody has yet found wrong.
#
# THE PREDICATE IS THE TEST'S, BOTH HALVES. `_LEADING_SIZE_WORD` is imported
# above; the "bare count" half is inline in the test --
# `re.fullmatch(r"\d+", amount)` -- and BARE_COUNT spells it character for
# character. The test stops at a bare integer on purpose (its module comment):
# `400 g` / `large open mushrooms` reads fine with the size as an adjective,
# `½` / `small bunch of chives` likewise, and a `small handful of parsley` with
# no amount at all IS the amount. None of those is moved, and only the last is
# reported, because it is the one a reader of the diff would otherwise take for
# a miss.
#
# WHAT IT REFUSES, EACH NAMED IN THE REPORT RATHER THAN GUESSED AT:
#   - no `amount:`, or an empty one: no count to attach the word to. Surfaced
#     by `report_size_words_with_no_count`, never rewritten. All 38 on
#     2026-09-24 were the handful/bunch idiom the test calls the amount.
#   - a remainder starting `or`: `1` / `large or 2 small onions` carries a
#     second count inside the item, and `1 large` / `or 2 small onions` is
#     worse than what was there. Three drafts. An eye, not a rule.
#   - `baby`: the regex has it, and it is a KIND as often as a size -- baby
#     gem, baby corn, baby spinach, baby plum tomatoes. DECISIONS §6 records
#     Helen's ruling that `baby gem` is a kind, and a script that strips it
#     produces `2 baby` / `gem lettuce`, which passes the test and is wrong.
#     Skipped and named, for the reviewer to move by hand if she wants it.
#   - an escape or an inner quote in either value, or a bare item whose
#     remainder would start with a YAML indicator: rewrapping it is a
#     judgement about the text, the same line fix_scalar_quoting draws.
#
# BYTE-PRESERVING BY CONSTRUCTION. It touches exactly two lines per hit, keeps
# each line's indentation, gap and quote style, and never goes through a
# dumper. `tests/test_tidy_drafts.py` proves the whole file byte for byte.
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
    own keys sit at the column the dash line's key starts in, so a nested
    mapping's `item:` (deeper) and the enclosing group's (shallower) are both
    left to their own entries. `ingredient_groups:` is a list of groups each
    holding a list of items, and this is what stops the group entry -- which
    spans every item under it -- from claiming the first item's lines.
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

    Only where the suite's predicate fires -- a bare integer count beside an
    item starting with a size word -- and never in the shapes the section
    comment above lists, each of which is SKIPPED and says so.
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


def report_size_words_with_no_count(path, text):
    """A size word on an item with no `amount:` to carry it. Surfaced, never moved.

    Every one measured on 2026-09-24 was `small handful of ...` or `small bunch
    of ...`, which the recipe rule's own comment says is the amount and not a
    stray adjective. It is reported anyway because a reader of the pass's diff
    who knows 108 drafts were the wrong way round would otherwise take a
    `small handful` that survived it for a miss.
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


FOOD_FIXERS = [
    ("quoting", fix_scalar_quoting),
    ("quoting", fix_flow_quoting),
    ("dashes", fix_en_dashes),
    ("typography", fix_typography),
    ("accents", fix_accents),
    ("meta", fix_meta_block),
    ("size", fix_size_words),
]

# THE MISSING ENTRIES ARE THE POINT OF HAVING TWO TABLES.
# `fix_flow_quoting` reads `main_ingredients` and `tags`, which no drink has;
# `fix_meta_block` runs the #429 migration over food's three flags, and a
# drink's `meta:` is a five-key block in its own order that nobody asked to
# migrate; `fix_size_words` rewrites an `amount`, which on a drink is the
# recorded harm above, beside an `item`, which a drink retired on 2026-09-21.
# A single table with an `if site == ...` inside each fixer would have been the
# same code and a worse place to read the answer.
DRINK_FIXERS = [
    ("quoting", only_where_editable(
        partial(fix_scalar_quoting, fields=DRINK_SCALAR_FIELDS))),
    ("dashes", only_where_editable(fix_en_dashes)),
    ("typography", only_where_editable(fix_typography)),
    ("accents", only_where_editable(fix_accents)),
]

RULE_NAMES = sorted({n for n, _ in FOOD_FIXERS} | {n for n, _ in DRINK_FIXERS})


# =============================================================================
# REPORTERS -- never fixed, always surfaced
# =============================================================================

# THE PREDICATE IS IMPORTED FROM THE SUITE, NOT RE-TYPED, and the first draft of
# this file proves why: a CLAUDE-marker scan with re.I on it matched `QQ Claude
# ...`, which is the documented interleaved-rewrite convention (MANUAL §4) and
# not an instruction at all. It reported hundreds of files as needing attention
# and every one was that convention. The real rule is case-sensitive. MANUAL
# §12: "if you scan and find lots of problems, be suspicious of your own
# findings before reporting them."
#
# THERE WAS A SECOND REPORTER HERE AND IT IS GONE, 2026-09-01. It flagged a
# title whose head-clause words are absent from the filename, 19 drafts, and
# Helen ruled the whole class out: "let's not run the title matches slug-ish
# test over drafts". A draft's title is still the SOURCE's title while the slug
# is already the dish, so the divergence is the ingest working, not failing --
# see the reason on test_title_and_slug_dont_diverge in test_drafts.py's
# NOT_FOR_DRAFTS. It was 19 of the 21 lines this script printed, so removing it
# is most of what makes the report readable.
CLAUDE_MARKER = re.compile(r"[^\"\n]{0,10}\bCLAUDE\b[^\"\n]{0,40}")


def report_claude_markers(path, text):
    return [f"instruction left for Claude: {h.strip()[:70]}"
            for h in CLAUDE_MARKER.findall(text)]


def report_drink_faults_left_alone(path, text):
    """Mechanical faults the DRINKS SUITE names that this script will not fix.

    WITHOUT THIS THE REPORT WOULD BE MISLEADING RATHER THAN MERELY INCOMPLETE.
    The drinks suite blanks only the verbatim keys before it looks, so it checks
    an `amount`, a `generic`, a `glass` and a method step; this script edits
    none of them. A drink with a hyphenated range in its amount would print
    nothing here and fail pytest, and the natural reading of that is "the tidy
    pass missed one" rather than "the tidy pass declined one on purpose".

    Two of the three kinds are not fixed for EITHER collection and are listed
    for the same reason: a non-house spelling (`demarara -> demerara`) is a
    word rather than a character, and a temperature without its degree sign
    turns up in a drink about once a year and has never yet turned up wrong.
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


# ONE ROW PER PRIVATE REPO. The name is what `--site` takes, the root is where
# the files are, and the two tables are what makes the food/drink boundary a
# thing you can read in one place rather than a condition inside six fixers.
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write the fixes; without it nothing is changed")
    ap.add_argument("--only", default="",
                    help="comma-separated subset of: " + ",".join(RULE_NAMES)
                         + " (meta is food's alone)")
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
    args = ap.parse_args()

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
          "an `item` or a `suggestion` (somebody else's\n  words), and every "
          "`QQ` line. A dash or an accent inside one of those is a\n  question "
          "for the vocabulary or for the source, not a formatting fix -- see "
          "the\n  module docstring, and the reported-never-changed section "
          "above for the ones\n  the drinks suite will still fail on.")
    if not args.apply:
        print("\nNothing was written. Re-run with --apply to write the fixes.")


if __name__ == "__main__":
    main()
