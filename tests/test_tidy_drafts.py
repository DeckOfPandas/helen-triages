"""What `scripts/tidy_drafts.py` does, proved on fixtures and never on Helen's drafts.

Nothing here reads or writes a real drafts repo: every case builds one file
under this repo's own `tmp/` and removes it again, because the system `/tmp`
is forbidden and both private repos are absent in a worktree and in CI.

The assertions are byte for byte: `AFTER` is the entire expected output, so
every line of it that is not a changed line is one the pass must leave alone.
"It fixed the faults" is satisfied by a script that also edits something else.
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

pytestmark = pytest.mark.shared

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "tidy_drafts.py"


# ---- One drink: every fault the pass fixes, and the same faults off limits ----
# To fix: the unquoted `tagline:` (test_drink_scalar_fields_are_quoted), `--`
# in the tagline and an ingredient note (test_drink_typography), and `2-3` in
# the tagline, that note and a note's text
# (test_drink_number_ranges_use_en_dashes). The same `--` and `2-3` sit in an
# `amount`, a `QQ` generic, a `suggestion` and a `QQ` note, where the pass does
# not go. Keys are in page order (#1213), so the `order` rule has nothing to
# do and every count below is the prose faults alone; see `ORDER_BEFORE`.
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

# Four lines differ from `BEFORE` and no others: the tagline (quoted, em dash,
# en dash), the ingredient note (em dash, en dash), and note 1 (en dash).
# Every other line is copied character for character.
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

    Not `tmp_path`: nothing in this project writes under the system `/tmp`.
    """
    root = ROOT / "tmp" / "test_tidy_drafts_drinks"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    yield root
    shutil.rmtree(root)


