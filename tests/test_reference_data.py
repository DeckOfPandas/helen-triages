"""The reference data layer's own invariants.

WHY THIS FILE EXISTS. _data/food/internal_temperatures.yml now holds every
temperature TWICE: once as the display string the pages and a recipe's meta
line print ("48–50°C"), and once as a numeric pair the temperature ruler draws
from (pull_min: 48, pull_max: 50).

Duplicating a fact is normally the thing to avoid, and the alternative was
considered: store numbers only and render the strings in Liquid. It was not
taken, for two reasons. The strings carry words the numbers can't ("74–75°C in
the thigh", "~63°C, opaque and flaking", "70°C+") so they'd need their own
qualifier fields anyway; and deriving them would mean rewriting ~60 call sites
across internal-temperatures.html and _layouts/recipe.html, which is a lot of
churn to land in one go for a page that is about to be redesigned anyway.

So: duplication, guarded. That is this project's own idiom -- the same reason
test_internal_temp_ref_resolves exists, and the same reason taxonomy tags are
checked against a declared list rather than trusted. A duplicate that a test
proves consistent is a cache; a duplicate nothing checks is a bug waiting.

IF THE DERIVED VERSION IS EVER BUILT, delete this file with it -- it is
scaffolding for the duplication, not a rule about temperatures.
"""
import pathlib
import re

import pytest


# Mirrors tmp/add_numbers.py's own parser, deliberately reimplemented rather
# than imported: a test that shares its parser with the thing that generated
# the data would agree with itself no matter how wrong both were.
_RANGE = re.compile(r"^(\d+(?:\.\d+)?)\s*(?:°C)?\s*[–-]\s*(\d+(?:\.\d+)?)")
_SINGLE = re.compile(r"^(\d+(?:\.\d+)?)")

TEMP_KEYS = ("pull", "rested", "endpoint", "target", "tender_at", "carryover",
             "passes_through")


def _walk(node, path=()):
    """Every dict in the tree, with its dotted path."""
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            yield from _walk(value, path + (key,))


def _numbers_in(text):
    stripped = text.replace("~", "").strip()
    m = _RANGE.match(stripped)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = _SINGLE.match(stripped)
    if m:
        return float(m.group(1)), float(m.group(1))
    return None


def _nodes_with_temps(data):
    for path, node in _walk(data):
        for key in TEMP_KEYS:
            if isinstance(node.get(key), str):
                yield ".".join(path + (key,)), node, key


def test_every_temperature_string_has_numbers(internal_temperatures):
    """A figure the ruler can't draw is a figure that silently disappears.

    The one legitimate exception is a field whose value is a sentence rather
    than a measurement -- tuna's carryover is prose about how hard to sear,
    with no number in it at all -- so the rule is "has a leading figure implies
    has numbers", not "every key has numbers".
    """
    missing = []
    for dotted, node, key in _nodes_with_temps(internal_temperatures):
        if _numbers_in(node[key]) is None:
            continue
        if f"{key}_min" not in node or f"{key}_max" not in node:
            missing.append(f"{dotted} = {node[key]!r}")

    assert not missing, (
        "these temperature strings start with a figure but carry no "
        "numeric pair, so nothing can plot them:\n  " + "\n  ".join(missing)
    )


def test_numbers_agree_with_their_strings(internal_temperatures):
    """The whole point of the file. Change one, this catches the other."""
    wrong = []
    for dotted, node, key in _nodes_with_temps(internal_temperatures):
        if f"{key}_min" not in node:
            continue
        parsed = _numbers_in(node[key])
        if parsed is None:
            wrong.append(f"{dotted}: has {key}_min but {node[key]!r} has no figure")
            continue
        lo, hi = parsed
        if node[f"{key}_min"] != lo or node[f"{key}_max"] != hi:
            wrong.append(
                f"{dotted}: string {node[key]!r} says {lo:g}–{hi:g}, "
                f"but {key}_min/{key}_max say "
                f"{node[f'{key}_min']:g}–{node[f'{key}_max']:g}"
            )

    assert not wrong, (
        "numeric fields have drifted from the strings they duplicate — edit "
        "both, or delete the numbers and derive them:\n  " + "\n  ".join(wrong)
    )


