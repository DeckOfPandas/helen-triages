"""The reference data layer's own invariants.

WHY THIS FILE EXISTS. _data/food/internal_temperatures.yml now holds every
temperature TWICE: once as the display string the pages and a recipe's meta
line print ("48–50°C"), and once as a numeric pair the temperature charts draws
from (out_at_min: 48, out_at_max: 50).

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


# Mirrors scripts/build_cooking_methods.py's own parser, deliberately reimplemented rather
# than imported: a test that shares its parser with the thing that generated
# the data would agree with itself no matter how wrong both were.
_RANGE = re.compile(r"^(\d+(?:\.\d+)?)\s*(?:°C)?\s*[–-]\s*(\d+(?:\.\d+)?)")
_SINGLE = re.compile(r"^(\d+(?:\.\d+)?)")

TEMP_KEYS = ("out_at", "rested", "endpoint", "target", "tender_at", "carryover",
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
    """A figure the charts can't draw is a figure that silently disappears.

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
    """`70°C+` has no upper bound, and out_at_max repeats out_at_min to say so.

    Without the flag a consumer can't tell "70 to 70" (a point) from "70 and
    up" (an open end), and the charts would draw a well-done steak as a 3px
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
    """A rested figure below its own out_at figure would be a transcription slip.

    Carryover only goes one way: meat keeps cooking after it leaves the heat.
    This is the check that would have caught a digit swap in any of the 30-odd
    pull/rested pairs, none of which anything else verifies.
    """
    wrong = []
    for path, node in _walk(internal_temperatures):
        if "out_at_min" in node and "rested_min" in node:
            if node["rested_min"] < node["out_at_min"]:
                wrong.append(
                    f"{'.'.join(path)}: rests to {node['rested_min']:g}°C but "
                    f"is pulled at {node['out_at_min']:g}°C"
                )
    assert not wrong, "\n  ".join(wrong)


def test_every_temperature_fits_on_the_chart_axis(internal_temperatures):
    """No figure may fall outside the chart's own axis.

    This is a real bug caught the hard way, not a hypothetical. The charts's axis
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
    # Follows the dials, which moved from assets/css/reference-demo.scss to
    # _sass/food/_temperature-chart.scss on 2026-08-14 when the chart stopped
    # being a demo and started drawing on recipe pages. This test caught the
    # move itself, which is the behaviour you want from a guard that reads
    # another file: it failed loudly rather than silently bounding nothing.
    scss = (pathlib.Path(__file__).resolve().parent.parent
            / "_sass" / "food" / "_temperature-chart.scss")
    if not scss.exists():
        pytest.skip("the chart stylesheet has gone; nothing to bound against")

    text = scss.read_text(encoding="utf-8")
    bounds = {}
    for name in ("tc-min", "tc-max"):
        m = re.search(rf"^\${name}:\s*(-?\d+(?:\.\d+)?)\s*;", text, re.M)
        assert m, f"couldn't find ${name} in {scss.name}"
        bounds[name] = float(m.group(1))

    lo, hi = bounds["tc-min"], bounds["tc-max"]
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
        f"these figures fall outside the charts' {lo:g}–{hi:g}°C axis, so their "
        f"bars would be drawn off the end of the track:\n  "
        + "\n  ".join(outside)
        + "\n\nWiden $tc-min/$tc-max in assets/css/reference-demo.scss."
    )


def _doneness_spectra(node, path=()):
    """Every doneness map under a protein, with the dotted path that holds it.

    FINDS THEM RATHER THAN GUESSING WHERE THEY LIVE. The first version of this
    reached for a known sub-key -- `for key in ("roasting", "tender_roast")` --
    which works for exactly the four proteins it was written against and
    silently finds nothing for anything else. Walking means a protein that
    keeps its spectrum under any other name (venison.loin, venison.haunch) is
    checked the day it is added, without anyone remembering to teach this
    function a fifth key.
    """
    if not isinstance(node, dict):
        return
    if isinstance(node.get("doneness"), dict):
        yield path, node["doneness"]
    for key, value in node.items():
        if key != "doneness":
            yield from _doneness_spectra(value, path + (key,))


