"""What a `makes:` line counts -- GitHub issue #1286.

On a recipe whose yield is `makes:`, the recipe page's scaler counts THE THING
MADE. Helen, 2026-10-04: "the scaler giving the number of items made ... would
be clearest to me. Never tell me how many cookies are in a portion!!!"

`_plugins/food_yield.rb` reads the line; this file asks it about every shape
the collection writes. The parser is Ruby, and the house rule (MANUAL §11.2,
and tests/test_food_shopping.py's own header) is that a Python copy of a Ruby
rule is drift that passes while the site is wrong. So nothing here re-implements
it: `scripts/food_yield.rb` runs the REAL module over a list of strings and
prints what it made of each, and one subprocess answers the whole file.

NO JEKYLL BUILD. The module is plain Ruby with no Jekyll in it, on purpose, so
this is a tenth of a second and not twenty.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

# Suite marker, so `pytest -m food` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one.
pytestmark = pytest.mark.food

ROOT = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Every shape, with Helen's ruling beside the ones she ruled on. The value is
# what the parser must return for the fields named; None means "no reading",
# which keeps the portions box exactly as it was.
# -----------------------------------------------------------------------------
COUNT = "count"
MEASURE = "measure"

CASES = {
    # --- a count of a named thing. A RANGE READS AS ITS LOWER NUMBER since
    # 2026-10-07 -- Helen: "lower number please, new ruling." It was the
    # midpoint ("Take the midpoint") for the three days before.
    "4–6 waffles, depending on your waffle iron":
        dict(kind=COUNT, base=4, low=4, high=6, stem="waffles", box="4", plus=False),
    "20–24 truffles": dict(kind=COUNT, base=20, stem="truffles", box="20"),
    "10–12 swans": dict(kind=COUNT, base=10, stem="swans", box="10"),
    "12 fairy cakes": dict(kind=COUNT, base=12, stem="fairy cakes", singular=False),
    "12 normal Yorkshire puddings":
        dict(kind=COUNT, base=12, stem="normal Yorkshire puddings"),
    "4 eggs": dict(kind=COUNT, base=4, stem="eggs"),
    "Estimated 24 cookies": dict(kind=COUNT, base=24, prefix="Estimated", stem="cookies"),
    "about 15 squares": dict(kind=COUNT, base=15, prefix="about", stem="squares"),
    # Helen: 'Can Delia\'s pancakes please scale as "8 pancakes", "16 pancakes".'
    # The file says "about 8" today, which names nothing (below); THIS is the
    # line it needs.
    "about 8 pancakes":
        dict(kind=COUNT, base=8, prefix="about", stem="pancakes", box="8", plus=False),
    # The thing ends at a comma, a bracket or an alternative.
    "1 large jar, or several small ones":
        dict(kind=COUNT, base=1, stem="large jar", singular=True),
    "2 pies (to serve 6)": dict(kind=COUNT, base=2, stem="pies"),
    "3 batches (total around 2.2 kg)": dict(kind=COUNT, base=3, stem="batches"),
    # The noun that takes the plural is the one before "of".
    "2 large rounds of 4": dict(kind=COUNT, base=2, stem="large rounds", rest=" of 4"),

    # --- these three read 5–6, 26 and 5–6 while a range took its midpoint
    # ("Midpoints that land on a half can become a range of one."). The lower
    # number never lands on a half, so no reading starts as a range of one.
    "4–7 buns": dict(kind=COUNT, base=4, low=4, high=7, box="4"),
    "24–28 rolls": dict(kind=COUNT, base=24, box="24"),
    "4 to 7 buns": dict(kind=COUNT, base=4, box="4"),

    # --- "64+ tiny macarons, 128+ tiny macarons": the plus is kept ------------
    "64+ tiny macarons":
        dict(kind=COUNT, base=64, stem="tiny macarons", box="64+", plus=True),

    # --- a number WORD at the start is a count: "Two 8-inch cakes" -----------
    "one 8-inch cake":
        dict(kind=COUNT, base=1, stem="8-inch cake", singular=True, times=True),
    "one double-layer 8-inch cake":
        dict(kind=COUNT, base=1, stem="double-layer 8-inch cake", times=False),
    "one 7-inch round cake": dict(kind=COUNT, base=1, stem="7-inch round cake", times=True),
    "one pie": dict(kind=COUNT, base=1, stem="pie", singular=True, times=False),
    'one 9"-square tin': dict(kind=COUNT, base=1, stem='9"-square tin', times=True),
    "Two 8-inch cakes": dict(kind=COUNT, base=2, stem="8-inch cakes", singular=False),

    # --- '"1 dozen" doubled can be "two dozen". Our scaler is integer.' ------
    "1 dozen mince pies":
        dict(kind=COUNT, base=1, stem="dozen mince pies", invariable=True),
    "about 3 dozen": dict(kind=COUNT, base=3, prefix="about", stem="dozen", invariable=True),

    # --- "950 ml for one order of a recipe becomes 1900 ml for 2" ------------
    "950 ml": dict(kind=MEASURE, base=950, unit="ml", prefix="", box="950"),
    "about 300 ml": dict(kind=MEASURE, base=300, unit="ml", prefix="about"),
    "approx. 75 g": dict(kind=MEASURE, base=75, unit="g", prefix="approx."),
    "approx. 140 g": dict(kind=MEASURE, base=140, unit="g", prefix="approx."),
    "About 750 ml": dict(kind=MEASURE, base=750, unit="ml", prefix="About"),
    "1 litre": dict(kind=MEASURE, base=1, unit="litre"),
    "about 2 kg (3 meals)": dict(kind=MEASURE, base=2, unit="kg"),
    "250 g, enough for approximately 8 ramen dishes": dict(kind=MEASURE, base=250, unit="g"),

    # --- no count at the START: the portions box stays -----------------------
    # 'for "some" we can retain the previous guess we made at portions'
    "Some": None,
    "some": None,
    "I mean, who cares, make double anyway": None,
    "N/A, bring a spoon": None,
    "however many you make": None,
    "QQ": None,
    # A number word that is NOT the yield's count, because it is not first.
    "Plenty for two people": None,
    "Enough for one normal lemon meringue pie": None,
    "Enough to top my 1.5-l Pyrex dish (22 x 17 cm) — about one food processor bowl full": None,
    "slightly more than half as much as my spice blender will fit, hmph": None,
    "enough for that edge-brownie tin I made James buy me": None,
    # "8-inch" is never the count: a digit that runs into a hyphen is a name.
    "8-inch cake": None,
    # `a` is not a number word here.
    "a batch": None,

    # --- a count of NOTHING NAMED: no word to put after the box --------------
    # Not ruled. "portions" is the one word it must not become, so these keep
    # today's control until Helen says what the word is.
    "about 8": None,
    "18": None,
    "12–16": None,
    "around 10": None,
    "9 or 16": None,
    # --- shapes nobody writes, which the integer box could not hold ----------
    "1.5 litres": None,
    "300–400 ml": None,
    "2.5 loaves": None,
}


def _ask(texts):
    """Run the real parser over `texts`. One subprocess, however many."""
    if shutil.which("ruby") is None:
        if os.environ.get("CI"):
            pytest.fail(
                "No ruby in CI, so _plugins/food_yield.rb cannot be asked "
                "anything and skipping would report green for the only check "
                "of what the scaler counts on a `makes:` recipe (#1286)."
            )
        pytest.skip("no ruby on this machine; the yield parser is Ruby")
    result = subprocess.run(
        ["ruby", "scripts/food_yield.rb", *texts],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, (
        "scripts/food_yield.rb failed:\n" + result.stdout[-2000:] + result.stderr[-2000:]
    )
    return json.loads(result.stdout)


def _front_matter(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1]) or {}
    except (IndexError, yaml.YAMLError):
        return {}


def _makes(folder):
    out = {}
    for path in sorted((ROOT / folder).rglob("*.md")):
        if ".git" in path.parts or path.name == "README.md":
            continue
        makes = _front_matter(path).get("makes")
        if makes not in (None, ""):
            out[path.stem] = str(makes)
    return out


PUBLISHED = _makes("_food_recipes")
DRAFTS = _makes("_food_drafts") if (ROOT / "_food_drafts").is_dir() else {}


@pytest.fixture(scope="module")
def readings():
    return _ask(sorted(set(CASES) | set(PUBLISHED.values()) | set(DRAFTS.values())))


@pytest.mark.parametrize("text", sorted(CASES))
def test_a_makes_line_is_read_as_what_it_counts(readings, text):
    """Each shape, against the fields that matter for it."""
    want, got = CASES[text], readings[text]
    if want is None:
        assert got is None, (
            f"`makes: {text!r}` must have NO reading, so the page keeps the "
            f"portions box; the parser returned {got}."
        )
    else:
        assert got is not None, f"`makes: {text!r}` was not read at all."
        wrong = {k: (got.get(k), v) for k, v in want.items() if got.get(k) != v}
        assert not wrong, (
            f"`makes: {text!r}` was misread. field: (got, wanted) -> {wrong}"
        )


def test_makes_is_never_read_as_people():
    """The rule #1286 must not weaken: 950 ml is not 950 portions.

    `portions_for` in _plugins/food_shopping.rb decides how many a recipe
    FEEDS, from `serves:` and then `serves_estimate:`, and must not look at
    `makes:` at all. What is new is `made_for`, a second and separate answer.
    Checked in the source because the alternative is a build, and what would
    go wrong is exactly one line.
    """
    source = (ROOT / "_plugins" / "food_shopping.rb").read_text(encoding="utf-8")
    start = source.index("def portions_for(doc)")
    body = source[start:source.index("\n    end\n", start)]
    code = "\n".join(line.split("#", 1)[0] for line in body.splitlines())
    assert "makes" not in code, (
        "`portions_for` in _plugins/food_shopping.rb now reads `makes:`. A "
        "yield is never a head count -- that is what `serves_estimate:` is for."
    )
    assert 'doc.data["made"] = made_for(doc, yields)' in source, (
        "_plugins/food_shopping.rb no longer hangs `made` on each recipe, so "
        "every `makes:` recipe is back to saying portions (#1286)."
    )


# The published recipes whose `makes:` has no count of a named thing at its
# start. THESE KEEP THE PORTIONS BOX, "~" and all. Named one by one because
# this is the list Helen was shown, and a recipe joining or leaving it is a
# change to what her page says.
KEEPS_PORTIONS = {
    # no number at all -- 'for "some" we can retain the previous guess'
    "caramel": "I mean, who cares, make double anyway",
    "cherry-glaze": "Some",
    "chocolate-ganache": "N/A, bring a spoon",
    "five-spice-powder": "some",
    "gluten-free-crumble-topping":
        "Enough to top my 1.5-l Pyrex dish (22 x 17 cm) — about one food processor bowl full",
    "goats-cheese-squash-rosemary-griddle-cakes": "Plenty for two people",
    "grandmas-lemon-curd": "Enough for one normal lemon meringue pie",
    "mixed-spice-powder":
        "slightly more than half as much as my spice blender will fit, hmph",
    "slow-cooked-duck-legs-confit": "however many you make",
    "the-one-true-chocolate-brownies":
        "enough for that edge-brownie tin I made James buy me",
    # `delias-classic-pancakes` WAS HERE as `about 8`, a count of nothing
    # named. Helen, 2026-10-04: "Can Delia's pancakes please scale as "8
    # pancakes", "16 pancakes"." The fix was the data, not a rule for unnamed
    # counts: the recipe says `about 8 pancakes` now and is read like any other.
}


def test_the_published_recipes_that_keep_the_portions_box_are_the_listed_ones(readings):
    unread = {slug: text for slug, text in PUBLISHED.items() if readings[text] is None}
    assert unread == KEEPS_PORTIONS, (
        "The published `makes:` recipes with no reading -- the ones whose "
        "scaler still says portions -- are not the listed set.\n"
        f"  now unread, not listed: {sorted(set(unread) - set(KEEPS_PORTIONS))}\n"
        f"  listed, now read:       {sorted(set(KEEPS_PORTIONS) - set(unread))}\n"
        f"  text changed:           "
        f"{sorted(s for s in set(unread) & set(KEEPS_PORTIONS) if unread[s] != KEEPS_PORTIONS[s])}\n"
        "If that is intended, move the recipe in KEEPS_PORTIONS and tell Helen "
        "which page changed what it counts."
    )


def test_every_reading_starts_from_a_whole_number_or_a_range_of_one(readings):
    """'Our scaler is integer.' Over every real line, published and drafts.

    The box shows a whole number, or a range of one ("5–6") for a figure on a
    half. Since 2026-10-07 a `makes:` range reads as its lower number, so no
    real line starts on a half; the half branch is kept so that a reading
    which ever does is still held to the shape the page can show.
    """
    problems = []
    for text in sorted(set(PUBLISHED.values()) | set(DRAFTS.values())):
        got = readings[text]
        if got is None:
            continue
        base = got["base"]
        if base < 1 or (base * 2) != int(base * 2):
            problems.append(f"{text!r}: base {base}")
        elif base != int(base) and got["box"] != f"{int(base)}–{int(base) + 1}":
            problems.append(f"{text!r}: base {base} shown as {got['box']!r}")
        elif base == int(base) and got["box"].rstrip("+") != str(int(base)):
            problems.append(f"{text!r}: base {base} shown as {got['box']!r}")
    assert not problems, "a `makes:` reading the integer box cannot hold:\n  " + "\n  ".join(problems)


# =============================================================================
# THE HALF STEP -- "Half a recipe would be great where the numbers aren't
# insane! Can we judge that?" (Helen, 2026-10-04)
# =============================================================================
# _plugins/food_half_recipe.rb judges it at build time. As above, the REAL
# judge is asked, through scripts/food_yield.rb --half, once.

def _recipe(makes, items, estimate=4, serves=None):
    return {"makes": makes, "serves": serves, "serves_estimate": estimate,
            "ingredient_groups": [{"items": [
                {"amount": a, "item": i} if a is not None else {"item": i}
                for a, i in items]}]}


# name: (recipe, offered a half?, a word the reason must contain or None)
HALF_CASES = {
    # --- weights and volumes always halve ------------------------------------
    "grams and ml": (_recipe("12 buns", [("125 g", "butter"), ("313 ml", "milk"),
                                         ("1.2 kg", "flour"), ("1 litre", "stock")]), True, None),
    # --- spoons halve down to an eighth, no further --------------------------
    "quarter tsp": (_recipe("12 buns", [("¼ tsp", "salt"), ("1½ tbsp", "oil")]), True, None),
    "eighth tsp": (_recipe("12 buns", [("⅛ tsp", "black pepper")]), False, "eighth"),
    "third cup": (_recipe("12 buns", [("⅓ cup", "milk")]), False, "quarter cup"),
    # --- a cup goes down to a quarter and no further -------------------------
    # The waffles: 1¾ cups halved is "⅞ cups". "Please take the half step off
    # the waffles. 2-3 waffles isn't enough!!!!"
    "one and three quarter cups": (_recipe("12 buns", [("1¾ cups", "milk")]), False, "quarter cup"),
    "quarter cup": (_recipe("12 buns", [("¼ cup", "oil")]), False, "quarter cup"),
    "half cup": (_recipe("12 buns", [("½ cup", "oil"), ("2 cups", "flour")]), True, None),
    "the waffles": (_recipe("4–6 waffles", [("2 large", "eggs"), ("1¾ cups", "whole milk"),
                                            ("½ cup", "groundnut oil")]), False, "1¾ cups"),
    "heaped tbsp": (_recipe("12 buns", [("1 heaped tbsp", "tomato purée")]), True, None),
    "bracket restates": (_recipe("12 buns", [("1 tbsp (6 g)", "cloves")]), True, None),
    # --- a count halves only if even, or halvable ----------------------------
    "two eggs": (_recipe("12 buns", [("2 large", "eggs")]), True, None),
    "three eggs": (_recipe("12 buns", [("3 large", "eggs")]), False, "3 large eggs"),
    "one egg": (_recipe("12 buns", [("1", "egg yolk")]), False, "does not halve"),
    "one lemon": (_recipe("12 buns", [("1", "lemon, zest and juice")]), True, None),
    "one large onion": (_recipe("12 buns", [("1 large", "onion, diced")]), True, None),
    "three garlic cloves": (_recipe("12 buns", [("3 cloves", "garlic")]), True, None),
    # --- "In: leaf, star anise, nutmeg, stock cube, sachet, tin, jar." -------
    "half a nutmeg": (_recipe("12 buns", [("½ small", "whole nutmeg")]), True, None),
    "one star anise": (_recipe("12 buns", [("1 large", "star anise")]), True, None),
    "three bay leaves": (_recipe("12 buns", [("3", "dried bay leaves, torn")]), True, None),
    "one stock cube": (_recipe("12 buns", [("1", "chicken stock cube")]), True, None),
    "one sachet": (_recipe("12 buns", [("1 x 7 g sachet", "dried yeast")]), True, None),
    "one jar of an ingredient": (_recipe("12 buns", [("1 jar", "roasted peppers")]), True, None),
    # --- "Eggs: not halvable for food recipes." and the lot of another recipe -
    "one lot": (_recipe("950 ml", [("1 lot", "[sweet cream base](../x/)")]), False, "does not halve"),
    "three cardamom pods": (_recipe("12 buns", [("3 (3 g)", "black cardamom pods")]), False, "does not halve"),
    "one sprig": (_recipe("12 buns", [("1 sprig", "rosemary")]), False, "does not halve"),
    "one tin": (_recipe("12 buns", [("1 x 400 g", "tin tomatoes")]), True, None),
    "one can": (_recipe("12 buns", [("1 x 400 g can", "chickpeas")]), False, "does not halve"),
    "two tins": (_recipe("12 buns", [("2 x 400 g cans", "chickpeas")]), True, None),
    "a range of eggs": (_recipe("12 buns", [("2–3", "eggs")]), False, "does not halve"),
    # --- what does not scale cannot object -----------------------------------
    "no amount": (_recipe("12 buns", [(None, "salt, to taste"), ("some", "pepper")]), True, None),
    "by-eye measures": (_recipe("12 buns", [("1 handful", "parsley"), ("1 pinch", "salt")]), True, None),
    # --- the yield has to halve too ------------------------------------------
    "one cake": (_recipe("one 8-inch cake", [("200 g", "flour")]), False, "less than one"),
    "one jar": (_recipe("1 jar", [("200 g", "sugar")]), False, "less than one"),
    "one dozen": (_recipe("1 dozen mince pies", [("200 g", "flour")]), False, "less than one"),
    "one litre": (_recipe("1 litre", [("200 g", "bones")]), False, "less than one"),
    "four waffles": (_recipe("4–6 waffles", [("2 large", "eggs")]), True, None),
    "two burgers": (_recipe("2 burgers", [("200 g", "mince")]), True, None),
    "odd ml": (_recipe("125 ml", [("50 ml", "soy sauce")]), True, None),
    # --- the portions box: even halves, odd does not -------------------------
    "some, four": (_recipe("Some", [("200 g", "sugar")], estimate=4), True, "4 portions"),
    "some, five": (_recipe("Some", [("200 g", "sugar")], estimate=5), False, "odd"),
}

# NOT HERE, AND HELEN'S OWN CALL: henrys-sunday-waffles. "Please take the half
# step off the waffles. 2-3 waffles isn't enough!!!!" -- it goes by the cup
# rule (1¾ cups would halve to ⅞), not by naming the recipe.
#
# The published `makes:` recipes that ARE offered a half step. Named, because
# this is the list Helen was given to check against recipes she knows; the
# rest of the published `makes:` recipes are not offered one.
GETS_A_HALF_STEP = {
    "ajitsuke-tamago", "ben-jerrys-sweet-cream-base-1", "ben-jerrys-sweet-cream-base-2",
    "ben-jerrys-sweet-cream-base-3", "bens-chocolate-ice-cream",
    # caramel: since 2026-10-08, when Helen moved its estimate from 5 to 6
    # (#1089). Five was refused as odd; six halves to three.
    "caramel", "cherry-glaze",
    "chocolate-ganache", "delias-classic-pancakes", "five-spice-powder",
    "gluten-free-crumble-topping", "grandmas-fairy-cakes",
    "henrys-dark-chocolate-almond-truffles",
    "jerrys-chocolate-ice-cream", "macarons", "mixed-spice-powder",
    "mrs-nicholsons-creme-patissiere",
    "mrs-nicholsons-yorkshire-puddings", "slow-cooked-duck-legs-confit",
    "sweet-potato-chocolate-brownies", "teriyaki-sauce", "wagamama-teriyaki-sauce",
    "wagamama-yakitori-sauce",
}


@pytest.fixture(scope="module")
def verdicts():
    if shutil.which("ruby") is None:
        if os.environ.get("CI"):
            pytest.fail("No ruby in CI, so the half-recipe judge cannot be asked (#1286).")
        pytest.skip("no ruby on this machine; the half-recipe judge is Ruby")
    recipes = [dict(recipe, key="case:" + name) for name, (recipe, _ok, _why) in HALF_CASES.items()]
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        fm = _front_matter(path)
        if fm.get("makes") in (None, ""):
            continue
        recipes.append({"key": "published:" + path.stem, "makes": str(fm["makes"]),
                        "serves": fm.get("serves"),
                        "serves_estimate": fm.get("serves_estimate"),
                        "ingredient_groups": fm.get("ingredient_groups")})
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    handoff = scratch / f"half-recipe-{os.getpid()}.json"
    handoff.write_text(json.dumps(recipes, ensure_ascii=False, default=str), encoding="utf-8")
    try:
        result = subprocess.run(
            ["ruby", "scripts/food_yield.rb", "--half", str(handoff.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    finally:
        handoff.unlink(missing_ok=True)
    assert result.returncode == 0, (
        "scripts/food_yield.rb --half failed:\n" + result.stdout[-2000:] + result.stderr[-2000:]
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize("name", sorted(HALF_CASES))
def test_the_half_step_is_offered_only_where_halving_is_sane(verdicts, name):
    _recipe_, want, reason = HALF_CASES[name]
    got = verdicts["case:" + name]["half"]
    assert got["ok"] is want, (
        f"{name}: the judge said {'yes' if got['ok'] else 'no'} to a half "
        f"recipe ({got['why']}); it should say {'yes' if want else 'no'}."
    )
    assert reason is None or reason in got["why"], (
        f"{name}: the judge's reason should mention {reason!r}; it gave {got['why']!r}."
    )


def test_the_published_recipes_offered_a_half_step_are_the_listed_ones(verdicts):
    offered = {key.split(":", 1)[1] for key, v in verdicts.items()
               if key.startswith("published:") and v["half"]["ok"]}
    refused = {key.split(":", 1)[1]: v["half"]["why"] for key, v in verdicts.items()
               if key.startswith("published:") and not v["half"]["ok"]}
    assert len(offered) + len(refused) > 30, (
        f"only {len(offered) + len(refused)} published `makes:` recipes were "
        f"judged; the scan has stopped finding them."
    )
    assert offered == GETS_A_HALF_STEP, (
        "The published recipes offered a half step are not the listed set.\n"
        f"  now offered, not listed: {sorted(offered - GETS_A_HALF_STEP)}\n"
        f"  listed, now refused:     "
        f"{sorted((s, refused.get(s)) for s in GETS_A_HALF_STEP - offered)}\n"
        "If that is intended, update GETS_A_HALF_STEP and tell Helen which "
        "page gained or lost its ½."
    )
