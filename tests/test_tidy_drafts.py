"""What `/tidy-drafts` does to a DRINK, proved on a fixture and not on Helen's.

`scripts/tidy_drafts.py` grew a cocktails half on 2026-09-05, at Helen's
request: *"Widen please -- cocktail drafts passing will save me a lot of time."*
The food half has been run for real three times and its evidence is the diff it
left behind; the drinks half had no such history, and the first thing anyone
would want to do to get one is point it at `_cocktail_drafts/`. That is exactly
what must not happen while she is proofreading the staged drinks, so this module
is the evidence instead.

NOTHING HERE READS OR WRITES A REAL DRAFTS REPO. Every case builds one drink
under this repo's own `tmp/` and removes it again -- the same construction
`tests/test_ingest_inbox.py` uses and for the same two reasons: `/tmp` is
forbidden by CLAUDE.md, and both private repos are absent in a worktree and in
CI, so a test that needed one would be a test that mostly skips.

THE ASSERTION IS BYTE-FOR-BYTE, and that is the design. "It fixed the six
faults" is easy to satisfy, and easy to satisfy while also doing something else
to the other thirty lines; a script whose whole safety story is "read the diff
afterwards" has to be provable by comparing whole files. So `AFTER` below is the
entire expected output, and every line of it that is not one of the four changed
lines is a line the pass must have left exactly alone.
"""
from __future__ import annotations

import contextlib
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Suite marker, so `pytest -m shared` runs this. test_suite_hygiene.py asserts
# every module declares one -- an unmarked file is silently missed by every
# filtered run. `shared` because the script serves both collections, which is
# also why test_ingest_inbox.py chose it.
pytestmark = pytest.mark.shared

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "tidy_drafts.py"


# =============================================================================
# ONE DRINK, CARRYING EVERY CLASS THE PASS TOUCHES AND EVERY CLASS IT MUST NOT
# =============================================================================
# The faults it MUST fix -- six of them across four lines, all in Helen's own
# prose and every one named by tests/test_cocktails.py:
#
#   1. `tagline:` is an unquoted scalar   test_drink_scalar_fields_are_quoted
#   2. `--` in the tagline                test_drink_typography[double hyphen]
#   3. `--` in an ingredient's note       test_drink_typography[double hyphen]
#   4. `2-3` in the tagline               test_drink_number_ranges_use_en_dashes
#   5. `2-3` in an ingredient's note      test_drink_number_ranges_use_en_dashes
#   6. `2-3` in a note's text             test_drink_number_ranges_use_en_dashes
#
# THE SAME FAULT APPEARS IN MORE THAN ONE PLACE ON PURPOSE. A tagline is the
# obvious prose field and the one anybody would remember to allow; an
# ingredient's `note:` sits two lines below an `amount:` and a `generic:` that
# are both off limits, and a `notes:` entry's `text:` sits directly above a `QQ`
# one. Those are the boundaries worth having a fixture for.
#
# Everything else in the file is a fault of the same MECHANICAL SHAPE sitting
# somewhere the pass does not go, and each is here because leaving it out would
# make the byte-for-byte assertion below prove less than it looks like it does.
#
# THE FIRST POUR USED TO CARRY AN `item:`, and it was the off-limits case for
# "somebody else's words on an ingredient". The field was retired on 2026-09-21,
# and its content moved to where the page can actually show it -- `generic`,
# behind a `QQ `. The fixture followed, which makes it a better case than it
# was: `item` was excluded by being named in a key list, while this line is
# excluded twice over, by `generic` being a closed vocabulary AND by the QQ
# predicate. Both mechanisms have to fail for the `--` in it to be "corrected".
#
# THE KEYS ARE IN PAGE ORDER, since #1213 added the `order` rule to the default
# pass: `meta` and `mood` sit under `garnish`, where the page prints SHIP IT?
# and the mood chips. So the stock fixture gives that rule nothing to do, and
# every count below is still the count of the prose faults alone. The rule's own
# fixture is `ORDER_BEFORE`, further down.
BEFORE = '''---
title: "Test Drink"
tagline: Sharp -- and bright, 2-3 dashes of it
glass:
  - "old fashioned"
garnish:
  - "lemon twist"
meta:
  ship: "meh"
  rewritten: false
  awaiting_fix: false
  proofread: false
mood:
  - "clear"
ingredients:
  - amount: "30-45 ml"
    generic: "QQ Somebody Else's Rum -- as printed on the label"
  - amount: "10 ml"
    generic: "cane sugar syrup 2:1"
    note: "A 2-3 ml difference is not worth measuring -- use the 10."
  - amount: "1 dash"
    generic: "aromatic bitters"
    suggestion:
      - "Angostura"
      - "Peychaud's -- if you have it"
method:
  - "Stir all ingredients with ice."
  - "Strain."
notes:
  - label: "Balance"
    text: "Give it 2-3 stirs more than you think."
  - label: "QQ"
    text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"
source: ""
source_url: ""
---
'''

# FOUR LINES DIFFER FROM `BEFORE` AND NO OTHERS: the tagline (quoted, em dash,
# en dash), the ingredient note (em dash, en dash), and note 1 (en dash). Every
# other line here is copied from BEFORE character for character, including the
# four that carry the identical faults in places the pass does not go.
AFTER = '''---
title: "Test Drink"
tagline: "Sharp — and bright, 2–3 dashes of it"
glass:
  - "old fashioned"
garnish:
  - "lemon twist"
meta:
  ship: "meh"
  rewritten: false
  awaiting_fix: false
  proofread: false
mood:
  - "clear"
ingredients:
  - amount: "30-45 ml"
    generic: "QQ Somebody Else's Rum -- as printed on the label"
  - amount: "10 ml"
    generic: "cane sugar syrup 2:1"
    note: "A 2–3 ml difference is not worth measuring — use the 10."
  - amount: "1 dash"
    generic: "aromatic bitters"
    suggestion:
      - "Angostura"
      - "Peychaud's -- if you have it"
method:
  - "Stir all ingredients with ice."
  - "Strain."
notes:
  - label: "Balance"
    text: "Give it 2–3 stirs more than you think."
  - label: "QQ"
    text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"
source: ""
source_url: ""
---
'''