@pytest.mark.parametrize("protein", ["beef", "pork", "lamb", "steak", "venison"])
def test_doneness_levels_ascend(internal_temperatures, protein):
    """Rare must be cooler than medium, which must be cooler than well done.

    Reads the levels in the order the file declares them, because that order is
    what every page renders — so this checks the data as published, not a
    sorted copy of it.

    THE TRAP HERE IS A SILENT SKIP, not a wrong number. This test used to walk
    to a `roasting`/`tender_roast` sub-key and `pytest.skip` when it found no
    `doneness` map underneath. Adding "venison" to the parametrize list would
    then have LOOKED like coverage and been none at all: venison's spectra sit
    on `loin` and `haunch`, neither key matched, the lookup returned None, and
    the new parametrisation would have reported itself green while checking
    nothing — the exact shape of failure HANDOVER §12 and tests/
    test_suite_hygiene.py exist for. So there is no skip left in here: the
    spectra are found by walking, and an empty result is a failure.
    """
    spectra = list(_doneness_spectra(internal_temperatures[protein]))
    assert spectra, (
        f"{protein} is in this test's parametrize list but no node under it "
        f"carries a `doneness` map, so there is nothing to put in order. "
        f"Either the data moved and this list is stale, or the protein never "
        f"had a spectrum and doesn't belong here — don't skip past it."
    )

    for path, doneness in spectra:
        where = ".".join((protein,) + path)
        levels = [(name, spec["out_at_min"]) for name, spec in doneness.items()
                  if "out_at_min" in spec]
        assert len(levels) > 1, (
            f"{where} has {len(levels)} level(s) with an out_at_min — a "
            f"one-level spectrum is trivially in order, which is the same "
            f"nothing-checked result as the skip this test used to do"
        )
        ascending = all(levels[i][1] <= levels[i + 1][1]
                        for i in range(len(levels) - 1))
        assert ascending, (
            f"{where}'s doneness levels aren't in ascending temperature order "
            f"as declared: {[(n, f'{t:g}°C') for n, t in levels]}"
        )


