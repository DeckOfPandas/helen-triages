"""`scripts/glass_fit_report.py` -- the judgement in `check`, with no build.

The report itself is not a test, on purpose (its header says why: every line
is a question for Helen about one drink). What IS testable is the arithmetic
that decides a line, and #1244's first list is why it needs pinning: audited
line by line on 2026-10-04, 10 of its 22 flags were the model's fault -- drinks
watered for things that were never shaken, drinks over by 3%, and a top flag
comparing against a range the site had stopped spending.

Synthetic glasses and rules, so a re-survey or a new ruling on dilution moves
nothing here. One glass: 200 ml, stemmed, wash line 0.75, so it takes 150 ml.
"""
import sys

import pytest

from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import glass_fit_report as gfr  # noqa: E402

pytestmark = pytest.mark.cocktails

GLASSES = {
    "icons": {"test glass": "test-glass"},
    "typical_ml": {"test-glass": {"n": 3, "min": 160, "median": 200, "mean": 200, "max": 240}},
}
RULES = {
    "dilution": {"shake": {"low": 0.25, "high": 0.25}, "build": {"low": 0, "high": 0}},
    "blended_multiplier": {"low": 1.9, "high": 2.1},
    "washline": {"stemmed": 0.75, "tumbler": 0.9},
    "stemmed": ["test-glass"],
    "ice_space": {"cubed": {"low": 0.31, "high": 0.61}},
    "half_fill": 0.5,
    "large_cube_ml": {"low": 120, "high": 131},
    "punch_cup_ml": {"low": 90, "high": 120},
    "lost_below": 0.5,
    "tolerance": 0.10,
    "top_room_min": 0.25,
}
TOP_UP = {"champagne": {"ml_min": 80, "ml_max": 100}}


def _drink(top=False):
    ingredients = [{"amount": "100 ml", "generic": "gin"}]
    if top:
        ingredients.append({"amount": "(top)", "generic": "champagne"})
    return {"glass": ["test glass"], "serve": {"ice": "none"}, "ingredients": ingredients}


def _verdict(total, top=0.0, family="shake", after=0.0, aside=0.0, drink=None):
    _, results = gfr.check(drink or _drink(bool(top)), total, top, family,
                           GLASSES, RULES, TOP_UP, after=after, aside=aside)
    assert len(results) == 1
    return results[0][1]


def test_a_drink_over_by_less_than_the_tolerance_is_not_flagged():
    """150 ml of room, 10% tolerance: flagged above 165 ml in the glass."""
    assert _verdict(128) == "ok", "128 x 1.25 = 160 ml, 7% over: the model's noise"
    assert _verdict(136) == "tight", "136 x 1.25 = 170 ml, 13% over: a finding"


def test_too_big_for_the_largest_glass_also_needs_the_margin():
    """The largest glass takes 180 ml, so "over" starts above 198."""
    assert _verdict(156) == "tight", "195 ml: over a typical glass, inside the largest's margin"
    assert _verdict(160) == "over", "200 ml: over the largest by more than 10%"


def test_only_what_was_shaken_is_watered():
    """THE DARK 'N' STORMY CASE: ginger beer added after the shake.

    140 ml of recipe with 60 of it added afterwards is 80 x 1.25 + 60 =
    160 ml, which fits. Watering all 140 gives 175 ml, which is flagged --
    and that was the fault in the first list.
    """
    assert _verdict(140) == "tight", "all of it watered: 175 ml"
    assert _verdict(140, after=60) == "ok", "60 ml added after the shake: 160 ml"


def test_what_is_not_in_the_glass_is_not_counted_in_it():
    """A shell's rum is in the recipe and in the units; it is not in the glass."""
    assert _verdict(140) == "tight"
    assert _verdict(140, aside=25) == "ok", "(140 - 25) x 1.25 = 144 ml"


def test_the_top_flag_fires_only_when_there_is_hardly_any_room():
    """The house range says a top is at least 80 ml; a quarter of that is 20.

    A build leaving 60 ml was flagged by the first list ("less room than the
    house range expects") and is not now: since #1179 the site sizes the top
    from that room, so 60 ml IS the top. A build leaving 10 ml still is.
    """
    assert _verdict(72 + 60, top=60) == "ok", "72 x 1.25 = 90 ml of build, 60 ml of room"
    assert _verdict(112 + 10, top=10) == "top", "112 x 1.25 = 140 ml of build, 10 ml of room"


def test_the_judgements_the_report_reads_are_declared_in_the_real_data():
    """`check` reads these two keys off fit_rules; a rename would be a KeyError
    in a report nobody runs in CI."""
    import yaml
    rules = yaml.safe_load(
        (ROOT / "_data" / "cocktails" / "glasses.yml").read_text(encoding="utf-8"))["fit_rules"]
    for key in ("tolerance", "top_room_min"):
        assert isinstance(rules.get(key), (int, float)) and 0 < rules[key] < 1, (
            f"fit_rules.{key} must be a share between 0 and 1; it is {rules.get(key)!r}"
        )
