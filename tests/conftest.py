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

# THE MAGIC BAG — dishes Helen makes without a recipe, added 2026-08-26.
#
# A THIRD COLLECTION AND A THIRD FIXTURE, not a widening of `recipe`. Every
# structural rule in test_front_matter.py is unconditional on purpose, and
# folding these in would force each one to grow an `if` — a magic-bag entry has
# no method, no source and no method_short, all of which a recipe MUST have. The
# separate list keeps the recipe rules absolute and gives the new shape its own
# spec in test_magic_bag.py, exactly as the `recipe`/`draft` split already does.
#
# IT IS IN THIS PUBLIC REPO, unlike _food_drafts/, so DRAFTS_PRESENT has no
# equivalent here: CI sees the whole collection. If that ever changes, this
# needs the same treatment issue #378 gave drafts, and test_suite_hygiene.py's
# registries are where it would have to be declared.
MAGIC_BAG_DIR = ROOT / "_food_magic_bag"

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
        # THE MAGIC BAG'S FLAT `ingredients:` LIST, added 2026-08-26. A recipe
        # carries `ingredient_groups` and no `ingredients`; a magic-bag entry
        # carries `ingredients` and no `ingredient_groups`, and both halves are
        # enforced (test_front_matter.py, test_magic_bag.py). So this branch is
        # a no-op on every recipe rather than a behaviour change to them, and
        # the ingredient-vocabulary rules — salted vs unsalted butter, which
        # soy, which sugar — reach the new collection without being rewritten
        # for it. Those rules are about the WORDS, and a magic-bag entry's words
        # go on the page like any other.
        for item in self.fm.get("ingredients") or []:
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
        # Magic-bag ingredient notes — see ingredient_items above for why this
        # is a no-op on a recipe. A note here renders exactly as a recipe's
        # does, so it is held to the same typography and house style.
        for item in self.fm.get("ingredients") or []:
            if isinstance(item, dict) and item.get("note"):
                out.append((f"note on '{item.get('item')}'", item["note"]))
        return out


def _load(directory: Path) -> list[Recipe]:
    """Every .md at or below `directory`, recursively.

    RECURSIVE SINCE 2026-08-20, AND IT MATTERS. This used to be `glob("*.md")`,
    which was correct while `_food_drafts/` was flat. Helen then built a
    three-stage staging pipeline -- `to-cook/`, `to-rewrite/`, `to-promote/` --
    and moved drafts into it, at which point every draft test stopped seeing
    them. Not failing on them: not looking at them, and reporting green.

    That is the same failure `DRAFTS_PRESENT` below exists to prevent, arriving
    through a new door: a suite that is honest about the files it read and
    silent about the ones it never opened. The staged drafts are the ones
    closest to publication, so they were precisely the wrong ones to stop
    checking.

    `sorted()` over `rglob` orders by full path, so a staged draft sorts under
    its folder rather than among the flat ones. Ids still come from the stem.

    A `README.md` AT THE ROOT IS NOT A RECIPE, and it is the ONLY name skipped.
    `_food_drafts/` gained one on 2026-09-03 (the private repos had described
    themselves nowhere) and this loader raised on it at import, taking the
    whole suite down before a test ran. The skip is by exact name rather than
    "anything without front matter", because a draft that has lost its
    delimiters is exactly the file that should fail loudly, not vanish.
    """
    if not directory.is_dir():
        return []
    return [Recipe(p) for p in sorted(directory.rglob("*.md"))
            if not (p.name == "README.md" and p.parent == directory)]


ALL_RECIPES = _load(RECIPES_DIR)
ALL_DRAFTS = _load(DRAFTS_DIR)
ALL_MAGIC_BAG = _load(MAGIC_BAG_DIR)

# ARE THE PRIVATE DRAFTS EVEN HERE? -- GitHub issue #378.
#
# `_food_drafts/` is a separate, private, gitignored repository. A CI checkout
# therefore has the ~82 published recipes and NONE of the ~290 drafts, so
# ALL_DRAFTS is an empty list there and every draft-reading check silently
# examines a fraction of what it does locally.
#
# That is this repository's own worst failure mode wearing a new hat (HANDOVER
# 12): the tests do not fail, they find fewer offenders and report green. The
# green is true of what they scanned and misleading about what they did not.
#
# Exposed as a value rather than left for each test to re-derive from
# `if not ALL_DRAFTS`, so tests/test_suite_hygiene.py can insist every
# draft-reading test makes a deliberate choice about it. See
# test_every_draft_reading_test_says_what_it_does_without_drafts.
DRAFTS_PRESENT = bool(ALL_DRAFTS)

