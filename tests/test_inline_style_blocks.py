"""Inline `<style>` blocks parse — issue #649.

A stray `*/` in a `<style>` block cost Helen three rounds on 2026-09-01 and was
invisible to everything in the suite. The identical slip in a `.scss` file is a
loud build error; Jekyll does not parse inline `<style>`, Sass never sees it, and
nothing else looked.

ITS OWN MODULE RATHER THAN A TAIL ON test_site_config.py. The question is about a
CSS construct, not about site configuration -- it started there only because the
source-scanning helpers did. Keeping it separate also stops three branches
appending to the end of one file and conflicting over it, which is what actually
prompted the move.
"""
from __future__ import annotations

import pathlib
import re

import pytest

# Suite marker, so `pytest -m shared` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parent.parent


# --- an inline <style> block whose comments do not balance --------------------
#
# #649. A stray `*/` in a `<style>` block cost Helen three rounds on 2026-09-01
# and was invisible to every test here.
#
# WHAT IT DOES TO A PAGE, because "a typo in a comment" undersells it. Prose was
# written into a declaration block after the comment above it had closed. The
# parser met raw text, recovered by skipping to the next `;`, and swallowed a
# custom property on the way -- so `padding: var(--that-property) ...` became
# invalid at computed-value time and computed to its INITIAL value, zero, on all
# four sides. And it was not one stray delimiter but NINETEEN: the first inverted
# the parser, and from there every comment was read as CSS and every rule as
# comment.
#
# THE ASYMMETRY IS THE WHOLE ISSUE. The identical slip in a `.scss` file is a
# loud build error. Jekyll does not parse inline `<style>`, Sass never sees it,
# and nothing else looked -- so the same mistake is caught instantly in one place
# and silently in the other, and the silent one is where hand-written comparison
# CSS goes.
#
# IT RECURRED WITHIN THE HOUR, in the same file, while the fix was being written
# up. That is HANDOVER 12's "you will write down a rule instead of following it",
# and it is why this is a test rather than a note.
#
# SCOPE: `_dev/` pages are `output: false` and never ship, so this guards a
# development INSTRUMENT rather than the shipped site. That is an argument for
# keeping it cheap, not for skipping it -- the instrument is what Helen looks at,
# and her three rounds are the cost being avoided.

STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)


def _comment_faults(css: str):
    """Unbalanced or nested CSS comment delimiters, as (line, what) pairs.

    A HAND SCANNER RATHER THAN A CSS PARSER, deliberately. The failure being
    caught is exactly a delimiter one, there is no CSS parser in this
    environment, and a real parser would also have to be taught that these
    blocks contain Liquid. Strings are tracked because `content: "*/"` is legal
    and must not read as a delimiter.
    """
    faults = []
    i, line, n = 0, 1, len(css)
    in_comment = False
    comment_line = 0
    quote = None
    while i < n:
        ch = css[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if in_comment:
            if css.startswith("*/", i):
                in_comment = False
                i += 2
                continue
            if css.startswith("/*", i):
                # CSS comments do not nest; this is the shape the 2026-09-01
                # slip made 19 times over, once the parser had been inverted.
                faults.append((line, "`/*` opened inside a comment "
                                     f"(already open since line {comment_line})"))
                i += 2
                continue
            i += 1
            continue
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            i += 1
            continue
        if css.startswith("/*", i):
            in_comment = True
            comment_line = line
            i += 2
            continue
        if css.startswith("*/", i):
            faults.append((line, "`*/` closes a comment that was never opened"))
            i += 2
            continue
        i += 1
    if in_comment:
        faults.append((comment_line, "`/*` is never closed"))
    return faults


def _pages_with_inline_style():
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in {"tmp", "_site", "node_modules", ".git"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "<style" in text:
            yield rel, text


def test_every_inline_style_block_has_balanced_comments():
    """A `*/` that closes nothing inverts the parser for the rest of the block.

    Run over every page in the repo carrying a `<style>`, not just `_dev/`: the
    four that have one today are all dev instruments, and the rule is about the
    construct rather than the folder.
    """
    problems = []
    found = 0
    for rel, text in _pages_with_inline_style():
        for block in STYLE_BLOCK.findall(text):
            found += 1
            # Line number of the block's start, so the report points somewhere.
            offset = text.index(block)
            base = text[:offset].count("\n")
            for line, what in _comment_faults(block):
                problems.append(f"{rel}:{base + line}  {what}")

    assert found, (
        "No inline <style> block was found anywhere in the repo. Either they "
        "have all gone (in which case delete this test) or this scanner has "
        "stopped finding them -- the second is the one that fails quietly."
    )
    assert not problems, (
        "Unbalanced CSS comments in an inline <style> block. The parser treats "
        "everything after the first stray delimiter as the opposite of what it "
        "looks like -- rules become comments and comments become rules -- and "
        "nothing else in the build says so:\n  " + "\n  ".join(problems)
    )


def test_the_comment_scanner_catches_the_2026_09_01_shape():
    """The guard's own guard: a scanner that never fires protects nothing.

    Written because this test is otherwise unfalsifiable in the repo's happy
    state -- every real block balances, so a scanner returning `[]` for
    everything would pass `test_every_inline_style_block_has_balanced_comments`
    for ever and look like it was working.
    """
    # The real shape: prose written after the comment above it had closed.
    broken = """
      .thing {
        /* a note about padding */
        padding: var(--pad);
        and then some prose that was meant to be inside the comment */
      }
    """
    faults = _comment_faults(broken)
    assert faults, "the scanner did not see a `*/` closing nothing."
    assert "never opened" in faults[0][1]

    assert _comment_faults("/* fine */ .a { color: red; }") == []
    assert _comment_faults('.a::after { content: "*/"; }') == [], (
        "a `*/` inside a string is legal CSS and must not be read as a "
        "delimiter, or the guard cries wolf on correct code."
    )
    assert _comment_faults("/* unterminated") != []
    assert _comment_faults("/* outer /* inner */") != [], (
        "CSS comments do not nest; the second `/*` is the 2026-09-01 shape."
    )
