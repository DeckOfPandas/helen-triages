#!/usr/bin/env python3
"""Run everything that says whether the repo is sound, in one command.

    python3 scripts/verify.py

  pytest                              content and structure
  node --test tests/js/*.test.js      the JS suite
  derive_cocktail_moods.py            did a vocabulary change move a mood?
  build_ingest_vocab.py --check       are the standalone docs in step?
  check_slug_keys.py                  does every slug-keyed entry name a drink?
  check_glass_regen.py                would regenerating the glasses change one?

A check may report SKIP, which is neither a pass nor a failure (#1106). Exit
code 2 from `check_slug_keys.py` means the drafts clone is absent and it
verified nothing; the run stays green and the line says SKIP.

pytest's line is its pass/skip count, never its last line, which is a timing
(`--durations` in pytest.ini). conftest's "Not evidence about ..." blocks are
printed beneath it, because a green count without them overstates the run.

The JS test files are globbed here, not listed, so a new test file cannot be
left out silently. Never run two of these at once: concurrent runs share one
`.jekyll-cache` and one `tmp/`. Exits non-zero if anything fails.
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# pytest's closing count: "3021 passed, 14 skipped, 2 warnings in 81.2s".
PYTEST_COUNT = re.compile(r"\b\d+ (passed|failed|error|errors|skipped)\b")


def summary(name: str, lines: list[str]) -> str:
    """The one line that says how a check went."""
    if name == "pytest":
        for ln in reversed(lines):
            if PYTEST_COUNT.search(ln):
                return ln.strip("= ")
    return lines[-1] if lines else ""


def caveats(lines: list[str]) -> list[str]:
    """conftest's "Not evidence about ..." blocks, each heading and its body.

    A block is its heading and the indented lines under it, up to the next
    line that is not indented.
    """
    out, inside = [], False
    for ln in lines:
        if ln.startswith("Not evidence about"):
            out.append(ln)
            inside = True
        elif inside and ln.startswith("  "):
            out.append(ln)
        else:
            inside = False
    return out


def js_suite() -> list[str]:
    """`node --test` over every JS test file there is.

    The reporter is pinned to TAP: the `# fail 0` this check looks for is TAP,
    and Node's default reporter differs between versions.
    """
    files = sorted(glob.glob(os.path.join(ROOT, "tests", "js", "*.test.js")))
    return ["node", "--test", "--test-reporter=tap", *files]


# (name, argv, a string the output must contain for a pass -- or None,
#  the exit code that means SKIPPED rather than failed -- or None)
def checks() -> list[tuple[str, list[str], str | None, int | None]]:
    return [
        # No `-q` here: pytest.ini's addopts has one, and a second makes it
        # `-qq`, which prints no pass/skip count at all.
        ("pytest", ["python3", "-m", "pytest"], None, None),
        ("node --test", js_suite(), "# fail 0", None),
        ("moods", ["python3", "scripts/derive_cocktail_moods.py"], "0 differ",
         None),
        ("ingest vocab", ["python3", "scripts/build_ingest_vocab.py", "--check"],
         "matches its generator", None),
        # 2 means "no drafts clone, so I verified nothing" (#1106). Not a
        # failure: the private repo is absent in a fresh worktree and in CI.
        ("slug keys", ["python3", "scripts/check_slug_keys.py"], None, 2),
        ("glass regen", ["python3", "scripts/check_glass_regen.py"],
         "reproduces the shipped set exactly", None),
    ]


def main() -> int:
    js = js_suite()
    if len(js) <= 2:
        print("No JS test files found -- the glob is wrong, or you are not in "
              "the repo root. Refusing to report a pass on zero tests.")
        return 1

    failed, skipped = [], []
    for name, cmd, expect, skip_code in checks():
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               timeout=1800)
        except FileNotFoundError as exc:
            # A missing binary is a failure, not a skip: the check did not run.
            print("%-14s FAIL   %s" % (name, exc))
            failed.append(name)
            continue

        out = (r.stdout + r.stderr).strip()
        lines = [ln for ln in out.split("\n") if ln.strip()]

        if skip_code is not None and r.returncode == skip_code:
            # The check ran, declined to answer, and said why. Its FIRST line
            # carries the reason; the last is the remedy, which is no use here.
            print("%-14s SKIP   %s" % (name, (lines[0] if lines else "")[:84]))
            skipped.append(name)
            continue

        ok = r.returncode == 0
        if ok and expect:
            ok = expect in out
        # pytest exits 0 with `-q` even when the tail says failures, in some
        # wrappers; ask the output as well as the code.
        if name == "pytest":
            ok = ok and " failed" not in out

        print("%-14s %s   %s" % (name, "PASS" if ok else "FAIL",
                                 summary(name, lines)[:84]))
        for ln in caveats(lines):
            print("               " + ln[:160])
        if not ok:
            failed.append(name)
            for ln in lines:
                if any(m in ln for m in ("FAILED", "AssertionError", "not ok",
                                         "Error", "differ")):
                    print("               " + ln[:160])

    print()
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    if skipped:
        print("All green, but " + ", ".join(skipped)
              + " verified nothing -- see the SKIP line above.")
        return 0
    print("All green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