# Written once. A skip reported as bare "skipped" is barely better than a pass.
NO_DRAFTS_REASON = (
    "_food_drafts/ is absent -- it is a separate private repo, so a CI checkout "
    "has none of it. This check reads drafts ONLY, so it has nothing to examine "
    "and says so rather than passing: a pass would claim the drafts were "
    "checked and found clean. Issue #378."
)


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
    if "magic_bag" in metafunc.fixturenames:
        metafunc.parametrize("magic_bag", ALL_MAGIC_BAG,
                             ids=[m.slug for m in ALL_MAGIC_BAG])


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


# =============================================================================
# UN-REWRITTEN `QQ` TEXT IS NOT CHECKED FOR HOUSE STYLE. Issue #426.
# =============================================================================
# Helen: "don't normalise oven temp, the dash, or 'minutes' -- ideally just skip
# the whole line for simple normalisation tasks", of a step like
#
#     - step: "QQ bake at 150C for 30-40 minutes"
#
# `QQ` is her marker for "not rewritten yet" (HANDOVER_v26.md §4/§12): the line
# is still the SOURCE's wording, sitting in the file waiting to be replaced
# wholesale. Correcting its degree sign or its dash is tidying text that is
# about to be deleted, and it does it by editing someone else's words -- which
# is the one thing the marker exists to stop.
#
# THE SAME ARGUMENT IS ALREADY IN THIS MODULE'S DOCSTRING, for
# test_no_oven_conversions, which was left out of this file entirely because it
# "would fire on exactly the unrewritten `QQ`/`PLACEHOLDER` source text those
# markers exist to protect". #426 is that judgement applied at the granularity
# it should always have had: per LINE, not per test. A test can then keep
# guarding every rewritten step in a file that still has un-rewritten ones,
# instead of being dropped wholesale or firing wholesale.
#
# THIS OVERTURNS ONE EARLIER DECISION, explicitly rather than quietly.
# test_temperatures_use_degree_c's docstring argued a degree sign is "pure
# formatting, no information lost either way -- safe to enforce even inside an
# un-rewritten `QQ`/`PLACEHOLDER` step". That is true about the character and
# wrong about the line: the edit is safe, the habit of editing there is not, and
# Helen has now ruled the other way. The 2026-08-11 bug it was seeded from --
# 14 drafts writing "180C" -- is still caught everywhere it matters.
#
# WHAT IT IS WORTH, measured on the drafts present 2026-08-21: 66 of the 67
# house-style violations in the whole drafts folder were inside QQ lines, and 29
# of the 30 failing files failed for no other reason. The one real failure was
# invisible underneath them.
#
# ONLY AT THE START OF THE VALUE, never anywhere in it. A rewritten step that
# happens to mention QQ mid-sentence is finished prose and gets checked like any
# other. The marker is a prefix, and treating it as a substring would let any
# line opt out of house style by mentioning it.
# LIVES IN conftest, NOT IN test_drafts.py, SINCE 2026-08-21 -- and the move is
# what let the draft/recipe rule duplication collapse. These read a `Recipe`,
# and `Recipe` is the same class for both collections, so the natural home is
# beside it.
#
# APPLYING THEM TO A PUBLISHED RECIPE IS A NO-OP, measured before relying on it:
# across every file in `_food_recipes/`, `checkable_raw(r) == r.raw` and
# `checkable_prose(r) == r.prose`, because `test_no_qq_placeholder` forbids the
# marker there at all. That is what makes it safe for ONE shared rule to blank
# QQ lines unconditionally and be correct for both collections -- rather than
# two copies of the rule differing by a call nobody can tell is deliberate.
#
# `QQ Claude` IS THE ONE EXCEPTION AND IT IS NOT AN EXEMPTION FROM THE RULE --
# it is the rule read correctly. The marker means "SOMEBODY ELSE'S wording,
# awaiting a rewrite", which is why correcting its dash is off limits: it edits
# words that are about to be deleted. A `QQ Claude` line is the opposite. It is
# the paraphrase, written here, and HANDOVER §4 says outright that it "IS held
# to normal house style, same as any other prose it writes".
#
# FOUND BY MEASUREMENT ON 2026-09-01, after the interleaved format became the
# default for every draft and the corpus gained ~1,000 of these lines. 15 number
# ranges were sitting in `QQ Claude` prose with hyphens instead of en dashes --
# invisible to test_number_ranges_use_en_dashes, and to `scripts/tidy_drafts.py`,
# which carries its own copy of this pattern for the same reason. Every one was
# in a file paired BEFORE that session, so the hole had been open since the
# format was invented on 2026-08-21 and only showed when the volume grew.
#
# The lookahead is what a reader most needs to see here: the pattern is not
# "starts with QQ", it is "starts with QQ and is not the rewrite".
_QQ_LINE = re.compile(r"""^\s*             # indent
                          (?:-\s*)?        # optional list dash
                          (?:[a-z_]+:\s*)? # optional key, e.g. `step: `
                          (?:['"])?        # optional opening quote
                          QQ\b(?!\s+Claude\b)""", re.X)


