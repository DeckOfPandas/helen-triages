"""A comment block in a kit file is at most eight lines, fifteen at the head of
a file. A shell script's header is its manual and is not held to it.

Whole-line comments: `#` in Python, shell, YAML and Ruby; `//` and `/* */`
in JavaScript and Sass; `<!-- -->` in HTML. In the kit every tracked file is
read; in a project, only the files .claude/kit/kit.lock lists, so a project's
own code is its own business.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HASH = {".py", ".sh", ".yml", ".yaml", ".rb"}
SLASH = {".js", ".scss"}
MARKUP = {".html"}
BLOCK_LINES, HEADER_LINES = 8, 15


def comment_lines(suffix: str, lines: list[str]):
    """The line numbers of the whole-line comments in a file."""
    inside = None
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if suffix in HASH:
            if s.startswith("#") and not s.startswith("#!"):
                yield n
        elif inside:
            yield n
            if inside in s:
                inside = None
        elif suffix in SLASH and s.startswith("//"):
            yield n
        elif suffix in SLASH and s.startswith("/*"):
            yield n
            inside = None if "*/" in s else "*/"
        elif suffix in MARKUP and s.startswith("<!--"):
            yield n
            inside = None if "-->" in s else "-->"


def long_blocks(suffix: str, text: str) -> list[str]:
    numbers = list(comment_lines(suffix, text.split("\n")))
    found, start = [], None
    for i, n in enumerate(numbers):
        if start is None:
            start = n
        if i + 1 < len(numbers) and numbers[i + 1] == n + 1:
            continue
        header = start <= 3
        limit = HEADER_LINES if header else BLOCK_LINES
        if n - start + 1 > limit and not (header and suffix == ".sh"):
            found.append(f"line {start}: {n - start + 1} lines (limit {limit})")
        start = None
    return found


def kit_files() -> list[str]:
    if (ROOT / "kit" / "manifest").is_file():
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
        return out.stdout.split()
    lock = ROOT / ".claude" / "kit" / "kit.lock"
    return sorted(json.loads(lock.read_text(encoding="utf-8"))["files"]) if lock.is_file() else []


def test_no_kit_comment_block_is_too_long():
    files = [f for f in kit_files() if Path(f).suffix in HASH | SLASH | MARKUP and (ROOT / f).is_file()]
    assert files, "no kit file to read: is this a kit checkout or a synced project?"
    over = [f"{f}: {'; '.join(b)}" for f in files
            if (b := long_blocks(Path(f).suffix, (ROOT / f).read_text(encoding="utf-8")))]
    assert not over, ("comment blocks over eight lines (fifteen at a file's head):\n  "
                      + "\n  ".join(over)
                      + "\nKeep the constraint in the present tense; the story goes in the commit message.")


@pytest.mark.parametrize("suffix,text,expected", [
    (".py", "x = 1\ny = 2\nz = 3\n" + "# a\n" * 9, 1),
    (".py", "x = 1\ny = 2\nz = 3\n" + "# a\n" * 8, 0),
    (".py", "x = 1\n" + "# a\n" * 9, 0),
    (".py", "# a\n" * 15 + "x = 1\n", 0),
    (".py", "# a\n" * 16, 1),
    (".sh", "#!/bin/sh\n" + "# a\n" * 40, 0),
    (".sh", "#!/bin/sh\n# a\nx=1\n" + "# a\n" * 9, 1),
    (".js", "// a\n" * 16, 1),
    (".js", "x();\ny();\nz();\n/*\n" + " * a\n" * 8 + " */\n", 1),
    (".html", "<p>\n<!--\n" + "a\n" * 3 + "-->\n", 0),
])
def test_the_scan_counts_blocks_as_the_rule_says(suffix, text, expected):
    assert len(long_blocks(suffix, text)) == expected
