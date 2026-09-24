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
BEFORE = '''---
title: "Test Drink"
tagline: Sharp -- and bright, 2-3 dashes of it
glass:
  - "old fashioned"
garnish:
  - "lemon twist"
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
mood:
  - "clear"
notes:
  - label: "Balance"
    text: "Give it 2-3 stirs more than you think."
  - label: "QQ"
    text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"
source: ""
source_url: ""
meta:
  ship: "meh"
  rewritten: false
  awaiting_fix: false
  proofread: false
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
mood:
  - "clear"
notes:
  - label: "Balance"
    text: "Give it 2–3 stirs more than you think."
  - label: "QQ"
    text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"
source: ""
source_url: ""
meta:
  ship: "meh"
  rewritten: false
  awaiting_fix: false
  proofread: false
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


def run(root, *extra):
    """The script as Helen runs it, on a copy, with the drinks rules."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--site", "cocktails",
         "--drafts-dir", str(root), "--allow-dirty", *extra],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"the script exited {result.returncode}:\n{result.stdout}\n"
        f"{result.stderr}"
    )
    return result.stdout


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
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--site", "food",
         "--drafts-dir", str(root), "--allow-dirty", *extra],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"the script exited {result.returncode}:\n{result.stdout}\n{result.stderr}"
    )
    return result.stdout


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