def is_qq(value) -> bool:
    """True if this scalar is un-rewritten SOURCE text.

    `QQ Claude` is deliberately False -- see the note on `_QQ_LINE`. It carries
    the marker so Helen can see the pair at a glance, not because it is
    somebody else's words.
    """
    if not isinstance(value, str):
        return False
    stripped = value.lstrip()
    return stripped.startswith("QQ") and not stripped.startswith("QQ Claude")


def checkable_text(raw: str) -> str:
    """One file's raw text with every un-rewritten `QQ` line blanked.

    Blanked rather than dropped so line COUNT is preserved: these strings feed
    failure messages, and a report whose line numbers are off by however many
    QQ lines happened to precede it is worse than no line numbers at all.

    TAKES TEXT, NOT A `Recipe`, since 2026-09-03 (#670). The cocktails
    collection has no `Recipe` object -- tests/test_cocktails.py has its own
    loader and its own schema -- but it has the same `QQ` marker meaning the
    same thing, so the exemption has to be reachable from a plain string.
    `checkable_raw` below is the food-shaped door onto it and is unchanged.
    """
    return "\n".join("" if _QQ_LINE.match(line) else line
                     for line in raw.split("\n"))


def checkable_raw(recipe) -> str:
    """`recipe.raw` with every un-rewritten `QQ` line blanked."""
    return checkable_text(recipe.raw)


def checkable_prose(recipe) -> list[tuple[str, str]]:
    return [(loc, text) for loc, text in recipe.prose if not is_qq(text)]


def _relative(recipe: Recipe) -> str:
    """The file's real path from the repo root.

    REBUILT FROM recipe.path, NOT FROM THE SLUG, since 2026-08-21. These used to
    return f"{collection}/{slug}.md", which was true while both collections were
    flat. `_load` went recursive on 2026-08-20 to pick up Helen's staging
    subfolders, and from that moment a failure in `to-promote/foo.md` reported
    itself as `_food_drafts/foo.md` -- a path with no file at it. You cannot open
    what the message names, and the one place it matters is the moment you are
    trying to fix a red test.
    """
    return recipe.path.resolve().relative_to(ROOT).as_posix()


def where(recipe: Recipe, detail: str = "") -> str:
    """Consistent location prefix for failure messages."""
    return _relative(recipe) + (f" — {detail}" if detail else "")


def where_draft(draft: Recipe, detail: str = "") -> str:
    """Same as where(), for a _food_drafts/ file — the two collections are
    never confused in a failure message even though they share the Recipe
    class.
    """
    return _relative(draft) + (f" — {detail}" if detail else "")


# =============================================================================
# HOUSE STYLE THAT IS NOT ABOUT FOOD — GitHub issue #670
# =============================================================================
# An en dash, an accent, a quoted scalar and a degree sign are properties of
# Helen's WRITING, not of a recipe. `model_instructions/INGEST_ONE_COCKTAIL.md`
# §7 demands every one of them of a drink in the same words the food formatter
# uses — and until 2026-09-03 nothing checked a single one, because
# tests/test_style.py is parametrised over the food `recipe` fixture and this
# module is explicitly the food suite (see the header, L28–32).
#
# So the CORE of each corpus-agnostic rule lives here, taking a string, and the
# per-collection test keeps its own assert, its own message and its own
# parametrisation. Three surfaces already consume these — recipes and drafts
# (tests/test_style.py, tests/test_drafts.py), the prose pages
# (tests/test_prose_pages.py, which imported them from test_style.py by name
# from the day it was written) and now drinks (tests/test_cocktails.py).
#
# WHY NOT MOVE THE TESTS THEMSELVES. A food failure message says "recipe", cites
# a food issue number and names food fields; a drink's cannot. Sharing the
# PREDICATE and not the message is what lets the drink rules exist at all
# without touching a single food test id — `pytest --collect-only` is
# byte-identical across this change on the food half.
#
# WHY NOT LEAVE THEM IN test_style.py AND IMPORT FROM THERE. That is what
# test_prose_pages.py does, and it works; but test_style.py is `pytest.mark.food`
# and a cocktails module importing the food suite to borrow its spelling list
# reads as an accident waiting to be tidied away. A rule that belongs to neither
# collection belongs beside `checkable_text`, which is already exactly that.

