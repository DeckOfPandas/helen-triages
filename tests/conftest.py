"""Shared fixtures and helpers for the food test suite, and the house-style
predicates the cocktails suite shares.

Run from the repo root:

    pytest -q                               # everything
    pytest -q tests/test_front_matter.py    # one file
    pytest -q -k cavolo                     # everything touching one recipe

A test that takes `recipe`, `draft` or `magic_bag` is parametrised per file,
so its failure names the file it came from.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


# --- the two session builds ---------------------------------------------------
# Defined here, not in a test module: a session fixture imported into a second
# module is a second definition with its own cache, so the site would build
# twice. test_rendered_pages.py reads the HTML and test_browser_smoke.py runs
# it in Chromium (#1200).

BUILD_DIR = ROOT / "tmp" / "_test_site"
PROD_BUILD_DIR = ROOT / "tmp" / "_test_site_prod"


# In CI a missing bundler fails rather than skips: the toolchain is installed
# on purpose there, and a skip would report green for the only tests that
# check built output. GitHub Actions sets CI=true.
def _require_bundler():
    if shutil.which("bundle") is not None:
        return
    if os.environ.get("CI"):
        pytest.fail(
            "No bundler in CI. The Ruby setup step did not take effect, so the "
            "rendered-output tests cannot build the site -- and skipping them "
            "here would report green for the only tests that check what is "
            "actually published."
        )
    pytest.skip("no bundler on this machine; skipping rendered-output tests")


@pytest.fixture(scope="session")
def site() -> Path:
    """Build once per run, into the project's own tmp/ (never /tmp — CLAUDE.md).

    Uses the local config as well as the production one, so drafts build and the
    output matches what Helen actually looks at.
    """
    _require_bundler()

    result = subprocess.run(
        ["bundle", "exec", "jekyll", "build",
         "--config", "_config.yml,_config_local.yml",
         "--destination", str(BUILD_DIR)],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        pytest.fail(
            "jekyll build failed, so nothing below can be trusted:\n"
            + result.stdout[-2000:] + result.stderr[-2000:]
        )
    yield BUILD_DIR
    shutil.rmtree(BUILD_DIR, ignore_errors=True)


@pytest.fixture(scope="session")
def prod_site() -> Path:
    """A second build, with the production config alone -- no _config_local.yml.

    Locally drafts have `output: true`, so every link to one resolves. In
    production `output: false`, and a link to a draft is a 404 that the `site`
    fixture cannot see (#235).
    """
    _require_bundler()

    result = subprocess.run(
        ["bundle", "exec", "jekyll", "build",
         "--config", "_config.yml",
         "--destination", str(PROD_BUILD_DIR)],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        pytest.fail(
            "production jekyll build failed:\n"
            + result.stdout[-2000:] + result.stderr[-2000:]
        )
    yield PROD_BUILD_DIR
    shutil.rmtree(PROD_BUILD_DIR, ignore_errors=True)

# Jekyll only finds a collection at `_<name>` directly under the repo root, so
# the source directories carry the site in their name and cannot nest under
# food/. These are the food collections; tests/test_cocktails.py has its own
# loader and schema.
RECIPES_DIR = ROOT / "_food_recipes"
DRAFTS_DIR = ROOT / "_food_drafts"

# The magic bag is a third collection with its own fixture, not a widening of
# `recipe`: an entry has no method, no source and no method_short, all of which
# a recipe must have. Its spec is tests/test_magic_bag.py.
# The fixture file is parametrised alongside the real entries, so the schema is
# exercised while the collection is empty (#1201). It lives under tests/, which
# Jekyll excludes, and is not in ALL_MAGIC_BAG: the cross-collection sweeps
# read real dishes only. An empty magic bag is not a defect, so nothing asserts
# it is non-empty; `_report_empty_magic_bag` says so at the end of the run.
MAGIC_BAG_DIR = ROOT / "_food_magic_bag"
MAGIC_BAG_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "magic_bag" / "zzz-fixture-dish.md"

# Food's own vocabulary: taxonomy, filter sections, pantry, ingredient words.
DATA_DIR = ROOT / "_data" / "food"

# Shared across the mono-repo: accented_words.yml is house style, not food
# vocabulary, and applies to a drink as it does to a recipe.
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
        # The magic bag's flat `ingredients:` list. A recipe carries
        # `ingredient_groups` and no `ingredients`, so this is a no-op there,
        # and the ingredient-vocabulary rules reach the magic bag unchanged.
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
        # Magic-bag ingredient notes; a no-op on a recipe, as in
        # `ingredient_items`.
        for item in self.fm.get("ingredients") or []:
            if isinstance(item, dict) and item.get("note"):
                out.append((f"note on '{item.get('item')}'", item["note"]))
        return out


def _load(directory: Path) -> list[Recipe]:
    """Every .md at or below `directory`, recursively.

    Recursive because `_food_drafts/` holds staging subfolders (PIPELINE.md
    §3): a flat glob stops reading the staged drafts and reports green.
    `sorted()` over `rglob` orders by full path; ids still come from the stem.

    A `README.md` at the root is the only name skipped, and by exact name: a
    draft that has lost its front matter delimiters must fail loudly, not
    vanish.
    """
    if not directory.is_dir():
        return []
    return [Recipe(p) for p in sorted(directory.rglob("*.md"))
            if not (p.name == "README.md" and p.parent == directory)]


ALL_RECIPES = _load(RECIPES_DIR)
ALL_DRAFTS = _load(DRAFTS_DIR)
ALL_MAGIC_BAG = _load(MAGIC_BAG_DIR)
# Raises at import if the file is gone, which is the point: the fixture is what
# stands between this spec and testing nothing.
MAGIC_BAG_FIXTURE = Recipe(MAGIC_BAG_FIXTURE_PATH)

# Are the private drafts here? (#378) `_food_drafts/` is a separate, private,
# gitignored repository, so a CI checkout has the published recipes and none of
# the drafts: ALL_DRAFTS is empty there, and a draft-reading check finds fewer
# offenders and reports green.
# Exposed as a value so tests/test_suite_hygiene.py can insist every
# draft-reading test makes a deliberate choice about it
# (test_every_draft_reading_test_says_what_it_does_without_drafts).
DRAFTS_PRESENT = bool(ALL_DRAFTS)

# Written once. A skip reported as bare "skipped" is barely better than a pass.
NO_DRAFTS_REASON = (
    "_food_drafts/ is absent -- it is a separate private repo, so a CI checkout "
    "has none of it. This check reads drafts ONLY, so it has nothing to examine "
    "and says so rather than passing: a pass would claim the drafts were "
    "checked and found clean. Issue #378."
)


def pytest_generate_tests(metafunc):
    """Parametrise any test that asks for `recipe`, `draft` or `magic_bag`.

    `recipe` and `draft` are separate fixtures over separate lists
    (ALL_RECIPES, ALL_DRAFTS), so a recipe-only rule is never silently
    enforced against a draft, or the reverse.
    """
    if "recipe" in metafunc.fixturenames:
        metafunc.parametrize("recipe", ALL_RECIPES, ids=[r.slug for r in ALL_RECIPES])
    if "draft" in metafunc.fixturenames:
        if not ALL_DRAFTS:
            UNCREATED.append(metafunc.definition.name)
        metafunc.parametrize("draft", ALL_DRAFTS, ids=[d.slug for d in ALL_DRAFTS])
    if "magic_bag" in metafunc.fixturenames:
        # The fixture first, then every real entry -- so this is never an empty
        # list. See MAGIC_BAG_FIXTURE_PATH above (#1201).
        metafunc.parametrize(
            "magic_bag", [MAGIC_BAG_FIXTURE] + ALL_MAGIC_BAG,
            ids=["fixture:" + MAGIC_BAG_FIXTURE.slug]
                + [m.slug for m in ALL_MAGIC_BAG])


# --- what this run never looked at --------------------------------------------
# Reports, never fails: nothing here can turn a run red (DECISIONS §11).
# When the drafts are absent, the per-file cases of a `draft`-parametrised test
# are never created, so the run is quieter, not noisier, and no single test can
# show how much went unopened. `UNCREATED` names those tests at collection
# time. It covers food's `draft` fixture only: the cocktails suite has its own
# loader and skips with a reason, which is already visible.
COCKTAIL_DRAFTS_DIR = ROOT / "_cocktail_drafts"

UNCREATED: list[str] = []

_CLONE = {
    "_food_drafts": "sh scripts/git-clone-agent.sh helen-triages-food-private _food_drafts",
    "_cocktail_drafts": "sh scripts/git-clone-agent.sh helen-triages-cocktails-private _cocktail_drafts",
}


def _absent_drafts() -> list[str]:
    return [d.name for d in (DRAFTS_DIR, COCKTAIL_DRAFTS_DIR) if not d.is_dir()]


def pytest_report_header(config):
    """One line at the top, so the caveat is present before the dots start."""
    absent = _absent_drafts()
    if not absent:
        return None
    return f"drafts: {', '.join(absent)} absent -- this run is not evidence about them"


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """The same fact at the END, which is where a green run is actually read.

    A header scrolls away behind several thousand dots. This does not.
    """
    try:
        _report_absent_drafts(terminalreporter.write_line)
    except Exception:
        pass            # a report that breaks a run would be worse than none
    try:
        _report_browser_skips(terminalreporter.write_line,
                              terminalreporter.stats.get("skipped", []))
    except Exception:
        pass
    try:
        _report_empty_magic_bag(terminalreporter.write_line)
    except Exception:
        pass


# Said at the end when the magic bag is empty (#1201): the schema tests ran
# against the fixture, which is not evidence about a real dish. Reports, never
# fails; silent once the collection has an entry.
def _report_empty_magic_bag(write, entries=None):
    entries = ALL_MAGIC_BAG if entries is None else entries
    if entries:
        return
    write("")
    write("Not evidence about the magic bag:", bold=True)
    write("  _food_magic_bag/ has no entries, so tests/test_magic_bag.py ran "
          "against its fixture only")
    write(f"  ({MAGIC_BAG_FIXTURE_PATH.relative_to(ROOT).as_posix()}). The "
          "schema is tested; no real dish is.")


def _report_absent_drafts(write):
    absent = _absent_drafts()
    if not absent:
        return
    write("")
    write("Not evidence about the drafts:", bold=True)
    for name in absent:
        write(f"  {name} is absent -- {_CLONE[name]}")
    if UNCREATED:
        n = len(UNCREATED)
        write(f"  {n} per-draft check{'s' if n != 1 else ''} in this suite "
              f"produced no tests at all, rather than failing or skipping.")
    write("  Cloning is reading: it needs no ask, and both clones make the "
          "suite whole.")


# The browser smoke test skips whenever Chromium cannot launch (#1200). A skip
# on every run is a test that never runs, so the run says so at the end, with
# the probe's own reason. Computed from this run's skip reports, not from state
# the test module sets, so it cannot claim a skip that did not happen.
BROWSER_SMOKE = "test_browser_smoke.py"


def _report_browser_skips(write, skipped):
    reasons = []
    for rep in skipped:
        if BROWSER_SMOKE not in getattr(rep, "nodeid", ""):
            continue
        longrepr = getattr(rep, "longrepr", None)
        reason = longrepr[2] if isinstance(longrepr, tuple) else str(longrepr)
        reasons.append(reason.removeprefix("Skipped: "))
    if not reasons:
        return
    n = len(reasons)
    write("")
    write("Not evidence about a real browser:", bold=True)
    write(f"  {n} browser smoke test{'s' if n != 1 else ''} skipped -- "
          f"{sorted(set(reasons))[0]}")
    write("  Locally: sh scripts/browser/install.sh. CI installs no browser "
          "until the workflow does (#1200).")


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


# --- un-rewritten `QQ` text is not checked for house style (#426) --------------
# A `QQ` line is still the source's wording, waiting to be replaced whole;
# correcting its dash edits someone else's words (MANUAL §5).
# Only at the start of the value: treating the marker as a substring would let
# any line opt out of house style by mentioning it.
# `QQ Claude` is not exempt: that line is the paraphrase written here and is
# held to house style, hence the lookahead. `QQ_LINE` in scripts/tidy_drafts.py
# mirrors this pattern; keep the two in step.
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

    Blanked rather than dropped so the line count is preserved: these strings
    feed failure messages that cite line numbers. Takes text, not a `Recipe`,
    because tests/test_cocktails.py has its own loader and the same marker
    (#670).
    """
    return "\n".join("" if _QQ_LINE.match(line) else line
                     for line in raw.split("\n"))


def checkable_raw(recipe) -> str:
    """`recipe.raw` with every un-rewritten `QQ` line blanked.

    A no-op on a published recipe, where `test_no_qq_placeholder` forbids the
    marker, so one shared rule is correct for both collections.
    """
    return checkable_text(recipe.raw)


def checkable_prose(recipe) -> list[tuple[str, str]]:
    return [(loc, text) for loc, text in recipe.prose if not is_qq(text)]


def _relative(recipe: Recipe) -> str:
    """The file's real path from the repo root.

    Built from `recipe.path`, not from the slug: `_load` is recursive, so a
    staged draft sits in a subfolder and a slug-built path names no file.
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


# --- house style that is not about food (#670) ---------------------------------
# An en dash, an accent, a quoted scalar and a degree sign are properties of
# the writing, not of a recipe. The core of each corpus-agnostic rule lives
# here and takes a string; each collection's test keeps its own assert, message
# and parametrisation, so sharing a predicate changes no test id.

# ISO dates are blanked before the range rule runs: `2026-08-12` is three
# number pairs joined by hyphens and matches a range.
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER_RANGE = re.compile(r"(?<![\d.])\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?(?![\d.])")

# The two typography rules true of any prose this site publishes; the rest of
# test_style.py's TYPOGRAPHY table is food's own. That table splices these in,
# in order: reordering would reorder every `test_typography[...]` id.
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


# --- notes are sentences (#711) -----------------------------------------------
# A note starts with a capital and ends with a full stop. Leading punctuation
# is skipped before the capital is looked for: a quoted term opening a sentence
# is not a missing capital, and `'00' flour` cannot carry a case, so a digit
# satisfies it. A `QQ` note is a placeholder, not prose, and is never checked.
# An ellipsis is deliberate: see NOTE_EXCEPTIONS in tests/test_style.py.
_NOTE_LEADING = "\"'“‘‘’([`*"


def note_is_a_sentence(text: str) -> bool:
    """A note starts with a capital (or a digit) and ends with . ! or ?"""
    s = (text or "").strip()
    if not s:
        return True
    if not s.endswith((".", "!", "?")):
        return False
    head = s.lstrip(_NOTE_LEADING)
    if not head:
        return False
    first = head[0]
    return first.isdigit() or not first.isalpha() or first.isupper()


def note_problems(text: str) -> list[str]:
    """Which of the two clauses a note fails, for the assertion message."""
    s = (text or "").strip()
    if not s:
        return []
    out = []
    head = s.lstrip(_NOTE_LEADING)
    if head and head[0].isalpha() and not head[0].isupper():
        out.append("no capital")
    if not s.endswith((".", "!", "?")):
        out.append("no full stop")
    return out


def notes_of(fm: dict) -> list[tuple[str, str]]:
    """(where, text) for every human-written note on a recipe or a drink.

    A note is a string or a `{label, text}` mapping; both reach this as plain
    text. Method-step notes are not here: they have their own test, and
    folding them in would make one failure report two unrelated fields.
    """
    out = []
    for note in fm.get("notes") or []:
        if isinstance(note, dict):
            if is_qq(note.get("label")) or is_qq(note.get("text")):
                continue
            out.append(("notes", str(note.get("text") or "")))
        else:
            if is_qq(note):
                continue
            out.append(("notes", str(note)))
    for item in fm.get("ingredients") or []:
        if isinstance(item, dict) and item.get("note") and not is_qq(item["note"]):
            out.append((f"ingredient {item.get('generic') or item.get('item') or '?'}",
                        str(item["note"])))
    return out


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
