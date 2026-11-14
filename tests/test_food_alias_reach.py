"""Every food alias key is still reachable (#1480).

An alias key in _data/food/ingredient_words.yml fires only when an ingredient
string, after the strips, is exactly that key. This hands
tests/js/alias-reach.js every string food/index.html hands the pickers and
asks which keys none of them reach. A dead key is REPORTED at the end of the
run, never failed: a fix to a recipe line can retire an alias, and a red main
stops every deploy. The test itself fails only if the check cannot run.
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest
import yaml

import conftest
from conftest import ALL_DRAFTS, ALL_RECIPES, ROOT

pytestmark = pytest.mark.food

WORDS = ROOT / "_data" / "food" / "ingredient_words.yml"
REACH = ROOT / "tests" / "js" / "alias-reach.js"


def picker_strings(recipes) -> list[str]:
    """What food/index.html gives the pickers: each `main_ingredients` entry,
    and each `item:` cut at its first comma, then its first bracket, trimmed
    and lowercased. A link item (opening `[`) gives nothing."""
    out = []
    for recipe in recipes:
        out += [str(m) for m in recipe.fm.get("main_ingredients") or []]
        for item in recipe.ingredient_items:
            item = str(item)
            if item.startswith("["):
                continue
            name = item.split(",")[0].split("(")[0].strip().lower()
            if name:
                out.append(name)
    return out


def test_picker_strings_follow_the_index():
    class Fake:
        fm = {"main_ingredients": ["Chicken"]}
        ingredient_items = ["onions, sliced", "stock (homemade)", "[pastry](x)", ""]
    assert picker_strings([Fake()]) == ["Chicken", "onions", "stock"]


def _reach(tmp_path, vocabulary, strings):
    given = tmp_path / "alias-reach.json"
    given.write_text(json.dumps({"vocabulary": vocabulary, "strings": strings}),
                     encoding="utf-8")
    run = subprocess.run(["node", str(REACH), str(given)],
                         capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


def test_the_check_tells_a_dead_key_from_a_live_one(tmp_path):
    """A key reached only through the strips is live; a key nothing produces
    is dead; and the end-of-run report names it."""
    if shutil.which("node") is None:
        pytest.fail("node is not installed, so the alias check cannot run")
    vocabulary = yaml.safe_load(WORDS.read_text(encoding="utf-8"))
    vocabulary["aliases"] = {"beef or venison stock": ["beef stock"],
                             "zzz never written": "x"}
    result = _reach(tmp_path, vocabulary, ["500 ml beef or venison stock"])
    assert result["dead"] == ["zzz never written"]

    lines = []
    conftest._report_dead_aliases(lambda text="", **_: lines.append(text),
                                  result["dead"])
    assert any("zzz never written" in line for line in lines), lines
    conftest._report_dead_aliases(lambda text="", **_: lines.append("!"), [])
    assert "!" not in lines, "an empty list must print nothing"


def test_every_alias_key_is_reachable(tmp_path):
    if not ALL_DRAFTS:
        pytest.skip(
            "_food_drafts/ is absent (private, gitignored repo). Some alias "
            "keys exist for drafts only, so without them this would report "
            "live keys as dead. Runs on a machine with the drafts checked out.")
    assert ALL_RECIPES, "no published recipes, so this would check nothing"
    if shutil.which("node") is None:
        pytest.fail("node is not installed, so the alias check cannot run")
    vocabulary = yaml.safe_load(WORDS.read_text(encoding="utf-8"))
    assert vocabulary.get("aliases"), f"{WORDS.name} has no aliases to check"

    result = _reach(tmp_path, vocabulary, picker_strings(ALL_RECIPES + ALL_DRAFTS))
    assert result["entries"] > 100, f"only {result['entries']} picker entries built"
    conftest.DEAD_ALIASES[:] = result["dead"]
