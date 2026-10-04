"""The Ruby amount parser, tested without a Jekyll build -- #1199.

`_plugins/amount.rb` is the one reading of an `amount:` string that the costs,
units and card generators share. Until 2026-10-04 it was a regex retyped in
each of them, exercised only through rendered pages.

`tests/fixtures/amounts.json` is the golden file: every distinct amount in the
published cocktail collection, plus a few shapes worth pinning, each with what
the Ruby parser reads (`number`, `unit`, `ml`) and what the browser's
`parseAmount` reads (`js`). `tests/js/shopping-list.test.js` reads the same
rows, so the two languages are held to one file.

THE TWO PARSERS ARE NOT THE SAME GRAMMAR AND THE FILE SAYS WHERE. The JS one
folds a plural (`dashes` -> `dash`), reads a bare `15` as a count and `half` as
0.5; the Ruby one keeps the unit as written and reads neither. Those rows are
in the fixture so the difference is a recorded fact, not a discovery.
"""
import json
import shutil
import subprocess

import pytest
import yaml

from conftest import ROOT

pytestmark = pytest.mark.cocktails

FIXTURE = ROOT / "tests" / "fixtures" / "amounts.json"


def _rows():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_the_ruby_parser_reads_every_fixture_amount_as_the_fixture_says():
    assert shutil.which("ruby"), (
        "no `ruby` on the path, so the parser every generator shares cannot be "
        "run. The site cannot build without it either."
    )
    result = subprocess.run(
        ["ruby", "scripts/parse_amounts.rb", str(FIXTURE)],
        cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr[-2000:]
    got = {r["amount"]: (r["number"], r["unit"], r["ml"])
           for r in json.loads(result.stdout)}
    want = {r["amount"]: (r["number"], r["unit"], r["ml"]) for r in _rows()}
    assert want, "the fixture is empty, so this would pass having read nothing"
    wrong = [f"{a!r}: fixture {want[a]}, parser {got.get(a)}"
             for a in want if got.get(a) != want[a]]
    assert not wrong, (
        "_plugins/amount.rb no longer reads these as tests/fixtures/amounts.json "
        "says. If the parser is right, the fixture row is what changes -- by "
        "hand, having read it:\n  " + "\n  ".join(wrong)
    )


def test_the_fixture_holds_every_amount_a_published_drink_writes():
    """A golden file that has not met an amount says nothing about it."""
    known = {r["amount"] for r in _rows()}
    missing = {}
    recipes = sorted((ROOT / "_cocktail_recipes").glob("*.md"))
    assert recipes, "no published drinks found, so nothing was compared"
    for path in recipes:
        fm = yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1]) or {}
        for ing in fm.get("ingredients") or []:
            if isinstance(ing, dict) and "amount" in ing:
                amount = str(ing["amount"]).strip()
                if amount not in known:
                    missing.setdefault(amount, path.stem)
    assert not missing, (
        "tests/fixtures/amounts.json has no row for: "
        + ", ".join(f"{a!r} ({s})" for a, s in sorted(missing.items()))
        + ". Add one, with what each parser should read."
    )


def test_where_both_parsers_read_a_number_it_is_the_same_number():
    """The one thing the two grammars must agree on.

    A row may be a quantity to one parser and not to the other (`15`, `half`),
    and the unit may be folded on one side. But where both say "this is N of
    something", N is N -- or the shopping list and the price disagree about
    how much gin is in a drink.
    """
    both = [r for r in _rows() if r["number"] is not None and r["js"]]
    assert both, "no fixture row is a quantity to both parsers"
    wrong = [f"{r['amount']!r}: ruby {r['number']}, js {r['js']['quantity']}"
             for r in both if float(r["number"]) != float(r["js"]["quantity"])]
    assert not wrong, "the fixture records a disagreement:\n  " + "\n  ".join(wrong)