@pytest.fixture
def drinks():
    """A drafts root under this repo's own `tmp/`, removed afterwards.

    NOT `tmp_path`, and CLAUDE.md is why: nothing in this project writes under
    the system `/tmp`, for any reason. `tmp/` is gitignored here.
    """
    root = ROOT / "tmp" / "test_tidy_drafts_drinks"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    yield root
    shutil.rmtree(root)


# CALLED IN THIS PROCESS, NOT AS A SUBPROCESS -- #1271.
#
# Every test here used to start a fresh Python for the script, and the script
# imports its rules from the suite (conftest, test_front_matter,
# test_cocktails, test_style), so each start re-read and re-parsed every
# recipe, draft and drink before looking at the one fixture file. Measured
# 2026-10-02: about 1.7s a test, 54s for the module. This process has those
# modules loaded already, so `main(argv)` costs milliseconds.
#
# THE COMMAND LINE ITSELF STILL HAS ONE TEST,
# `test_the_command_line_runs_as_helen_types_it`, because an in-process call
# cannot see a script that no longer starts: a broken import at the top, a
# `main()` that stopped reading `sys.argv`, the `__main__` guard going missing.
sys.path.insert(0, str(ROOT / "scripts"))
import tidy_drafts  # noqa: E402


def _tidy(site, root, *extra):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            tidy_drafts.main(["--site", site, "--drafts-dir", str(root),
                              "--allow-dirty", *extra])
        except SystemExit as exc:
            raise AssertionError(
                f"the script exited {exc.code!r}:\n{out.getvalue()}") from exc
    return out.getvalue()


def run(root, *extra):
    """The script's own `main`, on a copy, with the drinks rules."""
    return _tidy("cocktails", root, *extra)


def test_the_command_line_runs_as_helen_types_it(drinks):
    """One real subprocess, and it must say what the in-process call says."""
    path = write_drink(drinks)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--site", "cocktails",
         "--drafts-dir", str(drinks), "--allow-dirty"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"the script exited {result.returncode}:\n{result.stdout}\n"
        f"{result.stderr}"
    )
    assert result.stdout == run(drinks), (
        "The command line and the in-process call disagree about the same "
        "file, so the rest of this module is no longer testing what Helen "
        "runs."
    )
    assert path.read_text(encoding="utf-8") == BEFORE


def write_drink(root, name="test-drink.md", text=BEFORE):
    path = root / name
    path.write_text(text, encoding="utf-8")
    return path


# =============================================================================

def test_the_report_names_every_fault_and_writes_nothing(drinks):
    """Report mode is the default and it is the half that must never write."""
    path = write_drink(drinks)
    out = run(drinks)

    assert "would apply 6 mechanical change(s) across 1 file(s)" in out, out
    assert "[quoting] tagline:" in out, out
    assert out.count("[typography] double hyphen -> em dash") == 2, out
    assert out.count("[dashes]") == 3, out
    assert path.read_text(encoding="utf-8") == BEFORE, (
        "report mode wrote to the file. Nothing else in this module matters if "
        "the default run is not read-only."
    )


def test_apply_fixes_exactly_those_and_touches_nothing_else(drinks):
    """Byte-for-byte, because "it fixed six things" is the weaker claim.

    A LINE-BY-LINE DIFF IN THE FAILURE MESSAGE, not a 34-line repr against
    another 34-line repr. The one bug this script has ever had produced output
    that looked entirely plausible in a diff -- it was caught by parsing the
    result, not by reading it -- so when this does fail, the thing to see first
    is which lines moved.
    """
    path = write_drink(drinks)
    run(drinks, "--apply")
    got = path.read_text(encoding="utf-8")
    if got != AFTER:
        moved = [f"    line {i}\n      want: {w!r}\n      got:  {g!r}"
                 for i, (w, g) in enumerate(zip(AFTER.split("\n"),
                                                got.split("\n")), 1)
                 if w != g]
        pytest.fail("--apply did not produce the expected drink:\n"
                    + "\n".join(moved or ["(line counts differ)"]))


@pytest.mark.parametrize("line", [
    'text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"',
    'amount: "30-45 ml"',
    'generic: "QQ Somebody Else\'s Rum -- as printed on the label"',
    '- "Peychaud\'s -- if you have it"',
])
def test_the_lines_the_pass_must_not_touch_survive_apply(drinks, line):
    """Each of these carries a fault the pass fixes elsewhere in the same file.

    That is the whole point of the parametrisation: `2-3` and `--` are fixed
    three lines up, so a rule that had leaked out of Helen's prose would show
    here rather than in a general "nothing changed" assertion that a
    do-nothing script would also pass.

    A `QQ` NOTE IS THE FIRST CASE AND THE LOAD-BEARING ONE. On a drink the
    marker sits behind a key -- `text: "QQ - ..."` -- and the drinks half asks
    `conftest.checkable_text`, which knows that. This is the test that fails if
    anybody ever "simplifies" it to something that does not.

    THE FOOD PATTERN DID NOT KNOW THAT UNTIL 2026-09-22, and this docstring said
    so approvingly for three weeks -- "the food QQ pattern ... matches that line
    not at all" was written as a reason the DRINKS side is careful, and never
    read as the statement about FOOD that it also was. It was a real hole: 534
    lines in `_food_drafts/` were QQ lines the food pass could not see, five of
    them carrying a fault it would have "corrected". See the test below, which
    is the food half of this one.
    """
    path = write_drink(drinks)
    assert line in path.read_text(encoding="utf-8"), (
        f"the fixture no longer contains {line!r}, so this case is checking "
        f"nothing. Fix the fixture, never this assertion."
    )
    run(drinks, "--apply")
    assert line in path.read_text(encoding="utf-8"), (
        f"the tidy pass edited a line it must leave alone:\n  {line}"
    )


