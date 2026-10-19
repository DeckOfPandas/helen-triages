"""Assertions about BUILT HTML, not about the data behind it.

Every other test reads YAML, front matter or SCSS source, and a fault in what
Liquid emits from correct data passes all of them. The builds are slow, so they
are session fixtures in conftest.py, and the tests skip rather than fail where
bundler is not installed.
"""
from __future__ import annotations

import contextlib
import decimal
import html as html_module
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess

import pytest
import yaml

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parent.parent

# `site` and `prod_site` live in conftest.py: a session fixture imported into
# a second module is a second definition with its own cache, and
# tests/test_browser_smoke.py reads the same production build (#1200).
from conftest import _require_bundler  # noqa: E402  (used by built_with_fixtures)
from conftest import _absent_drafts  # noqa: E402  (the notes floor, below)


# --- building with throwaway fixtures ----------------------------------------
# Tests that need a recipe the suite forbids in the real collection (a missing
# gate flag, `proofread: false` on a promoted file) write it into a COPY of the
# source tree, never into `_food_recipes/` or `_cocktail_recipes/`: the session
# builds read those directories, and so does a concurrent pytest (#1153).
# The copy carries whatever drafts collections the machine has; `.git`, the
# caches and the tooling directories are left out.
_COPY_IGNORE = shutil.ignore_patterns(
    ".git", "tmp", "_site", "node_modules", ".claude", "__pycache__",
    ".pytest_cache", ".jekyll-cache")


@contextlib.contextmanager
def built_with_fixtures(name, files, local=False):
    """Build the site from a copy of the tree, plus `files`.

    `files` maps a repo-relative path to its text. Yields the output directory;
    removes the copy and the output afterwards whatever happens.

    Production config alone unless `local=True`, which adds `_config_local.yml`
    for a question only the local build can answer: the production gate removes
    a held-back dish before the index renders (#1201).
    """
    _require_bundler()
    src = ROOT / "tmp" / f"_fixture_src_{name}"
    out = ROOT / "tmp" / f"_fixture_out_{name}"
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    try:
        shutil.copytree(ROOT, src, ignore=_COPY_IGNORE, symlinks=True)
        for relpath, text in files.items():
            target = src / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

        configs = [src / "_config.yml"]
        if local:
            configs.append(src / "_config_local.yml")
        result = subprocess.run(
            ["bundle", "exec", "jekyll", "build",
             "--source", str(src),
             "--config", ",".join(str(c) for c in configs),
             "--destination", str(out)],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        assert result.returncode == 0, (
            "jekyll build failed, so nothing this test asserts can be "
            "trusted:\n" + result.stdout[-2000:] + result.stderr[-2000:]
        )
        yield out
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(out, ignore_errors=True)


# One fixture build shared by every test that needs one (#1271). Safe only
# because each test asserts on its own `zzz-` pages by name: a test that counts
# pages, or needs the build without another test's fixtures, calls
# `built_with_fixtures` directly. Files are declared at import, beside the test
# that reads them, because the build needs all of them before the first test.
_FIXTURE_FILES = {}


def _in_the_fixture_build(files):
    """Add `files` (repo-relative path -> text) to the shared fixture build."""
    clash = sorted(set(files) & set(_FIXTURE_FILES))
    assert not clash, (
        f"Two tests put a fixture at the same path: {', '.join(clash)}. One "
        "would overwrite the other in the shared build and its test would be "
        "reading the wrong file. Give each its own `zzz-` slug."
    )
    _FIXTURE_FILES.update(files)
    return files


@pytest.fixture(scope="module")
def fixture_site():
    with built_with_fixtures("shared", _FIXTURE_FILES) as out:
        yield out


def test_no_link_in_the_production_build_points_at_a_file_that_isnt_there(prod_site):
    """Every internal link in the built PRODUCTION site resolves (#235).

    tests/test_page_links.py reads templates and trusts a link built from
    `recipe.url`, which Jekyll computes even for a document it never writes.
    A .pdf link is skipped: scripts/generate_pdfs.py writes those after Jekyll;
    test_pdf_link_points_where_the_pdfs_are_written owns that pair.
    """
    baseurl = "/helen-triages"
    problems = []
    checked = 0

    for html_file in sorted(prod_site.rglob("*.html")):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        page_url = "/" + str(html_file.relative_to(prod_site).parent).replace("\\", "/").strip(".") + "/"
        for href in re.findall(r'<a\b[^>]*?\bhref="([^"]+)"', text, re.I):
            href = href.strip()
            if (href.startswith("#") or href.endswith(".pdf")
                    or re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)", href)):
                continue
            path = href.split("#")[0].split("?")[0]
            if not path:
                continue
            if not path.startswith("/"):
                path = str(pathlib.PurePosixPath(page_url).joinpath(path))
            if path.startswith(baseurl):
                path = path[len(baseurl):]
            path = str(pathlib.PurePosixPath(path))          # normalise ../
            checked += 1
            target = prod_site / path.lstrip("/")
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                problems.append(
                    f"{html_file.relative_to(prod_site)}: href=\"{href}\" -> "
                    f"{path} does not exist in the production build"
                )

    assert checked, (
        "No internal links found anywhere in the production build. Either the "
        "site has no links, or the scan has stopped matching -- and a scan "
        "that finds nothing passes."
    )
    assert not problems, (
        f"{len(problems)} link(s) 404 in the PRODUCTION build (they may work "
        f"locally, which is the whole point of this test):\n  "
        + "\n  ".join(sorted(set(problems))[:20])
    )


def page(site: pathlib.Path, url: str) -> str:
    path = site / url.strip("/") / "index.html"
    assert path.exists(), f"{url} did not build"
    return path.read_text(encoding="utf-8")


def temps() -> dict:
    return yaml.safe_load(
        (ROOT / "_data" / "food" / "internal_temperatures.yml").read_text(encoding="utf-8"))


def chart_of(html: str) -> str:
    """Just the doneness section of a recipe page."""
    assert 'id="doneness"' in html, "this recipe rendered no doneness chart"
    return html[html.index('id="doneness"'):]


def rows(fragment: str) -> list[tuple[str, str]]:
    """(label, value) for each chart row, in order."""
    labels = [re.sub(r"<[^>]+>", "", l).strip()
              for l in re.findall(r'class="tc-row-label">(.*?)</div>', fragment, re.S)]
    values = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", v)).strip()
              for v in re.findall(r'class="tc-value"[^>]*>(.*?)</div>', fragment, re.S)]
    return list(zip(labels, values))


# --- the leak ----------------------------------------------------------------

def test_only_tough_cuts_are_labelled_tender_at(site):
    """`{% assign %}` in an include writes to the including PAGE's scope, so a
    `prefix` set on one row is still set on the next. Only the tough cuts and
    the All summary may say "tender at".
    """
    html = page(site, "/food/reference/internal-temperatures/")
    labelled = [(l, v) for l, v in rows(html) if v.startswith("tender at")]
    assert len(labelled) == 5, (
        f"expected exactly 5 rows to say 'tender at' (beef's tough cuts, pork's, "
        f"lamb's and venison's slow-cooked, and the All summary), found "
        f"{len(labelled)}: {labelled}"
    )


# --- the safety zone ---------------------------------------------------------

def test_the_safety_zone_renders_where_the_data_says(site):
    """The shaded zone is present, at the node's `safety_min` rather than a
    number written into the markup."""
    data = temps()
    for url, node in (
        ("/food/recipes/teriyaki-salmon/", data["fish"]["salmon"]),
        ("/food/reference/internal-temperatures/", data["pork"]["roasting"]),
    ):
        html = page(site, url)
        fragment = chart_of(html) if "recipes" in url else html
        found = re.findall(r'class="tc-unsafe" style="--t:(\d+);', fragment)
        assert str(node["safety_min"]) in found, (
            f"{url}: expected a shaded zone at {node['safety_min']}°C, found {found or 'none'}"
        )


def test_a_protein_with_no_threshold_shades_nothing(site):
    """The inverse, and it matters as much: UK guidance treats pink beef as fine,
    so a beef page implying otherwise would be its own kind of wrong."""
    fragment = chart_of(page(site, "/food/recipes/roast-beef-fillet/"))
    assert "tc-unsafe" not in fragment, "beef has no safety threshold and must not shade"


# --- the chart says what the data says ---------------------------------------

def test_a_recipe_chart_draws_every_level_once(site):
    data = temps()
    fragment = chart_of(page(site, "/food/recipes/roast-beef-fillet/"))
    drawn = rows(fragment)
    levels = data["beef"]["tender_roast"]["doneness"]
    assert len(drawn) == len(levels), f"{len(levels)} levels in the data, {len(drawn)} drawn"
    for (_, value), spec in zip(drawn, levels.values()):
        assert spec["out_at"] in value, f"row {value!r} doesn't show its own out-at figure"


def test_exactly_one_level_is_marked_as_the_recipes_own(site):
    """`doneness:` in front matter decides which row is marked. A typo resolves
    to nothing and the chart recommends nothing, silently — which is why
    test_doneness_names_a_real_level exists, and this is the other half of it."""
    fragment = chart_of(page(site, "/food/recipes/roast-beef-fillet/"))
    marked = re.findall(r'class="tc-row tc-row--suggested"', fragment)
    assert len(marked) == 1, f"expected 1 suggested row, found {len(marked)}"
    assert "this recipe" in fragment


# --- placement ---------------------------------------------------------------

def test_the_chart_sits_below_notes_and_out_of_the_metadata(site):
    """The chart sits below Notes, is linked to, and is not a cell in the
    metadata grid."""
    html = page(site, "/food/recipes/roast-beef-fillet/")
    assert "<strong>Internal temp</strong>" not in html, "the meta cell is back"
    assert html.index('id="doneness"') > html.index("recipe-section-notes"), \
        "the chart has drifted above Notes"
    assert 'href="#doneness"' in html, "nothing links to the chart"


# --- notes, and the two ways a note renders as nothing -----------------------
# `site`, not `prod_site`: a placeholder note (`{label: "", text: ""}`) exists
# only on a draft page, which only the local build renders. An empty note box
# is valid HTML, so nothing but these tests reports one.

HASH_DUMP = re.compile(r'\{(?:&quot;|")(?:label|text)(?:&quot;|")=(?:&gt;|>)')
NOTE_BLOCK = re.compile(
    r'<(p|div) class="note">\s*<span class="note-label">(.*?)</span>(.*?)</\1>',
    re.S)
NOTES_HEADING = re.compile(r"cocktail-section-heading--notes|recipe-section-notes")

# A floor, not the figure: Helen writes notes most days.
NOTES_FLOOR = 350

# The floor where the drafts are not cloned (CI, a fresh worktree): only
# published notes render there (#378). Set well below the published figure,
# because a recipe leaves the build when an agent edits it and takes its notes
# with it.
NOTES_FLOOR_PUBLISHED = 100


def _pages_with_notes(site):
    for path in sorted(site.rglob("index.html")):
        html = path.read_text(encoding="utf-8")
        if NOTES_HEADING.search(html) or 'class="note-label"' in html:
            yield path, html


def test_no_page_renders_a_note_as_a_ruby_hash(site):
    """A note's mapping never reaches the page as a Ruby hash.

    Not the pin for an empty placeholder note: markdown swallows that mapping,
    and `test_no_page_renders_an_empty_note_box` catches it. This catches a
    note rendered where markdown does not run, such as an attribute.
    """
    dumps = [str(p.relative_to(site)) for p, html in _pages_with_notes(site)
             if HASH_DUMP.search(html)]
    assert not dumps, (
        f"{len(dumps)} page(s) print a note's MAPPING instead of its text, "
        f"first five: {dumps[:5]}. A layout is testing `note.text` for truth to "
        f"decide whether the note is a pair or a bare string; an empty `text:` "
        f"is a placeholder, not a bare string. Test the KEYS -- "
        f"`note.label == nil and note.text == nil` -- as both layouts do."
    )


def test_no_page_renders_an_empty_note_box(site):
    """A note with nothing in it is a label floating in the grid with no text
    beside it. It reads as a bug on the page and as nothing at all to the build.
    """
    empty = []
    for path, html in _pages_with_notes(site):
        for _tag, label, body in NOTE_BLOCK.findall(html):
            if not re.sub(r"<[^>]+>", "", body).strip():
                empty.append(f"{path.relative_to(site)} ({label!r})")
    assert not empty, (
        f"{len(empty)} empty note box(es), first five: {empty[:5]}. Both "
        f"layouts skip a note whose text is empty; something has rendered one."
    )


def test_no_page_prints_a_notes_heading_with_no_note_under_it(site):
    """A NOTES heading needs a note under it. `notes: []` is truthy in Liquid,
    and a list of placeholders is not empty, so the layouts count the notes
    that will actually render before printing the heading.
    """
    stray = []
    for path, html in _pages_with_notes(site):
        if NOTES_HEADING.search(html) and not NOTE_BLOCK.search(html):
            stray.append(str(path.relative_to(site)))
    assert not stray, (
        f"{len(stray)} page(s) print a NOTES heading with no note to "
        f"introduce, first five: {stray[:5]}."
    )


def test_the_three_note_tests_above_are_looking_at_notes(site):
    """The three tests above pass by finding nothing, so this pins that the
    build has notes and that NOTE_BLOCK matches the markup.

    Two floors, by whether the drafts are cloned: without them only published
    notes render.
    """
    absent = _absent_drafts()
    floor = NOTES_FLOOR_PUBLISHED if absent else NOTES_FLOOR
    rendered = sum(len(NOTE_BLOCK.findall(html))
                   for _p, html in _pages_with_notes(site))
    assert rendered >= floor, (
        f"only {rendered} notes render across the local build, below the floor "
        f"of {floor} ("
        + (f"published pages only: {', '.join(absent)} not cloned"
           if absent else "drafts included, measured on 2026-10-01")
        + "). Either the build is missing pages it should have -- in which "
        "case the three tests above assert nothing -- or `NOTE_BLOCK` no "
        "longer matches the markup the layouts emit, which is the same thing."
    )


# --- the class that isn't there ----------------------------------------------

def test_every_class_we_emit_has_a_rule_in_the_stylesheet(site):
    """A class in the markup with no rule behind it renders nothing and errors
    nowhere: Liquid, Sass and the build all accept it.

    Scoped to the prefixes this project owns; `site-` is the chrome that
    _layouts/default.html emits (#227). Modifiers are checked as written,
    against the COMPILED css, where Sass's `&--suggested` is a real selector.
    """
    OURS = ("tc-", "ct-", "doneness", "site-")
    sources = (list(pathlib.Path("_includes").rglob("*.html"))
               + list(pathlib.Path("_layouts").rglob("*.html"))
               + list(pathlib.Path("food").rglob("*.html"))
               + list(pathlib.Path("assets/js").rglob("*.js")))

    emitted: dict[str, list[str]] = {}
    for path in sources:
        text = path.read_text(encoding="utf-8")
        # class="a b" in markup, and class='a b' inside JS template strings.
        for attr in re.findall(r"""class=['"]([^'"{}]+)['"]""", text):
            for name in attr.split():
                if name.startswith(OURS):
                    emitted.setdefault(name, []).append(str(path))

    css = (site / "assets" / "css" / "food.css").read_text(encoding="utf-8")
    orphans = [f"{name} — emitted by {sorted(set(where))[0]}"
               for name, where in sorted(emitted.items())
               if f".{name}" not in css]

    assert not orphans, (
        "these classes are written into markup but styled nowhere, so they "
        "render as unstyled elements:\n  " + "\n  ".join(orphans)
    )


def test_every_icon_partial_class_has_a_styled_base(site):
    """Classes inside `_includes/**/*.svg` resolve to a styled BASE (#396).

    The test above reads `*.html` and `*.js` only. Most modifiers in the icon
    partials are unstyled hooks beside a styled base (MANUAL §11.3), so only
    the base is required, in either stylesheet.

    Blind spot: a typo in the MODIFIER half passes, including in a modifier
    that does carry a rule (`.glass-icon--tiki-mug`).
    """
    partials = sorted(pathlib.Path("_includes").rglob("*.svg"))
    assert partials, (
        "No .svg partials found under _includes/ — this check would pass while "
        "examining nothing, which is the failure mode it was written to fix. "
        "If the icons genuinely moved, point this at their new home."
    )

    css = ""
    for sheet in ("food.css", "cocktails.css"):
        path = site / "assets" / "css" / sheet
        assert path.exists(), f"{sheet} was not built — cannot judge coverage."
        css += path.read_text(encoding="utf-8")

    emitted: dict[str, list[str]] = {}
    for path in partials:
        for attr in re.findall(r"""class=['"]([^'"{}]+)['"]""",
                               path.read_text(encoding="utf-8")):
            for name in attr.split():
                emitted.setdefault(name, []).append(str(path))

    assert emitted, (
        "No classes found in any icon partial. Either they stopped using "
        "classes — in which case delete this test rather than let it pass "
        "silently — or the attribute pattern has stopped matching."
    )

    orphans = []
    for name, where in sorted(emitted.items()):
        base = name.split("--", 1)[0]
        if f".{base}" not in css:
            orphans.append(f"{name} (base .{base}) — in {sorted(set(where))[0]}")

    assert not orphans, (
        "Icon classes whose base has no rule in either stylesheet, so they "
        "render as unstyled shapes:\n  " + "\n  ".join(orphans)
        + "\n\nA BEM modifier with a styled base is fine — an unused hook, "
          "MANUAL 11.3. A base with no rule at all is a typo or a deletion "
          "that took the rule and left the markup."
    )


def test_every_chart_row_draws_its_filled_bar(site):
    """Every chart row draws the filled bar that carries its figure; the tests
    above assert on the label, value and zone around it, never on the mark."""
    for url in ("/food/reference/internal-temperatures/", "/food/recipes/roast-beef-fillet/"):
        html = page(site, url)
        fragment = chart_of(html) if "recipes" in url else html
        row_count = len(re.findall(r'class="tc-row[ "]', fragment))
        bars = len(re.findall(r'class="tc-out-at"', fragment))
        assert row_count and bars == row_count, (
            f"{url}: {row_count} chart rows but {bars} filled bars — "
            f"every row must draw the figure it is about"
        )


# --- every text control has a piece of state behind it (#274) ----------------
# tests/js/filter-state.test.js proves the clear-all predicate handles every
# field FIELD_SPEC declares; it cannot prove FIELD_SPEC declares every control
# the page holds. So the ids are read from the BUILT index, and an input this
# map does not name is a failure.
CONTROL_STATE_FIELDS = {
    "ingredient-search-box": "isSearching",
    "name-search-box": "nameQuery",
    "exclude-search-box": "isExcludeSearching",
}


