"""_data/food/ingredient_hints.yml: the stock, spice, paste and vanilla hints' figures (MANUAL
§8.2). assets/js/food-hints.js trusts this shape, and tests/js/food-hints.test.js
uses a fixture of it; this holds the real file to that fixture's shape."""
from __future__ import annotations

import pathlib

import pytest
import yaml

pytestmark = pytest.mark.food

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = yaml.safe_load((ROOT / "_data" / "food" / "ingredient_hints.yml").read_text(encoding="utf-8"))

# Helen chose all six brands for the stock hint.
BRANDS = {"Kallo", "Knorr", "Oxo", "Marigold bouillon", "Bay's Kitchen", "M&S concentrate"}


def test_the_stock_hint_names_all_six_brands():
    names = {p["name"] for p in DATA["stock"]["products"]}
    assert names == BRANDS, f"products are {sorted(names)}, Helen chose {sorted(BRANDS)}"


def test_every_stock_figure_is_a_known_flavour_and_a_positive_volume():
    flavours = set(DATA["stock"]["flavours"])
    wrong = []
    for p in DATA["stock"]["products"]:
        assert p.get("unit"), f"{p['name']} has no unit"
        for flavour, ml in p["flavours"].items():
            if flavour not in flavours:
                wrong.append(f"{p['name']}: {flavour!r} is not in stock.flavours")
            if not isinstance(ml, (int, float)) or ml <= 0:
                wrong.append(f"{p['name']} {flavour}: {ml!r} is not a volume")
    assert not wrong, "\n".join(wrong)


def test_vanilla_is_paste_pod_and_extract_one_for_one():
    """Helen's ruling (#1517): 1 tsp paste = 1 tsp extract = 1 pod."""
    forms = {f["name"]: f for f in DATA["vanilla"]["forms"]}
    assert set(forms) == {"vanilla bean paste", "vanilla pod", "vanilla extract"}
    assert {f["name"]: (f["unit"], f["per_pod"]) for f in forms.values()} == {
        "vanilla bean paste": ("tsp", 1), "vanilla pod": ("pod", 1),
        "vanilla extract": ("tsp", 1)}
    assert "essence" in DATA["vanilla"]["unless"], "vanilla essence was not ruled on"


def test_every_spice_has_words_and_a_weight_and_its_whole_form_a_figure():
    wrong = []
    for s in DATA["spices"]:
        if not s.get("match"):
            wrong.append(f"{s['name']}: no match words")
        if not isinstance(s.get("g_per_tsp"), (int, float)) or not 0.5 < s["g_per_tsp"] < 6:
            wrong.append(f"{s['name']}: g_per_tsp {s.get('g_per_tsp')!r} is not a teaspoon's weight")
        whole = s.get("whole")
        if whole is None:
            continue
        if not whole.get("match"):
            wrong.append(f"{s['name']}: whole form has no match words")
        if ("g_per_tsp" in whole) == ("g_each" in whole):
            wrong.append(f"{s['name']}: whole form needs exactly one of g_per_tsp, g_each")
        if "g_each" in whole and not s.get("per_whole_tsp"):
            wrong.append(f"{s['name']}: a counted whole form needs per_whole_tsp")
    assert not wrong, "\n".join(wrong)


# Helen's ruling on #1528: a whole form only where a reputable figure exists.
SOURCED_WHOLE = {"cumin", "coriander", "nutmeg", "black pepper", "fennel", "fenugreek"}


def test_only_the_sourced_whole_spices_have_a_whole_figure():
    have = {s["name"] for s in DATA["spices"] if s.get("whole")}
    assert have == SOURCED_WHOLE, (
        f"whole forms are {sorted(have)}; the sourced ones are {sorted(SOURCED_WHOLE)}. "
        "A new one needs a reputable figure and Helen's say-so (#1528)."
    )


def test_the_pastes_are_the_jars_figures_and_helens_lemongrass():
    per = {p["name"]: (p["fresh"], p["tsp_per"]) for p in DATA["pastes"]}
    assert per == {
        "ginger": ("cm", [1, 1]), "galangal": ("cm", [1, 1]),
        "garlic": ("count", [1, 1]), "lemongrass": ("count", [1, 2])}