# =============================================================================
# THE FOOD HALF, WHICH DID NOT EXIST UNTIL 2026-09-22
# =============================================================================
# Every test above runs `--site cocktails`. The food rules had no test of which
# lines they must not touch at all, which is how `QQ_LINE` went three weeks
# allowing only a list dash in front of the marker while the drinks half was
# carefully asking a pattern that knew about keys.
#
# THE FIXTURE CARRIES THE SAME FAULT IN BOTH PLACES, exactly as the drinks one
# does: `2-3` and `--` in prose the pass SHOULD fix, and the identical `2-3` and
# `--` behind a `QQ` where it must not. A "nothing changed" assertion would pass
# on a do-nothing script; this one cannot.

FOOD_BEFORE = '''---
title: "Test Recipe"
tagline: "QQ - rewrite: a bright, sharp thing, 2-3 ways"
source: "Adapted from Somebody"
source_type: person
serves: "4"
prep_time: "QQ, plus 30 mins resting -- it needs it"
cook_time: "20 mins"
main_ingredients: ["gnocchi", "sage"]
star_ingredient: "pasta"
tags: ["carbs party"]
ingredient_groups:
  - name: "the lot"
    items:
    - amount: "500 g"
      item: "gnocchi"
      note: "give it 2-3 mins -- no more"
method:
  - "QQ original Fry for 2-3 mins -- until golden."
  - "QQ Claude Fry 2-3 mins -- until golden."
notes:
  - label: "QQ"
    text: "QQ - the source said 2-3 mins -- reproduce, do not correct"
meta:
  rewritten: false
  awaiting_fix: false
  proofread: false
---
'''


@pytest.fixture
def food():
    root = ROOT / "tmp" / "test_tidy_drafts_food"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    yield root
    shutil.rmtree(root)


def run_food(root, *extra):
    return _tidy("food", root, *extra)


@pytest.mark.parametrize("line", [
    'tagline: "QQ - rewrite: a bright, sharp thing, 2-3 ways"',
    'prep_time: "QQ, plus 30 mins resting -- it needs it"',
    '    text: "QQ - the source said 2-3 mins -- reproduce, do not correct"',
    '  - "QQ original Fry for 2-3 mins -- until golden."',
])
def test_a_food_qq_behind_a_key_survives_apply(food, line):
    """A marker behind a KEY is still a marker, and the food pass now knows it.

    THE FOUR CASES ARE THE FOUR SHAPES THE OLD PATTERN MISSED. It allowed an
    optional list dash and an optional quote and nothing else, so only the
    fourth of these -- the method step -- was ever skipped. The other three
    carry `2-3` and `--` that the pass fixes two lines away in the same file,
    so a leak shows here rather than hiding in a general assertion.

    MEASURED WHEN THIS WAS WRITTEN: 534 lines in `_food_drafts/` were QQ lines
    the old pattern could not see, 248 of them taglines added the day before,
    and five in four files carried a fault it would have rewritten.
    """
    path = food / "test-recipe.md"
    path.write_text(FOOD_BEFORE, encoding="utf-8")
    assert line in path.read_text(encoding="utf-8"), (
        f"the fixture no longer contains {line!r}, so this case checks nothing. "
        f"Fix the fixture, never this assertion."
    )
    run_food(food, "--apply")
    assert line in path.read_text(encoding="utf-8"), (
        f"the food tidy pass edited a QQ line it must leave alone:\n  {line}"
    )


def test_a_food_qq_claude_line_is_still_held_to_house_style(food):
    """The one QQ shape the pass MAY edit, and it must still edit it.

    A widened skip that swallowed `QQ Claude` would be the opposite failure and
    just as invisible: that line is our own paraphrase, and MANUAL §4 holds it
    to house style like any other prose. Fifteen hyphenated ranges were hiding
    behind an over-wide pattern on 2026-09-01, which is why this is a test and
    not a comment.
    """
    path = food / "test-recipe.md"
    path.write_text(FOOD_BEFORE, encoding="utf-8")
    run_food(food, "--apply")
    got = path.read_text(encoding="utf-8")
    assert '"QQ Claude Fry 2–3 mins — until golden."' in got, (
        "a `QQ Claude` line is OUR prose and must still be tidied:\n"
        + "\n".join(l for l in got.split("\n") if "QQ Claude" in l)
    )


def test_food_prose_outside_a_qq_is_still_fixed(food):
    """And the pass must still do its job, or the tests above prove nothing."""
    path = food / "test-recipe.md"
    path.write_text(FOOD_BEFORE, encoding="utf-8")
    run_food(food, "--apply")
    got = path.read_text(encoding="utf-8")
    assert 'note: "give it 2–3 mins — no more"' in got, (
        "the ingredient note is Helen's own prose and carries both faults; if "
        "it is untouched the skip has swallowed the whole file:\n"
        + "\n".join(l for l in got.split("\n") if "no more" in l)
    )


# =============================================================================
# THE UNIT SPACE -- Helen, 2026-10-01
# =============================================================================
# "Please add unit spaces (15ml -> 15 ml) as a mechanical fix to perform at
# ingest, and check when I ask you to check drafts."
#
# One fixture carrying every shape the rule meets on the real corpus: a food
# `amount:` (the 13 that drifted from 1,461), an `item:` with a unit mid-phrase,
# a `QQ Claude` line that MUST be fixed, a `QQ original` line that must not, and
# the three near-misses that would be silent if the pattern were loose -- `2kg`
# (which a short-first alternation turns into `2k g`), an already-spaced amount,
# and a temperature, which wants a degree sign from a different rule.
UNITS_BEFORE = '''---
title: "Test Recipe"
tagline: "A test"
source: "Adapted from Somebody"
source_type: person
serves: 4
ingredient_groups:
  - name: ""
    items:
    - amount: "40g"
      item: butter
    - amount: "2kg"
      item: "pork shoulder, in 3cm chunks"
    - amount: "250 ml"
      item: "stock, dissolved in 100ml water"
    - amount: "1"
      item: "tin, in a 9in dish, or 5inches across"
method:
  - "QQ original Melt 40g of butter and heat the oven to 180C."
  - "QQ Claude Melt 40g of butter and heat the oven to 180°C fan."
notes:
  - "Use 15ml of it and keep the rest."
meta:
  rewritten: false
  awaiting_fix: false
  proofread: false
---
'''