def test_every_text_input_on_the_index_has_state_behind_it(site):
    html = (site / "food" / "index.html").read_text(encoding="utf-8")
    ids = set(re.findall(r'<input[^>]*type="text"[^>]*id="([^"]+)"', html))
    assert ids, (
        "no text inputs found on the built index page. Either the page lost its "
        "search boxes or this regex stopped matching -- either way the check "
        "below is now vacuous, which is exactly the trap it exists inside."
    )

    unknown = sorted(ids - set(CONTROL_STATE_FIELDS))
    assert not unknown, (
        f"the index page has text input(s) {unknown} that this test has never "
        f"been told about. Every box a user can type into needs a field in "
        f"FIELD_SPEC (assets/js/filter-state.js), or clear-all cannot see it and "
        f"will not offer itself while the box holds a half-finished search -- "
        f"GitHub issues #52, #274. Add the field, then name it here. Do not "
        f"delete the id from this list to make the failure go away."
    )

    spec = (ROOT / "assets" / "js" / "filter-state.js").read_text(encoding="utf-8")
    declared = set(re.findall(r"^\s{4}(\w+):\s*\{\s*empty:", spec, re.M))
    wiring = (ROOT / "assets" / "js" / "filters.js").read_text(encoding="utf-8")

    for box_id in sorted(ids):
        field = CONTROL_STATE_FIELDS[box_id]
        assert field in declared, (
            f"#{box_id} is mapped to the state field '{field}', which "
            f"FIELD_SPEC does not declare."
        )
        # Declared but never assigned is the same bug wearing a disguise: the
        # field exists, the sweep covers it, and nothing ever sets it.
        assert re.search(rf"state\.{re.escape(field)}\s*=", wiring), (
            f"nothing in filters.js ever assigns state.{field}, so typing in "
            f"#{box_id} leaves the state untouched and clear-all stays hidden."
        )


def test_the_awaiting_fix_gate_fires_in_the_production_build(prod_site):
    """Held-back recipes are absent from the production build; cleared are present.

    The only test that the gate does anything, against a real production build
    (#331, #667). The split asks the gate's own question: `awaiting_fix: false`
    AND `proofread: true`. Both directions, because a plugin that dropped every
    document would satisfy the held-back half.
    """
    import yaml as _yaml
    import re as _re

    held, clear = [], []
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        fm = _re.match(r"\A---\n(.*?)\n---", raw, _re.S)
        meta = (_yaml.safe_load(fm.group(1)) or {}).get("meta", {}) or {}
        passes = meta.get("awaiting_fix") is False and meta.get("proofread") is True
        (clear if passes else held).append(path.stem)

    assert clear, (
        "No publishable recipes at all -- this test would pass while checking "
        "nothing, which is what tests/test_suite_hygiene.py exists to prevent."
    )

    published = [s for s in held if (prod_site / "food" / "recipes" / s / "index.html").exists()]
    assert not published, (
        "Recipe(s) the gate should hold back were PUBLISHED anyway:\n  "
        + "\n  ".join(published)
        + "\n\nThe gate has failed open. Check _plugins/publish_gate.rb "
          "still reads `awaiting_fix` AND `proofread`, that _config.yml sets "
          "`show_awaiting_fix: false`, and that the build is not running in "
          "Jekyll's safe mode, which ignores _plugins/ without warning."
    )

    vanished = [s for s in clear if not (prod_site / "food" / "recipes" / s / "index.html").exists()]
    assert not vanished, (
        "Cleared recipe(s) missing from the production build:\n  "
        + "\n  ".join(vanished)
        + "\n\nThe gate is over-firing, or something else is dropping documents."
    )


# `proofread: true` on these fixtures so that the awaiting_fix leg is the only
# one that can fail: `proofread: false` would hold the page back whatever the
# plugin did with the key under test (#667).
FAIL_CLOSED_FIXTURE = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'source: "test"\nmain_ingredients: ["salt"]\nstar_ingredient: "salt"\n'
    'tags: []\ningredient_groups:\n  - items:\n    - item: salt\n'
    'method:\n  - "Nothing."\nmethod_short:\n  - ""\nmeta:\n  rewritten: true\n'
    '  proofread: true\n{flag}  cooked_before: false\n'
    '---\n')
FAIL_CLOSED_CASES = {
    "zzz-gate-no-flag": "",                             # field absent entirely
    "zzz-gate-old-key": "  awaiting-fix: false\n",      # only the old spelling
}
_in_the_fixture_build({
    f"_food_recipes/{slug}.md": FAIL_CLOSED_FIXTURE.format(t=slug, flag=flag)
    for slug, flag in FAIL_CLOSED_CASES.items()})


def test_the_gate_fails_closed_on_a_missing_or_misspelled_flag(fixture_site):
    """A recipe with no `awaiting_fix`, or only the old `awaiting-fix`, does not
    publish: the gate publishes only on an explicit `false` (#331).

    Fixtures, because tests/test_front_matter.py forbids both states in the real
    collection. The control recipe must be present in the same output, or a
    failed build or a gate that hid everything would pass.
    """
    out = fixture_site
    published = [s for s in FAIL_CLOSED_CASES
                 if (out / "food" / "recipes" / s / "index.html").exists()]
    assert not published, (
        "The gate FAILED OPEN for:\n  " + "\n  ".join(published)
        + "\n\n_plugins/publish_gate.rb must publish only on an "
          "explicit `awaiting_fix: false`. A missing key and the old "
          "hyphenated key must both hold the page back."
    )
    assert (out / "food" / "recipes" / "caramel" / "index.html").exists(), (
        "The control recipe is missing too, so this build proves nothing "
        "about the gate -- it either failed or is hiding everything."
    )


# --- the second leg of the gate: `proofread` (#667) --------------------------
# Both states are written, because a single held-back fixture is satisfied by
# a plugin that drops every document.

FOOD_GATE_FIXTURE = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'source: "test"\nmain_ingredients: ["salt"]\nstar_ingredient: "salt"\n'
    'tags: []\ningredient_groups:\n  - items:\n    - item: salt\n'
    'method:\n  - "Nothing."\nmethod_short:\n  - ""\nmeta:\n  rewritten: true\n'
    '  awaiting_fix: false\n  proofread: {proofread}\n  cooked_before: false\n'
    '---\n'
)

# The smallest drink the schema accepts (#669). The tagline is not the "QQ"
# placeholder, which a promoted drink may not carry.
DRINK_GATE_FIXTURE = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'glass:\n  - "coupe"\ngarnish:\n  - "lime twist"\n'
    'ingredients:\n  - amount: "50 ml"\n    generic: "London dry gin"\n'
    '  - amount: "25 ml"\n    generic: "lime juice"\n'
    'method:\n  - "Shake all ingredients with ice."\n'
    'mood:\n  - "sharp"\nnotes: []\nsource: ""\nsource_url: ""\n'
    'meta:\n  ship: "yes"\n'
    '  rewritten: true\n  awaiting_fix: false\n  proofread: {proofread}\n---\n'
)


_in_the_fixture_build({
    f"_food_recipes/{slug}.md": FOOD_GATE_FIXTURE.format(t=slug, proofread=value)
    for slug, value in {"zzz-gate-unproofread": "false",
                        "zzz-gate-proofread": "true"}.items()})


def test_an_unproofread_recipe_does_not_reach_the_production_build(fixture_site):
    """`awaiting_fix: false, proofread: false` is held back; `proofread: true`
    publishes (#667).

    The pair is the test: the two fixtures differ in exactly one key, so only
    the flag under test explains one URL existing and the other not.
    """
    out = fixture_site
    assert not (out / "food" / "recipes" / "zzz-gate-unproofread" / "index.html").exists(), (
        "A recipe with `meta.proofread: false` was PUBLISHED. The gate's "
        "second leg has failed open -- _plugins/publish_gate.rb must "
        "publish only when `awaiting_fix == false` AND `proofread == "
        "true` (#667). Everything Helen has not read is now live."
    )
    assert (out / "food" / "recipes" / "zzz-gate-proofread" / "index.html").exists(), (
        "The control recipe -- identical but for `meta.proofread: true` -- "
        "is missing too, so this build proves nothing about the gate. It "
        "is over-firing, or the build dropped everything."
    )


# --- the magic bag mark (#1201, settling #507) -------------------------------
# A magic-bag row carries a quiet mark where `draft` goes, and nothing filters
# on it. A dish the gate holds back is a draft too: locally its row says
# `draft` then `magic bag`, magic bag always on the right. Fixtures, because
# the real collection is Helen's to fill; one held-back fixture per gate leg,
# because a dish failing both passes whichever leg the template forgot.
MAGIC_BAG_MARK_FIXTURE = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'main_ingredients: ["salt"]\ningredients:\n  - "salt"\n'
    'meta:\n  awaiting_fix: {awaiting_fix}\n  proofread: {proofread}\n---\n'
)
MAGIC_BAG_MARK = '<span class="badge badge-magic-bag">magic bag</span>'
DRAFT_MARK = '<span class="badge badge-draft">draft</span>'
MARK_SLOT = re.compile(r'<div class="badge-group-meta">(.*?)</div>', re.S)

MAGIC_BAG_LIVE = "zzz-magic-bag-mark"
MAGIC_BAG_HELD_BACK = {                     # slug -> (awaiting_fix, proofread)
    "zzz-magic-bag-unread": ("false", "false"),
    "zzz-magic-bag-awaiting": ("true", "true"),
}
MAGIC_BAG_MARK_FILES = {
    f"_food_magic_bag/{slug}.md": MAGIC_BAG_MARK_FIXTURE.format(
        t=slug, awaiting_fix=awaiting_fix, proofread=proofread)
    for slug, (awaiting_fix, proofread) in
    {MAGIC_BAG_LIVE: ("false", "true"), **MAGIC_BAG_HELD_BACK}.items()}

_in_the_fixture_build(MAGIC_BAG_MARK_FILES)


@pytest.fixture(scope="module")
def local_fixture_site():
    """The LOCAL build of a copy of the tree holding the magic-bag fixtures.

    A second fixture build, because `draft` beside `magic bag` exists only
    where the gate is skipped. Its own files only: the shared build's gate
    fixtures would all publish locally.
    """
    with built_with_fixtures("local", MAGIC_BAG_MARK_FILES, local=True) as out:
        yield out


def _index_rows(html: str) -> dict[str, str]:
    """url -> that row's markup, off a built food index."""
    rows = {}
    for chunk in html.split('<li data-url="')[1:]:
        url, _, rest = chunk.partition('"')
        rows[url] = rest
    return rows


def _mark_slot(row: str) -> str:
    """What a row holds where `draft` goes, with the whitespace taken out."""
    match = MARK_SLOT.search(row)
    assert match, "an index row has no .badge-group-meta at all."
    return "".join(match.group(1).split())


def test_a_magic_bag_dish_carries_the_quiet_mark_where_draft_goes(fixture_site):
    """On the live site a magic-bag row has the mark in the `draft` slot, and
    nothing else is there.

    Three controls: a recipe's slot is EMPTY, or a template printing the mark
    on every row passes; the held-back twins have no page and no row (#235);
    and no row on a production index says `draft`.
    """
    out = fixture_site
    assert (out / "food" / "magic-bag" / "zzz-magic-bag-mark" / "index.html").exists(), (
        "The proofread magic-bag fixture built no page, so nothing below is "
        "about the mark: the collection, its permalink or the gate has changed."
    )
    published = [slug for slug in MAGIC_BAG_HELD_BACK
                 if (out / "food" / "magic-bag" / slug / "index.html").exists()]
    assert not published, (
        "Magic-bag entries the gate should hold back were PUBLISHED: "
        f"{published}."
    )

    html = (out / "food" / "index.html").read_text(encoding="utf-8")
    rows = _index_rows(html)

    listed = [slug for slug in MAGIC_BAG_HELD_BACK
              if f"/food/magic-bag/{slug}/" in rows]
    assert not listed, (
        "The production index lists magic-bag dishes the gate held back, "
        f"linking to pages that were never written: {listed}."
    )
    assert "/food/magic-bag/zzz-magic-bag-mark/" in rows, (
        "The proofread magic-bag fixture has no row on the production index. "
        "The magic bag joins the index unconditionally (MANUAL §4.3); a dish "
        "hidden from the index is a dish forgotten."
    )
    want = "".join(MAGIC_BAG_MARK.split())
    got = _mark_slot(rows["/food/magic-bag/zzz-magic-bag-mark/"])
    assert got == want, (
        "A magic-bag row should hold exactly the `magic bag` mark in "
        f".badge-group-meta, where `draft` goes. It holds: {got!r}"
    )

    control = _mark_slot(rows["/food/recipes/caramel/"])
    assert control == "", (
        "A recipe's row has something in the mark slot on the live site: "
        f"{control!r}. Only a magic-bag dish is marked there."
    )
    assert "badge-draft" not in html, (
        "The PRODUCTION index carries a `draft` mark. Drafts do not publish, "
        "so a row saying so is a row that should not be there (#235)."
    )


def test_a_held_back_magic_bag_dish_says_draft_then_magic_bag_locally(local_fixture_site):
    """Locally, a dish the gate holds back carries BOTH marks, `magic bag` on
    the right; a publishable one carries `magic bag` alone (#1201).

    `.badge-group-meta` is a flex row packed to its right-hand end, so the mark
    written last is the rightmost. One fixture per gate leg: a template reading
    only `proofread` would miss the dish awaiting a fix. The publishable dish
    and a real recipe are the controls.
    """
    out = local_fixture_site
    html = (out / "food" / "index.html").read_text(encoding="utf-8")
    rows = _index_rows(html)

    both = "".join((DRAFT_MARK + MAGIC_BAG_MARK).split())
    for slug in MAGIC_BAG_HELD_BACK:
        url = f"/food/magic-bag/{slug}/"
        assert (out / "food" / "magic-bag" / slug / "index.html").exists(), (
            f"The local build wrote no page for {slug}. The local build skips "
            "the gate so that the dishes being worked on can be read."
        )
        assert url in rows, f"{slug} has no row on the LOCAL index."
        got = _mark_slot(rows[url])
        assert got == both, (
            f"{slug} is held back by the publish gate, so locally its row "
            "should say `draft` then `magic bag` -- magic bag on the right. "
            f"It holds: {got!r}"
        )

    live = _mark_slot(rows[f"/food/magic-bag/{MAGIC_BAG_LIVE}/"])
    assert live == "".join(MAGIC_BAG_MARK.split()), (
        "A magic-bag dish that passes the gate should carry `magic bag` alone "
        f"on the local index too. It holds: {live!r}"
    )
    control = _mark_slot(rows["/food/recipes/caramel/"])
    assert control == "", (
        f"A published recipe's row is marked on the local index: {control!r}."
    )


def test_the_magic_bag_mark_is_the_draft_marks_look_and_is_written_last(fixture_site):
    """One CSS rule for both marks, and one container, magic bag LAST (#1201).

    Reads the COMPILED stylesheet: every rule that styles one mark must name
    the other. The template half pins both marks in the one slot, `magic bag`
    after `draft`, and the slot packed to its right-hand end, which is what
    turns "written last" into "on the right".
    """
    css = (fixture_site / "assets" / "css" / "food.css").read_text(encoding="utf-8")
    styled = [{s.strip() for s in selector.split(",")}
              for selector, _ in _rules(css)
              if ".badge-draft" in selector or ".badge-magic-bag" in selector]
    assert styled, (
        "No rule in the built food.css names `.badge-draft` or "
        "`.badge-magic-bag`, so neither mark has the quiet look."
    )
    apart = [sorted(s) for s in styled
             if not {".badge-draft", ".badge-magic-bag"} <= s]
    assert not apart, (
        "The two marks no longer share their styling -- these rules name one "
        f"and not the other: {apart}. Helen's ruling on #1201 gives the magic "
        "bag the draft mark's own look; style both in one rule."
    )

    template = (ROOT / "food" / "index.html").read_text(encoding="utf-8")
    slots = [m for m in MARK_SLOT.findall(template) if "badge" in m]
    assert len(slots) == 1, (
        f"food/index.html has {len(slots)} .badge-group-meta slots holding a "
        "mark; there should be exactly one."
    )
    slot = slots[0]
    assert MAGIC_BAG_MARK in slot and DRAFT_MARK in slot, (
        "The `magic bag` and `draft` marks are no longer written into the same "
        ".badge-group-meta on food/index.html, so they cannot sit side by side."
    )
    assert slot.index(DRAFT_MARK) < slot.index(MAGIC_BAG_MARK), (
        "`magic bag` is written before `draft` in the slot, which puts it on "
        "the LEFT. Helen, 2026-10-04: \"Always sit magic bag on the right.\""
    )
    packed_right = [body for selector, body in _rules(css)
                    if selector.split(",")[-1].strip().endswith(".badge-group-meta")
                    and re.search(r"justify-content:\s*flex-end", body)]
    assert packed_right, (
        "`.badge-group-meta` is no longer `justify-content: flex-end` in the "
        "built food.css, so the last mark written is not at the right-hand "
        "end of the row and a lone `magic bag` has moved."
    )
    row_tags = [line for line in template.splitlines() if "<li data-url=" in line]
    assert len(row_tags) == 1, "food/index.html no longer has exactly one row tag."
    assert "magic" not in row_tags[0] and "data-meta" not in row_tags[0], (
        "The index row carries an attribute about the magic bag. Nothing may "
        "filter on it: the mark is a mark and not a filter (#1201, settling "
        f"#507). The row tag is: {row_tags[0].strip()}"
    )


# --- "For the to finish:" (#814) ---------------------------------------------
# One recipe carrying every kind of ingredient-group name the layout tells
# apart: a bare noun, three names that open with "to ", and a variation.

GROUP_HEADING_FIXTURE = (
    '---\ntitle: "zzz-814-group-headings"\n'
    'tagline: "Temporary fixture, deleted by the test."\n'
    'source: "test"\nmain_ingredients: ["salt"]\nstar_ingredient: "salt"\n'
    'tags: []\ningredient_groups:\n'
    '  - name: dressing\n    items:\n    - item: salt\n'
    '  - name: to finish\n    items:\n    - item: salt\n'
    '  - name: to decorate\n    items:\n    - item: salt\n'
    '  - name: to serve\n    items:\n    - item: salt\n'
    '  - name: "variation: plain"\n    items:\n    - item: salt\n'
    'method:\n  - "Nothing."\nmethod_short:\n  - ""\nmeta:\n  rewritten: true\n'
    '  awaiting_fix: false\n  proofread: true\n  cooked_before: false\n'
    '---\n'
)