def test_ranges_are_the_right_way_round(internal_temperatures):
    backwards = []
    for dotted, node, key in _nodes_with_temps(internal_temperatures):
        lo, hi = node.get(f"{key}_min"), node.get(f"{key}_max")
        if lo is not None and hi is not None and lo > hi:
            backwards.append(f"{dotted}: {key}_min {lo:g} > {key}_max {hi:g}")
    assert not backwards, "\n  ".join(backwards)


def test_open_ended_figures_are_flagged(internal_temperatures):
    """`70°C+` has no upper bound, and pull_max repeats pull_min to say so.

    Without the flag a consumer can't tell "70 to 70" (a point) from "70 and
    up" (an open end), and the ruler would draw a well-done steak as a 3px
    tick. The flag and the string have to agree in both directions, so neither
    can be updated alone.
    """
    problems = []
    for dotted, node, key in _nodes_with_temps(internal_temperatures):
        open_in_string = node[key].rstrip().endswith("+")
        flagged = node.get(f"{key}_open") is True
        if open_in_string and not flagged:
            problems.append(f"{dotted} = {node[key]!r} needs `{key}_open: true`")
        if flagged and not open_in_string:
            problems.append(
                f"{dotted} has `{key}_open: true` but {node[key]!r} isn't open-ended"
            )
    assert not problems, "\n  ".join(problems)


def test_carryover_moves_the_temperature_up(internal_temperatures):
    """A rested figure below its own pull figure would be a transcription slip.

    Carryover only goes one way: meat keeps cooking after it leaves the heat.
    This is the check that would have caught a digit swap in any of the 30-odd
    pull/rested pairs, none of which anything else verifies.
    """
    wrong = []
    for path, node in _walk(internal_temperatures):
        if "pull_min" in node and "rested_min" in node:
            if node["rested_min"] < node["pull_min"]:
                wrong.append(
                    f"{'.'.join(path)}: rests to {node['rested_min']:g}°C but "
                    f"is pulled at {node['pull_min']:g}°C"
                )
    assert not wrong, "\n  ".join(wrong)


def test_every_temperature_fits_on_the_ruler_axis(internal_temperatures):
    """No figure may fall outside the chart's own axis.

    This is a real bug caught the hard way, not a hypothetical. The ruler's axis
    ran 40–100°C while tuna's blue rare sits at 38°C, so that bar computed a
    NEGATIVE left offset, escaped its track and printed over the row label.
    Helen spotted it as a spacing problem ("the bar for tuna slightly obscures
    the word"); it was the axis silently clipping its own data.

    Nothing else could catch it. CSS has no opinion about a negative percentage,
    the page still builds, every test still passes, and the only symptom is a
    bar in slightly the wrong place — which reads as a styling nit rather than
    as a wrong number.

    So the bounds are read from the stylesheet rather than repeated here: the
    two files cannot disagree, and narrowing the axis to make a chart look
    tidier fails immediately rather than quietly cropping whatever now falls
    outside it.
    """
    scss = (pathlib.Path(__file__).resolve().parent.parent
            / "assets" / "css" / "reference-demo.scss")
    if not scss.exists():
        pytest.skip("the ruler stylesheet has gone; nothing to bound against")

    text = scss.read_text(encoding="utf-8")
    bounds = {}
    for name in ("tr-min", "tr-max"):
        m = re.search(rf"^\${name}:\s*(-?\d+(?:\.\d+)?)\s*;", text, re.M)
        assert m, f"couldn't find ${name} in {scss.name}"
        bounds[name] = float(m.group(1))

    lo, hi = bounds["tr-min"], bounds["tr-max"]
    outside = []
    for dotted, node, key in _nodes_with_temps(internal_temperatures):
        # Carryover is a DIFFERENCE between two temperatures, not a temperature,
        # so it has no business being plotted on this axis and is exempt.
        if key == "carryover":
            continue
        for suffix in ("_min", "_max"):
            value = node.get(f"{key}{suffix}")
            if value is not None and not (lo <= value <= hi):
                outside.append(f"{dotted}{suffix} = {value:g}°C")

    assert not outside, (
        f"these figures fall outside the ruler's {lo:g}–{hi:g}°C axis, so their "
        f"bars would be drawn off the end of the track:\n  "
        + "\n  ".join(outside)
        + "\n\nWiden $tr-min/$tr-max in assets/css/reference-demo.scss."
    )