def test_unit_spacing_fixes_an_amount_an_item_and_prose(food):
    """The three places food carries a unit, all fixed.

    THE AMOUNT IS THE ONE WORTH A TEST. Measured 2026-10-01 across both food
    collections: `amount:` reads `40 g` 1,461 times and `40g` 13 times, so the
    spaced form is the house form by a factor of 112 and the thirteen are drift.
    On a DRINK the same rule must not reach an amount at all -- see
    test_unit_spacing_never_touches_a_drinks_amount.
    """
    path = food / "test-recipe.md"
    path.write_text(UNITS_BEFORE, encoding="utf-8")
    run_food(food, "--apply")
    got = path.read_text(encoding="utf-8")

    for want in ('amount: "40 g"',
                 'item: "pork shoulder, in 3 cm chunks"',
                 'dissolved in 100 ml water',
                 '"Use 15 ml of it and keep the rest."'):
        assert want in got, (
            f"{want!r} is missing, so the unit space did not land there:\n"
            + got
        )


def test_unit_spacing_matches_the_longest_unit_first(food):
    """A short-first alternation corrupts the unit, and plausibly.

    THIS IS THE ONLY FAILURE IN THE RULE THAT PRODUCES A WRONG ANSWER WHICH
    READS ALMOST RIGHT: `2kg` -> `2k g` and `5inches` -> `5 in ches` both parse
    fine and would survive a skim of the diff. Nothing else here would say so.

    The script sorts `UNITS` by length in code rather than relying on a
    hand-ordered list, so the class is impossible rather than merely tested
    against -- and adding a unit tomorrow cannot reintroduce it. This pins the
    outcome anyway, because the sort is the kind of line somebody "tidies".
    """
    path = food / "test-recipe.md"
    path.write_text(UNITS_BEFORE, encoding="utf-8")
    run_food(food, "--apply")
    got = path.read_text(encoding="utf-8")

    assert 'amount: "2 kg"' in got, "2kg should become 2 kg"
    assert "9 in dish" in got, "9in should become 9 in"
    assert "5 inches across" in got, "5inches should become 5 inches"

    for corrupt in ("2k g", "5 in ches", "9 i n"):
        assert corrupt not in got, (
            f"a shorter unit matched first and corrupted the string: {corrupt!r}\n"
            + got
        )


def test_unit_spacing_leaves_a_qq_original_alone_and_fixes_qq_claude(food):
    """The pair, in one test, because they are one decision.

    A `QQ original` line is the source's own wording awaiting Helen's rewrite,
    and respacing it is editing someone else's text (MANUAL 5). `QQ Claude` is
    OUR paraphrase and is held to house style. A skip wide enough to swallow
    both would pass every other test in this file.
    """
    path = food / "test-recipe.md"
    path.write_text(UNITS_BEFORE, encoding="utf-8")
    run_food(food, "--apply")
    got = path.read_text(encoding="utf-8")

    assert '"QQ original Melt 40g of butter and heat the oven to 180C."' in got, (
        "the QQ original line was edited:\n"
        + "\n".join(l for l in got.split("\n") if "QQ original" in l)
    )
    assert "QQ Claude Melt 40 g of butter" in got, (
        "the QQ Claude line is ours and must be fixed:\n"
        + "\n".join(l for l in got.split("\n") if "QQ Claude" in l)
    )


def test_unit_spacing_leaves_a_temperature_to_its_own_rule(food):
    """`180C` is not this rule's business.

    It wants a DEGREE SIGN, which this script reports and never fixes -- "a
    spelling is a word, not a character". Spacing it to `180 C` would half-fix
    it and make the real fault harder to see, so `C` is deliberately absent from
    the unit list.
    """
    path = food / "test-recipe.md"
    path.write_text(UNITS_BEFORE, encoding="utf-8")
    run_food(food, "--apply")
    got = path.read_text(encoding="utf-8")
    assert "180 C" not in got, (
        "a temperature was spaced by the unit rule, which hides the missing "
        "degree sign:\n"
        + "\n".join(l for l in got.split("\n") if "180" in l)
    )
    assert "180°C fan" in got, "the already-correct temperature was disturbed"


def test_unit_spacing_never_touches_a_drinks_amount(drinks):
    """On a drink the rule reaches Helen's prose and nothing else.

    THE RECORDED HARM, from this script's own doc:
    anitas-attitude-adjuster said `amount: "Top (30-45) ml"` beside a QQ note
    quoting that string back verbatim, so editing the amount desynchronised the
    note from the value it describes. Food has no such pairing and is fixed.

    A drink cannot actually carry `15ml` -- `measures:` declares the unit and
    not the glue, so it would fail test_every_amount_is_readable_as_a_quantity
    first -- which is why this pins the WIRING rather than waiting for a drink
    to prove it.
    """
    path = write_drink(drinks)
    before = path.read_text(encoding="utf-8")
    assert "amount:" in before, "the drinks fixture has no amount to protect"

    run(drinks, "--apply", "--only", "units")
    got = path.read_text(encoding="utf-8")

    before_amounts = [l for l in before.split("\n") if "amount:" in l]
    after_amounts = [l for l in got.split("\n") if "amount:" in l]
    assert before_amounts == after_amounts, (
        "a drink's amount was rewritten by the unit rule:\n"
        + "\n".join(f"  {b}  ->  {a}"
                     for b, a in zip(before_amounts, after_amounts) if a != b)
    )