_in_the_fixture_build(
    {"_food_recipes/zzz-814-group-headings.md": GROUP_HEADING_FIXTURE})

GROUP_HEADING = re.compile(r'<h3 class="recipe-group-heading">([^<]*)</h3>')


def test_a_group_named_to_something_is_its_own_heading(fixture_site):
    """A group name opening with "to " prints as itself, capitalised, with the
    colon; a bare noun gets "For the" (#814).

    A fixture, so the rule is tested whatever names the published collection
    holds.
    """
    page = fixture_site / "food" / "recipes" / "zzz-814-group-headings" / "index.html"
    assert page.exists(), "the #814 fixture recipe was not built"
    headings = GROUP_HEADING.findall(page.read_text(encoding="utf-8"))
    assert headings == [
        "For the dressing:", "To finish:", "To decorate:", "To serve:",
        "Variation: plain",
    ], (
        "ingredient-group headings are not what _layouts/recipe.html should "
        f"print for [dressing, to finish, to decorate, to serve, variation: "
        f"plain]: {headings}"
    )


def test_no_built_food_page_says_for_the_to(site):
    """#814, over everything that builds locally, drafts included, so a name
    the rule does not reach shows up by file. `site` and not `prod_site`:
    `_food_drafts/` holds group names the published collection does not, and
    only the local build renders it.
    """
    problems, seen = [], 0
    for page in sorted((site / "food").rglob("index.html")):
        for heading in GROUP_HEADING.findall(page.read_text(encoding="utf-8")):
            seen += 1
            if re.match(r"for the (to|for|the) ", heading, re.I):
                problems.append(f"{page.parent.name}: {heading!r}")
    assert seen > 50, (
        f"only {seen} group headings were found under food/, so GROUP_HEADING "
        f"no longer matches the layout's markup and this test reads nothing."
    )
    assert not problems, (
        'a food page prints a group heading that opens "For the to/for/the '
        '..." (#814):\n  ' + "\n  ".join(problems)
    )


# --- the scaler counts the thing made (#1286) --------------------------------
SCALE_CONTROL = re.compile(
    r'<div class="recipe-scale-controls"[^>]*>(.*?)</div>', re.S)


def _scale_control(site_dir, slug):
    page = site_dir / "food" / "recipes" / slug / "index.html"
    assert page.exists(), f"{slug} was not built"
    match = SCALE_CONTROL.search(page.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def _what_the_control_says(control):
    """The control's markup WITHOUT its class attributes, lowercased.

    The input keeps the class `recipe-scale-portions` on a `makes:` recipe --
    one control, one set of hooks for the script and the stylesheet -- and a
    class name is not something the page SAYS. Everything a reader or a
    screen reader meets is left in: the text, `title`, `aria-label`, `value`.
    """
    return re.sub(r'\sclass="[^"]*"', "", control).lower()


def test_a_makes_recipe_counts_what_it_makes_and_never_says_portions(prod_site):
    """A `makes:` recipe's scaler counts the thing made, starting at the lower
    number of a range, and never says "portions" (#1286).

    tests/test_food_yield.py checks the reading of every `makes:` line without
    a build; this checks it reaches the page. A `makes:` with no count at its
    start keeps the portions box, and a `serves:` recipe is untouched.
    """
    waffles = _scale_control(prod_site, "henrys-sunday-waffles")
    assert waffles is not None, "the waffles page has no scaler control"
    assert 'value="4"' in waffles and "data-made=" in waffles, (
        "the waffles' box should start at 4, the lower number of 4–6, and carry "
        f"the build's reading in data-made:\n{waffles}"
    )
    assert re.search(r'<span class="recipe-scale-word">\s*waffles\s*</span>', waffles), (
        f"the word after the waffles' box should be `waffles`:\n{waffles}"
    )
    assert 'aria-label="waffles to make"' in waffles, (
        "the waffles' box shows a derived figure (what N recipes make), so "
        f"its label must name the thing:\n{waffles}"
    )
    assert "portion" not in _what_the_control_says(waffles), (
        "the waffles' scaler still says portions somewhere -- in the word, "
        f"the `~` title or an aria-label:\n{waffles}"
    )

    # The half step is the build's verdict, carried as one attribute. The fairy
    # cakes halve; the waffles do not, because 1¾ cups of milk would halve to
    # ⅞; and "one 8-inch cake" has no half.
    fairy = _scale_control(prod_site, "grandmas-fairy-cakes") or ""
    assert "data-made=" in fairy and "data-half-recipe" in fairy, (
        "the fairy cakes should be offered a half recipe -- "
        f"_plugins/food_half_recipe.rb's verdict has not reached the page:\n{fairy}"
    )
    assert "data-half-recipe" not in waffles, (
        f"the waffles are offered a half recipe again (⅞ cups of milk):\n{waffles}"
    )
    page = (prod_site / "food" / "recipes" / "grandmas-fairy-cakes" / "index.html").read_text(encoding="utf-8")
    assert "data-singulars=" in page and "&quot;leaves&quot;:&quot;leaf&quot;" in page, (
        "the scaler is not handed ingredient_words.yml's `singulars`, so a "
        "count that comes down to one keeps its plural where a trailing `s` "
        "does not explain it (#1286)."
    )
    cake = _scale_control(prod_site, "beetroot-chocolate-cake") or ""
    assert "data-made=" in cake and "data-half-recipe" not in cake, (
        f"half of one 8-inch cake is not offered; the page says it is:\n{cake}"
    )

    expected = {
        # slug: (box, the word after it)
        "bens-chocolate-ice-cream": ("950", "ml"),
        "beetroot-chocolate-cake": ("1", "× 8-inch cake"),
        "sweet-shortcrust-pastry-mince-pies": ("1", "dozen mince pies"),
        "macarons": ("64+", "tiny macarons"),
        # `makes:` says "8 scones (2 large rounds of 4)": scones, not rounds.
        "grandmas-scones": ("8", "scones"),
    }
    problems = []
    for slug, (box, word) in expected.items():
        control = _scale_control(prod_site, slug) or ""
        said = re.search(r'<span class="recipe-scale-word">(.*?)</span>', control, re.S)
        got = (
            (re.search(r'<input[^>]*\bvalue="([^"]*)"', control) or [None, None])[1],
            " ".join(said.group(1).split()) if said else None,
        )
        if got != (box, word) or "portion" in _what_the_control_says(control):
            problems.append(f"{slug}: wanted {(box, word)}, the page has {got}")
    assert not problems, (
        "a `makes:` recipe's scaler does not count what it makes (#1286):\n  "
        + "\n  ".join(problems)
    )

    some = _scale_control(prod_site, "cherry-glaze") or ""
    assert "data-portions=" in some and "portions</span>" in some and "data-made" not in some, (
        "cherry-glaze (`makes: Some`) should keep the portions box, word and "
        f"`~` -- Helen: 'retain the previous guess':\n{some}"
    )
    assert "data-whole-recipes" in some, (
        "cherry-glaze should step in WHOLE RECIPES -- Helen: 'if \"some\" is "
        "originally guessed to be 4 portions, 2x should be 8 portions' -- "
        f"and its input no longer says so:\n{some}"
    )
    served = _scale_control(prod_site, "moules-mariniere") or ""
    assert 'data-portions="4"' in served and "data-made" not in served, (
        f"a `serves:` recipe's scaler should be untouched:\n{served}"
    )
    assert "data-whole-recipes" not in served, (
        "a `serves:` recipe steps a portion at a time (#1005); moules "
        f"marinière has been marked for whole-recipe steps:\n{served}"
    )


# --- the garnish step reads as English (#1138, #1143) ------------------------

GARNISH_DRINK = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'glass:\n  - "coupe"\ngarnish:\n{garnish}'
    'ingredients:\n  - amount: "50 ml"\n    generic: "London dry gin"\n'
    '  - amount: "25 ml"\n    generic: "lime juice"\n'
    'method:\n  - "Shake all ingredients with ice."\n'
    'mood:\n  - "sharp"\nnotes: []\nsource: ""\nsource_url: ""\n'
    'meta:\n  made_before: true\n  ship: "yes"\n'
    '  rewritten: true\n  awaiting_fix: false\n  proofread: true\n---\n'
)


def _garnish_lines(items):
    return "".join(f'  - "{g}"\n' for g in items)


GARNISH_CASES = {
    # slug: (garnishes, the sentence it must render)
    "zzz-garnish-one": (
        ["brandied cherry"],
        "Garnish with a brandied cherry."),
    "zzz-garnish-two": (
        ["brandied cherry", "lemon wheel"],
        "Garnish with a brandied cherry and a lemon wheel."),
    "zzz-garnish-three": (
        ["mint sprig", "fruit wedges", "maraschino cherry"],
        "Garnish with a mint sprig, fruit wedges and a maraschino cherry."),
    "zzz-garnish-four": (
        ["mint sprig", "raspberries", "lemon wheel", "brandied cherry"],
        "Garnish with a mint sprig, raspberries, a lemon wheel "
        "and a brandied cherry."),
}
_in_the_fixture_build({
    f"_cocktail_recipes/{slug}.md":
    GARNISH_DRINK.format(t=slug, garnish=_garnish_lines(garnishes))
    for slug, (garnishes, _) in GARNISH_CASES.items()})


def test_the_garnish_step_punctuates_a_list_and_drops_the_article_on_a_plural(fixture_site):
    """`A, B and C` with no serial comma, and no `a` before a plural (#1138,
    #1143).

    A built page, because the rule is Liquid in `_layouts/cocktail.html` and
    nothing else can call it. Fixtures, because a public test may never require
    a draft (#624). `fruit wedges` is not in garnish.yml's `no_article` list:
    it models a plural nobody has declared.
    """
    out = fixture_site
    for slug, (_, expected) in GARNISH_CASES.items():
        page = out / "cocktails" / "recipes" / slug / "index.html"
        assert page.exists(), f"{slug} did not build"
        html = page.read_text(encoding="utf-8")
        found = re.search(r"<li>Garnish with (.*?)\.</li>", html, re.S)
        assert found, f"{slug} rendered no garnish step at all"
        got = "Garnish with " + " ".join(
            re.sub(r"<[^>]+>", "", found.group(1)).split()) + "."
        assert got == expected, (
            f"{slug}\n  expected: {expected}\n  got:      {got}\n\n"
            "#1138 is the punctuation (one garnish is itself, two are joined "
            "by `and`, three or more are `A, B and C` with no serial comma) "
            "and #1143 is the article (nothing before a word ending in `s`, "
            "whether or not it is declared in garnish.yml's `no_article`). "
            "Both live in the garnish-step block of _layouts/cocktail.html."
        )


SHELL_DRINK = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'glass:\n  - "tiki mug"\ngarnish:\n{garnish}'
    'ingredients:\n  - amount: "50 ml"\n    generic: "London dry gin"\n'
    '  - amount: "25 ml"\n    generic: "lime juice"\n{shell}'
    'method:\n  - "Shake all ingredients with ice."\n'
    'mood:\n  - "sharp"\nnotes: []\nsource: ""\nsource_url: ""\n'
    'meta:\n  made_before: true\n  ship: "yes"\n'
    '  rewritten: true\n  awaiting_fix: false\n  proofread: true\n---\n'
)
SHELL_POUR = ('  - amount: "25 ml"\n    generic: "overproof Jamaican rum, unaged"\n'
              '    as: "shell"\n')


SHELL = "half an empty passion fruit shell"
SHELL_CASES = {
    # slug: (garnishes, has a shell pour, the garnish step or None)
    "zzz-shell-with-others": (["mint sprig", SHELL], True,
                              "Garnish with a mint sprig."),
    "zzz-shell-alone": ([SHELL], True, None),
    "zzz-shell-no-rum": ([SHELL], False, f"Garnish with {SHELL}."),
}
_in_the_fixture_build({
    f"_cocktail_recipes/{slug}.md": SHELL_DRINK.format(
        t=slug, garnish=_garnish_lines(garnishes),
        shell=SHELL_POUR if pour else "")
    for slug, (garnishes, pour, _) in SHELL_CASES.items()})


def test_a_filled_shell_is_named_in_the_meta_and_gets_no_garnish_step(fixture_site):
    """The shell is in `garnish:` and the page does not say it twice (#1256).

    A shell that an `as: "shell"` ingredient fills is named by the meta line
    and gets no generated garnish step. The third case keeps this honest: a
    shell with no rum in it is an ordinary garnish and keeps its step.
    """
    out = fixture_site
    for slug, (_, _, expected) in SHELL_CASES.items():
        page = out / "cocktails" / "recipes" / slug / "index.html"
        assert page.exists(), f"{slug} did not build"
        html = page.read_text(encoding="utf-8")
        assert re.search(r"<dt>Garnish</dt>\s*<dd>[^<]*" + re.escape(SHELL), html), (
            f"{slug}: the meta line does not name the shell, so the page "
            "reaches \"(shell)\" without having mentioned one.")
        found = re.search(r"<li>Garnish with (.*?)\.</li>", html, re.S)
        got = None if not found else "Garnish with " + " ".join(
            re.sub(r"<[^>]+>", "", found.group(1)).split()) + "."
        assert got == expected, (
            f"{slug}\n  expected: {expected}\n  got:      {got}\n\n"
            "A shell an `as: \"shell\"` pour fills is placed by the method "
            "and gets no generated step; a shell with no rum is an "
            "ordinary garnish. The garnish-step block of "
            "_layouts/cocktail.html decides."
        )


def test_no_garnish_contains_the_join_separator():
    """The garnish step joins its parts with `|` and splits them back.

    Liquid cannot append to an array, so the step builds one string and splits
    it. A garnish containing the separator would silently become two garnishes.
    """
    import yaml as _yaml
    data = _yaml.safe_load(
        (ROOT / "_data" / "cocktails" / "garnish.yml").read_text(encoding="utf-8"))
    offenders = []
    for group, values in (data.get("canonical") or {}).items():
        for g in (values or []):
            if isinstance(g, str) and "|" in g:
                offenders.append(f"{group}: {g!r}")
    assert not offenders, (
        "Garnish value(s) containing `|`, which the garnish step uses to join "
        "its parts before splitting them back:\n  " + "\n  ".join(offenders)
        + "\n\nEither rename the garnish or change the separator in "
          "_layouts/cocktail.html's garnish-step block."
    )


_in_the_fixture_build({
    f"_cocktail_recipes/{slug}.md": DRINK_GATE_FIXTURE.format(t=slug, proofread=value)
    for slug, value in {"zzz-gate-drink-unproofread": "false",
                        "zzz-gate-drink-proofread": "true"}.items()})


def test_the_gate_covers_a_promoted_drink(fixture_site):
    """The cocktail collection is gated too (#667, #668).

    It writes its own drinks because `_cocktail_drafts/` is a private repo,
    absent in CI, and a public test may never require private drink data (#624).
    """
    out = fixture_site
    held = out / "cocktails" / "recipes" / "zzz-gate-drink-unproofread" / "index.html"
    live = out / "cocktails" / "recipes" / "zzz-gate-drink-proofread" / "index.html"

    assert not held.exists(), (
        "A promoted drink with `meta.proofread: false` was PUBLISHED. "
        "`cocktail_recipes` is in GATED_COLLECTIONS, so the gate is "
        "failing open on the collection the whole of #668 exists to "
        "protect."
    )
    assert live.exists(), (
        "The control drink -- identical but for `meta.proofread: true` -- "
        "is missing too, so this build proves nothing. Either the gate is "
        "over-firing on drinks, or the cocktail collection is not being "
        "written at all."
    )

    # The index agrees with the gate: the plugin empties `site.cocktail_recipes`
    # of the held-back drink at :post_read. A URL that exists and a listing
    # that mentions it are two separate leaks (#276).
    index = (out / "cocktails" / "index.html").read_text(encoding="utf-8")
    assert "zzz-gate-drink-unproofread" not in index, (
        "The production drinks index names a drink the gate held back. "
        "The listing and the URL are separate leaks (#276) and this is "
        "the listing one."
    )
    assert "zzz-gate-drink-proofread" in index, (
        "The production drinks index does not list a published drink. "
        "cocktails/index.html must read `site.cocktail_recipes` in every "
        "build and concatenate the drafts only under `site.show_drafts` "
        "-- an index gated on `show_drafts` alone shows nothing the day a "
        "drink is promoted."
    )


# --- the third leg, drinks only: `rewritten` (#1137) -------------------------
# Both drink-side flags are parameterised here: the rule is about the
# combination of `rewritten` and `made_before`, and only the first gates.

GATE_DRINK_ANY = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'glass:\n  - "coupe"\ngarnish:\n  - "lime twist"\n'
    'ingredients:\n  - amount: "50 ml"\n    generic: "London dry gin"\n'
    '  - amount: "25 ml"\n    generic: "lime juice"\n'
    'method:\n  - "Shake all ingredients with ice."\n'
    'mood:\n  - "sharp"\nnotes: []\nsource: ""\nsource_url: ""\n'
    'meta:\n  made_before: {made_before}\n  ship: "who knows"\n'
    '  rewritten: {rewritten}\n  awaiting_fix: false\n  proofread: true\n---\n'
)

GATE_FOOD_UNREWRITTEN = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'source: "test"\nmain_ingredients: ["salt"]\nstar_ingredient: "salt"\n'
    'tags: []\ningredient_groups:\n  - items:\n    - item: salt\n'
    'method:\n  - "Nothing."\nmethod_short:\n  - ""\nmeta:\n'
    '  rewritten: false\n  awaiting_fix: false\n  proofread: true\n'
    '  cooked_before: false\n---\n'
)


_in_the_fixture_build({
    **{f"_cocktail_recipes/{slug}.md":
       GATE_DRINK_ANY.format(t=slug, rewritten=rw, made_before=mb)
       for slug, (rw, mb) in {
           # slug: (rewritten, made_before)
           "zzz-1137-rewritten-unmade":     ("true",  "false"),
           "zzz-1137-unrewritten-made":     ("false", "true"),
           "zzz-1137-unrewritten-unmade":   ("false", "false"),
       }.items()},
    "_food_recipes/zzz-1137-food-unrewritten.md":
        GATE_FOOD_UNREWRITTEN.format(t="zzz-1137-food-unrewritten"),
})