@pytest.mark.parametrize("protein", ["beef", "pork", "lamb", "steak"])
def test_doneness_levels_ascend(internal_temperatures, protein):
    """Rare must be cooler than medium, which must be cooler than well done.

    Reads the levels in the order the file declares them, because that order is
    what every page renders — so this checks the data as published, not a
    sorted copy of it.
    """
    node = internal_temperatures[protein]
    for key in ("roasting", "tender_roast"):
        if key in node:
            node = node[key]
            break
    doneness = node.get("doneness")
    if not doneness:
        pytest.skip(f"{protein} has no doneness spectrum")

    levels = [(name, spec["pull_min"]) for name, spec in doneness.items()
              if "pull_min" in spec]
    ascending = all(levels[i][1] <= levels[i + 1][1]
                    for i in range(len(levels) - 1))
    assert ascending, (
        f"{protein}'s doneness levels aren't in ascending temperature order "
        f"as declared: {[(n, f'{t:g}°C') for n, t in levels]}"
    )


# =============================================================================
# COOKING METHODS — the calculator's data layer
# =============================================================================
# Generated from cooking-methods.html by tmp/emit_cooking_methods.py rather than
# retyped. These tests are what makes that generation trustworthy: a parser that
# quietly mis-reads one row in sixty-six produces a data file that looks
# perfectly plausible and schedules someone's dinner wrong.

import pytest as _pytest  # noqa: E402  (kept local to this appended section)

SHAPES = {"rate", "total", "staged", "by_doneness", "relative",
          "disputed", "unparsed"}


@_pytest.fixture
def cooking_methods():
    import pathlib as _p
    import yaml as _yaml
    path = (_p.Path(__file__).resolve().parent.parent
            / "_data" / "food" / "cooking_methods.yml")
    if not path.exists():
        _pytest.skip("_data/food/cooking_methods.yml does not exist yet")
    return _yaml.safe_load(path.read_text(encoding="utf-8"))


def _all_methods(data):
    for protein, node in data.items():
        for method in node["methods"]:
            yield protein, method


def test_every_method_declares_a_known_shape(cooking_methods):
    """`shape` is what the calculator branches on, so an unknown one is a
    silent no-op: the method renders with no timing and nobody notices."""
    bad = [f"{p}/{m['id']}: {m.get('shape')!r}"
           for p, m in _all_methods(cooking_methods)
           if m.get("shape") not in SHAPES]
    assert not bad, "\n  ".join(bad)


def test_rate_methods_carry_a_usable_rate(cooking_methods):
    bad = []
    for protein, m in _all_methods(cooking_methods):
        if m["shape"] != "rate":
            continue
        if "rate_min" not in m or "rate_max" not in m:
            bad.append(f"{protein}/{m['id']}: shape is rate but has no rate")
        elif m["rate_min"] > m["rate_max"]:
            bad.append(f"{protein}/{m['id']}: rate_min > rate_max")
    assert not bad, "\n  ".join(bad)


