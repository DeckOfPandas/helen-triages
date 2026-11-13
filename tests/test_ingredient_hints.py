"""_data/food/ingredient_hints.yml: the stock and spice hints' figures (MANUAL
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


def test_every_spice_has_words_a_weight_and_something_to_say():
    wrong = []
    for s in DATA["spices"]:
        if not s.get("match"):
            wrong.append(f"{s['name']}: no match words")
        if not isinstance(s.get("g_per_tsp"), (int, float)) or not 0.5 < s["g_per_tsp"] < 6:
            wrong.append(f"{s['name']}: g_per_tsp {s.get('g_per_tsp')!r} is not a teaspoon's weight")
        if not (s.get("whole") or s.get("fresh_tbsp_per_tsp")):
            wrong.append(f"{s['name']}: no whole spice and no fresh figure, so no hint to give")
    assert not wrong, "\n".join(wrong)