def test_an_unrewritten_drink_is_held_back_but_an_unmade_one_publishes(fixture_site):
    """`rewritten: true` gates a drink; `made_before` does not (#1137, #722).

    Four fixtures in one build, because each row alone is satisfied by a plugin
    that does nothing or by one that drops everything:

        drink, rewritten,     unmade  -> PUBLISHES
        drink, NOT rewritten, made    -> held
        drink, NOT rewritten, unmade  -> held
        FOOD,  NOT rewritten          -> PUBLISHES (drinks only; food keeps two)

    The last row guards a refactor that reads the flags without the collection
    name, which would take every unrewritten food recipe off the live site.
    """
    out = fixture_site

    def drink_live(slug):
        return (out / "cocktails" / "recipes" / slug / "index.html").exists()

    assert drink_live("zzz-1137-rewritten-unmade"), (
        "A drink with `rewritten: true` and `made_before: false` was HELD "
        "BACK. An unmade drink must publish -- #722, and #1137 restates it: "
        "the live site is where Helen picks what to try next and reads it "
        "while making it. `made_before` must not be a leg of the gate."
    )
    assert not drink_live("zzz-1137-unrewritten-made"), (
        "A drink with `rewritten: false` was PUBLISHED. #1137 makes that "
        "flag the third leg of the gate for `cocktail_recipes`: the prose "
        "on a published drink is Helen's, and until this leg existed the "
        "only thing checking was the promotion procedure remembering to."
    )
    assert not drink_live("zzz-1137-unrewritten-unmade"), (
        "An unrewritten, unmade drink was PUBLISHED. The two flags are "
        "separate questions: being unmade is fine, being unrewritten is "
        "not, and this row is what stops the pair being read as one."
    )
    assert (out / "food" / "recipes" / "zzz-1137-food-unrewritten"
            / "index.html").exists(), (
        "A FOOD recipe with `rewritten: false` was HELD BACK. #1137 is "
        "drinks only -- Helen ruled on cocktails, and food keeps its two "
        "legs. The new leg must be scoped to the `cocktail_recipes` "
        "collection; unscoped, it takes every unrewritten recipe off the "
        "live site."
    )


# --- one header and one footer for the whole repo (#374) ---------------------
# One artefact, not two kept in step. Each half can be individually correct
# while two built pages disagree, so these tests compare the output.

def _chrome_of(html: str) -> dict[str, str]:
    """The two shared-chrome blocks, verbatim, out of one built page."""
    nav = re.search(r'<nav class="site-nav-icons">.*?</nav>', html, re.S)
    footer = re.search(r'<footer class="site-footer">.*?</footer>', html, re.S)
    return {
        "header nav": nav.group(0) if nav else "",
        "footer": footer.group(0) if footer else "",
    }


def test_the_header_and_footer_are_identical_on_every_page(prod_site):
    """The footer is byte-identical across both sites; the nav row is
    byte-identical across every page OF A SITE, and names the other site.

    Identical source text, with nothing normalised away. The nav row is one
    template and one loop over sites.yml with no per-site key (#374); its
    output varies because each site's row names the other site and never its
    own, which also stops the loop showing both, or neither, after a third
    entry.
    """
    pages = {
        "/food/": prod_site / "food" / "index.html",
        "/cocktails/": prod_site / "cocktails" / "index.html",
        # A collection document too: a recipe reaches default.html through
        # recipe.html, so its chrome arrives by a different route.
        "/food/recipes/caramel/": prod_site / "food" / "recipes" / "caramel" / "index.html",
    }
    for url, path in pages.items():
        assert path.exists(), (
            f"{url} is not in the production build, so this test would compare "
            f"fewer pages than it claims to -- and an empty comparison passes. "
            f"If that page is genuinely gone, replace it here with one that "
            f"still exists rather than dropping it."
        )

    chromes = {url: _chrome_of(p.read_text(encoding="utf-8")) for url, p in pages.items()}

    for block in ("header nav", "footer"):
        for url, chrome in chromes.items():
            assert chrome[block], (
                f"No {block} found in {url}. Either _layouts/default.html stopped "
                f"emitting it, or its wrapper element was renamed -- and a test "
                f"that finds nothing to compare passes while checking nothing."
            )

    # The footer: one, everywhere.
    reference_url, reference = next(iter(chromes.items()))
    for url, chrome in chromes.items():
        if chrome["footer"] == reference["footer"]:
            continue
        raise AssertionError(
            f"The footer differs between {reference_url} and {url}.\n\n"
            f"{reference_url}:\n{reference['footer']}\n\n"
            f"{url}:\n{chrome['footer']}\n\n"
            f"There is ONE footer in this repo (issue #374). A difference here "
            f"means something in _layouts/default.html has started branching on "
            f"site_key again, or a value it reads out of _data/sites.yml has "
            f"become per-site when it should be in _data/chrome.yml."
        )

    # The nav: one per SITE. Two food pages by two routes must agree exactly.
    assert chromes["/food/"]["header nav"] == chromes["/food/recipes/caramel/"]["header nav"], (
        "The header nav differs between /food/ and /food/recipes/caramel/:\n\n"
        f"{chromes['/food/']['header nav']}\n\n"
        f"{chromes['/food/recipes/caramel/']['header nav']}\n\n"
        "Within a site the row must be identical on every page; a recipe reaches "
        "default.html through recipe.html and must not arrive with a different one."
    )

    # And each site's row is the door to the OTHER site, never to itself.
    sites = yaml.safe_load((ROOT / "_data" / "sites.yml").read_text(encoding="utf-8")) or {}
    words = {key: f"[ {s['word']} ]" for key, s in sites.items()}
    for url, key in (("/food/", "food"), ("/cocktails/", "cocktails")):
        nav = chromes[url]["header nav"]
        assert words[key] not in nav, (
            f"{url}'s header nav names its own site, {words[key]!r}. The tape "
            f"above already says where you are; the row is for the other site."
        )
        others = [w for k, w in words.items() if k != key]
        for w in others:
            assert w in nav, (
                f"{url}'s header nav does not name {w!r}. The row exists to be "
                f"the door to the other site (Helen, 2026-09-10); a site with no "
                f"door in the row is the #374 failure -- one site with no nav -- "
                f"in a new shape."
            )


def test_every_chrome_class_has_a_rule_in_every_site_stylesheet(site):
    """A class the shared header or footer emits must be styled on BOTH sites.

    test_every_class_we_emit_has_a_rule_in_the_stylesheet reads food.css only,
    so a chrome rule under _sass/food/ satisfies it and is absent on cocktails
    (#374). Derived from the template and the icon partials, not from a list,
    so a class added to the chrome is covered.
    """
    layout = ROOT / "_layouts" / "default.html"
    sites = yaml.safe_load((ROOT / "_data" / "sites.yml").read_text(encoding="utf-8")) or {}

    # default.html includes icons/github.svg literally, and icons/<icon>.svg
    # for every site, so the icon partials' own classes are chrome too.
    icon_names = ["github"] + [(s or {}).get("icon") for s in sites.values()]
    sources = [layout] + [
        ROOT / "_includes" / "icons" / f"{n}.svg" for n in icon_names if n
    ]
    for path in sources:
        assert path.exists(), (
            f"{path.relative_to(ROOT)} does not exist, so this test would scan "
            f"less chrome than it claims to. Check _data/sites.yml's `icon` "
            f"values and _layouts/default.html's own includes."
        )

    emitted = set()
    for path in sources:
        for attr in re.findall(r"""class=['"]([^'"{}]+)['"]""", path.read_text(encoding="utf-8")):
            emitted.update(attr.split())
    assert emitted, (
        "No classes found in the shared chrome at all. The template's class "
        "attributes are built with Liquid now, or the pattern went stale -- "
        "and a scan that finds nothing passes."
    )

    stylesheets = {
        key: site / "assets" / "css" / f"{(cfg or {}).get('css', key)}.css"
        for key, cfg in sites.items()
    }
    styled_in = {}
    for key, css_path in stylesheets.items():
        assert css_path.exists(), (
            f"{key}'s stylesheet was not built at {css_path.name}. Check "
            f"_data/sites.yml's `css` value against assets/css/."
        )
        css = css_path.read_text(encoding="utf-8")
        styled_in[key] = {name for name in emitted if f".{name}" in css}

    # Divergence only: a class styled by at least one site must be styled by
    # all of them. Not "every chrome class has a rule somewhere": that would
    # fire on BEM modifier hooks that no site styles (MANUAL §11.3), which is
    # not a fork.
    everywhere = set().union(*styled_in.values()) if styled_in else set()
    forked = []
    for name in sorted(everywhere):
        absent = sorted(k for k, styled in styled_in.items() if name not in styled)
        if absent:
            present = sorted(k for k, styled in styled_in.items() if name in styled)
            forked.append(f".{name} — styled in {present}, missing from {absent}")

    assert not forked, (
        "Shared chrome class(es) styled on some sites and not others:\n  "
        + "\n  ".join(forked)
        + "\n\nThe header and the footer are one artefact (issue #374), so a "
          "rule for one of their classes belongs in _sass/shared/_chrome.scss "
          "or _sass/shared/_layout.scss -- never in a single site's directory. "
          "If the rule needs a colour, use $color-accent: that is what the "
          "tenth palette-contract variable is for."
    )


def test_every_published_page_links_a_stylesheet(prod_site):
    """A page with no site_key links no stylesheet at all, and says nothing.

    _layouts/default.html links the stylesheet inside `{% if this_site %}`, so
    a page whose site_key is missing, misspelled, or lost when it moved out of
    the directory whose _config.yml default supplied it renders unstyled
    (MANUAL §2.4). Reads the production build: this is about what publishes.
    """
    pages = sorted(prod_site.rglob("index.html")) + [
        p for p in prod_site.rglob("*.html") if p.name != "index.html"
    ]
    assert pages, (
        f"No built pages found under {prod_site} -- the build produced nothing "
        f"and an empty scan passes."
    )

    naked = []
    for path in pages:
        html = path.read_text(encoding="utf-8", errors="replace")
        # The root redirect is a bare <meta http-equiv="refresh"> with no layout
        # and nothing to style (#204).
        if "http-equiv=\"refresh\"" in html.replace("'", '"'):
            continue
        if 'rel="stylesheet"' not in html:
            naked.append("/" + str(path.relative_to(prod_site).parent).replace("\\", "/") + "/")

    assert not naked, (
        "Published page(s) linking no stylesheet at all:\n  "
        + "\n  ".join(sorted(naked))
        + "\n\nThese render as unstyled HTML. The cause is almost always a "
          "missing or wrong `site_key`: _config.yml assigns it by DIRECTORY, so "
          "a page at the repo root, or one that has just moved between "
          "directories, inherits none and must declare it in its own front "
          "matter. _layouts/default.html links the stylesheet inside "
          "`{% if this_site %}` and emits nothing when that is false -- there "
          "is no fallback and no warning."
    )


def test_both_ingredient_pickers_mark_their_word_matches(site):
    """The include and exclude pickers both emphasise a real word match (#390).

    Both call `IS.buildMasterList` and `IS.search` and get the same
    `hasWordMatch` flag (MANUAL §8.1). The classes are added with
    `classList.add`, which the class-attribute scan above does not reach, so
    this checks: both builders apply a --word-match class, no call site drops
    the flag, and both classes have a rule in the compiled CSS.
    """
    # Comments are stripped before matching: a comment in filters.js that
    # names `r.hasWordMatch` would otherwise count as a call passing it.
    raw = (ROOT / "assets" / "js" / "filters.js").read_text(encoding="utf-8")
    js = re.sub(r"//.*$", " ", re.sub(r"/\*.*?\*/", " ", raw, flags=re.S), flags=re.M)

    problems = []
    for builder, cls in (("makeIngredientButton", "btn-ingredient--word-match"),
                         ("makeExcludeButton", "btn-exclude--word-match")):
        if f"function {builder}(" not in js:
            problems.append(f"{builder}() is gone or renamed — this test cannot see what it guards")
            continue
        if f"'{cls}'" not in js:
            problems.append(f"{builder}() does not add .{cls}")

    # Call sites, matched as calls and not as mentions of a name; the lookbehind
    # excludes the two function DEFINITIONS, whose parameter lists name
    # `wordMatch`.
    calls = re.findall(
        r"(?<!function )make(?:Ingredient|Exclude)Button\(([^)]*)\)", js
    )
    dropped = [c for c in calls if "hasWordMatch" not in c and "true" not in c]

    # The rule, not a count of call sites: no call may drop the flag (#387).
    assert calls, (
        "No calls to the picker button builders found at all. Either they were "
        "renamed or this pattern went stale, and a scan matching nothing passes."
    )
    if dropped:
        problems.append(
            f"{len(dropped)} of {len(calls)} picker-button call sites pass no "
            f"word-match argument, so those buttons can never be marked as "
            f"matches: {dropped}"
        )

    css = (site / "assets" / "css" / "food.css").read_text(encoding="utf-8")
    for cls in ("btn-ingredient--word-match", "btn-exclude--word-match"):
        if f".{cls}" not in css:
            problems.append(f".{cls} is emitted by filters.js but styled nowhere")

    assert not problems, (
        "The two ingredient pickers have drifted apart:\n  " + "\n  ".join(problems)
        + "\n\nThey share one code path and one set of ranked results (MANUAL "
          "8.1). A match treatment on one and not the other is drift. The shared "
          "emphasis lives in _sass/shared/_rule.scss as @mixin "
          "index-chip-word-match($colour); each picker passes its own "
          "colour."
    )


# Properties that change how much room a button takes up. A selected filter
# button that declares one of these has moved every button after it on the row.
LAYOUT_PROPERTIES = (
    "font-size", "letter-spacing", "padding", "padding-left", "padding-right",
    "margin", "margin-left", "margin-right", "border", "border-width",
    "border-left-width", "border-right-width", "word-spacing", "width",
)


def _selects_a_chosen_button(selector: str, buttons: tuple[str, ...],
                             chosen: str) -> bool:
    """Does ONE selector (no commas) target a filter button in its chosen state?

    Both classes anywhere in the selector, in either order, outside any `:not()`.

    Either order, because `@extend` of a placeholder holding `&.is-on` compiles
    to `.is-on.btn-chaos`, chosen class first (#1086). Outside `:not()`, because
    `.btn-mood:hover:not(.is-on)` names both classes and means a button that is
    NOT chosen.
    """
    bare = re.sub(r":not\([^()]*\)", "", selector)
    if f".{chosen}" not in bare:
        return False
    # `(?![-\w])` so `.btn-tag` does not match `.btn-tag-thing`.
    return any(re.search(r"\." + re.escape(b) + r"(?![-\w])", bare)
               for b in buttons)


def test_no_active_filter_button_changes_its_own_width(site):
    """Selecting a filter must not resize it, on either site. Issue #389.

    A chosen-state rule that sets a type metric re-measures the button and
    slides the rest of its row along. Read from the compiled CSS, so every
    selector extending the active base is covered. -webkit-text-stroke is
    absent on purpose: it occupies no space (MANUAL §13.4.2).
    """
    # (stylesheet, the filter-button classes, the class that means "chosen").
    scans = (
        ("food.css", ("btn-tag", "btn-star", "btn-meta",
                      "btn-ingredient", "btn-exclude"), "active"),
        ("cocktails.css", ("btn-mood", "btn-chaos"), "is-on"),
    )

    for stylesheet, buttons, chosen in scans:
        css = (site / "assets" / "css" / stylesheet).read_text(encoding="utf-8")

        # Rules whose selector says "a filter button in its selected state".
        blocks = re.findall(r"([^{}]+)\{([^{}]*)\}", css)
        active = [(sel.strip(), body) for sel, body in blocks
                  if any(_selects_a_chosen_button(part, buttons, chosen)
                         for part in sel.split(","))]
        assert active, (
            f"No active filter-button rules found in {stylesheet}. Either the "
            f"class naming changed or this pattern went stale -- and a scan that "
            f"matches nothing passes while checking nothing."
        )

        offenders = []
        for sel, body in active:
            for decl in body.split(";"):
                prop = decl.split(":")[0].strip().lower()
                if prop in LAYOUT_PROPERTIES:
                    offenders.append(f"{sel} declares {decl.strip()}")

        assert not offenders, (
            f"Active filter-button rule(s) in {stylesheet} declare a property "
            f"that changes the button's size:\n  " + "\n  ".join(sorted(set(offenders)))
            + "\n\nThe button grows or shrinks the moment it is selected, and every "
              "button after it on the row moves (issue #389). A selected state may "
              "change colour, a fill (.tag-shape on food, `background` on "
              "cocktails) and -webkit-text-stroke, none of which occupies space. "
              "If a metric genuinely must change, change the RESTING state to "
              "match so the two agree."
        )


# Properties that give a box vertical size of its own, i.e. that an EMPTY
# element would still occupy. `gap` is deliberately absent: it only ever
# appears between children, so an empty flex box with a gap is still zero-high.
VERTICAL_SPACE_PROPERTIES = (
    "margin", "margin-top", "margin-bottom",
    "padding", "padding-top", "padding-bottom",
    "height", "min-height",
)


def _is_all_zero(value: str) -> bool:
    """True if every length in a (possibly shorthand) value is zero."""
    parts = value.split()
    return bool(parts) and all(
        re.fullmatch(r"0(?:px|rem|em|%|vh)?", p, flags=re.I) for p in parts
    )


