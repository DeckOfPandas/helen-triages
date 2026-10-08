"""`scripts/check_food_tags.py` -- the report, and the hints it reads.

The script never fails a recipe, so these tests are about the two things that
can rot quietly: a hint naming a tag or star that no longer exists (it would
then report nothing, for ever, and look healthy), and the word matcher.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_food_tags as checker  # noqa: E402

# Suite marker, so `pytest -m food` can run this half alone.
pytestmark = pytest.mark.food


def test_every_hint_names_a_declared_tag_or_star(taxonomy):
    hints = taxonomy.get("tag_hints") or {}
    assert hints, "`tag_hints` is missing from _data/food/taxonomy.yml."
    declared_tags = set()
    for group in (taxonomy.get("tags") or {}).values():
        declared_tags.update(group)
    stars = set(taxonomy.get("star_ingredients") or [])
    bad = [f"tags.{t}" for t in hints.get("tags") or {} if t not in declared_tags]
    bad += [f"star_ingredient.{s}" for s in hints.get("star_ingredient") or {} if s not in stars]
    assert not bad, (
        f"`tag_hints` names {bad}, which taxonomy.yml does not declare. A hint "
        f"for a retired or renamed tag reports nothing and looks healthy; "
        f"rename or remove it."
    )


def test_every_hint_has_a_shape_the_checker_reads(taxonomy):
    hints = taxonomy.get("tag_hints") or {}
    bad = []
    for kind in ("tags", "star_ingredient"):
        for name, hint in (hints.get(kind) or {}).items():
            keys = set(hint or {})
            if not keys or keys - {"title", "ingredients_all", "text_any"}:
                bad.append(f"{kind}.{name}: {sorted(keys)}")
    assert not bad, (
        f"These hints carry a key check_food_tags.py does not read, or none at "
        f"all, so they can never fire: {bad}"
    )


@pytest.mark.parametrize("text, word, expected", [
    ("Chicken and Prawn Pad Thai", "prawn", True),
    ("Garlic Prawns", "prawn", True),
    ("A Load of Codswallop", "cod", False),
    ("Graham Cracker Crust", "ham", False),
    ("Peanut Butter Ice Cream", "ice cream", True),
    ("Miso Salmon Traybake", "SALMON", True),
])
def test_words_match_whole_and_plural(text, word, expected):
    assert checker.has_word(text, word) is expected


def test_a_missing_tag_and_a_blank_star_are_both_reported():
    hints = {
        "tags": {"salad": {"title": ["salad"]},
                 "bakes": {"ingredients_all": ["flour", "sugar"]}},
        "star_ingredient": {"poultry": {"title": ["chicken"]},
                            "pork": {"title": ["pork"]}},
    }
    fm = {
        "title": "Chicken Salad",
        "tags": ["virtuous"],
        "ingredient_groups": [{"items": [{"item": "plain flour"}, {"item": "caster sugar"}]}],
    }
    missing, stars = checker.check(fm, hints)
    assert [t for t, _why in missing] == ["salad", "bakes"]
    assert [(s, star) for s, star, _why in stars] == [("poultry", "")]


def test_a_phrase_is_found_in_grouped_steps_and_notes_but_frozen_peas_are_not():
    hints = {"tags": {"freezable": {"text_any": ["freezes well", "frozen for up to"]}}}
    grouped = {"title": "Ragù", "tags": [], "ingredient_groups": [],
               "method_groups": [{"name": "sauce", "steps": ["Simmer. It freezes well."]}]}
    noted = {"title": "Ragù", "tags": [], "ingredient_groups": [],
             "notes": [{"label": "keeping", "text": "Frozen for up to three months."}]}
    peas = {"title": "Tabbouleh", "tags": [], "ingredient_groups": [],
            "method": ["Mix in the frozen peas and freeze nothing."]}
    assert [t for t, _w in checker.check(grouped, hints)[0]] == ["freezable"]
    assert [t for t, _w in checker.check(noted, hints)[0]] == ["freezable"]
    assert checker.check(peas, hints) == ([], [])


def test_a_recipe_that_agrees_is_silent():
    hints = {"tags": {"salad": {"title": ["salad"]}},
             "star_ingredient": {"poultry": {"title": ["chicken"]},
                                 "pork": {"title": ["pork"]}}}
    fm = {"title": "Chicken and Pork Salad", "tags": ["salad"],
          "star_ingredient": "pork", "ingredient_groups": []}
    assert checker.check(fm, hints) == ([], [])
