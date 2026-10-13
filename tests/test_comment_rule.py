"""The comment rule in CLAUDE.md, "Writing -- replace, never append", held as a
ratchet: a comment block is at most eight lines (fifteen at the head of a
file), and a comment carries no date.

Whole-line comments only. Not read: a Python docstring, a JSDoc `@param` or
`@returns` line, and a shell script's header, which is its manual.
`KNOWN_LONG` and `KNOWN_DATED` are the exceptions, as a count per file, each
with its reason. A count never rises: shorten the comment, or put the story
in the commit message.
"""
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.shared

ROOT = Path(__file__).resolve().parent.parent
HASH = {".py", ".yml", ".yaml", ".rb", ".sh"}
SLASH = {".js", ".scss"}
MARKUP = {".html"}
# Recipes and documents are prose; fixtures and the image are not ours to trim.
NOT_SCANNED = ("_food_recipes/", "_cocktail_recipes/", "model_instructions/",
               "tests/fixtures/", ".devcontainer/", "assets/vendor/")
DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
BLOCK_LINES, HEADER_LINES = 8, 15

KNOWN_LONG = {
    # Not a comment: a string the script writes out as a YAML header.
    "scripts/build_cooking_methods_prose.py": 1,
}

KNOWN_DATED = {
    # Not a comment: a line of a block scalar that opens with an issue number.
    "_data/cocktails/ingredients.yml": 1,
    # The three below quote a date as an example of the text their code reads.
    "scripts/build_decisions_index.py": 2,
    "tests/conftest.py": 1,
    "tests/test_style.py": 1,
}


def _comment_lines(path, lines):
    """(line number, text) for each whole-line comment in a file."""
    if path.suffix in HASH:
        for n, line in enumerate(lines, 1):
            s = line.strip()
            if s.startswith("#") and not s.startswith("#!"):
                yield n, s
    elif path.suffix in SLASH:
        inside = False
        for n, line in enumerate(lines, 1):
            s = line.strip()
            if inside:
                if not s.startswith("* @"):
                    yield n, s
                inside = "*/" not in s
            elif s.startswith("//"):
                yield n, s
            elif s.startswith("/*"):
                yield n, s
                inside = "*/" not in s
    else:
        closer = None
        for n, line in enumerate(lines, 1):
            s = line.strip()
            if closer:
                yield n, s
                if closer in s:
                    closer = None
            elif re.match(r"\{%-?\s*comment", s):
                yield n, s
                closer = None if "endcomment" in s else "endcomment"
            elif s.startswith("<!--"):
                yield n, s
                closer = None if "-->" in s else "-->"


def _scan():
    """{file: (long blocks, dated lines)}, each a list of line numbers."""
    listed = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.split("\n")
    found = {}
    for name in listed:
        path = ROOT / name
        if (not name or name.startswith(NOT_SCANNED) or not path.is_file()
                or path.suffix not in HASH | SLASH | MARKUP):
            continue
        lines = path.read_text(encoding="utf-8").split("\n")
        long_blocks, dated, start, prev = [], [], None, None
        for n, text in list(_comment_lines(path, lines)) + [(None, "")]:
            if n is not None and DATE.search(text):
                dated.append(n)
            if n is not None and prev is not None and n == prev + 1:
                prev = n
                continue
            if start is not None:
                header = start <= 3
                limit = HEADER_LINES if header else BLOCK_LINES
                if prev - start + 1 > limit and not (header and path.suffix == ".sh"):
                    long_blocks.append(start)
            start = prev = n
        found[name] = (long_blocks, dated)
    return found


def test_the_scan_reads_comments_in_every_kind_of_file():
    """An empty scan would pass both tests below, so it is refused here."""
    found = _scan()
    for suffix in sorted((HASH | SLASH | MARKUP) - {".yaml"}):
        assert any(name.endswith(suffix) for name in found), (
            f"no {suffix} file was scanned: `git ls-files` returned nothing "
            "the comment rule could read"
        )


def test_no_comment_block_is_longer_than_the_rule_allows():
    """A whole-line comment block is at most eight lines, fifteen as a file
    header. A file may hold as many longer ones as `KNOWN_LONG` says."""
    over = []
    for name, (long_blocks, _) in sorted(_scan().items()):
        if len(long_blocks) > KNOWN_LONG.get(name, 0):
            starts = ", ".join(str(n) for n in long_blocks)
            over.append(f"{name}: {len(long_blocks)} long blocks (allowed "
                        f"{KNOWN_LONG.get(name, 0)}), starting at lines {starts}")
    assert not over, (
        "A comment block is over eight lines (fifteen at the head of a file):\n  "
        + "\n  ".join(over)
        + "\nKeep the constraint, in the present tense, and put the story in "
        "the commit message. CLAUDE.md, 'Writing -- replace, never append'."
    )


def test_no_comment_carries_a_date():
    """A comment says what must stay true, not when it was found. A file may
    hold as many dated comment lines as `KNOWN_DATED` says."""
    over = []
    for name, (_, dated) in sorted(_scan().items()):
        if len(dated) > KNOWN_DATED.get(name, 0):
            lines = ", ".join(str(n) for n in dated)
            over.append(f"{name}: {len(dated)} dated lines (allowed "
                        f"{KNOWN_DATED.get(name, 0)}), lines {lines}")
    assert not over, (
        "A comment carries a date:\n  " + "\n  ".join(over)
        + "\nThe date belongs in the commit message, and a ruling of Helen's "
        "in DECISIONS.md. CLAUDE.md, 'Writing -- replace, never append'."
    )