def test_an_empty_search_results_pool_reserves_no_space(site):
    """An empty ingredient/exclude pool must take up no room. Issue #589.

    A `:not(:empty)` rule can only add to an unconditional one beneath it, so
    any unconditional vertical size on `.search-results` makes the empty pool
    a different height from the full one, and the chosen pill jumps when the
    pool empties.
    """
    css = (site / "assets" / "css" / "food.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    blocks = re.findall(r"([^{}]+)\{([^{}]*)\}", css)
    pool_rules = [(" ".join(sel.split()), body) for sel, body in blocks
                  if ".search-results" in sel]
    assert pool_rules, (
        "No .search-results rules found in the compiled CSS. Either the class "
        "was renamed or this scan went stale -- and a scan that matches nothing "
        "passes while checking nothing (MANUAL 12)."
    )

    offenders = []
    for sel, body in pool_rules:
        # A rule that already says "only when it has content" is the intended
        # shape, not the bug.
        if ":not(:empty)" in sel or ":empty" in sel:
            continue
        for decl in body.split(";"):
            if ":" not in decl:
                continue
            prop, _, value = decl.partition(":")
            prop = prop.strip().lower()
            if prop in VERTICAL_SPACE_PROPERTIES and not _is_all_zero(value.strip()):
                offenders.append(f"{sel} declares {prop}: {value.strip()}")

    assert not offenders, (
        "A .search-results rule gives the pool vertical size unconditionally:\n  "
        + "\n  ".join(sorted(set(offenders)))
        + "\n\nThat space is paid by every session that never opens the picker, "
          "and it makes the EMPTY pool a different height from the full one -- "
          "which is issue #589, the chosen LEAVE OUT pill dropping a few pixels "
          "below the chip you clicked. Put the declaration on the "
          "`:not(:empty)` rule in _sass/food/_category-labels.scss instead, "
          "which is the one place the pool's spacing is meant to live."
    )


def _luminance(css_colour):
    """Relative luminance of a CSS colour, 0 (black) to 1 (white).

    Takes `rgb(r, g, b)` or `#rrggbb`: Sass emits the former for a computed
    colour and the latter for a literal or a plain alias.
    """
    css_colour = css_colour.strip()
    if css_colour.startswith("#"):
        hexs = css_colour.lstrip("#")
        if len(hexs) == 3:
            hexs = "".join(ch * 2 for ch in hexs)
        nums = [float(int(hexs[i:i + 2], 16)) for i in (0, 2, 4)]
    else:
        nums = [float(n) for n in re.findall(r"[\d.]+", css_colour)[:3]]
    channels = []
    for raw in nums:
        c = raw / 255.0
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def test_the_exclude_hover_is_actually_darker_than_the_state_it_replaces(site):
    """A matched LEAVE OUT tag must darken when hovered. Issue #403.

    Word-matched candidates rest at $color-exclude-active (#390), so a hover
    of the same colour is a no-op. Both values derive from one root, so an
    edit to either step can collapse them. Compared on relative luminance,
    because "darker" is the claim and two strings can be one colour.
    """
    css = (site / "assets" / "css" / "food.css").read_text(encoding="utf-8")

    def colour_of(pattern, what):
        match = re.search(pattern, css, re.S)
        assert match, (
            f"Could not find {what} in the compiled CSS. The selector was "
            f"renamed or the rule is gone -- and a scan that finds nothing "
            f"passes while checking nothing."
        )
        return match.group(1).strip()

    resting = colour_of(r"\.btn-exclude--word-match \{[^}]*?color: ([^;]+);",
                        "the resting colour of a matched LEAVE OUT candidate")
    hover = colour_of(
        r"\.btn-exclude:not\(\.btn-exclude--active\):hover[^{]*\{[^}]*?color: ([^;]+);",
        "the hover colour of a LEAVE OUT pool candidate")

    assert _luminance(hover) < _luminance(resting), (
        f"Hovering a word-matched LEAVE OUT candidate does not darken it: it "
        f"rests at {resting} and hovers to {hover}.\n"
        f"Issue #403 asked for these to darken, like the include picker. If the "
        f"two are equal the hover is a literal no-op and the tag does not "
        f"respond to the cursor at all; if the hover is lighter, the pool "
        f"brightens while every other filter section on the page darkens.\n"
        f"$color-exclude-hover must stay a deeper cut than $color-exclude-active."
    )


# The only files that belong at the root of the built site. Directories are not
# checked -- those are pages, and every other test here is about pages.
EXPECTED_ROOT_FILES = {
    "index.html",     # the bare redirect to /food/ (issue #204)
    "sitemap.xml",    # jekyll-sitemap
    "robots.txt",
    "README.md",      # deliberately published; it is the repo's front page
    "LICENSE",
    # GitHub Pages serves a root 404.html for any URL it cannot find, so the
    # file has to be here and not in a directory (#1086).
    "404.html",
}


def test_the_built_site_root_holds_nothing_unexpected(prod_site):
    """Nothing lands at the built site's root without being listed here.

    Jekyll copies the source directory, so `.gitignore` says nothing about
    what ships: a tracked file reaches the site unless `_config.yml` excludes
    it (#414). Run against the production build, which is what deploys.
    """
    found = {p.name for p in prod_site.iterdir() if p.is_file()}
    assert found, (
        f"No files at all at the root of {prod_site} -- the build produced "
        f"nothing, and an empty scan passes."
    )

    unexpected = found - EXPECTED_ROOT_FILES
    assert not unexpected, (
        "Unexpected file(s) at the root of the built site:\n  "
        + "\n  ".join(sorted(unexpected))
        + "\n\nEither add an `exclude:` entry in _config.yml, or -- if it really "
          "should ship -- add it to EXPECTED_ROOT_FILES here with a note saying "
          "what it is for."
    )

    missing = EXPECTED_ROOT_FILES - found
    assert not missing, (
        f"Expected root file(s) missing from the build: {sorted(missing)}.\n"
        f"Either something stopped being published, or this list has gone stale "
        f"-- and a stale allowlist is how this check would quietly stop meaning "
        f"anything."
    )


# Wording that only a note to Helen uses. Phrases, not words: "remove" alone
# is in recipes.
NOTE_TO_SELF = re.compile(
    r"remove this (?:note|line)|remove once (?:confirmed|you)|checked once|your call whether",
    re.IGNORECASE)


def test_no_published_file_ships_a_note_to_helen(prod_site):
    """A note written for Helen in a data file must not reach a reader, not
    even in a page's embedded JSON, where view-source shows it (#1387).
    Covers every HTML and JSON file in the production build."""
    files = sorted(prod_site.rglob("*.html")) + sorted(prod_site.rglob("*.json"))
    assert files, f"No HTML or JSON under {prod_site} -- an empty scan passes."
    found = []
    for path in files:
        for m in NOTE_TO_SELF.finditer(path.read_text(encoding="utf-8")):
            found.append(f"{path.relative_to(prod_site)}: ...{m.group(0)}...")
    assert not found, (
        "The production build ships text written for Helen:\n  " + "\n  ".join(found[:10])
        + "\n\nEither drop the field from what the page embeds (`without_keys`, "
          "_plugins/without_keys.rb) or resolve the note in the data.")


def test_the_cocktail_index_marks_and_styles_everything_it_lights_up(site):
    """Three JS-applied classes on the drinks index, and each must have a rule.

    They are applied with classList/className, never written into a
    `class="..."` attribute, so the scan in
    test_every_class_we_emit_has_a_rule_in_the_stylesheet does not reach
    them (#390 is the food-side precedent): btn-pool--word-match (#549),
    drink-card-hit, and drink-name-hit (#564).
    """
    raw = (ROOT / "assets" / "js" / "cocktail-index.js").read_text(encoding="utf-8")
    js = re.sub(r"//.*$", " ", re.sub(r"/\*.*?\*/", " ", raw, flags=re.S), flags=re.M)

    problems = []
    for cls in ("btn-pool--word-match", "drink-card-hit", "drink-name-hit"):
        if cls not in js:
            problems.append(f"cocktail-index.js never applies .{cls}")

    # The flag has to reach the chip builder (#390). A chosen chip passes
    # false on purpose: it is already selected.
    calls = re.findall(r"(?<!function )chip\(([^)]*)\)", js)
    assert calls, (
        "No calls to the pool chip builder found at all. Either it was renamed "
        "or this pattern went stale, and a scan matching nothing passes."
    )
    if len(calls) < 3:
        problems.append(
            f"only {len(calls)} chip() call sites; expected the chosen chip, the "
            f"(all) button and the ranked result to be built separately"
        )
    dropped = [c for c in calls if c.count(",") < 2]
    if dropped:
        problems.append(
            f"{len(dropped)} of {len(calls)} chip() call sites pass no word-match "
            f"argument, so those chips can never be marked: {dropped}"
        )

    # Matched as a whole class name: a plain `in` check is satisfied by
    # `.drink-name-hit-unused`, so a rule renamed out of use would pass.
    css = (site / "assets" / "css" / "cocktails.css").read_text(encoding="utf-8")
    for cls in ("btn-pool--word-match", "drink-card-hit", "drink-name-hit"):
        if not re.search(rf"\.{re.escape(cls)}(?![\w-])", css):
            problems.append(f".{cls} is applied by cocktail-index.js but styled nowhere")

    assert not problems, (
        "The drinks index lights something up that nothing styles, or stops "
        "lighting it at all:\n  " + "\n  ".join(problems)
        + "\n\nA card that survived a filter it cannot explain is the one thing "
          "MANUAL §9.13 says a card must never be, and a candidate pool that "
          "marks nothing is issue #390 on the other index."
    )


# --- a form control nobody gave a colour (#654) -------------------------------
# An `<input>` does not inherit `color`: it takes the UA stylesheet's
# near-black `fieldtext` whatever its ancestors say, so on an inverted palette
# its text is invisible while the build and the class-has-a-rule scan stay
# green. `color` only is the cheap version of this check.

# Controls that put TEXT on the screen. A checkbox, radio, range or hidden input
# paints no glyphs, so `color` is not what makes it visible and requiring one
# would be noise. `file` is excluded because its label is browser chrome.
TEXTLESS_INPUT_TYPES = {
    "hidden", "checkbox", "radio", "range", "color", "file", "image", "reset",
}

FORM_CONTROL = re.compile(r"<(input)\b([^>]*?)/?>", re.I)
# Buttons, selects and textareas WRAP their content, and the content is the
# question -- see `_paints_text` below.
WRAPPING_CONTROL = re.compile(
    r"<(button|select|textarea)\b([^>]*)>(.*?)</\1\s*>", re.I | re.S)
ATTR = re.compile(r"""(\w[\w-]*)\s*=\s*['"]([^'"]*)['"]""")


def _paints_text(inner_html: str) -> bool:
    """Does this control put glyphs on the screen?

    `<button class="cocktail-toggle-track">` holds one empty span and is drawn
    in background and border alone, so asking it for a `color` is the wrong
    question. Tags are stripped and a real character looked for; `aria-label`
    is not counted, because it is never painted.
    """
    return bool(re.sub(r"<[^>]*>", "", inner_html).strip())

# A `color:` declaration, and not `background-color`, `border-color`,
# `accent-color`, `caret-color` or a `--custom-color` property: the lookbehind
# is what separates them.
COLOR_DECL = re.compile(r"(?<![-\w])color\s*:")


def _rules(css: str):
    """(selector, body) for every rule in a compiled stylesheet.

    Not a parser: an at-rule's inner rules come back with the outer selector
    text attached to the first. That can only make the test more forgiving;
    it never invents a `color` that is not there.
    """
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        yield match.group(1).strip(), match.group(2)


def _colouring_selectors(css: str):
    """Every selector whose rule declares an explicit `color`."""
    return [sel for sel, body in _rules(css) if COLOR_DECL.search(body)]


def _controls_on(html: str):
    """(tag, id, classes, input_type) for every form control that paints text."""
    out = []
    for tag, attrs in FORM_CONTROL.findall(html):
        a = dict(ATTR.findall(attrs))
        itype = (a.get("type") or "text").lower()
        # An input has no content to inspect, so the TYPE is the whole test: a
        # text or number box displays what you type and a checkbox does not.
        if itype in TEXTLESS_INPUT_TYPES:
            continue
        out.append(("input", a.get("id", ""), a.get("class", "").split(), itype))
    for tag, attrs, inner in WRAPPING_CONTROL.findall(html):
        if not _paints_text(inner):
            continue
        a = dict(ATTR.findall(attrs))
        out.append((tag.lower(), a.get("id", ""), a.get("class", "").split(),
                    (a.get("type") or tag).lower()))
    return out


def test_every_form_control_is_given_a_colour(site):
    """Every text-bearing control on a built page has an explicit `color`. #654.

    The match is generous: a control counts as coloured if any colouring
    selector names its id, one of its classes or its bare tag. That
    over-accepts across pages; a stricter version needs a cascade resolver.
    `_dev/` pages never ship and are out of scope.
    """
    pages = [p for p in sorted(site.rglob("*.html"))
             if p.relative_to(site).parts[0] not in {"dev", "_dev"}]
    assert pages, "the build produced no pages outside _dev/."

    # One stylesheet read per sheet, not per page.
    cache = {}

    def colouring_for(html):
        # Not anchored on `.css'`: _layouts/default.html links the sheet with
        # a `?v=` cache-buster, and the named group drops it.
        link = re.search(
            r"""href=['"][^'"]*assets/css/(?P<name>[^'"/?]+\.css)""", html)
        if not link:
            return None, None
        name = link.group("name")
        if name not in cache:
            path = site / "assets" / "css" / name
            cache[name] = _colouring_selectors(path.read_text(encoding="utf-8")) \
                if path.exists() else []
        return name, cache[name]

    problems = []
    seen = set()
    checked = 0
    for page in pages:
        html = page.read_text(encoding="utf-8", errors="replace")
        controls = _controls_on(html)
        if not controls:
            continue
        sheet, selectors = colouring_for(html)
        if selectors is None:
            continue  # no stylesheet linked; a different test owns that
        for tag, cid, classes, itype in controls:
            key = (sheet, tag, cid, tuple(sorted(classes)), itype)
            if key in seen:
                continue
            seen.add(key)
            checked += 1
            names = [f"#{cid}"] if cid else []
            names += [f".{c}" for c in classes]
            if any(any(n in sel for n in names) for sel in selectors):
                continue
            # Fall back to a bare-tag rule: `input, select { color: ... }`.
            if any(re.search(rf"(^|[\s,>+~]){tag}([\s,.:\[]|$)", sel)
                   for sel in selectors):
                continue
            where = page.relative_to(site)
            label = f"#{cid}" if cid else (".".join(classes) or "(no class)")
            problems.append(
                f"<{tag} type={itype}> {label}  in {where}  ({sheet})"
            )

    assert checked, (
        "No text-bearing form controls were found on any built page. The "
        "site has lost its search boxes and buttons, or this scan has gone "
        "stale -- and a scan that finds nothing passes."
    )
    assert not problems, (
        "These form controls have no explicit `color` anywhere in the compiled "
        "stylesheet -- not by id, not by class, not by tag. A control that is "
        "not given one takes the UA stylesheet's near-black `fieldtext` "
        "whatever its ancestors say, which is invisible on a dark ground and "
        "makes no build or test go red (#654):\n  " + "\n  ".join(sorted(problems))
    )


def test_the_colour_declaration_pattern_does_not_count_background_color():
    """The guard's own guard: `background-color` must not read as `color`.

    If it did, the test above would pass on an input with a background and no
    colour, which is #654 itself.
    """
    assert COLOR_DECL.search("color: red")
    assert COLOR_DECL.search("a { color:var(--x) }")
    assert not COLOR_DECL.search("background-color: red")
    assert not COLOR_DECL.search("border-color: red")
    assert not COLOR_DECL.search("accent-color: red")
    assert not COLOR_DECL.search("caret-color: red")
    assert not COLOR_DECL.search("--brand-color: red")


def test_paints_text_skips_the_switch_and_keeps_the_buttons():
    """`_paints_text` skips the empty switch and nothing with a word in it.

    It is the one place the colour guard decides not to look, so over-skipping
    would turn the whole guard green.
    """
    # The drink page's read/make switch.
    assert not _paints_text('<span class="cocktail-toggle-knob"></span>')
    assert not _paints_text("")
    assert not _paints_text("   \n  ")

    # Everything with a word in it still counts, however it is wrapped.
    assert _paints_text("make it")
    assert _paints_text('<span class="btn-label">clear</span>')
    assert _paints_text('&times; clear')
    assert _paints_text('deal again <span class="universe-again-icon">&#8635;</span>')


def test_a_control_with_no_colouring_rule_is_reported():
    """The colour guard, run on a stylesheet that does not colour the control.

    Without this the scan, the selector match and the fallback could all break
    at once and still pass on a repo where everything happens to be coloured.
    """
    css = ".drink-search-input { background: #000; border: 1px solid #333; }"
    selectors = _colouring_selectors(css)
    assert selectors == [], (
        "a rule declaring only `background` was read as declaring `color`."
    )

    css_fixed = css + " .drink-search-input { color: #eee; }"
    assert any(".drink-search-input" in s for s in _colouring_selectors(css_fixed))


# --- a mark that is computed, carried, and then styled away (#653) ------------
# A class can have a rule and a later, more specific rule turning it off, which
# a "does the class have a rule" scan cannot see. So this reads the compiled
# CSS and resolves per picker section: a sectioned rule (0,2,0) beats the bare
# class (0,1,0) wherever it sits in the file.

WORD_MATCH = ".btn-pool--word-match"
PICKER_SECTIONS = ("drink-search--include", "drink-search--exclude")

# The mark is a stroke (@mixin index-chip-word-match). What cancels a stroke is
# its shorthand or its width going to zero; `-color` is not matched, because
# the hover rule moves that without unstyling anything.
DECORATION = re.compile(
    r"(?<![-\w])-webkit-text-stroke(?:-width)?\s*:\s*([^;}]+)")


def _is_no_stroke(value):
    return value.strip() in ("0", "none") or value.strip().startswith(("0 ", "0px"))


def _word_match_decoration(css: str):
    """Effective stroke for the mark, per picker section.

    Returns {section: value|None}. `None` means no rule in that section's
    cascade says anything, so the base rule stands.
    """
    base = None
    per_section = {name: None for name in PICKER_SECTIONS}

    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector, body = match.group(1).strip(), match.group(2)
        if WORD_MATCH not in selector:
            continue
        decl = DECORATION.findall(body)
        if not decl:
            continue
        value = decl[-1].strip()
        sectioned = [s for s in PICKER_SECTIONS if s in selector]
        if sectioned:
            for name in sectioned:
                per_section[name] = value
        else:
            base = value

    return base, per_section


def test_the_word_match_mark_survives_in_both_pickers(site):
    """HAS TO HAVE and LEAVE OUT must both paint the prefix-match mark. #653.

    The mark is a stroke in both pools; a section may restate it in its own
    colour but may not cancel it.
    """
    css_path = site / "assets" / "css" / "cocktails.css"
    assert css_path.exists(), "cocktails.css was not built."
    css = css_path.read_text(encoding="utf-8")

    assert WORD_MATCH in css, (
        f"`{WORD_MATCH}` has no rule in the compiled cocktails stylesheet at "
        f"all, so neither picker marks a word match. cocktail-index.js still "
        f"emits the class."
    )

    base, per_section = _word_match_decoration(css)
    assert base and not _is_no_stroke(base), (
        f"the base `{WORD_MATCH}` rule declares -webkit-text-stroke "
        f"{base!r}. The mark IS the stroke; without it the class is emitted "
        f"and paints nothing."
    )

    cancelled = [
        f"{name}: -webkit-text-stroke {value!r}"
        for name, value in per_section.items()
        if value is not None and _is_no_stroke(value)
    ]
    assert not cancelled, (
        "One picker cancels the word-match mark that the other one shows. This "
        "is #653 returning: the flag is computed, carried to the call site and "
        "then styled away on one side, so the same three letters typed into "
        "HAS TO HAVE and LEAVE OUT mark different chips.\n  "
        + "\n  ".join(cancelled)
    )


def test_both_pickers_get_the_word_match_class_from_one_builder():
    """`btn-pool--word-match` is applied by one shared builder. #390.

    The CSS test above catches the mark being styled away in one pool; this
    catches it never being applied to one.
    """
    js = (ROOT / "assets" / "js" / "cocktail-index.js").read_text(encoding="utf-8")
    applications = re.findall(r"btn-pool--word-match", js)
    assert applications, (
        "cocktail-index.js no longer applies `btn-pool--word-match` anywhere, "
        "so no chip in either picker is marked."
    )
    assert len(applications) == 1, (
        f"`btn-pool--word-match` is applied in {len(applications)} places in "
        f"cocktail-index.js. It was one shared builder, which is what made the "
        f"two pickers agree; two call sites is how they start to differ. If "
        f"this split on purpose, both sites need their own test."
    )


def test_the_decoration_resolver_sees_a_cancelling_rule():
    """The resolver's own guard: it sees a sectioned rule cancelling the mark.

    Without this it could return `None` for everything and the test above
    would pass on a stylesheet that cancels the mark in both pickers.
    """
    good = (".btn-pool--word-match { color: #f0c; -webkit-text-stroke: 0.5px #f0c; }"
            ".drink-search--exclude .btn-pool--word-match { color: #eee; }")
    base, sections = _word_match_decoration(good)
    assert base == "0.5px #f0c"
    assert sections["drink-search--exclude"] is None

    # #653's shape: one section styling it away.
    bad = good + (".drink-search--exclude .btn-pool--word-match "
                  "{ -webkit-text-stroke: 0; }")
    base, sections = _word_match_decoration(bad)
    assert _is_no_stroke(sections["drink-search--exclude"]), (
        "the resolver did not see a sectioned rule cancelling the mark."
    )

    # The longhand cancels identically and must not slip past.
    longhand = good + (".drink-search--include .btn-pool--word-match "
                       "{ -webkit-text-stroke-width: 0px; }")
    _, sections = _word_match_decoration(longhand)
    assert _is_no_stroke(sections["drink-search--include"])

    # A section restating the stroke in its own colour is not a cancellation.
    restated = good + (".drink-search--exclude .btn-pool--word-match "
                       "{ -webkit-text-stroke: 0.5px #aaa; }")
    _, sections = _word_match_decoration(restated)
    assert not _is_no_stroke(sections["drink-search--exclude"])

    # `-webkit-text-stroke-color` is not the mark going away.
    assert DECORATION.search("-webkit-text-stroke-color: red") is None


# --- the shopping list's built data (#801) ------------------------------------
# The aisle matcher is Ruby (_plugins/food_shopping.rb) and runs inside Jekyll,
# so the built page is the only place it can be checked; a Python copy of the
# rule could pass while the site is wrong.

def _shopping_blob(site, page="index.html"):
    """The #recipe-ingredients JSON off the built food index."""
    html = (site / "food" / page).read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="recipe-ingredients">(.*?)</script>',
        html, re.S)
    assert match, (
        "the built food index has no #recipe-ingredients block, so the shopping "
        "list has no data and silently shows nothing."
    )
    return json.loads(match.group(1))