# =============================================================================
# THE SIZE WORD, #577 -- excluded 2026-08-29, scripted 2026-09-24
# =============================================================================
# One fixture carrying every shape the `size` rule meets on the real corpus, in
# the proportions that matter: the four it MUST move (quoted, bare, item-first,
# two-word `extra large`), and every shape it must NOT -- a weight, a fraction,
# a missing amount, an `or` remainder, `baby`, and a size word behind a `QQ`.
# The file is otherwise clean, so the count in the report is the rule's alone.
SIZE_BEFORE = '''---
title: "Test Recipe"
tagline: "A test"
source: "Adapted from Somebody"
source_type: person
serves: "4"
prep_time: "10 mins"
cook_time: "20 mins"
main_ingredients: ["onions", "eggs"]
star_ingredient: "eggs"
tags: ["carbs party"]
ingredient_groups:
  - name: "the lot"
    items:
    - amount: "2"
      item: "large onions, roughly chopped"
    - amount: "3"
      item: large eggs
      note: "at room temperature"
    - item: "small garlic clove, crushed"
      amount: "1"
    - amount: "2"
      item: "extra large eggs"
    - amount: "400 g"
      item: "large open mushrooms"
    - amount: "½"
      item: "small bunch of chives, finely chopped"
    - item: "small handful of parsley, roughly chopped"
    - amount: "1"
      item: "large or 2 small onions, roughly chopped"
    - amount: "2"
      item: "baby gem lettuces, shredded"
    - amount: "1"
      item: "QQ large tin of something"
method:
  - "Cook it."
notes:
  - label: "Balance"
    text: "Taste it."
meta:
  rewritten: false
  awaiting_fix: false
  proofread: false
---
'''

# EIGHT LINES DIFFER FROM `SIZE_BEFORE` AND NO OTHERS: the amount and the item
# of the first four entries. Every other line is copied character for
# character, including the six entries that carry a size word the rule must
# leave where it is.
SIZE_AFTER = '''---
title: "Test Recipe"
tagline: "A test"
source: "Adapted from Somebody"
source_type: person
serves: "4"
prep_time: "10 mins"
cook_time: "20 mins"
main_ingredients: ["onions", "eggs"]
star_ingredient: "eggs"
tags: ["carbs party"]
ingredient_groups:
  - name: "the lot"
    items:
    - amount: "2 large"
      item: "onions, roughly chopped"
    - amount: "3 large"
      item: eggs
      note: "at room temperature"
    - item: "garlic clove, crushed"
      amount: "1 small"
    - amount: "2 extra large"
      item: "eggs"
    - amount: "400 g"
      item: "large open mushrooms"
    - amount: "½"
      item: "small bunch of chives, finely chopped"
    - item: "small handful of parsley, roughly chopped"
    - amount: "1"
      item: "large or 2 small onions, roughly chopped"
    - amount: "2"
      item: "baby gem lettuces, shredded"
    - amount: "1"
      item: "QQ large tin of something"
method:
  - "Cook it."
notes:
  - label: "Balance"
    text: "Taste it."
meta:
  rewritten: false
  awaiting_fix: false
  proofread: false
---
'''


def test_size_words_report_names_the_moves_and_the_refusals_and_writes_nothing(food):
    path = food / "test-recipe.md"
    path.write_text(SIZE_BEFORE, encoding="utf-8")
    out = run_food(food, "--only", "size")

    assert "would apply 4 mechanical change(s) across 1 file(s)" in out, out
    assert '[size] 2 / large onions, roughly chopped -> "2 large" / "onions, roughly chopped"' in out, out
    assert '[size] 2 / extra large eggs -> "2 extra large" / "eggs"' in out, out
    assert out.count("[size] SKIPPED") == 2, out
    assert "SKIPPED: a second count inside the item" in out, out
    assert "SKIPPED: `baby` is a kind as often as a size" in out, out
    assert "reported, never changed: 1 file(s)" in out, out
    assert ("size word with no count to carry it, left in the item: "
            "small handful of parsley") in out, out
    assert path.read_text(encoding="utf-8") == SIZE_BEFORE, (
        "report mode wrote to the file."
    )


def test_size_words_apply_moves_exactly_four_and_touches_nothing_else(food):
    """Byte for byte, as the drink fixture is, and for the same reason.

    The one bug this script has ever had produced a plausible-looking diff on
    341 files; the size rule rewrites two fields per hit, which is exactly the
    shape Helen excluded it for on 2026-08-29, so the proof is the whole file.
    """
    path = food / "test-recipe.md"
    path.write_text(SIZE_BEFORE, encoding="utf-8")
    run_food(food, "--only", "size", "--apply")
    got = path.read_text(encoding="utf-8")
    if got != SIZE_AFTER:
        moved = [f"    line {i}\n      want: {w!r}\n      got:  {g!r}"
                 for i, (w, g) in enumerate(zip(SIZE_AFTER.split("\n"),
                                                got.split("\n")), 1)
                 if w != g]
        pytest.fail("--apply did not produce the expected recipe:\n"
                    + "\n".join(moved or ["(line counts differ)"]))