def test_relative_methods_can_find_a_base(cooking_methods):
    """A `relative` row borrows another row's timing ("same as plain
    equivalent"). The calculator looks for the first `rate` row in the same
    group — if there isn't one, the row silently declines instead of
    borrowing, which looks identical to a genuine refusal and isn't one."""
    orphans = []
    for protein, m in _all_methods(cooking_methods):
        if m["shape"] != "relative":
            continue
        group = m.get("group")
        siblings = [s for s in cooking_methods[protein]["methods"]
                    if s.get("group") == group and s["shape"] == "rate"]
        if not siblings:
            orphans.append(f"{protein}/{m['id']} (group {group!r})")
    assert not orphans, (
        "these rows are defined against a base that doesn't exist in their "
        "group:\n  " + "\n  ".join(orphans)
    )


def test_temp_refs_resolve(cooking_methods, internal_temperatures):
    """The link between the two reference datasets. Same failure mode as
    test_internal_temp_ref_resolves: Liquid and JS both return undefined for a
    bad path rather than erroring, so the 'done at' line just disappears."""
    bad = []
    for protein, node in cooking_methods.items():
        ref = node.get("internal_temp_ref")
        if not ref:
            continue
        walk = internal_temperatures
        for key in ref.split("."):
            walk = walk.get(key) if isinstance(walk, dict) else None
        if walk is None:
            bad.append(f"{protein}: internal_temp_ref {ref!r} doesn't resolve")
    assert not bad, "\n  ".join(bad)


def test_worked_examples_agree_with_their_own_formulas(cooking_methods):
    """Some notes carry a worked example ("For 2.5 kg: ~2 hrs"). Where one
    exists it is a free, independent check on the parsed rate — the prose and
    the numbers were written by different hands at different times, so
    agreement is real evidence rather than a tautology."""
    import re as _re
    wrong = []
    for protein, m in _all_methods(cooking_methods):
        if m["shape"] != "rate":
            continue
        note = m.get("notes") or ""
        ex = _re.search(r"For\s+([\d.]+)\s*kg:\s*~?\s*([\d.]+)\s*(hrs?|min)", note)
        if not ex:
            continue
        kg = float(ex.group(1))
        want = float(ex.group(2)) * (60 if ex.group(3).startswith("hr") else 1)
        lo = m["rate_min"] * kg + m.get("flat_add", 0)
        hi = m["rate_max"] * kg + m.get("flat_add_max", m.get("flat_add", 0))
        if not (lo - 1 <= want <= hi + 1):
            wrong.append(
                f"{protein}/{m['id']}: note says {want:g} min for {kg} kg, "
                f"formula gives {lo:g}–{hi:g}"
            )
    assert not wrong, "\n  ".join(wrong)


def test_no_method_produces_an_absurd_time(cooking_methods):
    """A misparsed rate is most likely to show up as a wild number, not a
    slightly wrong one — hours read as minutes, or a weight range captured as a
    rate. Anything over 24 hours for a mid-range weight is a parser bug, not a
    recipe."""
    absurd = []
    for protein, m in _all_methods(cooking_methods):
        if m["shape"] != "rate":
            continue
        kg = min(max(m.get("weight_min", 2), 2), 6)
        hi = m["rate_max"] * kg + m.get("flat_add_max", m.get("flat_add", 0))
        if hi > 24 * 60:
            absurd.append(
                f"{protein}/{m['id']}: {hi / 60:.1f} hrs for {kg} kg "
                f"(from {m['timing']!r})"
            )
    assert not absurd, "\n  ".join(absurd)


