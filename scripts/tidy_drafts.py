#!/usr/bin/env python3
"""Tidy `_food_drafts/` -- the mechanical half only, on request.

RUN IT THROUGH `/tidy-drafts`, not by hand, unless you know why you are here.
`.claude/commands/tidy-drafts.md` is the procedure: branch the drafts repo,
report, apply, run pytest, commit there. This file is only the engine.

    python3 scripts/tidy_drafts.py                  # report, change nothing
    python3 scripts/tidy_drafts.py --apply          # write the fixes
    python3 scripts/tidy_drafts.py --only quoting,meta

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

  - It never touches a `QQ` line. HANDOVER §5, issue #426.
  - It never touches `source:` -- a citation is reproduced as the publication
    spells it, so "Cafe Delites" is correct and accenting it is a misquote.
  - It never touches a slug or filename, which must stay ASCII.
  - It never resolves a CONTENT judgement. Which milk, which flour, which
    mustard, whether an oven figure is the fan one, whether a note's first word
    is a proper noun -- ~25 rules and 600-odd hits across the corpus, listed in
    test_drafts.py's NOT_FOR_DRAFTS, every one of which needs Helen or her
    source material. They are reported and left alone.
  - It never renames a file, and never retitles one. A title/slug divergence is
    reported with both strings; the one precedent went the file's way, not the
    title's (HANDOVER §10.1), and it is a decision each time.
  - It never runs a YAML dumper over a draft.

SCOPE SETTLED WITH HELEN, 2026-08-29: pure formatting, plus the #429 `meta:`
migration, plus title/slug divergence as a REPORT. Size words (108 drafts,
moving a word between `amount:` and `item:`) were considered and excluded --
mechanical in shape, but it rewrites two fields per hit and the precedent
records real fixes that needed an eye.

Cocktail drafts are deliberately out of scope: that schema is mid-migration
(#544, #571, #573), so a tidy pass there would be fixing things about to change
shape. Revisit when it settles.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "_food_drafts"
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
from test_taxonomy import _head_clause_words  # noqa: E402

FLOW_FIELDS = ["main_ingredients", "tags"]

# The retired keys that live under `meta:` -- derived from the suite's own
# authoritative RETIRED dict (HANDOVER §4 calls it that), not listed again.
# Anything retired at the TOP level is a different rule and not this script's.
META_RETIRED = [k for k in RETIRED if k not in META_ORDER]

# Optional and additive, and legitimate on a DRAFT alongside the three
# (HANDOVER §4, issue #418). The recipe-side rule forbids it outright, which is
# why it is named here and not in META_ORDER.
META_OPTIONAL = ["claude_rewritten"]

ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER_RANGE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)(?![\d.])")
# `QQ Claude` IS EXCLUDED, and deliberately -- see the long note on `_QQ_LINE`
# in tests/conftest.py, which this mirrors. The marker protects SOMEBODY ELSE'S
# wording; a `QQ Claude` line is the paraphrase written here, and HANDOVER §4
# holds it to normal house style like any other prose. Fifteen hyphenated
# number ranges were hiding behind the old pattern on 2026-09-01.
QQ_LINE = re.compile(r"^\s*(-\s*)?[\"']?QQ\b(?!\s+Claude\b)")


# =============================================================================
# Reading the corpus
# =============================================================================

def load_drafts():
    """Every draft, or a loud refusal. Never an empty list treated as success.

    #537's lesson, and it cost the glass icons twice in two days: a script whose
    input is legitimately empty most of the time must check BEFORE it acts, not
    report `0 files ->` as though that were a result.
    """
    if not DRAFTS.is_dir():
        sys.exit(
            f"{DRAFTS.name}/ is not here. It is a separate private repo "
            f"(helen-triages-food-private), gitignored from this one, so a "
            f"clean checkout does not have it. Nothing to tidy; nothing done."
        )
    files = sorted(DRAFTS.rglob("*.md"))
    if not files:
        sys.exit(
            f"{DRAFTS.name}/ exists but holds no .md files. That is not the "
            f"absent-repo case, so either the checkout is broken or this glob "
            f"has gone stale. Refusing to report success over an empty corpus."
        )
    return files


def split_front_matter(text):
    m = FRONT_MATTER.match(text)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3), text[m.end():]


def is_qq(line):
    return bool(QQ_LINE.match(line))


# =============================================================================
# FIXERS -- each takes the whole file text and returns (new_text, [what changed])
# =============================================================================

def fix_scalar_quoting(text, path):
    parts = split_front_matter(text)
    if not parts:
        return text, []
    open_, fm, close, body = parts
    changed, out = [], []
    for line in fm.split("\n"):
        m = re.match(rf"^({'|'.join(SCALAR_STRING_FIELDS)}):([ \t]*)(.+)$", line)
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
    measured 2026-08-29 -- and HANDOVER §5 says in as many words that
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


FIXERS = [
    ("quoting", fix_scalar_quoting),
    ("quoting", fix_flow_quoting),
    ("dashes", fix_en_dashes),
    ("typography", fix_typography),
    ("accents", fix_accents),
    ("meta", fix_meta_block),
]


# =============================================================================
# REPORTERS -- never fixed, always surfaced
# =============================================================================

# BOTH PREDICATES ARE IMPORTED FROM THE SUITE, NOT RE-TYPED, and the first
# draft of this file proves why. It invented its own versions and both flooded:
#
#   - a title/slug check comparing a slugified title to the filename reported
#     `watercress-and-beef-noodle-soup` against `watercress-beef-noodle-soup`,
#     i.e. the ordinary convention of dropping a stopword, plus garbage for
#     every accented title ("Comté" -> "comt"). The real rule is much narrower:
#     every word of the title's HEAD CLAUSE must appear somewhere in the slug.
#   - a CLAUDE-marker scan with re.I on it matched `QQ Claude ...`, which is the
#     documented interleaved-rewrite convention (HANDOVER §4) and not an
#     instruction at all. The real rule is case-sensitive.
#
# Between them they reported hundreds of files as needing attention, and every
# one was a documented convention. HANDOVER §12: "if you scan and find lots of
# problems, be suspicious of your own findings before reporting them."
CLAUDE_MARKER = re.compile(r"[^\"\n]{0,10}\bCLAUDE\b[^\"\n]{0,40}")


def report_title_slug(path, text):
    m = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.M)
    if not m:
        return []
    missing = _head_clause_words(m.group(1)) - set(re.findall(r"[a-z0-9]+", path.stem))
    if not missing:
        return []
    return [f"title/slug divergence: head-clause word(s) {sorted(missing)} "
            f"appear nowhere in the filename. Title {m.group(1)!r}, file "
            f"{path.stem!r}. Either the title changed without a rename or the "
            f"rename never happened -- confirm WHICH before touching either. "
            f"Never fixed here."]


def report_claude_markers(path, text):
    return [f"instruction left for Claude: {h.strip()[:70]}"
            for h in CLAUDE_MARKER.findall(text)]


REPORTERS = [report_title_slug, report_claude_markers]


# =============================================================================

def dirty_drafts():
    r = subprocess.run(["git", "status", "--porcelain"], cwd=DRAFTS,
                       capture_output=True, text=True)
    return [l for l in r.stdout.split("\n") if l.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write the fixes; without it nothing is changed")
    ap.add_argument("--only", default="",
                    help="comma-separated subset of: "
                         + ",".join(sorted({n for n, _ in FIXERS})))
    ap.add_argument("--allow-dirty", action="store_true",
                    help="run even though _food_drafts/ has uncommitted changes")
    ap.add_argument("--drafts-dir", default=None,
                    help="operate on a different directory. Exists so this can "
                         "be proved against a COPY before it is ever pointed "
                         "at Helen's real drafts -- see the command doc.")
    args = ap.parse_args()

    if args.drafts_dir:
        global DRAFTS
        DRAFTS = Path(args.drafts_dir).resolve()

    wanted = {s.strip() for s in args.only.split(",") if s.strip()}
    unknown = wanted - {n for n, _ in FIXERS}
    if unknown:
        sys.exit(f"--only names no such rule: {sorted(unknown)}")

    files = load_drafts()

    if args.apply and not args.allow_dirty:
        dirt = dirty_drafts()
        if dirt:
            sys.exit(
                f"_food_drafts/ has {len(dirt)} uncommitted change(s):\n  "
                + "\n  ".join(dirt[:10])
                + "\n\nRefusing to write on top of them, because the whole "
                  "safety story here is that you can read the diff afterwards "
                  "and see exactly what this script did. Mixed in with your own "
                  "edits you cannot. Commit or stash them first, or pass "
                  "--allow-dirty if you know they are unrelated."
            )

    fixed, reports, total = {}, {}, 0
    for path in files:
        text = original = path.read_text(encoding="utf-8")
        notes = []
        for name, fn in FIXERS:
            if wanted and name not in wanted:
                continue
            text, said = fn(text, path)
            notes += [f"[{name}] {s}" for s in said]
        found = []
        for reporter in REPORTERS:
            found += reporter(path, original)

        rel = path.relative_to(ROOT).as_posix()
        if notes:
            fixed[rel] = notes
            total += len([n for n in notes if "REPORT ONLY" not in n
                          and "SKIPPED" not in n])
        if found:
            reports[rel] = found
        if args.apply and text != original:
            path.write_text(text, encoding="utf-8")

    verb = "applied" if args.apply else "would apply"
    print(f"{len(files)} drafts scanned.\n")
    print(f"=== {verb} {total} mechanical change(s) across {len(fixed)} file(s)")
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

    print("\n=== NOT looked at, and deliberately")
    print("  Content judgement -- which milk, which flour, which mustard, "
          "whether an\n  oven figure is the fan one, whether a note's first "
          "word is a proper noun.\n  ~25 rules, listed with counts in "
          "tests/test_drafts.py's NOT_FOR_DRAFTS.\n  Every one needs Helen or "
          "her source material. Run pytest to see them.")
    if not args.apply:
        print("\nNothing was written. Re-run with --apply to write the fixes.")


if __name__ == "__main__":
    main()
