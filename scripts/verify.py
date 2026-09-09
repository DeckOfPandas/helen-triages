#!/usr/bin/env python3
"""Run everything that says whether the repo is sound, in one command.

    python3 scripts/verify.py

FOUR CHECKS, AND THE POINT IS THAT THEY ARE ONE COMMAND. MANUAL §1 lists them
separately and they were being typed separately after every change, which has
two costs. The small one is four invocations instead of one. The real one is
that the last two are EASY TO FORGET -- `derive_cocktail_moods.py` is the only
thing that says whether a vocabulary edit silently moved a drink's moods, and
`build_ingest_vocab.py --check` is the only thing that says the standalone
ingest documents still match the data they are rendered from. Both have been
skipped in sessions that ran the two test suites and called it verified.

  pytest                              content and structure
  node --test tests/js/*.test.js      the JS suite
  derive_cocktail_moods.py            did a vocabulary change move a mood?
  build_ingest_vocab.py --check       are the standalone docs in step?

WHY THIS FILE IS COMMITTED AND NOT IN tmp/. It started as a scratch runner, and
`tests/js/cocktail-scale.test.js`'s own header explains why that was the wrong
place: the check it replaced lived in `tmp/smoke_scale_total.js`, "a scratch
file, gitignored, which is exactly the shape of check that stops being run".
Helen asked the same question the first day this existed. A verification step
nobody else can run is a verification step that stops happening.

THE JS FILES ARE GLOBBED HERE, NOT LISTED. The first version named all fourteen
so the shell never saw a `*`, and that is a trap rather than a tidiness: a test
file added tomorrow would be silently skipped and the run would still say PASS.
MANUAL §10 says the glob is required, and Python's glob satisfies it without
handing a wildcard to bash.

ONE PYTEST AT A TIME, still (MANUAL §1). `test_rendered_pages.py` writes
throwaway `zzz-gate-` recipes into the collections and deletes them after; a
second concurrent run collects them as real files and reports failures that
vanish on a clean rerun. This script cannot detect that -- it is on you.

Exits non-zero if anything fails, so it works as a gate.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def js_suite() -> list[str]:
    """`node --test` over every JS test file there is."""
    files = sorted(glob.glob(os.path.join(ROOT, "tests", "js", "*.test.js")))
    return ["node", "--test", *files]


# (name, argv, a string the output must contain for a pass -- or None)
def checks() -> list[tuple[str, list[str], str | None]]:
    return [
        ("pytest", ["python3", "-m", "pytest", "-q"], None),
        ("node --test", js_suite(), "# fail 0"),
        ("moods", ["python3", "scripts/derive_cocktail_moods.py"], "0 differ"),
        ("ingest vocab", ["python3", "scripts/build_ingest_vocab.py", "--check"],
         "matches its generator"),
    ]


def main() -> int:
    js = js_suite()
    if len(js) <= 2:
        print("No JS test files found -- the glob is wrong, or you are not in "
              "the repo root. Refusing to report a pass on zero tests.")
        return 1

    failed = []
    for name, cmd, expect in checks():
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               timeout=1800)
        except FileNotFoundError as exc:
            print("%-14s SKIP   %s" % (name, exc))
            failed.append(name)
            continue

        out = (r.stdout + r.stderr).strip()
        lines = [ln for ln in out.split("\n") if ln.strip()]

        ok = r.returncode == 0
        if ok and expect:
            ok = expect in out
        # pytest exits 0 with `-q` even when the tail says failures, in some
        # wrappers; ask the output as well as the code.
        if name == "pytest":
            ok = ok and " failed" not in out

        print("%-14s %s   %s" % (name, "PASS" if ok else "FAIL",
                                 (lines[-1] if lines else "")[:84]))
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
    print("All green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