def test_size_words_apply_parses_and_satisfies_the_recipe_rule(food):
    """Parsed both sides, on a copy -- the check that caught the `meta:` bug.

    The recipe rule's own predicate, imported and not retyped, must find
    nothing left in the file that the script had the standing to move; what
    remains is the six shapes it refused on purpose, every one of which the
    rule either does not flag (weight, fraction, no amount, QQ) or was left for
    an eye (`or`, `baby`).
    """
    import yaml
    sys.path.insert(0, str(ROOT / "tests"))
    from test_style import _LEADING_SIZE_WORD

    path = food / "test-recipe.md"
    path.write_text(SIZE_BEFORE, encoding="utf-8")
    before = yaml.safe_load(SIZE_BEFORE.split("---\n")[1])
    run_food(food, "--only", "size", "--apply")
    after = yaml.safe_load(path.read_text(encoding="utf-8").split("---\n")[1])

    items_before = before["ingredient_groups"][0]["items"]
    items_after = after["ingredient_groups"][0]["items"]
    assert len(items_before) == len(items_after) == 10
    for b, a in zip(items_before, items_after):
        assert set(b) == set(a), (b, a)
        for key in b:
            if key not in ("amount", "item"):
                assert b[key] == a[key], (key, b, a)
        # The rendered text is unchanged: amount + item reads the same.
        assert f"{b.get('amount', '')} {b['item']}".strip() == \
               f"{a.get('amount', '')} {a['item']}".strip(), (b, a)

    still = [i["item"] for i in items_after
             if re.fullmatch(r"\d+", str(i.get("amount", "")))
             and _LEADING_SIZE_WORD.match(i["item"])]
    assert still == ["large or 2 small onions, roughly chopped",
                     "baby gem lettuces, shredded"], still


def test_size_words_never_run_on_a_drink(drinks):
    """`--only size` on the drinks site changes nothing and says so.

    A drink's `amount` is the recorded harm the module docstring names, and a
    drink has no `item` since 2026-09-21. The rule is in FOOD_FIXERS alone.
    """
    path = write_drink(drinks)
    out = run(drinks, "--only", "size", "--apply")
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE


def test_a_range_in_an_amount_is_reported_rather_than_silently_declined(drinks):
    """The drinks suite fails on it, so the report has to say why it did not.

    `test_drink_number_ranges_use_en_dashes` checks amounts -- Helen, of
    `cook_time: "20-25 mins"`: "These still render to the user, so correct to en
    dash please." This script declines them on a recorded harm
    (anitas-attitude-adjuster, see the module docstring), and a decline that
    prints nothing is indistinguishable from a rule that is not running.
    """
    write_drink(drinks)
    out = run(drinks)
    assert "reported, never changed: 1 file(s)" in out, out
    assert "hyphenated number range, not this pass's to fix" in out, out
    assert '30-45 ml' in out, out


def test_a_file_with_no_front_matter_is_named_and_left_alone(drinks):
    """`_cocktail_drafts/README.md` is the live case and it is prose.

    The three line-wise fixers do not parse front matter, so before 2026-09-05
    a README containing `--` was a file this pass would have em-dashed. Absent
    this test the only symptom would be an em dash in a README nobody diffs.
    """
    write_drink(drinks)
    readme = drinks / "README.md"
    readme.write_text("# Drafts\n\nRun -- carefully -- with 2-3 checks.\n",
                      encoding="utf-8")
    out = run(drinks, "--apply")
    assert "no front matter" in out and "README.md" in out, out
    assert readme.read_text(encoding="utf-8") == (
        "# Drafts\n\nRun -- carefully -- with 2-3 checks.\n"
    )


def test_a_drink_in_a_staging_subfolder_is_reached(drinks):
    """`4-promote/` (`to-promote/` until 2026-09-14) is half the collection and
    a flat glob would miss it.

    22 of the 124 drinks live there. The food side went recursive on 2026-08-20
    for the same reason and the failure was invisible: a flat glob reports the
    files it found, all of them clean, and says nothing about the ones it did
    not look for.
    """
    (drinks / "4-promote").mkdir()
    path = write_drink(drinks, "4-promote/staged.md")
    out = run(drinks)
    assert "4-promote/staged.md" in out, out
    assert "would apply 6 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE


# =============================================================================
# THE NOTES SLOT, #1258
# =============================================================================
# Three notes, one of each kind the rule has to tell apart: imported text with
# an empty label (labelled), the empty pair (a slot, left exactly alone), and a
# note Helen has already headed (hers, left exactly alone).
NOTES_BEFORE = '''  - label: ""
    text: "Serves 4 -- as the source has it."
  - label: ""
    text: ""
  - label: "Balance"
    text: "Give it 2-3 stirs more than you think."
'''
NOTES_AFTER = NOTES_BEFORE.replace(
    '  - label: ""\n    text: "Serves 4', '  - label: "QQ"\n    text: "Serves 4')
STOCK_NOTES = BEFORE[BEFORE.index("notes:\n") + len("notes:\n"):
                     BEFORE.index('source: ""')]


@pytest.mark.parametrize("site", ["cocktails", "food"])
def test_notes_rule_labels_imported_text_and_nothing_else(drinks, site):
    """Byte for byte, on both sites, with the text of every note untouched."""
    before = BEFORE.replace(STOCK_NOTES, NOTES_BEFORE)
    path = write_drink(drinks, text=before)
    runner = run if site == "cocktails" else run_food
    out = runner(drinks, "--only", "notes", "--apply")
    assert "applied 1 mechanical change(s) across 1 file(s)" in out, out
    assert path.read_text(encoding="utf-8") == \
        BEFORE.replace(STOCK_NOTES, NOTES_AFTER)


@pytest.mark.parametrize("empty", ["notes: []\n", "notes:\n", "notes:  [ ]\n"])
def test_notes_rule_turns_an_empty_list_into_a_slot(drinks, empty):
    """`notes: []` -> the empty pair, and the file still parses to exactly that.

    PARSED AS WELL AS COMPARED, because the one bug this script has had wrote a
    plausible diff and an unparseable file.
    """
    import yaml
    path = write_drink(drinks, text=BEFORE.replace("notes:\n" + STOCK_NOTES,
                                                   empty))
    run(drinks, "--only", "notes", "--apply")
    got = path.read_text(encoding="utf-8")
    assert got == BEFORE.replace(STOCK_NOTES,
                                 '  - label: ""\n    text: ""\n'), got
    assert yaml.safe_load(got.split("---\n")[1])["notes"] == \
        [{"label": "", "text": ""}]


def test_notes_rule_is_idempotent_and_leaves_a_finished_file_alone(drinks):
    """The stock fixture has a headed note and a `QQ` one: nothing to do."""
    path = write_drink(drinks)
    out = run(drinks, "--only", "notes", "--apply")
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE


# =============================================================================
# KEY ORDER, #1213
# =============================================================================
# A drink in the order every draft was in before the rule: body first, `mood`
# after the method, `meta` last. It carries every optional key (`serve`,
# `serves`, `to_serve`), a comment INSIDE a block, a nested mapping, a flow
# list, a `{step, note}` pair and a `QQ` line with a `--` in it -- each a thing
# that must arrive in its new place exactly as it left the old one. The prose
# is otherwise clean, so `--only order` and the full pass must agree.
ORDER_BEFORE = '''---
title: "Test Punch"
tagline: "QQ"
snippet: "A line for the search result"
glass:
  - "punch bowl"
garnish: []
ingredients:
  - amount: "30-45 ml"            # a range the pass must not touch
    generic: "QQ Somebody Else's Rum -- as printed"
    suggestion: []
  - amount: "(top)"
    generic: "soda water"
    suggestion: ["Fever-Tree"]
    optional: true
serve:
  ice: "block"
  # a comment inside the block travels with it
  fill: "half"
serves: 8
method:
  - "Stir all ingredients with ice."
  - step: "Strain."
    note: "slowly"
to_serve: "Ladle and punch glasses."
mood:
  - "clear"
notes:
  - label: "QQ"
    text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"
source: ""
source_url: ""
meta:
  made_before: false
  ship: "who knows"
  rewritten: false
  awaiting_fix: false
  proofread: false
---
Body text under the front matter, left exactly alone.
'''

ORDER_AFTER = '''---
title: "Test Punch"
tagline: "QQ"
snippet: "A line for the search result"
glass:
  - "punch bowl"
garnish: []
meta:
  made_before: false
  ship: "who knows"
  rewritten: false
  awaiting_fix: false
  proofread: false
mood:
  - "clear"
ingredients:
  - amount: "30-45 ml"            # a range the pass must not touch
    generic: "QQ Somebody Else's Rum -- as printed"
    suggestion: []
  - amount: "(top)"
    generic: "soda water"
    suggestion: ["Fever-Tree"]
    optional: true
serve:
  ice: "block"
  # a comment inside the block travels with it
  fill: "half"
serves: 8
method:
  - "Stir all ingredients with ice."
  - step: "Strain."
    note: "slowly"
to_serve: "Ladle and punch glasses."
notes:
  - label: "QQ"
    text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"
source: ""
source_url: ""
---
Body text under the front matter, left exactly alone.
'''


def _front_matter(text):
    import yaml
    return yaml.safe_load(text.split("---\n")[1])


def test_key_order_report_names_the_move_and_writes_nothing(drinks):
    path = write_drink(drinks, text=ORDER_BEFORE)
    out = run(drinks, "--only", "order")
    assert "would apply 1 mechanical change(s) across 1 file(s)" in out, out
    assert "[order] top-level keys reordered, no line edited" in out, out
    assert path.read_text(encoding="utf-8") == ORDER_BEFORE


@pytest.mark.parametrize("only", [("--only", "order"), ()],
                         ids=["only-order", "the-full-pass"])
def test_key_order_apply_moves_whole_blocks_and_edits_no_line(drinks, only):
    """Byte for byte, and then the three claims the 2026-08-29 lesson asks for.

    THE DIFF OF A REORDER IS UNREADABLE BY CONSTRUCTION -- every moved block is
    a deletion in one place and an insertion in another -- so "read the diff"
    is worth even less here than it was for the `meta:` rewrite that broke 341
    drafts behind a plausible one. Hence: the same lines as a multiset, the
    same parsed data, and the declared order, each asserted separately so a
    failure says which.
    """
    from test_cocktails import TOP_LEVEL_KEYS_IN_ORDER

    path = write_drink(drinks, text=ORDER_BEFORE)
    run(drinks, "--apply", *only)
    got = path.read_text(encoding="utf-8")

    assert sorted(got.split("\n")) == sorted(ORDER_BEFORE.split("\n")), (
        "the reorder edited, added or dropped a line"
    )
    assert _front_matter(got) == _front_matter(ORDER_BEFORE), (
        "the reorder changed what the file parses to"
    )
    assert list(_front_matter(got)) == TOP_LEVEL_KEYS_IN_ORDER, (
        "the fixture carries every declared key, so after the pass its keys "
        f"are the declared list exactly: {list(_front_matter(got))}"
    )
    if got != ORDER_AFTER:
        moved = [f"    line {i}\n      want: {w!r}\n      got:  {g!r}"
                 for i, (w, g) in enumerate(zip(ORDER_AFTER.split("\n"),
                                                got.split("\n")), 1)
                 if w != g]
        pytest.fail("--only order did not produce the expected drink:\n"
                    + "\n".join(moved or ["(line counts differ)"]))


# =============================================================================
# TITLE CASE, #1089
# =============================================================================

def _titled(title, tagline='"A test"'):
    return BEFORE_CLEAN.replace('title: "Test Drink"', f"title: {title}") \
                       .replace('tagline: "A test"', f"tagline: {tagline}")


# `AFTER` is the tidied fixture, so it has no other fault for the full pass to
# find: whatever changes below is the title rule's doing and nothing else's.
BEFORE_CLEAN = AFTER.replace(
    'tagline: "Sharp — and bright, 2–3 dashes of it"', 'tagline: "A test"')


def test_titles_report_and_apply_change_the_title_line_only(drinks):
    before = _titled('"Frozen ginger Daiquiri (bramble style)"')
    path = write_drink(drinks, text=before)

    out = run(drinks, "--only", "titles")
    assert "[titles] title: Frozen ginger Daiquiri (bramble style) -> " \
           "Frozen Ginger Daiquiri (bramble style)" in out, out
    assert path.read_text(encoding="utf-8") == before, "report mode wrote"

    run(drinks, "--apply")
    assert path.read_text(encoding="utf-8") == \
        _titled('"Frozen Ginger Daiquiri (bramble style)"'), (
            "the full pass should change the title's capitals and nothing "
            "else; the bracketed qualifier keeps its own case"
        )