def test_every_oven_temperature_says_fan(cooking_methods):
    """House style is fan-only — HANDOVER §5, "°C always, FAN OVEN ONLY, never
    conventional or gas mark".

    The source page didn't follow it: three rows spelled out a fan/conventional
    pair and 63 gave a bare figure with no basis at all, which is the worst of
    the three options — a number you can't act on without guessing which oven
    it means, and a 20°C guess either way.

    Helen, on the calculator: "only one option has fan oven though, the rest say
    nothing... so 'fan' every time." This holds that.
    """
    import re as _re
    problems = []
    for protein, m in _all_methods(cooking_methods):
        oven = m.get("oven")
        if not oven:
            continue
        if "conventional" in oven.lower():
            problems.append(f"{protein}/{m['id']}: still names a conventional "
                            f"temperature — {oven!r}")
        for figure in _re.findall(r"\d+(?:\s*[–-]\s*\d+)?\s*°C(?!\s*fan)", oven):
            problems.append(f"{protein}/{m['id']}: {figure!r} doesn't say fan "
                            f"— {oven!r}")
    assert not problems, "\n  ".join(problems)


def test_oven_basis_is_recorded(cooking_methods):
    """Whether a fan figure was STATED by the source or INFERRED by us is the
    kind of thing that quietly becomes fact once it's been in a data file for a
    month. 63 of the 66 are inferred, on the evidence that every bare figure
    which could be checked against a stated pair in its own protein matched the
    fan half — good evidence, but evidence, not a citation."""
    missing = [f"{p}/{m['id']}" for p, m in _all_methods(cooking_methods)
               if m.get("oven") and m.get("oven_basis") not in {"stated", "inferred"}]
    assert not missing, (
        "these rows carry an oven temperature with no basis recorded:\n  "
        + "\n  ".join(missing)
    )


# --- the notes themselves ----------------------------------------------------

def test_notes_are_not_damaged(cooking_methods):
    """Correction history is stripped from notes on the way out of the page.
    The first implementation did it with `Corrected from[^.]*\\.?` — and `[^.]*`
    stops at the FIRST period, which in "a 1.7–2 kg bird takes ~3 hrs" is the
    one inside the number. Two notes ended up with a fragment welded on
    ("…rather than throughout7–2 kg bird takes ~3 hrs at this temperature)") and
    four more had a sentence fused onto the one before it.

    It mattered more than a demo bug, because these notes now render the
    published page. The generator splits on real sentence boundaries instead;
    this is what stops the class of bug coming back by another route.

    THE CHECKS ARE EXACT, NOT HEURISTIC, and that is deliberate. A first version
    also flagged "a lowercase word, a space, then a capital" as a fused
    sentence — which is genuinely the shape of the bug, and is also the shape of
    every proper noun in the middle of a sentence. It failed on "the American
    Lamb Board's own figures". A check that cries wolf on correct data gets
    switched off, so it is gone: unbalanced brackets, a figure welded onto a
    word, and a note that starts mid-sentence are all unambiguous.
    """
    import re as _re
    damaged = []
    for protein, m in _all_methods(cooking_methods):
        for field in ("notes", "source_note"):
            note = m.get(field)
            if not note:
                continue
            where = f"{protein}/{m['id']}.{field}"
            if note.count("(") != note.count(")"):
                damaged.append(f"{where}: unbalanced brackets — {note[:70]!r}")
            if _re.search(r"[a-z)]\d+\s*[–-]", note):
                damaged.append(f"{where}: a figure welded onto a word — {note[:70]!r}")
            if note[:1].islower():
                damaged.append(f"{where}: starts mid-sentence — {note[:70]!r}")
    assert not damaged, "\n  ".join(damaged)


def test_every_method_has_a_short_outcome(cooking_methods):
    """The calculator's decision table answers "which method", and it can only
    do that if every row has something to say in the column. Length is the
    point: a sentence there is just the note again, and you cannot scan a
    column of sentences."""
    problems = []
    for protein, m in _all_methods(cooking_methods):
        outcome = m.get("outcome")
        if not outcome:
            problems.append(f"{protein}/{m['id']}: no outcome")
        elif len(outcome.split()) > 5:
            problems.append(f"{protein}/{m['id']}: {len(outcome.split())} words — {outcome!r}")
    assert not problems, "\n  ".join(problems)


