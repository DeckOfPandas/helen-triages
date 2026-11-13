#!/usr/bin/env python3
"""Run the published collection's per-recipe rules against food drafts, in
place, and sort what they find. Reads only; nothing is copied or written.

    python3 scripts/promotion_qa.py                  # 1-rewrite/, 2-make/, 3-keep/, 4-promote/
    python3 scripts/promotion_qa.py 3-keep 2-make/fish-pie.md

Every function in tests/test_style.py, test_front_matter.py and
test_taxonomy.py taking a single `recipe` is called on conftest.Recipe(path).
Findings are grouped: AT 3-KEEP (fine before then, fixed when the draft reaches
3-keep/: the empty note pair, a link to another draft, a draft's
`claude_rewritten` flag), HELEN'S (conftest.HELENS_RULES: a QQ and the rules
only she settles) and FIX (everything else). In 3-keep/ and 4-promote/ the
suite enforces the same rules (conftest.STAGED_DRAFTS); this is the report
that sorts them. PIPELINE.md §3 says when this runs.
"""
import importlib
import inspect
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "_food_drafts"
FOLDERS = ["1-rewrite", "2-make", "3-keep", "4-promote"]
MODULES = ["test_style", "test_front_matter", "test_taxonomy"]

AT_3_KEEP = {"test_note_dicts_have_label_and_text", "test_internal_recipe_links_resolve",
             "test_meta_block_is_exactly_the_three_flags_in_order"}


def targets(args):
    paths = []
    for a in args or FOLDERS:
        p = DRAFTS / a
        if p.is_dir():
            paths += sorted(p.glob("*.md"))
        elif p.suffix == ".md" and p.exists():
            paths.append(p)
        else:
            sys.exit(f"promotion_qa.py: no draft or folder {a!r} under _food_drafts/")
    return paths


def main(argv):
    sys.path.insert(0, str(ROOT / "tests"))
    conftest = importlib.import_module("conftest")
    rules = [(n, f) for m in MODULES for n, f in inspect.getmembers(importlib.import_module(m), inspect.isfunction)
             if n.startswith("test_") and f.__module__ == m
             and list(inspect.signature(f).parameters) == ["recipe"]]
    totals = {"FIX": 0, "HELEN'S": 0, "AT 3-KEEP": 0}
    for path in targets(argv):
        recipe = conftest.Recipe(path)
        staged = path.parent.name in conftest.STAGED_FOLDERS
        found = []
        for name, rule in rules:
            try:
                rule(recipe)
            except AssertionError as e:
                group = ("HELEN'S" if name in conftest.HELENS_RULES
                         else "AT 3-KEEP" if name in AT_3_KEEP and not staged else "FIX")
                first = (str(e).strip().splitlines() or ["(no message)"])[0]
                found.append((group, f"{name}: {first[:200]}"))
            except BaseException as e:
                if type(e).__name__ not in ("Skipped", "XFailed"):
                    found.append(("FIX", f"{name}: ERROR {type(e).__name__}: {str(e)[:150]}"))
        print(f"== {path.relative_to(DRAFTS)}")
        for group in ("FIX", "HELEN'S", "AT 3-KEEP"):
            for _, line in [f for f in found if f[0] == group]:
                print(f"   {group}: {line}")
                totals[group] += 1
    print(", ".join(f"{k}: {v}" for k, v in totals.items()))
    return 1 if totals["FIX"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