# =============================================================================
# COOKING METHODS — the calculator's data layer
# =============================================================================
# Generated from cooking-methods.html by scripts/build_cooking_methods.py rather than
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
def test_every_protein_points_at_the_charts(cooking_methods):
    """Each protein carries `chart_anchor`, the section of the temperature charts
    holding its full doneness spectrum, so the "see other doneness" link has
    somewhere to go. Not derivable from internal_temp_ref: four birds share one
    chart section, and beef's ref points at tender_roast while the charts split
    beef three ways. A missing anchor doesn't error — the link just isn't
    rendered, and the page quietly dead-ends on one doneness figure."""
    missing = [p for p, node in cooking_methods.items() if not node.get("chart_anchor")]
    assert not missing, f"no chart_anchor for: {missing}"


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
    """The nine timing sections' surrounding prose now lives in the data, in
    ordered before/after lists. This asserts the count didn't quietly shrink:
    35 paragraphs across 14 groups, being 14 sources notes and 21 others
    (weight ranges, FOOD SAFETY flags, group intros, ham's Caveat).

    Was 30 across 12 groups until 2026-08-16, when venison arrived (issue #205)
    with two groups and five blocks: a weight range and a sources note on each,
    plus the slow-cooked group's intro line."""
    total = sum(len(g.get("before", [])) + len(g.get("after", []))
                for node in cooking_methods.values()
                for g in node.get("groups", []))
    sources = sum(1 for node in cooking_methods.values()
                  for g in node.get("groups", [])
                  for b in g.get("before", []) + g.get("after", [])
                  if b["kind"] == "sources")
    assert total == 35, f"expected 35 prose blocks, found {total}"
    assert sources == 14, f"expected 14 sources notes, found {sources}"


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

    scripts/build_cooking_methods.py parses cooking-methods.html — and that page now
    renders FROM this data file. Running the generator against the working copy
    therefore made it its own consumer: it found no tables, wrote an empty data
    file, and the page went blank. The generator is pinned to the pre-migration
    commit now so it can't recur, but the more useful lesson is that almost
    every test in this file passed on that empty file, vacuously, because
    "for every method…" is trivially true of no methods.

    So: assert the shape is there at all, before asserting things about it.
    """
    assert len(cooking_methods) == 9, (
        f"expected 9 proteins with timings, found {len(cooking_methods)}: "
        f"{sorted(cooking_methods)}"
    )
    total = sum(len(node["methods"]) for node in cooking_methods.values())
    assert total == 73, (
        f"expected 73 methods, found {total} — 66 were migrated, beef's "
        f"closed-oven-off method was dropped on 2026-08-14 at Helen's request "
        f"(65), and venison's eight arrived on 2026-08-16 with issue #205: "
        f"five roasting rows (haunch three ways, rack, loin) and three "
        f"slow-cooked ones (shoulder twice, shank). Neck is folded into the "
        f"shoulder rows on purpose — no UK source publishes a neck timing"
    )


def test_temperatures_written_into_method_text_match_the_data(internal_temperatures):
    """A figure typed into a method step has to agree with the data behind it.

    Front matter is never Liquid-templated (HANDOVER §4), so a temperature a
    cook needs mid-step can only be typed by hand — which re-creates exactly the
    duplication internal_temperatures.yml was built to end. The compromise is
    the one this project already makes elsewhere: duplicate, and guard it.

    SCOPED TO STEPS THAT LINK TO THE CHART. A method step is full of oven
    temperatures ("roast at 170-180°C fan"), and no parser can tell those from
    an internal one by looking. A step carrying `(#doneness)` has declared what
    its number means, so that link is the marker — which also means adding the
    link is what opts a step into being checked, rather than something separate
    to remember.
    """
    import pathlib as _p
    import re as _re
    import yaml as _yaml

    problems = []
    for path in sorted(_p.Path("_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        if "#doneness" not in raw:
            continue
        fm = _yaml.safe_load(raw.split("---")[1])
        ref = fm.get("internal_temp_ref")
        if not ref:
            problems.append(f"{path.name}: links to #doneness with no internal_temp_ref")
            continue

        node = internal_temperatures
        for key in ref.split("."):
            node = node.get(key) if isinstance(node, dict) else None
        if fm.get("doneness"):
            node = (node or {}).get("doneness", {}).get(fm["doneness"])
        if not node:
            continue                    # other tests own an unresolvable ref

        allowed = set()
        for k in ("out_at", "rested", "endpoint", "target", "tender_at"):
            lo, hi = node.get(f"{k}_min"), node.get(f"{k}_max")
            if lo is not None:
                allowed.add((lo, hi))

        for step in fm.get("method") or []:
            text = step.get("step") if isinstance(step, dict) else str(step)
            if "#doneness" not in text:
                continue
            # A linked step carries BOTH kinds of temperature -- "roast at
            # 170-180°C fan ... take it out at 52–54°C" -- so the link alone
            # isn't enough to tell them apart. House style is the discriminator:
            # every oven temperature on this site says "fan" (§5, enforced for
            # the methods data by test_every_oven_temperature_says_fan), and an
            # internal one never does. Meat has no fan setting.
            for lo, hi in _re.findall(r"(\d+)\s*[–-]\s*(\d+)\s*°C(?!\s*fan)", text):
                if (float(lo), float(hi)) not in allowed:
                    problems.append(
                        f"{path.name}: step says {lo}–{hi}°C beside its "
                        f"#doneness link, but {ref} offers "
                        f"{sorted(allowed) or 'nothing'}"
                    )

    assert not problems, "\n  ".join(problems)


# The three nodes whose doneness levels include figures that do NOT clear the
# guidance cited for them. Named explicitly rather than inferred: this is a
# specification, not a heuristic, and it is the list that decides whether a
# chart warns anybody.
#
# Beef, lamb, steak and venison are deliberately absent -- UK guidance treats
# pink beef and lamb as fine, so there is no line to draw. Venison is here for
# the same reason and not by oversight: FSA treats a whole cut of venison the
# way it treats beef and lamb, the bacteria are on the surface and the sear
# kills them, so a safety_min on venison.loin or venison.haunch would be a line
# with nothing behind it -- and this test would then demand one. Tuna has a
# safety_note about parasites and sourcing, and venison's is about mince, both
# of which a thermometer can't confirm and a threshold on a temperature axis
# can't express.
SAFETY_THRESHOLDS = {
    ("fish", "salmon"): 63,
    ("pork", "roasting"): 70,
    ("ham", "fresh"): 70,
}


def test_hazardous_spectra_carry_a_drawable_threshold(internal_temperatures):
    """A doneness level below the cited guidance must never render unqualified.

    THIS IS A REAL FAILURE, not a hypothetical. The recipe-page chart shipped
    without the shading on 2026-08-14, on the reasoning that the reference page
    had room to explain it. Teriyaki salmon then offered "rare, out at 43–49°C"
    as one of five equal options, with nothing anywhere on the page to say that
    four of the five sit under the FSA benchmark. Helen caught it.

    The threshold was a hard-coded `--t:63` in the charts page's markup, which is
    exactly why it couldn't travel to the second chart that needed it. It is a
    figure on the node now, so anything drawing that node draws the warning.
    """
    missing = []
    for path, expected in SAFETY_THRESHOLDS.items():
        node = internal_temperatures
        for key in path:
            node = node.get(key, {})
        ref = ".".join(path)
        if node.get("safety_min") != expected:
            missing.append(f"{ref}: safety_min is {node.get('safety_min')!r}, expected {expected}")
        if not node.get("safety_label"):
            missing.append(f"{ref}: no safety_label, so the line would be unlabelled")
        if not node.get("safety_summary"):
            missing.append(f"{ref}: no safety_summary — shading says 'below the line' "
                           f"but not which levels clear it")
    assert not missing, "\n  ".join(missing)


def test_a_threshold_actually_excludes_something(internal_temperatures):
    """A threshold no level falls below is decoration, and worse, it implies the
    page checked and found nothing wrong. Each of the three must genuinely
    exclude at least one doneness level, and must genuinely leave at least one
    clearing it — a line everything fails is a broken figure, not a warning.
    """
    def reaches(spec):
        """The highest temperature this level actually gets to.

        "Clears the guidance" is a claim about the temperature the food REACHES,
        not the one you take it out at -- salmon's well done comes out at
        60–63°C and rests to 65, and it is the 65 that clears the 63 benchmark.
        Comparing out-at figures instead said no salmon doneness clears it at
        all, which is both wrong and the kind of wrong that would have had
        someone "fix" the threshold rather than the test.

        (Pork is the case where reaching isn't sufficient -- FSA's table is
        about temperature HELD, not passed through on the way down. That is why
        its safety_summary says so in words: a single figure can't express it,
        and this test isn't trying to.)"""
        return max(spec.get("rested_max") or 0, spec.get("out_at_max") or 0)

    problems = []
    for path in SAFETY_THRESHOLDS:
        node = internal_temperatures
        for key in path:
            node = node.get(key, {})
        limit = node.get("safety_min")
        levels = node.get("doneness") or {}
        below = [n for n, s in levels.items() if reaches(s) < limit]
        clears = [n for n, s in levels.items() if reaches(s) >= limit]
        ref = ".".join(path)
        if not below:
            problems.append(f"{ref}: nothing falls below {limit}°C — why is the line there?")
        if not clears:
            problems.append(f"{ref}: NO level clears {limit}°C — the figure or the levels are wrong")
    assert not problems, "\n  ".join(problems)


def test_the_safety_zone_shares_the_bars_coordinate_space():
    """The shaded zone must be measured against the same thing the bars are.

    A chart row is a grid — a label column, then `1fr` — so a bar's percentage
    resolves against that `1fr`. The zone is absolutely positioned on .tc-plot,
    which is the WHOLE row width including the label column, so the same number
    means two different places. Salmon's 63°C line drew at roughly 54°C, about
    100px left of the figure it was labelled with.

    That under-stated the hazard in the only direction that matters: medium and
    medium-well sat to the right of a line they don't clear, on a chart added
    specifically to stop a low figure reading as an unqualified option.

    Checked in the SOURCE rather than by measuring a render, because there is no
    browser here — but the thing being asserted is the actual cause, not a
    symptom: if the zone's geometry doesn't mention the label column, it isn't
    working in the track's coordinate space and it is wrong again.
    """
    scss = (pathlib.Path(__file__).resolve().parent.parent
            / "_sass" / "food" / "_temperature-chart.scss")
    if not scss.exists():
        pytest.skip("the chart stylesheet has gone")
    text = scss.read_text(encoding="utf-8")

    problems = []
    for selector in (".tc-unsafe", ".tc-threshold-label"):
        start = text.index(selector + " {")
        block = text[start:text.index("\n}", start)]
        geometry = " ".join(
            line for line in block.splitlines()
            if line.strip().startswith(("left:", "width:"))
        )
        if "tc-track-start" not in geometry and "tc-track-width" not in geometry:
            problems.append(
                f"{selector} positions itself without the label column: {geometry.strip()!r}. "
                f"It shares .tc-plot with the bars but not their origin, so its "
                f"°C figure will land at a different place from theirs."
            )
    assert not problems, "\n  ".join(problems)


# =============================================================================
# DELIBERATELY NOT TESTED: cook_time against the method's own timings
# =============================================================================
# roast-beef-fillet said "30 mins" where its method adds up to nearer 40, and the
# obvious response is a test that sums the times in each method and flags the
# gap. Helen ruled it out on 2026-08-14, and the reasoning is better than the
# test would have been: "if a recipe contains complicated meat, a nudge to the
# temperature chart should catch most users."
#
# She is right that the drift is a symptom. A clock figure cannot answer "is it
# done", so tightening it buys very little, while the ", but check cooking
# temperatures" link in _layouts/recipe.html sends you to the thing that can.
# The test would also be fuzzy in the worst way -- half these methods say "until
# golden" -- so it would need an exception list longer than its own logic.
#
# Don't add it. If the arithmetic matters somewhere specific, fix that recipe.


# =============================================================================
# COVERAGE — the gap every other test in this file has
# =============================================================================
# Everything above validates recipes that OPTED IN. A recipe that should carry a
# temperature and doesn't is invisible to all of it: roast turkey and roast goose
# sat unwired for a day with 27 passing tests, because nothing was looking for
# absence.
#
# So this is the inverse test. It names the proteins we hold data for, finds
# published recipes whose main ingredients say one of them, and requires either
# an internal_temp_ref or an entry below saying why not.
#
# THE OPT-OUT LIST IS THE POINT, not a way round the test. Each entry is a
# decision with a reason attached, so "why doesn't the lamb one have a
# temperature?" is answered in the repo rather than in someone's memory.
# STAR INGREDIENT IS THE PRIMARY SIGNAL, because it is a declared vocabulary
# (taxonomy.yml, guarded by its own test) rather than free text. Indian Mutton
# Raan slipped past the first version of this test entirely: its main
# ingredients say "mutton leg" and the word list only knew "lamb", so a
# three-hour roast with "until done according to an in-oven probe" and no figure
# in it passed a test written specifically to find that.
#
# Its star_ingredient said "lamb" all along. The collection had already made the
# call that mutton files under lamb; the test just wasn't reading the field that
# knew.
#
# Only families we actually hold data for are mapped. `game` was absent until
# 2026-08-16 because there was no venison node to point at; issues #205 and #217
# added one, so it joins the list and the test starts asking every game recipe
# for a ref on its own -- which is what the note here always said would happen.
# `shellfish` is still out for the original reason: no shellfish node exists, so
# demanding a ref would be demanding something that doesn't exist. Add it the
# day the data does.
STAR_INGREDIENTS_WITH_DATA = {
    "beef", "duck", "game", "lamb", "pork", "poultry", "oily fish", "white fish",
}

# The fallback, used ONLY when a recipe declares no star ingredient at all.
# "mutton" and "hogget" are here now for the same reason lamb was.
PROTEIN_WORDS = {
    "mutton": "lamb", "hogget": "lamb",
    "chicken": "poultry", "turkey": "poultry", "goose": "poultry", "duck": "poultry",
    "beef": "beef", "steak": "beef", "oxtail": "beef", "brisket": "beef",
    "pork": "pork", "gammon": "ham", "ham": "ham",
    "lamb": "lamb", "salmon": "fish", "tuna": "fish", "trout": "fish",
    "cod": "fish", "haddock": "fish", "mackerel": "fish", "sea bass": "fish",
}

NO_TEMPERATURE_BECAUSE = {
    # Not the dish. The protein is a stock, a garnish or an accompaniment.
    # (cherry-glaze and plum-sauce-for-duck used to be listed here and no longer
    # need to be: their star_ingredient is "fruit", and free-text "beef stock"
    # stopped counting once the star became the primary signal.)
    "pancetta-white-bean-stew": "pancetta is cured and diced, not a cut cooked to a temperature",
    "smoked-mackerel-pate": "the mackerel arrives smoked; nothing is cooked",
    "toad-in-the-hole": "sausages; pork.roasting is loin and leg joints, "
                        "pork.slow_cooked is shoulder and belly, and neither is "
                        "a thing you probe — found by the star_ingredient net, "
                        "which the free-text one had been missing",

    # A cut the data doesn't cover. These are the honest gaps -- each one names a
    # real thing missing from internal_temperatures.yml rather than a chore.
    "cumin-mint-lamb-skewers": "grilled shoulder chunks; lamb.roasting is joints and "
                               "lamb.slow_cooked is a whole shoulder, neither is this",
    "vietnamese-spiced-braised-venison-haunch": "a 1 kg boneless haunch BRAISED for two "
                                                "hours, which is neither of the two "
                                                "venison shapes we hold: venison.haunch "
                                                "is a roasting spectrum and this joint "
                                                "never stops at a doneness, while "
                                                "venison.shoulder's 90–95°C is the right "
                                                "physics under the wrong cut name. It "
                                                "wants a braised-haunch figure, and "
                                                "there isn't one",

    # Chicken pieces in a wet dish. poultry.chicken's endpoint is written for a
    # WHOLE BIRD ("74–75°C in the thigh"), and a thigh in a stew reaches that
    # long before the dish is finished, so quoting it would be technically true
    # and useless. Helen's duck-leg reasoning (the figure says "in the thigh",
    # so a leg takes it) applies to a ROASTED leg, where the temperature is what
    # you stop at. Revisit if a pieces/braise figure is ever added.
    "chicken-a-la-king": "diced breast in a sauce; no figure for pieces",
    "chicken-cider-stew": "thighs and drumsticks braised; no figure for pieces",
    "chicken-sorrel-potato-stew": "leg braised; no figure for pieces",
    "indonesian-chicken-curry-gulai-ayam": "thighs in a curry; no figure for pieces",
    "thai-green-chicken-curry": "chicken in a curry; no figure for pieces",
}


def test_every_recipe_with_a_known_protein_has_a_temperature_or_a_reason():
    import re as _re
    import yaml as _yaml

    missing = []
    for path in sorted(pathlib.Path("_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        if not raw.startswith("---"):
            continue
        fm = _yaml.safe_load(raw.split("---")[1]) or {}
        if fm.get("internal_temp_ref") or path.stem in NO_TEMPERATURE_BECAUSE:
            continue
        # A DECLARED STAR WINS OUTRIGHT. If the recipe says what it is about,
        # that is the answer -- cherry-glaze is "fruit" however much duck its
        # ingredients mention, and the venison braise is "game" however much
        # beef stock is in it. The free-text net below is a FALLBACK for a
        # protein-led recipe that never set one, not a second opinion.
        star = (fm.get("star_ingredient") or "").strip().lower()
        if star:
            hits = [star] if star in STAR_INGREDIENTS_WITH_DATA else []
        else:
            mains = [str(x).lower() for x in (fm.get("main_ingredients") or [])]
            hits = sorted({fam for word, fam in PROTEIN_WORDS.items()
                           if any(_re.search(rf"\b{word}\b", m) for m in mains)})
        if hits:
            missing.append(f"{path.stem}: names {hits} — add an internal_temp_ref, "
                           f"or an entry in NO_TEMPERATURE_BECAUSE saying why not")
    assert not missing, "\n  ".join(missing)


def test_the_opt_out_list_has_no_stale_entries():
    """An opt-out for a recipe that has since been wired, renamed or deleted is
    worse than no entry: it silently exempts nothing while looking like a
    decision someone made."""
    import yaml as _yaml
    stale = []
    for slug in NO_TEMPERATURE_BECAUSE:
        path = pathlib.Path("_food_recipes") / f"{slug}.md"
        if not path.exists():
            stale.append(f"{slug}: no such recipe")
            continue
        fm = _yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1]) or {}
        if fm.get("internal_temp_ref"):
            stale.append(f"{slug}: now wired to {fm['internal_temp_ref']}, so the opt-out is dead")
    assert not stale, "\n  ".join(stale)


def test_chart_anchors_point_at_sections_that_exist(internal_temperatures):
    """Every chart_anchor has to match an id on the temperatures page.

    A wrong one doesn't error anywhere: the recipe's "more meat temperatures"
    link renders, resolves to a real page, and lands at the top of it. The only
    symptom is arriving in the wrong place, which reads as a missing scroll
    rather than a broken link — and it will happen the first time a section is
    renamed, which has already happened twice this week (Steak -> Beef: steak,
    Everything one scale -> All).
    """
    page = pathlib.Path("food/reference/temperatures.html")
    if not page.exists():
        pytest.skip("the temperatures page has moved; nothing to check against")
    ids = set(re.findall(r'id="([^"]+)"', page.read_text(encoding="utf-8")))

    broken = []
    for path, node in _walk(internal_temperatures):
        anchor = node.get("chart_anchor")
        if anchor and anchor not in ids:
            broken.append(f"{'.'.join(path)}: chart_anchor {anchor!r} — "
                          f"the page has {sorted(i for i in ids if i != 'top')}")
    assert not broken, "\n  ".join(broken)


def test_every_figure_a_recipe_can_point_at_has_a_chart_anchor(internal_temperatures):
    """Anchors have to be PRESENT, not just valid when present.

    test_chart_anchors_point_at_sections_that_exist checks the ones that are
    there. It cannot see a node that has none — and a missing anchor doesn't
    break anything visible: the chart still draws, the figure is still right,
    there is simply no way out to the rest of the spectrum. Indian Mutton Raan
    shipped like that, because an earlier pass added anchors by searching for
    "  slow_cooked:" and matched pork's copy of the key rather than lamb's.

    Any node carrying a figure is a node some recipe can name in
    internal_temp_ref, so any node carrying a figure needs somewhere to send
    them.
    """
    orphans = []
    for path, node in _walk(internal_temperatures):
        has_figure = any(k in node for k in ("doneness", "endpoint", "target", "tender_at"))
        if has_figure and not node.get("chart_anchor"):
            orphans.append(".".join(path))
    assert not orphans, (
        "these nodes hold a figure a recipe can point at, but no chart_anchor, "
        "so their 'more temperatures' link is silently omitted:\n  "
        + "\n  ".join(orphans)
    )
