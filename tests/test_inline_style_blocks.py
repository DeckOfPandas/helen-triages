"""Inline `<style>` blocks parse — issue #649.

A stray `*/` in a `.scss` file is a loud build error. In an inline `<style>`
block it is silent: Jekyll does not parse the block and Sass never sees it. The
parser recovers by skipping to the next `;`, which can swallow a custom
property, and from the first stray delimiter on every comment reads as CSS and
every rule as comment.

`_dev/` pages never ship, so this guards a development instrument: the pages
Helen looks at when comparing candidates.
"""
from __future__ import annotations

import pathlib
import re

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parent.parent

STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)


def _comment_faults(css: str):
    """Unbalanced or nested CSS comment delimiters, as (line, what) pairs.

    A hand scanner and not a CSS parser, deliberately: the failure is a
    delimiter one, and a real parser would have to be taught that these
    blocks contain Liquid. Strings are tracked because `content: "*/"` is
    legal and must not read as a delimiter.
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
                # CSS comments do not nest.
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

    Run over every page in the repo carrying a `<style>`, not just `_dev/`:
    the rule is about the construct, not the folder.
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

    Every real block balances, so a scanner returning `[]` for everything
    would pass `test_every_inline_style_block_has_balanced_comments` for ever.
    """
    # Prose written after the comment above it had closed.
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