def test_every_recipe_reaches_the_page_with_a_portion_count(site):
    """Every recipe in the blob has a portion count and names its yield's key.

    tests/test_food_shopping.py proves each recipe resolves to a number from
    the data files; this proves the number reached the page, which fails if
    the plugin stops running or returns early. Drafts are not let off (#815).
    `k` keeps a `makes:` from printing behind the word "serves".
    """
    blob = _shopping_blob(site)
    assert len(blob) > 80, (
        f"only {len(blob)} recipes in the shopping-list blob; the collection has "
        "86 plus the magic bag. The plugin or the row gate has changed."
    )

    unscalable = sorted(u for u, r in blob.items() if not r.get("p"))
    assert not unscalable, (
        "these recipes reached the page with no portion count, so the shopping "
        f"list can draw no box for them: {unscalable}. Add `serves_estimate:` "
        "to the recipe."
    )

    empty = sorted(u for u, r in blob.items() if not r.get("i"))
    assert not empty, (
        f"these recipes contribute nothing to a shopping list: {empty}"
    )

    unlabelled = sorted(u for u, r in blob.items()
                        if r.get("y") and r.get("k") not in ("serves", "makes"))
    assert not unlabelled, (
        "these recipes carry a yield with no `k` saying which key it came "
        f"from, so it will print behind the wrong word: {unlabelled}"
    )


def test_the_production_shopping_blob_holds_exactly_what_has_a_row(prod_site):
    """One row, one entry, in the build that ships.

    An extra entry is the direction that matters: it can be a draft's or a
    held-back recipe's ingredient list published on the live index, which only
    the production build shows (#235's shape). A row with no entry is a
    shortlisted recipe the shopping list silently ignores.
    """
    blob = _shopping_blob(prod_site)
    html = (prod_site / "food" / "index.html").read_text(encoding="utf-8")
    rows = set(re.findall(r'<li data-url="([^"]*)"', html))

    assert rows, "no recipe rows on the built production index at all."
    assert set(blob) - rows == set(), (
        "the shopping-list blob carries recipes that have no row on the "
        f"production index: {sorted(set(blob) - rows)}. The row gate and the "
        "blob's gate have drifted apart."
    )
    assert rows - set(blob) == set(), (
        "these rows can be shortlisted but contribute nothing to a shopping "
        f"list: {sorted(rows - set(blob))}"
    )


def test_the_shopping_list_assigns_an_aisle_to_almost_everything(site):
    """`other` stays small, and every stamped aisle is a declared one.

    An unmatched ingredient is not a bug, but `other` growing is the only
    signal that _data/food/aisles.yml needs a keyword. The ratchet is loose:
    it catches a keyword table that has stopped being loaded. Cross-recipe
    links are sent to `other` on purpose and are counted.
    """
    blob = _shopping_blob(site)
    declared = {a["key"] for a in yaml.safe_load(
        (ROOT / "_data" / "food" / "aisles.yml").read_text(encoding="utf-8"))["order"]}

    unknown = []
    other = {"published": [], "drafts": []}
    total = {"published": 0, "drafts": 0}
    for url, recipe in blob.items():
        where = "drafts" if "/food/drafts/" in url else "published"
        for ing in recipe["i"]:
            total[where] += 1
            if ing["s"] not in declared:
                unknown.append(f"{ing['n']!r} -> {ing['s']!r} ({url})")
            elif ing["s"] == "other":
                other[where].append(f"{ing['n']!r} ({url})")

    assert not unknown, (
        "ingredients were stamped with an aisle that _data/food/aisles.yml does "
        "not declare: " + "; ".join(unknown)
    )
    assert total["published"] > 700, (
        f"only {total['published']} published ingredients emitted; the "
        "collection has 778."
    )
    assert len(other["published"]) <= 20, (
        f"{len(other['published'])} of {total['published']} PUBLISHED "
        "ingredients have no aisle, which is more than this has ever needed. "
        "Add keywords to _data/food/aisles.yml:\n  "
        + "\n  ".join(sorted(other["published"]))
    )

    # Drafts are measured separately and held to a looser line: they are
    # absent in CI and in a fresh worktree, so this half runs only where they
    # are cloned, and it detects a table that stopped being read.
    if total["drafts"]:
        share = len(other["drafts"]) / total["drafts"]
        assert share <= 0.15, (
            f"{len(other['drafts'])} of {total['drafts']} DRAFT ingredients "
            f"({share:.0%}) have no aisle. Drafts are allowed a long tail -- "
            "they are unfinished and Helen adds them in batches -- but this is "
            "far enough out to suggest the keyword table is not being read."
        )


def test_water_is_never_on_a_shopping_list(site):
    """`never` drops plain water, and matches on the whole name.

    The second assertion is the one that bites: an ingredient that merely
    contains the word is still something you buy.
    """
    blob = _shopping_blob(site)
    names = [ing["n"].strip().lower()
             for recipe in blob.values() for ing in recipe["i"]]

    assert "water" not in names and "cold water" not in names, (
        "plain water is on the shopping list. _data/food/aisles.yml's `never` "
        "list is not being applied."
    )
    assert any("water" in name for name in names), (
        "no ingredient mentioning water survived at all, so `never` is matching "
        "as a keyword rather than on the whole name -- which would also drop "
        "'water mixed with 3 tsp cornstarch', a real ingredient."
    )


def test_the_shopping_list_and_the_ingredient_index_agree_on_a_name(site):
    """The shopping list and the index's exclusion vocabulary name things alike.

    food/index.html derives `data-all-ingredients` in Liquid and the plugin
    derives its names in Ruby; both cut an item at its first comma or open
    bracket. A cross-recipe link is the one legitimate difference (#273: the
    index drops it, the list keeps it), and is skipped by its `other` aisle.
    """
    blob = _shopping_blob(site)
    html = (site / "food" / "index.html").read_text(encoding="utf-8")

    rows = dict(re.findall(
        r'<li data-url="([^"]*)"[^>]*data-all-ingredients="([^"]*)"', html))
    assert len(rows) > 80, f"only {len(rows)} rows found on the built index."

    problems = []
    for url, recipe in blob.items():
        indexed = rows.get(url)
        if indexed is None:
            problems.append(f"{url} is in the shopping blob but has no row")
            continue
        # The attribute is `|`-delimited and self-delimiting at both ends.
        vocabulary = {w for w in html_module.unescape(indexed).split("|") if w}
        for ing in recipe["i"]:
            if ing["s"] == "other":
                continue    # a cross-recipe link, or genuinely unclassified
            if ing["n"].lower() not in vocabulary:
                problems.append(
                    f"{url}: the shopping list calls it {ing['n']!r}, which is "
                    f"not in that row's own ingredient vocabulary")

    assert not problems, (
        "the shopping list and the exclusion index disagree about an "
        "ingredient's name:\n  " + "\n  ".join(problems[:20])
    )


# --- "if you liked this, how about ..." on a drink page: four drinks (#927) ---
# Checked in the production build: `_config_local.yml` sets
# `show_awaiting_fix`, which switches _plugins/publish_gate.rb off, so a local
# row can legitimately offer a drink that is not live. A drink page shows four
# and a food recipe page three.

RELATED_SECTION = re.compile(r'<ul class="cocktail-related drink-cards">(.*?)</ul>', re.S)
# The name's link only: each card also carries chip links to the filtered
# index (`<a class="drink-card-mood ...">`), which are not offered drinks.
RELATED_LINK = re.compile(r'<span class="drink-card-tape-word"><a href="([^"]+)">')


def _drink_pages(built_site):
    """Every built drink page, found by walking the output rather than named.

    A page the walk cannot see is never checked, so callers assert the count
    is plausible.
    """
    return sorted((built_site / "cocktails" / "recipes").rglob("index.html"))


def test_every_published_drink_page_offers_four_other_published_drinks(prod_site):
    """#927. Exactly four, never itself, and every one of them a real page.

    Exactly four, not "at most": the template emits only candidates sharing a
    mood or a generic, so a drink sharing nothing would render a short row on
    its own page alone. `scripts/related_drinks.py` names which drink ran out of
    candidates. The template excludes `page.url`, so no row offers itself.
    """
    pages = _drink_pages(prod_site)
    assert len(pages) > 20, (
        f"only {len(pages)} drink pages in the production build, which is too "
        "few for this collection -- the corpus walk is looking in the wrong "
        "place, or the publish gate has held nearly everything back."
    )

    live = {"/" + str(p.relative_to(prod_site).parent).replace("\\", "/") + "/"
            for p in pages}
    baseurl = "/helen-triages"
    problems = []

    for page in pages:
        url = "/" + str(page.relative_to(prod_site).parent).replace("\\", "/") + "/"
        text = page.read_text(encoding="utf-8")
        section = RELATED_SECTION.search(text)
        if not section:
            problems.append(f"{url}: no related-drinks row at all")
            continue

        hrefs = RELATED_LINK.findall(section.group(1))
        if len(hrefs) != 4:
            problems.append(f"{url}: {len(hrefs)} related drinks, expected 4")

        for href in hrefs:
            target = href[len(baseurl):] if href.startswith(baseurl) else href
            if target == url:
                problems.append(f"{url}: offers itself as a related drink")
            if target not in live:
                problems.append(
                    f"{url}: offers {href}, which is not a published drink page")

    assert not problems, (
        "the related-drinks row (#927) is wrong on these pages:\n  "
        + "\n  ".join(problems[:20])
    )


# --- the same row on a recipe page: three recipes (#1005) ---------------------
# `scripts/related_recipes.py` is where to look when it fires.

RELATED_RECIPES_SECTION = re.compile(
    r'<ul class="recipe-list recipe-related">(.*?)</ul>', re.S)
# The TITLE's link only: each row also carries badge links to the filtered
# index, and those must not count as offered recipes.
RELATED_RECIPE_LINK = re.compile(r'<a class="recipe-title-link" href="([^"]+)">')


# --- the search-for-anything box's index (#1050) ------------------------------
# food/search.json and cocktails/search.json are generated from the same gated
# list each index renders. A page in the JSON that was not built is a dropdown
# result that 404s; a built page missing from it is one the box cannot find.

SEARCH_SITES = {
    "food": ["food/recipes", "food/magic-bag"],
    "cocktails": ["cocktails/recipes"],
}


@pytest.mark.parametrize("site_key", sorted(SEARCH_SITES))
def test_the_search_index_lists_exactly_the_published_pages(prod_site, site_key):
    path = prod_site / site_key / "search.json"
    assert path.exists(), (
        f"{site_key}/search.json was not built. The search box on every "
        f"{site_key} page fetches it and, without it, is only a name search."
    )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"{site_key}/search.json is not valid JSON ({exc}). A title or "
            "ingredient with a character the template hand-quoted, most likely "
            "-- every value goes through `jsonify`."
        ) from exc

    baseurl = "/helen-triages"
    assert data["home"] == f"{baseurl}/{site_key}/"
    assert data["items_label"], "the pages' group needs a label, placeholder or not"
    assert data["groups"], "no word groups at all -- the dropdown would offer names only"
    for group in data["groups"]:
        assert group["kind"] and group["label"] and group["param"] and group["field"], group
        # `param` must be a kind filter-state.js reads, or the index ignores the link.
        grammar = (ROOT / "assets" / "js" / "filter-state.js").read_text(encoding="utf-8")
        kinds = re.search(r"var KINDS = \[([^\]]+)\];", grammar).group(1)
        assert f"'{group['param']}'" in kinds, (
            f"{site_key}/search.json links {group['kind']} results with "
            f"?{group['param']}=, which filter-state.js's KINDS does not read."
        )

    listed = {item["u"] for item in data["items"]}
    built = set()
    for folder in SEARCH_SITES[site_key]:
        for page in (prod_site / folder).rglob("index.html"):
            built.add(baseurl + "/" + str(page.relative_to(prod_site).parent).replace("\\", "/") + "/")
    assert len(built) > 20, (
        f"only {len(built)} built pages under {SEARCH_SITES[site_key]} -- the "
        "corpus walk is looking in the wrong place."
    )
    assert listed == built, (
        f"{site_key}/search.json and the built pages disagree.\n"
        f"  in the JSON but not built (a result that 404s): {sorted(listed - built)}\n"
        f"  built but not in the JSON (a page the box cannot find): {sorted(built - listed)}\n"
        "The JSON copies the index's own list-building Liquid; whichever "
        "changed, change the other in the same commit."
    )
    for item in data["items"]:
        assert item["t"], f"{item['u']} has no title in the search index"


def test_the_drinks_search_offers_no_joined_ingredient_label(prod_site):
    """No `ing` term in the feed is a joined "X or Y" label -- #1051, #1130.

    A disjunctive `generic` prints as one joined label, which names no single
    HAS TO HAVE chip, and `?ing=` matches a chip whole. The feed offers each
    half instead. The expected halves come from each row's own generics
    through `card_names`, never from splitting the label on " or ":
    `card_name_joins` can rewrite a label so that a split yields no chip.
    """
    feed = json.loads((prod_site / "cocktails" / "search.json")
                      .read_text(encoding="utf-8"))
    offered = {term for item in feed["items"] for term in item.get("ing", [])}
    assert offered, "the drinks search feed offers no ingredients at all."

    index = (prod_site / "cocktails" / "index.html").read_text(encoding="utf-8")
    printed = set(re.findall(
        r'<span class="drink-card-ing" data-ing="[^"]*">(.*?)</span>', index, re.S))
    joined = {re.sub(r"<[^>]+>", "", label).strip() for label in printed
              if " or " in re.sub(r"<[^>]+>", "", label)}

    leaked = sorted(joined & offered)
    assert not leaked, (
        "the drinks search feed offers joined label(s) that name no chip:\n  "
        + "\n  ".join(leaked)
        + "\n\nEach would take a reader to an index filtered to nothing. "
          "cocktails/search.json must offer `ing.search_labels` -- the label "
          "in the pieces a filter can apply -- and never `ing.label` for a "
          "row with more than one generic."
    )

    # And the parts are actually there (#1130): offering nothing at all would
    # pass the check above vacuously.
    import yaml as _yaml

    front_matter = re.compile(r"\A---\n(.*?)\n---", re.S)
    vocab = _yaml.safe_load(
        (ROOT / "_data" / "cocktails" / "ingredients.yml").read_text(encoding="utf-8"))
    card_names = vocab.get("card_names") or {}
    hidden = set(vocab.get("not_on_cards") or [])

    offered_by_slug = {
        item["u"].rstrip("/").rsplit("/", 1)[-1]: item.get("ing", [])
        for item in feed["items"]
    }

    missing, checked = [], 0
    for path in sorted((ROOT / "_cocktail_recipes").glob("*.md")):
        match = front_matter.match(path.read_text(encoding="utf-8"))
        if not match or path.stem not in offered_by_slug:
            continue
        drink = _yaml.safe_load(match.group(1)) or {}
        for ing in (drink.get("ingredients") or []):
            if not isinstance(ing, dict):
                continue
            raw = ing.get("generic")
            generics = [str(g) for g in (raw if isinstance(raw, list) else [raw]) if g]
            if len(generics) < 2:
                continue
            # A row every one of whose generics is hidden is dropped from the
            # card altogether, so it offers nothing and owes nothing.
            wanted = [card_names.get(g, g) for g in generics if g not in hidden]
            if not wanted:
                continue
            checked += 1
            for part in wanted:
                if part not in offered_by_slug[path.stem]:
                    missing.append(
                        f"{path.stem}: pours {generics} -> {part!r} is not offered")

    assert checked, (
        "no published drink pours more than one generic, so this half of the "
        "test checked nothing. If that is now true of the collection, say so "
        "here rather than leaving a test that reads as though it bites."
    )
    assert not missing, (
        f"across {checked} multi-generic pour(s), a part is missing from that "
        "drink's search terms:\n  " + "\n  ".join(missing)
        + "\n\nThe drink genuinely answers a HAS TO HAVE question about "
          "either (#441, 'either would do'), and the index's own picker "
          "already offers both chips -- `buildPool` in cocktail-search.js "
          "adds one per generic. The feed must agree with it."
    )