# --- the page renders from this data now -------------------------------------

# Every column name _includes/food/method_table.html knows how to fill. A name
# outside this set renders an EMPTY CELL rather than failing, so the test is the
# only thing standing between a renamed column and a silently blank table.
KNOWN_COLUMNS = {
    "Method", "Oven temp", "Timing", "Timing (per kg)", "Temp change",
    "Covering", "Temp/covering", "Liquid", "Weight range", "Notes",
}


def test_group_columns_are_all_renderable(cooking_methods):
    unknown = []
    for protein, node in cooking_methods.items():
        for group in node.get("groups", []):
            for column in group.get("columns") or []:
                if column not in KNOWN_COLUMNS:
                    unknown.append(f"{protein}/{group['name']!r}: column {column!r}")
    assert not unknown, (
        "these columns would render as empty cells — teach "
        "_includes/food/method_table.html about them, or rename them:\n  "
        + "\n  ".join(unknown)
    )


def test_every_method_belongs_to_a_declared_group(cooking_methods):
    """The page renders a table per group and fills it by matching
    `method.group` to `group.name`. A method whose group doesn't match any
    declared one simply never appears — no error, no empty row, just a missing
    cooking method on a published page."""
    orphans = []
    for protein, node in cooking_methods.items():
        names = {g["name"] for g in node.get("groups", [])}
        if not names:
            continue
        for m in node["methods"]:
            if m.get("group") not in names:
                orphans.append(f"{protein}/{m['id']}: group {m.get('group')!r} "
                               f"not in {sorted(names)}")
    assert not orphans, "\n  ".join(orphans)


def test_prose_blocks_survived_the_move_into_data(cooking_methods):
    """The eight timing sections' surrounding prose now lives in the data, in
    ordered before/after lists. This asserts the count didn't quietly shrink:
    30 paragraphs across 12 groups, being 12 sources notes and 18 others
    (weight ranges, FOOD SAFETY flags, group intros, ham's Caveat)."""
    total = sum(len(g.get("before", [])) + len(g.get("after", []))
                for node in cooking_methods.values()
                for g in node.get("groups", []))
    sources = sum(1 for node in cooking_methods.values()
                  for g in node.get("groups", [])
                  for b in g.get("before", []) + g.get("after", [])
                  if b["kind"] == "sources")
    assert total == 30, f"expected 30 prose blocks, found {total}"
    assert sources == 12, f"expected 12 sources notes, found {sources}"


def test_outbound_links_are_still_in_the_data(cooking_methods):
    """The page's only four outbound links live INSIDE recipe-source notes.
    Flattening a source note to plain text would lose them without changing a
    single visible word of prose, which is why they get their own assertion."""
    blob = "".join(b["html"] for node in cooking_methods.values()
                   for g in node.get("groups", [])
                   for b in g.get("before", []) + g.get("after", []))
    for domain in ("waitrose.com", "jamieoliver.com", "goodto.com"):
        assert domain in blob, f"outbound link to {domain} has been lost"


def test_the_data_file_is_not_empty(cooking_methods):
    """A floor, and it exists because the floor gave way once.

    tmp/emit_cooking_methods.py parses cooking-methods.html — and that page now
    renders FROM this data file. Running the generator against the working copy
    therefore made it its own consumer: it found no tables, wrote an empty data
    file, and the page went blank. The generator is pinned to the pre-migration
    commit now so it can't recur, but the more useful lesson is that almost
    every test in this file passed on that empty file, vacuously, because
    "for every method…" is trivially true of no methods.

    So: assert the shape is there at all, before asserting things about it.
    """
    assert len(cooking_methods) == 8, (
        f"expected 8 proteins with timings, found {len(cooking_methods)}: "
        f"{sorted(cooking_methods)}"
    )
    total = sum(len(node["methods"]) for node in cooking_methods.values())
    assert total == 66, f"expected 66 methods, found {total}"