# Called in this process, not as a subprocess (#1271): the script imports its
# rules from the suite, so each fresh Python re-parses every recipe, draft and
# drink before it looks at the one fixture file.
# `test_the_command_line_runs_as_helen_types_it` is the one real subprocess,
# because an in-process call cannot see a script that no longer starts.
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
    """Byte for byte, because "it fixed six things" is the weaker claim.

    The failure names the lines that moved, not two whole-file reprs.
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

    So a rule that leaks out of Helen's prose shows here; a general "nothing
    changed" assertion is one a do-nothing script also passes. The `QQ` note
    is the load-bearing case: on a drink the marker sits behind a key
    (`text: "QQ - ..."`), which `conftest.checkable_text` knows.
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


# ---- The food half ----
# The fixture carries `2-3` and `--` in prose the pass should fix, and the
# identical faults behind a `QQ` where it must not.

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
    """A marker behind a key is still a marker.

    Three cases sit behind a key and the fourth behind a list dash. Each
    carries a `2-3` or a `--` that the pass fixes elsewhere in the same file,
    so a pattern that sees only the list-dash shape leaks here.
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
    """The one QQ shape the pass may edit, and it must still edit it.

    A `QQ Claude` line is our own paraphrase, held to house style like any
    other prose (MANUAL §5). A skip wide enough to swallow it hides faults as
    invisibly as a leak edits them.
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


# ---- The unit space (DECISIONS §5) ----
# One fixture carrying every shape the rule meets: a food `amount:`, an `item:`
# with a unit mid-phrase, a `QQ Claude` line that must be fixed, a `QQ original`
# line that must not, and three near-misses that are silent if the pattern is
# loose -- `2kg` (a short-first alternation gives `2k g`), an already-spaced
# amount, and a temperature, which wants a degree sign from a different rule.
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

    On a drink the same rule must not reach an amount at all:
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

    `2kg` -> `2k g` and `5inches` -> `5 in ches` both parse and survive a skim
    of the diff. The script sorts `UNITS` by length in code; this pins the
    outcome because that sort is a line somebody tidies away.
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
    and respacing it is editing someone else's text (MANUAL §5). `QQ Claude` is
    our paraphrase and is held to house style. A skip wide enough to swallow
    both passes the other unit tests.
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

    It wants a degree sign, which this script reports and never fixes. Spacing
    it to `180 C` half-fixes it and hides the real fault, so `C` is
    deliberately absent from the unit list.
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

    A `QQ` note may quote an amount back verbatim, so editing the amount
    desynchronises the note from the value it describes (the script's
    docstring has the case). A drink cannot carry `15ml` anyway --
    test_every_amount_is_readable_as_a_quantity fails first -- so this pins
    the wiring, not a live fault.
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


# ---- The size word, #577 ----
# One fixture carrying every shape the `size` rule meets: the four it must move
# (quoted, bare, item-first, two-word `extra large`), and every shape it must
# not -- a weight, a fraction, a missing amount, an `or` remainder, `baby`, and
# a size word behind a `QQ`. The file is otherwise clean, so the count in the
# report is the rule's alone.
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

# Eight lines differ from `SIZE_BEFORE` and no others: the amount and the item
# of the first four entries.
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
    """Byte for byte: the size rule rewrites two fields per hit, so the proof
    is the whole file (#577)."""
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
    """Parsed on both sides: a plausible diff can still be an unparseable file.

    The recipe rule's own predicate, imported and not retyped, finds nothing
    left that the script could move. What remains flagged is the two shapes
    left for an eye (`or`, `baby`).
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


# ---- #1356: tin-and-pan fats and flour ----
# To flag: a bare greasing butter, a frying oil with an amount and a note (the
# flag goes last), and a `QQ` line (the flag edits none of its words). To trim:
# a tail after a comma, one with no comma, and one after a bracket. Left: a
# deep-frying oil, icing sugar to dust, an already flagged line, a bracketed use,
# and a `QQ` line's tail.
INC_BEFORE = '''---
title: "Test Recipe"
ingredient_groups:
  - name: "the lot"
    items:
    - item: "butter, for greasing"
    - amount: "2 tbsp"
      item: "sunflower oil, for frying"
      note: "Or rapeseed."
    - item: "QQ butter, for greasing"
    - amount: "175 g"
      item: "butter, softened, plus extra for the tin"
    - amount: "200 g"
      item: salted butter, softened plus extra for the tin
    - item: "salted butter, to serve (optional), plus extra for the tin"
    - item: "vegetable oil, for deep-frying"
    - amount: "1 litre"
      item: sunflower oil, to deep-fry
    - item: "groundnut oil, for deep frying"
      amount: "2 litres"
    - item: "icing sugar, to dust"
    - item: "plain flour, for dusting"
      incidental: true
    - amount: "3 tbsp"
      item: "olive oil (a little for frying, the rest for the dressing)"
    - amount: "250 g"
      item: "QQ butter, plus extra for the tin"
method:
  - "Cook it."
---
'''

# Ten changes from `INC_BEFORE`: three `incidental: true` lines added, three
# items trimmed, two deep-frying items reworded and two amounts dropped.
INC_AFTER = '''---
title: "Test Recipe"
ingredient_groups:
  - name: "the lot"
    items:
    - item: "butter, for greasing"
      incidental: true
    - amount: "2 tbsp"
      item: "sunflower oil, for frying"
      note: "Or rapeseed."
      incidental: true
    - item: "QQ butter, for greasing"
      incidental: true
    - amount: "175 g"
      item: "butter, softened"
    - amount: "200 g"
      item: salted butter, softened
    - item: "salted butter, to serve (optional)"
    - item: "vegetable oil, for deep frying"
    - item: "sunflower oil, for deep frying"
    - item: "groundnut oil, for deep frying"
    - item: "icing sugar, to dust"
    - item: "plain flour, for dusting"
      incidental: true
    - amount: "3 tbsp"
      item: "olive oil (a little for frying, the rest for the dressing)"
    - amount: "250 g"
      item: "QQ butter, plus extra for the tin"
method:
  - "Cook it."
---
'''


def test_incidentals_report_names_each_change_and_writes_nothing(food):
    path = food / "test-recipe.md"
    path.write_text(INC_BEFORE, encoding="utf-8")
    out = run_food(food, "--only", "incidentals")
    assert "would apply 10 mechanical change(s) across 1 file(s)" in out, out
    assert "[incidentals] flagged incidental: butter, for greasing" in out, out
    assert ("[incidentals] trimmed: butter, softened, plus extra for the tin "
            "-> butter, softened") in out, out
    assert path.read_text(encoding="utf-8") == INC_BEFORE


def test_incidentals_apply_changes_exactly_the_expected_lines(food):
    """Byte for byte (#1356)."""
    path = food / "test-recipe.md"
    path.write_text(INC_BEFORE, encoding="utf-8")
    run_food(food, "--only", "incidentals", "--apply")
    got = path.read_text(encoding="utf-8")
    assert got == INC_AFTER, "\n".join(
        f"want {w!r}\ngot  {g!r}" for w, g in
        zip(INC_AFTER.split("\n"), got.split("\n")) if w != g) or "line counts differ"


def test_incidentals_apply_satisfies_both_recipe_rules(food):
    """The suite's predicate, imported: after the pass nothing is left for it
    to flag or trim except the `QQ` tail, which is Helen's to rewrite."""
    import yaml
    sys.path.insert(0, str(ROOT / "tests"))
    from test_taxonomy import incidental_verdict

    path = food / "test-recipe.md"
    path.write_text(INC_BEFORE, encoding="utf-8")
    run_food(food, "--only", "incidentals", "--apply")
    items = yaml.safe_load(path.read_text(encoding="utf-8").split("---\n")[1])[
        "ingredient_groups"][0]["items"]
    left = [(i["item"], incidental_verdict(i["item"])[0]) for i in items
            if incidental_verdict(i["item"])[0] == "trim"
            or (incidental_verdict(i["item"])[0] == "flag" and not i.get("incidental"))]
    assert left == [("QQ butter, plus extra for the tin", "trim")], left
    deep = [i for i in items if incidental_verdict(i["item"])[0] == "deep"]
    assert len(deep) == 3 and not any("amount" in i for i in deep), deep


def test_size_words_never_run_on_a_drink(drinks):
    """`--only size` on the drinks site changes nothing and says so.

    A drink's `amount` is off limits and a drink has no `item`. The rule is in
    FOOD_FIXERS alone.
    """
    path = write_drink(drinks)
    out = run(drinks, "--only", "size", "--apply")
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE


def test_a_range_in_an_amount_is_reported_rather_than_silently_declined(drinks):
    """The drinks suite fails on it, so the report has to say why it did not.

    `test_drink_number_ranges_use_en_dashes` checks amounts, and this script
    declines to edit one. A decline that prints nothing is indistinguishable
    from a rule that is not running.
    """
    write_drink(drinks)
    out = run(drinks)
    assert "reported, never changed: 1 file(s)" in out, out
    assert "hyphenated number range, not this pass's to fix" in out, out
    assert '30-45 ml' in out, out


def test_a_file_with_no_front_matter_is_named_and_left_alone(drinks):
    """`_cocktail_drafts/README.md` is the live case and it is prose.

    The line-wise fixers do not parse front matter, so without the guard the
    only symptom is an em dash in a README nobody diffs.
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
    """A drink in a staging subfolder (`4-promote/`) is reached.

    A flat glob reports the files it found, all of them clean, and says
    nothing about the ones it did not look for.
    """
    (drinks / "4-promote").mkdir()
    path = write_drink(drinks, "4-promote/staged.md")
    out = run(drinks)
    assert "4-promote/staged.md" in out, out
    assert "would apply 6 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE


# ---- The notes slot, #1258 ----
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
    """`notes: []` -> the empty pair, and the file still parses to exactly that."""
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


# ---- Key order, #1213 ----
# A drink out of page order: body first, `mood` after the method, `meta` last.
# It carries every optional key (`serve`,
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
    """Byte for byte, and three claims asserted separately so a failure says
    which: the same lines as a multiset, the same parsed data, the declared
    order.

    A reorder's diff is unreadable by construction -- every moved block is a
    deletion in one place and an insertion in another -- so reading it proves
    nothing.
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


# ---- Title case, #1089 ----

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
    """`--only order` on the food site changes nothing: the rule is for
    cocktail drafts (#1213)."""
    path = food / "test-recipe.md"
    path.write_text(FOOD_BEFORE, encoding="utf-8")
    out = run_food(food, "--only", "order", "--apply")
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == FOOD_BEFORE


def test_food_only_rules_do_not_run_on_a_drink(drinks):
    """`--only meta` on the drinks site changes nothing, and says so.

    Food's `meta:` migration (#429) drops keys a drink still carries
    (test_cocktails.META_KEYS_IN_ORDER) and reorders the rest, quietly, on
    every drink it is pointed at. The rules are in two tables so that cannot
    happen; this pins that the tables are still two.
    """
    path = write_drink(drinks)
    out = run(drinks, "--only", "meta", "--apply")
    assert "would apply" not in out
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE, (
        "food's `meta:` migration ran over a drink. Check that DRINK_FIXERS "
        "still omits fix_meta_block."
    )

# ---- A food group's name is quoted (#814) ----

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