def test_titles_leave_a_qq_title_alone(drinks):
    """The source's own title, awaiting a rewrite, is not Helen's to restyle."""
    before = _titled('"QQ frozen ginger daiquiri"')
    path = write_drink(drinks, text=before)
    out = run(drinks, "--only", "titles", "--apply")
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == before


def test_titles_are_a_cocktail_rule_only():
    """A food draft's title is the source's until promotion; not in scope."""
    names = [name for name, _ in tidy_drafts.FOOD_FIXERS]
    assert "titles" not in names


def test_key_order_is_idempotent(drinks):
    path = write_drink(drinks, text=ORDER_AFTER)
    out = run(drinks, "--only", "order", "--apply")
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == ORDER_AFTER


@pytest.mark.parametrize("before, why", [
    (ORDER_BEFORE.replace('source: ""\n', '# where it came from\nsource: ""\n'),
     "a column-0 line that is not a key"),
    (ORDER_BEFORE.replace("serves: 8\n", "servings: 8\n"),
     "undeclared key(s) ['servings']"),
    (ORDER_BEFORE.replace('source_url: ""\n', 'source_url: ""\nserves: 8\n'),
     "a top-level key appears twice"),
], ids=["column-0-comment", "undeclared-key", "duplicate-key"])
def test_key_order_refuses_what_needs_an_eye_and_says_so(drinks, before, why):
    """Each is left byte for byte as it was, and named under SKIPPED."""
    assert before != ORDER_BEFORE, "the fixture edit did not land"
    path = write_drink(drinks, text=before)
    out = run(drinks, "--only", "order", "--apply")
    assert "applied 0 mechanical change(s)" in out, out
    assert "[order] SKIPPED: " + why in out, out
    assert path.read_text(encoding="utf-8") == before


def test_key_order_never_runs_on_food(food):
    """`--only order` on the food site changes nothing. Helen asked for
    cocktails; a food recipe's order is not this rule's."""
    path = food / "test-recipe.md"
    path.write_text(FOOD_BEFORE, encoding="utf-8")
    out = run_food(food, "--only", "order", "--apply")
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == FOOD_BEFORE


def test_food_only_rules_do_not_run_on_a_drink(drinks):
    """`--only meta` on the drinks site changes nothing, and says so.

    The #429 `meta:` migration drops two retired keys and reorders three flags.
    A drink's `meta:` is five keys in its own order (test_cocktails.
    META_KEYS_IN_ORDER), two of which food RETIRED -- so the food migration
    pointed at a drink would strip them and reorder what is left, quietly, on
    all 124 files. The rules are in two tables precisely so this cannot happen;
    this is the test that says the tables are still two.
    """
    path = write_drink(drinks)
    out = run(drinks, "--only", "meta", "--apply")
    assert "would apply" not in out
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE, (
        "food's `meta:` migration ran over a drink. Check that DRINK_FIXERS "
        "still omits fix_meta_block."
    )

# =============================================================================
# A FOOD GROUP'S NAME IS QUOTED -- Helen, 2026-10-04
# =============================================================================
# "Let's make future recipes quote group titles, so add that to the tidy pass
# instructions, and ingestion instructions." Asked after #814 left
# `- name: cake` beside `- name: "Make the batter"` in one file.

GROUP_NAMES_BEFORE = (
    "---\n"
    'title: "Fixture"\n'
    "ingredient_groups:\n"
    "  - name: cake\n"
    "    items:\n"
    '      - amount: "100 g"\n'
    '        item: "plain flour"\n'
    '  - name: "lemon curd"\n'
    "    items:\n"
    '      - item: "name: not a group"\n'
    "method_groups:\n"
    "  - name: Make the cake\n"
    "    steps:\n"
    '      - "Mix."\n'
    "  - name: 'to serve'\n"
    "    steps:\n"
    '      - "Serve."\n'
    '  - name: the "good" one\n'
    "    steps:\n"
    '      - "Eat."\n'
    "---\n"
    "Body with - name: prose in it\n"
)


def test_group_names_are_quoted_and_nothing_else_moves():
    new, changed = tidy_drafts.fix_group_name_quoting(GROUP_NAMES_BEFORE, "fixture.md")
    expected = (GROUP_NAMES_BEFORE
                .replace("  - name: cake\n", '  - name: "cake"\n')
                .replace("  - name: Make the cake\n", '  - name: "Make the cake"\n'))
    assert new == expected, (
        "only the two bare group names should gain quotes: an already quoted "
        "name (either quote), an `item:` that merely contains `name:`, the "
        "body, and a name holding a double quote are all left exactly as "
        "written."
    )
    assert [c for c in changed if c.startswith("SKIPPED")] == [
        'SKIPPED group name: contains a double quote: the "good" one'
    ], "a name containing a double quote is reported, never escaped"

    import yaml
    before = yaml.safe_load(GROUP_NAMES_BEFORE.split("---", 2)[1])
    after = yaml.safe_load(new.split("---", 2)[1])
    assert before == after, "quoting a name changed what the file parses to"

    again, changed_again = tidy_drafts.fix_group_name_quoting(new, "fixture.md")
    assert again == new and not [c for c in changed_again if not c.startswith("SKIPPED")], (
        "the rule is not idempotent"
    )


def test_group_name_quoting_is_a_food_rule_under_quoting():
    food = [(n, f) for n, f in tidy_drafts.FOOD_FIXERS
            if f is tidy_drafts.fix_group_name_quoting]
    assert [n for n, _ in food] == ["quoting"], (
        "`--only quoting` on food must include the group names."
    )
    drink_fixers = [getattr(f, "func", f) for _, f in tidy_drafts.DRINK_FIXERS]
    assert tidy_drafts.fix_group_name_quoting not in drink_fixers, (
        "a drink has no groups; this rule has nothing to do there."
    )