# ISO DATES ARE BLANKED BEFORE THE RANGE RULE RUNS, not excluded by a cleverer
# pattern: `2026-08-12` is three number pairs joined by hyphens and matches a
# range perfectly. See test_style.py::test_number_ranges_use_en_dashes.
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER_RANGE = re.compile(r"(?<![\d.])\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?(?![\d.])")

# The two typography rules that are true of any English prose this site
# publishes. The rest of test_style.py's TYPOGRAPHY table is food's own —
# fractions, wikilinks and the reversed-bracket link shape are about a recipe
# page's markdown conventions — so the table there splices these in rather than
# moving wholesale. Order is preserved exactly: reordering it would reorder
# every `test_typography[...]` id.
SHARED_TYPOGRAPHY = [
    ("double hyphen", r"(?<!-)--(?!-)", "use an em dash —"),
    ("ASCII arrow", r"->", "use →"),
]

SPELLINGS = {
    r"\bdemarara\b": "demerara",
    r"\byogurt\b": "yoghurt",
    r"\bcreme fraiche\b": "crème fraîche",
    r"\bgruyere\b": "gruyère",
    r"\bpuree\b": "purée",
    r"\bsaute\b": "sauté",
    r"\bbain marie\b": "bain-marie",
}

DEGREELESS_TEMPERATURE = re.compile(r"\b(\d{2,3})\s*(?:oC|C\b)(?!\w)")


def number_range_hits(text: str) -> list[str]:
    """Every `3-4` written with a hyphen where an en dash belongs."""
    return NUMBER_RANGE.findall(ISO_DATE.sub(" ", text))


def spelling_problems(text: str) -> list[str]:
    """`['demarara -> demerara', ...]` for each non-house spelling present."""
    return [f"{pattern.strip(chr(92) + 'b')} -> {correct}"
            for pattern, correct in SPELLINGS.items()
            if re.search(pattern, text, re.I)]


def degreeless_temperatures(text: str) -> list[str]:
    """Every `200C` / `200oC` written without the degree sign."""
    return DEGREELESS_TEMPERATURE.findall(text)


def unquoted_scalars(fm_text: str, fields) -> list[str]:
    """`['title: Beef Wellington', ...]` for each bare scalar among `fields`.

    Reads the RAW front matter, never the parsed value: a quoted and an
    unquoted scalar parse identically, so the parsed value cannot tell you how
    it was written. A flow sequence or mapping is not a bare scalar and is
    skipped; booleans are never in `fields`, because quoting one turns it into
    the string "true" and every `is True` check in the suite silently reads
    False (test_front_matter.py, and scripts/tidy_drafts.py's header).
    """
    bad = []
    for field in fields:
        match = re.search(rf"^{field}:[ \t]*(.+)$", fm_text, re.M)
        if not match:
            continue
        value = match.group(1).rstrip()
        if value.startswith("[") or value.startswith("{"):
            continue          # a flow sequence/mapping, not a bare scalar
        if not (value.startswith('"') and value.endswith('"')):
            bad.append(f"{field}: {value}")
    return bad


def accented_words() -> dict:
    """The curated unaccented -> accented map, _data/accented_words.yml.

    Lives in `_data/`, not `_data/food/`, because it is HOUSE STYLE rather than
    food vocabulary — `crème de cassis` wants the same treatment `crème fraîche`
    gets. See SHARED_DATA_DIR at the top of this file.
    """
    path = SHARED_DATA_DIR / "accented_words.yml"
    if not path.exists():
        pytest.skip(
            "_data/accented_words.yml is missing. It is the curated list of "
            "culinary words whose correct spelling carries an accent."
        )
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("words") or {}


def accent_problems(fields: list[tuple[str, str]], words: dict) -> list[str]:
    """Every declared unaccented spelling found in `(location, text)` pairs."""
    problems = []
    for location, text in fields:
        for plain, accented in words.items():
            if re.search(rf"\b{re.escape(plain)}\b", text, re.I):
                problems.append(f"{location}: '{plain}' should be '{accented}'")
    return problems