def _recipe_pages(built_site):
    return sorted((built_site / "food" / "recipes").rglob("index.html"))


def test_every_published_recipe_page_offers_three_other_published_recipes(prod_site):
    """#1005. Exactly three, never itself, and every one of them a real page.

    The template emits only a candidate sharing a star, a tag or a main
    ingredient, so a recipe unlike everything else would render a short row
    on its own page alone. A promotion or a taxonomy edit can cause it.
    """
    pages = _recipe_pages(prod_site)
    assert len(pages) > 20, (
        f"only {len(pages)} recipe pages in the production build, which is too "
        "few for this collection -- the corpus walk is looking in the wrong "
        "place, or the publish gate has held nearly everything back."
    )

    live = {"/" + str(p.relative_to(prod_site).parent).replace("\\", "/") + "/"
            for p in pages}
    baseurl = "/helen-triages"
    problems = []

    for page in pages:
        url = "/" + str(page.relative_to(prod_site).parent).replace("\\", "/") + "/"
        text = page.read_text(encoding="utf-8")
        section = RELATED_RECIPES_SECTION.search(text)
        if not section:
            problems.append(f"{url}: no related-recipes row at all")
            continue

        hrefs = RELATED_RECIPE_LINK.findall(section.group(1))
        if len(hrefs) != 3:
            problems.append(f"{url}: {len(hrefs)} related recipes, expected 3")

        for href in hrefs:
            target = href[len(baseurl):] if href.startswith(baseurl) else href
            if target == url:
                problems.append(f"{url}: offers itself as a related recipe")
            if target not in live:
                problems.append(
                    f"{url}: offers {href}, which is not a published recipe page")

    assert not problems, (
        "the related-recipes row (#1005) is wrong on these pages:\n  "
        + "\n  ".join(problems[:20])
    )


def _script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _offered_slugs(text, section_re, link_re):
    section = section_re.search(text)
    if not section:
        return []
    return [href.rstrip("/").rsplit("/", 1)[-1] for href in link_re.findall(section.group(1))]


@pytest.mark.parametrize("kind", ["food", "drinks"])
def test_the_related_picks_are_the_scripts_picks_in_the_scripts_order(prod_site, kind):
    """#1090, #1183. Every built page offers exactly what
    `scripts/related_recipes.py` or `scripts/related_drinks.py` says, in the
    same order: the scripts are how a ranking is inspected, so a Liquid key
    that drifts from them makes every reading of them false."""
    if kind == "food":
        mirror = _script("related_recipes")
        corpus, moods = mirror.published(), mirror.mood_tags()
        expected = {s: mirror.picks(s, d, corpus, moods) for s, d in corpus}
        pages, section_re, link_re = (_recipe_pages(prod_site),
                                      RELATED_RECIPES_SECTION, RELATED_RECIPE_LINK)
    else:
        mirror = _script("related_drinks")
        corpus = mirror.published()
        expected = {s: [r["slug"] for r in mirror.picks(s, d, corpus)] for s, d in corpus}
        pages, section_re, link_re = _drink_pages(prod_site), RELATED_SECTION, RELATED_LINK
    built = {p.parent.name: _offered_slugs(p.read_text(encoding="utf-8"), section_re, link_re)
             for p in pages}

    assert sorted(built) == sorted(expected), (
        f"the {kind} script's published set and the build's pages differ: "
        f"only built {sorted(set(built) - set(expected))}, "
        f"only in the script {sorted(set(expected) - set(built))}. Its "
        "`published()` must read the same flags as _plugins/publish_gate.rb."
    )
    wrong = [f"{slug}: page {built[slug]}, script {expected[slug]}"
             for slug in sorted(built) if built[slug] != expected[slug]]
    assert not wrong, (
        f"{len(wrong)} {kind} page(s) offer different picks from the script:\n  "
        + "\n  ".join(wrong[:15])
    )


# --- how much liquid is in a drink (#1121, #1257) -----------------------------
# One sentence about volume is printed: the footer's "in a serving of Y ml",
# one glass, which never moves with the scaler. The plugin's batch figure is
# on the page unprinted, as `data-total-ml` on `.cocktail-scale-controls`, for
# scripts/glass_fit_report.py and for these tests. Production, so `prod_site`.

# group(1) is the figure.
SCALE_TOTAL = re.compile(
    r'<div class="cocktail-scale-controls" data-total-ml="([^"]*)"')
UNITS_LINE = re.compile(r'<p class="cocktail-units"(.*?)</p>', re.S)
# "(undiluted)" is required (#1291): a page stating millilitres without it
# fails every test that reads this pattern.
SERVING_OF = re.compile(
    r"in (?:a serving|each of \d+ servings) of ([\d.]+) ml \(undiluted\)\.")

# The drinks that state no volume, pinned by name: ones whose excluded amounts
# are the drink, so a figure would be wrong rather than rough (`volume_for` in
# _plugins/cocktail_units.rb). A topped drink is not one of them. A ratchet in
# both directions: a new name means a drink lost its figure, and a name
# leaving means one gained a figure, by a data fix or by the rule weakening.
NO_VOLUME_STATED = {
    "caipirinha",
    "pear-and-rosemary-bellini",
}


def test_the_drinks_that_state_no_volume_are_exactly_the_ones_that_cannot(prod_site):
    """#1121. The drinks printing no volume are exactly the pinned ones.

    Compared against the pinned drinks that are in the build: one held back
    by the publish gate has no page to judge, and is named in the failure
    message rather than read as having gained a figure. A drink in the build
    that prints or withholds wrongly still fails.
    """
    pages = _drink_pages(prod_site)
    assert len(pages) > 20, (
        f"only {len(pages)} drink pages in the production build -- the corpus "
        "walk is looking in the wrong place."
    )

    built = {p.parent.name for p in pages}
    silent = {p.parent.name for p in pages
              if not SCALE_TOTAL.search(p.read_text(encoding="utf-8"))}

    # The pinned drinks that are actually on the site. One that is not is dark
    # -- gated off by `awaiting_fix`/`proofread` -- and has no page to judge.
    expected = NO_VOLUME_STATED & built
    dark = sorted(NO_VOLUME_STATED - built)

    assert silent == expected, (
        (f"  ({', '.join(dark)}: not in the production build, so set aside "
         f"-- gated off the site, and unjudgeable until back on it)\n"
         if dark else "") +
        "the set of drinks printing no volume has moved.\n"
        f"  newly silent (lost a figure they used to print): "
        f"{sorted(silent - expected)}\n"
        f"  newly speaking (gained one): {sorted(expected - silent)}\n"
        "`volume_for` in _plugins/cocktail_units.rb has the rule: a drink says "
        "nothing only when its excluded ingredients ARE the drink, so a figure "
        "would be wrong rather than rough. A topped drink is NOT such a drink: "
        "its top is sized from its glass by `fitted_top_ml` (#1179), and falls "
        "back to the midpoint of its declared range only where the glass gives "
        "no answer."
    )


def test_a_drink_with_no_volume_keeps_the_units_sentence_it_had_before(prod_site):
    """A drink with no volume keeps the units sentence without the ml tail.

    Where the serving volume would be wrong the line ends "in a serving."
    (#753) and states no figure and no hedge.
    """
    problems = []
    for page in _drink_pages(prod_site):
        slug = page.parent.name
        if slug not in NO_VOLUME_STATED:
            continue
        units = UNITS_LINE.search(page.read_text(encoding="utf-8"))
        if not units:
            continue
        if SERVING_OF.search(units.group(1)) or " ml." in units.group(1):
            problems.append(f"{slug}: states a serving volume it cannot know")
        elif "in a serving." not in units.group(1) \
                and "servings." not in units.group(1):
            problems.append(f"{slug}: {' '.join(units.group(1).split())}")

    assert not problems, (
        "a drink with no stated volume must keep #753's own sentence:\n  "
        + "\n  ".join(problems)
    )


def test_no_drink_page_prints_a_batch_volume(prod_site):
    """No drink page prints an "Approximately X ml" line under the scaler. #1257.

    #1121 asked for that line and #1257 removed it; this stops the older
    ruling being restored in good faith.

    The words are looked for between the scaler and the method only: an
    ingredient note of Helen's ("Approximately 90 ml for this one.") sits
    above the scaler and is not a batch line.
    """
    offenders = []
    for page in _drink_pages(prod_site):
        html = page.read_text(encoding="utf-8")
        start = html.find('class="cocktail-scale-controls"')
        end = html.find('class="cocktail-method', start)
        scaler = html[start:end] if start != -1 else ""
        if "cocktail-scale-total" in html or re.search(r"Approximately\s", scaler):
            offenders.append(page.parent.name)
    assert not offenders, (
        "these drink pages print a batch volume line again: "
        f"{sorted(offenders)[:10]}\nHelen removed it (#1257). The figure "
        "lives on as `data-total-ml` on `.cocktail-scale-controls`, unprinted."
    )


def test_the_volume_attribute_agrees_with_the_footer_and_nothing_else_carries_it(prod_site):
    """`data-total-ml` sits on the scaler's controls and agrees with the footer.

    If it appeared on `.cocktail-units`, a per-serving figure would be one
    line of JavaScript from moving with the multiple box (#1257).
    """
    problems = []
    for page in _drink_pages(prod_site):
        html = page.read_text(encoding="utf-8")
        slug = page.parent.name

        for units in UNITS_LINE.finditer(html):
            if "data-total-ml" in units.group(1):
                problems.append(f"{slug}: the units line carries data-total-ml")

        total = SCALE_TOTAL.search(html)
        if not total:
            continue

        attr = total.group(1)
        assert re.fullmatch(r"[\d.]+", attr), f"{slug}: data-total-ml={attr!r}"
        figure = float(attr)
        assert figure > 0, f"{slug}: a volume of {figure}"

        # Where a drink is one glass the footer says the same number. A punch
        # divides by `serves:` and is left out of this comparison.
        units = UNITS_LINE.search(html)
        if units and "each of" not in units.group(1):
            said = SERVING_OF.search(units.group(1))
            if said and float(said.group(1)) != figure:
                problems.append(
                    f"{slug}: data-total-ml says {figure} ml and the units "
                    f"line says {said.group(1)} ml for the same single glass")

    assert not problems, (
        "the two volume figures on a drink page have come apart:\n  "
        + "\n  ".join(problems[:20])
    )


POUR_USE = re.compile(r'<span class="cocktail-use">')
# The direction's one legal home: the LAST child of the amount cell, straight
# after the amount span's closing tag and never inside it.
POUR_USE_UNDER_AMOUNT = re.compile(
    r'<span class="cocktail-measure">'
    r'(?:<span class="cocktail-amount"[^>]*>[^<]*</span>)?'
    r'<span class="cocktail-use">\([a-z]+\)</span></span>'
)

# #1132. One ingredient row's amount and name, as the page prints them. The
# amount span may carry attributes (a quiet row does), the name may hold the
# `.cocktail-unit-in-name` slot, and the bottle and "(optional)" that can
# follow the name are deliberately outside the second group.
POUR_AMOUNT_AND_NAME = re.compile(
    r'<span class="cocktail-amount"(?P<attrs>[^>]*)>(?P<amount>[^<]*)</span>'
    r'(?:<span class="cocktail-use">[^<]*</span>)?</span>\s*'
    r'<span class="cocktail-item"><span class="cocktail-item-name">'
    r'(?P<name>(?:[^<]|<span class="cocktail-(?:style-or|unit-in-name)">[^<]*</span>)*)</span>'
)


def _fold_word(word):
    """`cubes` and `cube`, `leaves` and `leaf`: one word. For the check below."""
    w = word.lower()
    if w == "leaves":
        return "leaf"
    if re.search(r"(sh|ch)es$", w):
        return w[:-2]
    return w[:-1] if w.endswith("s") and not w.endswith("ss") else w


def test_no_drink_page_says_a_unit_twice(prod_site):
    """#1132. No row prints a unit its ingredient's name already says, or `each`.

    The layout prints the number alone and leaves the unit to the name;
    `data-amount` still holds what the file says, which the scaler reads.
    Every built page is read, and the Classic Champagne Cocktail is checked
    by name so a matcher that has stopped matching cannot pass.
    """
    pages = _drink_pages(prod_site)
    assert len(pages) > 20, f"only {len(pages)} drink pages were built"

    problems, rows, quiet = [], 0, {}
    for page in pages:
        html = page.read_text(encoding="utf-8")
        for match in POUR_AMOUNT_AND_NAME.finditer(html):
            rows += 1
            amount = match.group("amount").split()
            name = re.sub(r"<[^>]+>", " ", match.group("name")).split()
            if "data-unit-quiet" in match.group("attrs"):
                quiet[page.parent.name] = (
                    " ".join(amount), " ".join(name), match.group("attrs").strip())
            if len(amount) != 2 or not name:
                continue
            if amount[1] == "each":
                problems.append(f"{page.parent.name}: '{' '.join(amount)}' prints `each`")
            elif len(name) > 1 and _fold_word(amount[1]) == _fold_word(name[-1]):
                problems.append(
                    f"{page.parent.name}: '{' '.join(amount)} {' '.join(name)}' "
                    f"says '{amount[1]}' twice")

    assert rows > 200, (
        f"only {rows} ingredient rows were matched across {len(pages)} drink "
        f"pages, so POUR_AMOUNT_AND_NAME has drifted from the layout's markup "
        f"and this test is reading almost nothing."
    )
    assert not problems, (
        "a drink page prints a unit its ingredient's name already says, or "
        "prints `each` (#1132). _layouts/cocktail.html decides which rows are "
        "quiet:\n  " + "\n  ".join(problems)
    )
    assert quiet.get("classic-champagne-cocktail") == (
        "1", "sugar cube", 'data-amount="1 cube" data-unit-quiet'
    ), (
        "the Classic Champagne Cocktail should print '1' beside 'sugar cube' "
        "and keep the written '1 cube' in data-amount for the scaler; got "
        f"{quiet.get('classic-champagne-cocktail')}"
    )


def test_a_pours_direction_sits_under_its_amount(prod_site):
    """#1263. `(float)`, `(shell)`, `(rinse)`, `(muddle)` go under the amount.

    A sibling of the amount span, never a child: cocktail-scale.js reads the
    whole text of every `.cocktail-amount` as a quantity, so a direction
    inside it would make the row silently unscalable.
    """
    pages = _drink_pages(prod_site)
    assert len(pages) > 20, f"only {len(pages)} drink pages were built"

    problems, seen = [], 0
    for page in pages:
        html = page.read_text(encoding="utf-8")
        marks = len(POUR_USE.findall(html))
        placed = len(POUR_USE_UNDER_AMOUNT.findall(html))
        seen += marks
        if marks != placed:
            problems.append(
                f"{page.parent.name}: {marks} direction(s), {placed} of them "
                "directly under an amount")

    assert seen, (
        "no built drink page carries a `.cocktail-use` at all, so this checked "
        "nothing. Either no published drink has an `as:` pour any more or the "
        "layout stopped rendering it."
    )
    assert not problems, (
        "a pour's direction is not the last child of its `.cocktail-measure` "
        "cell (_layouts/cocktail.html):\n  " + "\n  ".join(problems)
    )


# The page prints `(top)` (#1217). A matcher left on another spelling matches
# nothing and every topped-drink check passes unread (#1273), so
# `_topped_pages` asserts it found one. `(splash)` is not here: the volume sum
# sizes a `(top)` alone, so only a top can be divided by `serves:`.
TOP_UP_POUR = re.compile(r'<span class="cocktail-amount">\s*\(top\)\s*</span>')


def _topped_pages(built_site):
    """Every built drink page that prints a `(top)` in its amounts.

    Never empty, asserted here rather than in each caller: finding none means
    the matcher has gone stale, not that the drinks have.
    """
    pages = [p for p in _drink_pages(built_site)
             if TOP_UP_POUR.search(p.read_text(encoding="utf-8"))]
    assert pages, (
        "no built drink page prints a `(top)` amount, so every check on topped "
        "drinks would pass without reading one. Either the amount's spelling "
        "or the layout's markup around `.cocktail-amount` has changed -- fix "
        "TOP_UP_POUR to match what the page prints now (#1273)."
    )
    return pages


# --- a `(top)` is sized from its glass (#1179) --------------------------------
# `fitted_top_ml` in _plugins/cocktail_units.rb is the rule; these read what it
# printed. Where the glass gives no answer a top falls back to the midpoint of
# its declared range.

SCALE_ATTRS = re.compile(r'<div class="cocktail-scale-controls"([^>]*)>')


def _scale_attrs(html):
    found = SCALE_ATTRS.search(html)
    assert found, "the page has no `.cocktail-scale-controls`"
    return dict(re.findall(r'data-([a-z-]+)="([^"]*)"', found.group(1)))


def _glass_top(icon, ice, family, build):
    """What the glass leaves for a top, worked here from glasses.yml.

    A second writing of the plugin's sum on purpose: the test is whether the
    two agree. The figures are read, never typed, so a change to a wash line
    or a dilution moves the expectation with it.
    """
    glasses = yaml.safe_load(
        (ROOT / "_data" / "cocktails" / "glasses.yml").read_text(encoding="utf-8"))
    rules = glasses["fit_rules"]
    capacity = glasses["typical_ml"][icon]["median"]
    wash = capacity * rules["washline"]["stemmed" if icon in rules["stemmed"] else "tumbler"]
    if ice in rules["ice_space"]:
        wash *= 1 - rules["ice_space"][ice]["low"]
    served = build * (1 + rules["dilution"][family]["low"])
    return 5 * round((wash - served) / 5)


