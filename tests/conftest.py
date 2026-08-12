"""Shared fixtures and helpers for the Helen Triages Food test suite.

Run from the repo root:

    pytest -q                  # everything
    pytest -q tests/test_times.py   # one file
    pytest -q -k cavolo             # everything touching one recipe

Every test is parametrised per recipe file, so a failure names the file it
came from rather than making you go and find it.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent

# This is a mono-repo: food and cocktails are built from one Jekyll site, so a
# collection's source directory carries the site in its name. Jekyll only finds
# a collection at `_<name>` directly under the repo root — `food/_recipes/` is
# not discovered, and fails silently — so the directories cannot nest under
# food/ however much tidier that would read. See _config.yml.
#
# This suite is the FOOD suite. When cocktails has real files, these tests
# either get parametrised by collection or gain a sibling
# test_cocktail_front_matter.py; the food schema does not apply to a cocktail.
RECIPES_DIR = ROOT / "_food_recipes"
DRAFTS_DIR = ROOT / "_food_drafts"

# Food's own vocabulary: taxonomy, filter sections, pantry, ingredient words.
DATA_DIR = ROOT / "_data" / "food"

# Data that is genuinely shared across the mono-repo. accented_words.yml lives
# here rather than under food/ because it is HOUSE STYLE, not food vocabulary —
# British spellings and the curated unaccented→accented map apply to a cocktail
# recipe exactly as they do to a food one, and `crème de cassis` will want the
# same treatment `crème fraîche` gets.
SHARED_DATA_DIR = ROOT / "_data"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\s*(.*)\Z", re.S)


class Recipe:
    """One recipe file: its path, parsed front matter, and raw text."""

    def __init__(self, path: Path):
        self.path = path
        self.slug = path.stem
        self.raw = path.read_text(encoding="utf-8")
        match = FRONT_MATTER.match(self.raw)
        if match is None:
            raise ValueError(f"{path.name} has no front matter delimiters")
        self.fm = yaml.safe_load(match.group(1)) or {}
        self.body = match.group(2).strip()

    def __repr__(self) -> str:      # what pytest prints in the test id
        return self.slug

    # -- convenience accessors -------------------------------------------

    @property
    def ingredient_items(self) -> list[str]:
        out = []
        for group in self.fm.get("ingredient_groups") or []:
            for item in group.get("items") or []:
                if isinstance(item, dict) and item.get("item"):
                    out.append(item["item"])
                elif isinstance(item, str):
                    out.append(item)
        return out

    @property
    def method_steps(self) -> list[str]:
        out = []
        for step in self.fm.get("method") or []:
            out.append(step.get("step") if isinstance(step, dict) else step)
        for group in self.fm.get("method_groups") or []:
            for step in group.get("steps") or []:
                out.append(step.get("step") if isinstance(step, dict) else step)
        return [s for s in out if s]

    @property
    def prose(self) -> list[tuple[str, str]]:
        """Every stretch of human-readable prose, tagged with where it came from.

        Used by the typography and time-word tests so their failure messages can
        say "in a method step" rather than just "somewhere in the file".
        """
        out: list[tuple[str, str]] = []
        if self.fm.get("tagline"):
            out.append(("tagline", self.fm["tagline"]))
        for i, step in enumerate(self.method_steps, 1):
            out.append((f"method step {i}", step))
        for i, note in enumerate(self.fm.get("notes") or [], 1):
            if isinstance(note, dict):
                if note.get("label"):
                    out.append((f"note {i} label", note["label"]))
                if note.get("text"):
                    out.append((f"note {i}", note["text"]))
            else:
                out.append((f"note {i}", note))
        for i, short in enumerate(self.fm.get("method_short") or [], 1):
            if short:
                out.append((f"method_short {i}", short))
        for group in self.fm.get("ingredient_groups") or []:
            for item in group.get("items") or []:
                if isinstance(item, dict) and item.get("note"):
                    out.append((f"note on '{item.get('item')}'", item["note"]))
        return out


def _load(directory: Path) -> list[Recipe]:
    if not directory.is_dir():
        return []
    return [Recipe(p) for p in sorted(directory.glob("*.md"))]


ALL_RECIPES = _load(RECIPES_DIR)
ALL_DRAFTS = _load(DRAFTS_DIR)


def pytest_generate_tests(metafunc):
    """Parametrise any test that asks for a `recipe` or `draft` argument.

    A `draft`-parametrised hook lived here until 2026-08-10 with zero
    consumers, and was removed rather than kept "in case" — added back
    2026-08-11 for tests/test_drafts.py, the day one actually needed it.
    `recipe` and `draft` are deliberately separate fixtures over separate
    lists (ALL_RECIPES vs ALL_DRAFTS) so a recipe-only rule (e.g. a blank
    tagline, a missing `QQ`) never gets silently enforced against a draft,
    and vice versa — see test_drafts.py's own module docstring for which
    rules apply to both and which don't.

    The five tests that read `_food_drafts/` directly via the ALL_DRAFTS
    list rather than this fixture (test_no_main_ingredient_spelling_
    collisions, test_pantry_entries_are_actually_used, test_no_recipe_uses_
    the_retired_instructions_field, test_accents_in_drafts, test_pan_and_
    ingredient_sizes_use_digits_in_drafts) are cross-collection or module-
    level checks that don't want a per-file failure id, so they're left as
    they are rather than converted.
    """
    if "recipe" in metafunc.fixturenames:
        metafunc.parametrize("recipe", ALL_RECIPES, ids=[r.slug for r in ALL_RECIPES])
    if "draft" in metafunc.fixturenames:
        metafunc.parametrize("draft", ALL_DRAFTS, ids=[d.slug for d in ALL_DRAFTS])


@pytest.fixture(scope="session")
def all_recipes() -> list[Recipe]:
    return ALL_RECIPES


@pytest.fixture(scope="session")
def taxonomy() -> dict:
    """_data/food/taxonomy.yml — the food vocabulary layer.

    Namespaced by site in the mono-repo migration: cocktails has its own at
    _data/cocktails/taxonomy.yml, and the two schemas are deliberately separate.
    """
    path = DATA_DIR / "taxonomy.yml"
    if not path.exists():
        pytest.skip(
            "_data/food/taxonomy.yml does not exist. These tests are the spec "
            "for it — create the file and they will start enforcing the "
            "taxonomy automatically."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def internal_temperatures() -> dict:
    """_data/food/internal_temperatures.yml — pull temps, endpoints and

    carryover, single source of truth for both the reference page and a
    recipe's own `internal_temp_ref` front-matter field. See that file's own
    header comment for the shapes it uses.
    """
    path = DATA_DIR / "internal_temperatures.yml"
    if not path.exists():
        pytest.skip(
            "_data/food/internal_temperatures.yml does not exist. These "
            "tests are the spec for it."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def where(recipe: Recipe, detail: str = "") -> str:
    """Consistent location prefix for failure messages."""
    return f"_food_recipes/{recipe.slug}.md" + (f" — {detail}" if detail else "")


def where_draft(draft: Recipe, detail: str = "") -> str:
    """Same as where(), for a _food_drafts/ file — the two collections are
    never confused in a failure message even though they share the Recipe
    class.
    """
    return f"_food_drafts/{draft.slug}.md" + (f" — {detail}" if detail else "")