def _midpoint(generic):
    costs = yaml.safe_load(
        (ROOT / "_data" / "cocktails" / "costs.yml").read_text(encoding="utf-8"))
    row = (costs.get("top_up_ml") or {}).get(generic)
    assert row, f"costs.yml declares no `top_up_ml` for {generic}"
    return (float(row["ml_min"]) + float(row["ml_max"])) / 2


TOP_DRINK = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'glass:\n  - "{glass}"\ngarnish:\n  - "no garnish"\n{serve}'
    'ingredients:\n  - amount: "{gin} ml"\n    generic: "London dry gin"\n'
    '  - amount: "(top)"\n    generic: "{topper}"\n'
    'method:\n  - "{method}"\n  - "Top up."\n'
    'mood:\n  - "sharp"\nnotes: []\nsource: ""\nsource_url: ""\n'
    'meta:\n  made_before: true\n  ship: "yes"\n'
    '  rewritten: true\n  awaiting_fix: false\n  proofread: true\n---\n'
)
SHAKE = "Shake the gin with ice."
STIR = "Stir the gin with ice."

TOP_CASES = {
    # slug: (glass, serve block, gin ml, topper, method,
    #        (icon, ice, family) when the glass answers, else None)
    "zzz-top-flute": ("flute", 'serve:\n  ice: "none"\n', 60, "champagne", SHAKE,
                      ("flute", "none", "shake")),
    "zzz-top-highball-cubed": ("highball", 'serve:\n  ice: "cubed"\n', 50,
                               "soda water", STIR, ("highball", "cubed", "stir")),
    # The three ways back to the house range.
    "zzz-top-no-serve": ("flute", "", 60, "champagne", SHAKE, None),
    "zzz-top-full-glass": ("flute", 'serve:\n  ice: "none"\n', 150, "champagne",
                           SHAKE, None),
    "zzz-top-punch-bowl": ("punch bowl", 'serve:\n  ice: "none"\n', 60,
                           "champagne", SHAKE, None),
}
_in_the_fixture_build({
    f"_cocktail_recipes/{slug}.md": TOP_DRINK.format(
        t=slug, glass=glass, serve=serve, gin=gin, topper=topper, method=method)
    for slug, (glass, serve, gin, topper, method, _) in TOP_CASES.items()})


def test_a_top_is_sized_from_its_glass_and_falls_back_to_the_house_range(fixture_site):
    """#1179. Capacity to the wash line, less the ice, less the watered build.

    The midpoint wherever that sum has no answer: no `serve.ice`, a build
    that already fills the glass, and a punch bowl. The page says which it
    did in `data-top-from`. Fixtures, because the published set need not hold
    a drink that falls back and a public test may never require a draft (#624).
    """
    problems = []
    for slug, (_, _, gin, topper, _, fits) in TOP_CASES.items():
        page = fixture_site / "cocktails" / "recipes" / slug / "index.html"
        assert page.exists(), f"{slug} did not build"
        attrs = _scale_attrs(page.read_text(encoding="utf-8"))
        if fits:
            want_top, want_from = _glass_top(*fits, build=gin), "glass"
            assert want_top > 0, f"{slug}: this fixture was meant to fit its glass"
        else:
            want_top, want_from = _midpoint(topper), "range"
        got = (float(attrs.get("top-ml", "nan")), attrs.get("top-from"),
               float(attrs.get("total-ml", "nan")))
        want = (float(want_top), want_from, float(gin + want_top))
        if got != want:
            problems.append(f"{slug}: (top, from, total) is {got}, expected {want}")
    assert not problems, (
        "a `(top)` is not what its glass leaves room for (`fitted_top_ml`, "
        "_plugins/cocktail_units.rb):\n  " + "\n  ".join(problems)
    )


# What was never shaken (#1244), `added_after_ml` in
# _plugins/cocktail_units.rb: an amount a step holds back or an `as: "float"`
# is in the glass undiluted; an `as: "shell"` amount is not in the glass.
AFTER_DRINK = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'glass:\n  - "collins"\ngarnish:\n  - "no garnish"\nserve:\n  ice: "cubed"\n'
    'ingredients:\n  - amount: "50 ml"\n    generic: "London dry gin"\n{pours}'
    'method:\n{steps}'
    'mood:\n  - "sharp"\nnotes: []\nsource: ""\nsource_url: ""\n'
    'meta:\n  made_before: true\n  ship: "yes"\n'
    '  rewritten: true\n  awaiting_fix: false\n  proofread: true\n---\n'
)

AFTER_CASES = {
    # slug: (extra pours, method steps, {attribute: expected or None for absent})
    "zzz-after-held-back": (
        '  - amount: "90 ml"\n    generic: "ginger beer"\n',
        ["Shake all ingredients other than the ginger beer with ice.",
         "Strain while also pouring in the ginger beer."],
        {"after-ml": "90", "aside-ml": None, "method-family": "shake"}),
    "zzz-after-short-name": (
        '  - amount: "15 ml"\n    generic: "oloroso sherry"\n',
        ["Shake all ingredients other than the sherry with ice.", "Strain."],
        {"after-ml": "15", "aside-ml": None, "method-family": "shake"}),
    "zzz-after-float-and-shell": (
        '  - amount: "15 ml"\n    generic: "blended overproof rum"\n    as: "float"\n'
        '  - amount: "25 ml"\n    generic: "blended overproof rum"\n    as: "shell"\n',
        ["Shake everything except the float with ice.", "Strain."],
        {"after-ml": "15", "aside-ml": "25", "method-family": "shake"}),
    "zzz-after-nothing": (
        "", ["Shake all ingredients with ice.", "Strain."],
        {"after-ml": None, "aside-ml": None, "method-family": "shake"}),
    # "with a few" anywhere in the shake's own sentence is a short shake.
    "zzz-after-few-pebbles": (
        "", ["Shake all ingredients with a few pebbles of crushed ice.", "Strain."],
        {"after-ml": None, "aside-ml": None, "method-family": "short_shake"}),
}
_in_the_fixture_build({
    f"_cocktail_recipes/{slug}.md": AFTER_DRINK.format(
        t=slug, pours=pours, steps="".join(f'  - "{s}"\n' for s in steps))
    for slug, (pours, steps, _) in AFTER_CASES.items()})


def test_the_page_says_what_was_never_shaken_and_how_the_method_reads(fixture_site):
    """#1244. Only what went through the shaker is watered.

    `data-after-ml` is what is in the glass undiluted and `data-aside-ml` what
    is in the recipe and not in the glass. A method names an ingredient more
    shortly than the data does ("the sherry"), so a held-back amount matches
    when either name contains the other. Fixtures, so no real recipe is pinned.
    """
    problems = []
    for slug, (_, _, want) in AFTER_CASES.items():
        page = fixture_site / "cocktails" / "recipes" / slug / "index.html"
        assert page.exists(), f"{slug} did not build"
        attrs = _scale_attrs(page.read_text(encoding="utf-8"))
        got = {key: attrs.get(key) for key in want}
        if got != want:
            problems.append(f"{slug}: {got}, expected {want}")
    assert not problems, (
        "`added_after_ml` or `method_family` (_plugins/cocktail_units.rb) read "
        "a fixture drink wrongly:\n  " + "\n  ".join(problems)
    )


def test_the_tom_collins_tops_with_what_a_highball_leaves(prod_site):
    """The Tom Collins' top is what a highball leaves, and the footer agrees.

    60 + 30 + 22.5 = 112.5 ml, short-shaken, over cubed ice in a highball. The
    expectation is worked from glasses.yml, so a re-survey moves it; what is
    pinned is that the page and the rule agree, and that the units line's
    serving is the same volume.
    """
    page = prod_site / "cocktails" / "recipes" / "tom-collins" / "index.html"
    assert page.exists(), "the Tom Collins is not in the production build"
    html = page.read_text(encoding="utf-8")
    attrs = _scale_attrs(html)

    build = 60 + 30 + 22.5
    top = _glass_top("highball", "cubed", "short_shake", build)
    assert attrs.get("top-from") == "glass", (
        "the Tom Collins' top came from the house range, not its glass: "
        f"{attrs}. It has a highball, `serve.ice: cubed` and a build that fits."
    )
    assert float(attrs["total-ml"]) == build + top, (
        f"the Tom Collins totals {attrs['total-ml']} ml; its build is {build} "
        f"and a highball leaves {top} ml for the soda, so it should be "
        f"{build + top}. The old midpoint would give {build + _midpoint('soda water')}."
    )
    units = UNITS_LINE.search(html)
    serving = units and SERVING_OF.search(" ".join(units.group(1).split()))
    assert serving and float(serving.group(1)) == build + top, (
        "the units line's serving is not the volume the scaler carries: "
        f"{serving.group(1) if serving else 'no serving printed'} against "
        f"{build + top}."
    )


def test_no_topped_drink_is_also_a_punch(prod_site):
    """No drink both tops up and declares `serves:`.

    `serve_ml` divides the whole total by `serves:`, the top included. That
    is right about alcohol and wrong about a top, which fills one glass each.
    The first topped punch must fail here: add the top after the division in
    `volume_for`, and ask Helen what the page should then say. Read off the
    built page: a `serves:` drink's units line says "in each of N servings".
    """
    offenders = []
    for page in _topped_pages(prod_site):
        units = UNITS_LINE.search(page.read_text(encoding="utf-8"))
        if units and "each of" in units.group(1):
            offenders.append(page.parent.name)

    assert not offenders, (
        "these drinks both top up and declare `serves:`, which the volume sum "
        f"does not yet handle: {sorted(offenders)}\n"
        "`volume_for` in _plugins/cocktail_units.rb divides the top by "
        "`serves:` along with everything else, so each glass is credited with "
        "a fraction of one top instead of a whole one. Add the top after the "
        "division, and say so here."
    )


def test_the_aviation_prints_the_volume_its_own_amounts_add_up_to(prod_site):
    """One anchor with a real number in it: 52.5 + 15 + 7.5 + 15 = 90 ml.

    Every other volume test checks a relationship, which would still pass if
    the plugin's arithmetic were wrong the same way in both places. If the
    Aviation's amounts change, the fix is this number.
    """
    page = prod_site / "cocktails" / "recipes" / "aviation" / "index.html"
    assert page.exists(), "the Aviation is not in the production build"
    html = page.read_text(encoding="utf-8")

    total = SCALE_TOTAL.search(html)
    assert total, "no `data-total-ml` on the Aviation's scaler controls"
    assert total.group(1) == "90", (
        f"the Aviation totals {total.group(1)} ml; its amounts are "
        "52.5 + 15 + 7.5 + 15 = 90"
    )

    units = UNITS_LINE.search(html)
    assert units, "no units line on the Aviation"
    assert "of alcohol in a serving of 90 ml (undiluted)." in " ".join(units.group(1).split()), (
        "Helen's wording is 'Roughly X units of alcohol in a serving of Y ml "
        "(undiluted)' (#1121, and #1291 for the bracket). The line now "
        f"reads: {' '.join(units.group(1).split())!r}"
    )


# --- the glasses page (#295): every glass once, with the survey's numbers -----
_SHELF_ITEM = re.compile(
    r'<li class="glass-shelf-item">.*?style="--glass-ratio: ([\d.]+); --glass-shift: ([-\d.]+)".*?'
    r'<span class="glass-shelf-name">([^<]*)</span>\s*'
    r'<span class="glass-shelf-ml">([^<]*)</span>\s*'
    r'<span class="glass-shelf-range">([^<]*)</span>', re.S)


def _to_ten(ml):
    """Nearest 10, halves up -- what Liquid's `round` does, not Python's."""
    return int(decimal.Decimal(ml / 10).quantize(0, decimal.ROUND_HALF_UP)) * 10


def test_the_glasses_page_shows_every_glass_once_with_its_surveyed_ml(prod_site):
    """Every icon and any survey-only type, alphabetically, each with
    `typical_ml`'s mean and range to the nearest 10 ml, standing on its base.

    The count matters because the page builds its rows with a nested Liquid
    lookup, which returns nil silently: a lost row still renders (#295).
    """
    g = yaml.safe_load((ROOT / "_data" / "cocktails" / "glasses.yml")
                       .read_text(encoding="utf-8"))
    page = (prod_site / "cocktails" / "reference" / "glasses" / "index.html") \
        .read_text(encoding="utf-8")
    items = _SHELF_ITEM.findall(page)
    want = len(g["all_icons"]) + len(g.get("survey_only_types") or {})
    assert len(items) == want, f"{len(items)} glasses on the page, expected {want}"

    def litres(ml):
        return decimal.Decimal(ml / 1000).quantize(decimal.Decimal("0.1"),
                                                   decimal.ROUND_HALF_UP)

    def shown(ml):
        mean, low, high = (_to_ten(ml[k]) for k in ("mean", "min", "max"))
        if mean >= 1000:
            return f"{litres(mean)} L", f"{litres(low)}–{litres(high)} L"
        return f"{mean} ml", f"{low}–{high} ml"

    expected = sorted(shown(g["typical_ml"][k])
                      for k in list(g["all_icons"]) + list(g.get("survey_only_types") or {}))
    printed = sorted((m.strip(), r.strip()) for _, _, _, m, r in items)
    assert printed == expected, "the page's ml do not match glasses.yml's typical_ml"

    names = [n.strip() for _, _, n, _, _ in items]
    assert names == sorted(names), f"not in alphabetical order: {names}"

    ratios = [float(r) for r, _, _, _, _ in items]
    assert max(ratios) == 1.0, f"the tallest glass is drawn at {max(ratios)}, not 1"

    # Every drawing carries its base offset: unshifted, the mug's label sits
    # under its handle.
    shifts = {n.strip(): float(s) for _, s, n, _, _ in items}
    assert shifts["mug"] == g["base_centre"]["mug"] != 0, (
        "the mug is not shifted by its base_centre, so its label is centred on "
        "its handle again")


# --- the index's shopping list: batches, whole fruit, pointers (#1297) --------

def test_every_makes_recipe_reaches_the_shopping_list_as_a_batch_row(prod_site):
    """A `makes:` recipe's box on the shopping list counts batches. #1297.

    The blob says so with `w`, and carries `h` (half offered) and `m` (what
    one batch makes) beside it: the figures the recipe page's scaler reads,
    so the two controls step alike. A `serves:` recipe has no `w` and no `m`.
    """
    blob = _shopping_blob(prod_site)
    makes = {u: r for u, r in blob.items() if r["k"] == "makes"}
    serves = {u: r for u, r in blob.items() if r["k"] == "serves"}
    assert len(makes) >= 30, f"only {len(makes)} `makes:` recipes in the blob."

    not_batch = sorted(u for u, r in makes.items() if r.get("w") is not True)
    assert not not_batch, (
        "these `makes:` recipes reached the shopping list without `w`, so "
        f"their box counts portions again: {not_batch}"
    )
    wrong = sorted(u for u, r in makes.items()
                   if not isinstance(r.get("h"), bool) or "m" not in r)
    assert not wrong, f"`h` or `m` is missing beside `w` on: {wrong}"
    stray = sorted(u for u, r in serves.items() if "w" in r or "m" in r)
    assert not stray, f"a `serves:` recipe is marked as a batch row: {stray}"

    waffles = blob["/food/recipes/henrys-sunday-waffles/"]
    assert waffles["m"]["box"] == "4" and waffles["h"] is False, (
        "Henry's waffles should read 'batches of 4' with no half batch "
        f"(2026-10-04: '2-3 waffles isn't enough!!!!'); got {waffles['m']!r}, "
        f"h={waffles['h']!r}"
    )


def test_a_fruit_written_as_its_juice_or_zest_is_marked_for_the_list(site):
    """'zest of 1 lemon' reaches the list as one lemon's zest -- #1297.

    The matcher is Ruby inside Jekyll (_plugins/food_shopping.rb,
    `mark_fruit`), so the built page is the only place it can be checked.
    The local build, because it keeps a recipe held back for proofreading:
    the zest line's only published example may be one. Three real lines,
    one per shape:

      item: "finely grated zest of 1 lemon"      the count is in the item
      amount: "1", item: "lemon, juiced"         the part is after the comma
      amount: "1 tbsp", item: "lemon juice"      NOT a lemon: never marked
    """
    blob = _shopping_blob(site)

    def line(url, name):
        found = [i for i in blob[url]["i"] if i["n"] == name]
        assert len(found) == 1, f"{url} has {len(found)} lines named {name!r}"
        return found[0]

    zest = line("/food/recipes/raspberry-baked-cheesecake/",
                "finely grated zest of 1 lemon")
    assert (zest.get("f"), zest.get("c"), zest.get("pt")) == ("lemon", "1", ["zest"]), zest
    assert zest["s"] == "produce", zest

    juiced = line("/food/recipes/apple-coleslaw/", "lemon")
    assert juiced.get("pt") == ["juice"] and "f" not in juiced, juiced

    both = line("/food/recipes/cranberry-sauce/", "orange")
    assert sorted(both.get("pt", [])) == ["juice", "zest"], both

    bottled = line("/food/recipes/smoked-mackerel-pate/", "lemon juice")
    assert not ({"pt", "f", "x"} & set(bottled)), (
        f"45 ml of lemon juice was read as some number of lemons: {bottled}"
    )


def test_only_a_fruit_is_ever_marked_with_a_part(site):
    """The marks stay on citrus, across the drafts too -- #1297.

    "watermelon, rind kept on", "belly of pork, rind and bones removed" and
    "parmesan rind" all hold a part WORD. None is a fruit in `whole_fruit`,
    and a mark on one would let the list drop it as "the same fruit".
    """
    fruits = set(yaml.safe_load(
        (ROOT / "_data" / "food" / "scaling.yml").read_text(encoding="utf-8")
    )["whole_fruit"]["fruits"])
    blob = _shopping_blob(site)

    problems = []
    for url, recipe in blob.items():
        for ing in recipe["i"]:
            if "pt" not in ing and "f" not in ing:
                continue
            name = (ing.get("f") or ing["n"]).lower()
            last = name.split()[-1].rstrip("s")
            if last not in fruits:
                problems.append(f"{url}: {ing['n']!r} marked {ing.get('pt')}")
    assert not problems, "not a fruit, and marked as one:\n  " + "\n  ".join(problems)
