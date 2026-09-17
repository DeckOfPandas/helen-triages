"""Assertions about BUILT HTML, not about the data behind it.

WHY THIS FILE EXISTS. Every other test in this suite reads YAML, front matter or
SCSS source. Both of the worst bugs in the reference work got past all of them,
because both lived in the gap between correct data and what Liquid actually
emitted:

  - `{% assign prefix %}` inside an include leaked into the PAGE's scope, so
    "tender at" appeared in front of all 42 chart rows instead of 4. The data
    was perfect. Every test passed. It was caught by reading built HTML by hand.
  - The safety zone measured its width against a different element from the bars
    it was warning about, so salmon's 63°C line drew at about 54°C. Caught by
    Helen looking at a screenshot.

A build is slow enough that it is worth one session-scoped fixture and no more,
so this file stays deliberately small: a handful of assertions about the shapes
that would have caught those two, on the pages most likely to break.

It SKIPS rather than fails when Jekyll isn't available, so the rest of the suite
still runs on a machine without the Ruby toolchain.
"""
from __future__ import annotations

import html as html_module
import json
import os
import pathlib
import re
import shutil
import subprocess

import pytest
import yaml

# Suite marker, so `pytest -m shared` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "tmp" / "_test_site"


# A SKIP IS A LIE IN CI. Locally, "no bundler on this machine" is a fair reason
# to stand down: not every contributor has a Ruby toolchain, and the rest of the
# suite is still worth running. In CI the toolchain is installed on purpose, so
# a missing bundler means the setup step did not do its job -- and skipping
# would report green for the two tests that are the only ones checking BUILT
# output, including the production-only 404s that nothing local can reproduce.
#
# GitHub Actions sets CI=true. Fail there, skip here.
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
def site() -> pathlib.Path:
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


PROD_BUILD_DIR = ROOT / "tmp" / "_test_site_prod"


@pytest.fixture(scope="session")
def prod_site() -> pathlib.Path:
    """A SECOND build, with the production config alone -- no _config_local.yml.

    Worth the extra four seconds because the `site` fixture above cannot see
    this entire class of bug, and one of them shipped. Locally, drafts have
    `output: true`, so every link to one resolves and the page looks right. In
    production `output: false`, and a link to a draft is a 404 that nothing on
    a developer's machine can reproduce.

    That is not hypothetical: GitHub issue #235. food/index.html tested
    `{% if site.food_drafts %}` before concatenating drafts into the list --
    which is a test of whether the collection is DECLARED, always true, rather
    than whether it PUBLISHES. Ten drafts with meta.rewritten: true were listed
    on the live index, each linking to /helen-triages/food_drafts/<slug>.html,
    Jekyll's default URL for a document it never wrote. Helen found it by
    looking at the production mockup on :4002.
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


def test_no_link_in_the_production_build_points_at_a_file_that_isnt_there(prod_site):
    """Every internal link in the built PRODUCTION site resolves to something.

    tests/test_page_links.py checks the same idea in the templates, but it can
    only check what it can read: a link built in a loop from `recipe.url` is on
    its TRUSTED_DYNAMIC list, on the reasoning that Jekyll computes .url from
    the document's own permalink and it is therefore right by construction.
    Issue #235 is the counter-example -- .url is computed for a document that
    is never written, so it is a correct URL for a page that does not exist.
    Only the built output can tell you that, and only the production build.

    A .pdf link is skipped: scripts/generate_pdfs.py writes those onto the
    finished site AFTER Jekyll, in the deploy workflow, so they are legitimately
    absent here. test_pdf_link_points_where_the_pdfs_are_written owns that pair.
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
    """The `prefix` leak, as an assertion.

    `{% assign %}` in a Jekyll include writes to the including PAGE's scope, so a
    variable set on one row is still set on the next. Setting `prefix` only in
    the tender_at branch put "tender at" in front of every row after the first
    tough cut — whole birds, doneness ranges, all of it. Nothing but the rendered
    output shows this.
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
    """Present, and at the figure on the node rather than a number in markup.

    The zone was a hard-coded `--t:63` in one page's HTML, which is why it
    couldn't travel to the recipe pages that needed it and why salmon shipped
    for a day showing 43°C as an unqualified option.
    """
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
    """Helen, 2026-08-14: "it can't go above the fold", and "I don't like the
    internal temperature featuring in the metadata"."""
    html = page(site, "/food/recipes/roast-beef-fillet/")
    assert "<strong>Internal temp</strong>" not in html, "the meta cell is back"
    assert html.index('id="doneness"') > html.index("recipe-section-notes"), \
        "the chart has drifted above Notes"
    assert 'href="#doneness"' in html, "nothing links to the chart"


# --- the class that isn't there ----------------------------------------------

def test_every_class_we_emit_has_a_rule_in_the_stylesheet(site):
    """A class in the markup with no rule behind it renders NOTHING and errors
    NOWHERE. It is invisible to Liquid, to Sass, to the build and to every data
    test in this suite.

    This is not hypothetical. A regex renaming the data's `pull_*` fields to
    `out_at_*` also matched `class="tc-pull"` -- `-` isn't a word character, so
    the lookbehind meant to protect property accesses let it through. The markup
    started emitting `tc-out_at` while the stylesheet still defined `.tc-pull`,
    and every filled bar on the site silently lost its position, size and
    colour. The data was correct throughout. Helen found it by looking at three
    charts with no bars in them.

    Scoped to the prefixes this project owns, so a class from somewhere else
    isn't dragged in. Modifiers are checked as written (`tc-row--suggested`),
    against the COMPILED css, where Sass's `&--suggested` has already been
    resolved into a real selector.

    GitHub issue #227 added `site-`. The header nav classes from last week's
    food/cocktails switcher -- `site-nav-icons`, `site-nav-icon-link`,
    `site-about-link` in _layouts/default.html -- sat outside all three
    original prefixes, so a typo in one of them would have rendered an
    unstyled link and failed nothing. `site-` is scoped to exactly the site
    chrome this project owns (header, nav, logo, footer -- everything
    _layouts/default.html and _sass/shared/_layout.scss share between food
    and cocktails), the same shape of boundary as `tc-`/`ct-`/`doneness`
    scoping to one feature each, rather than a blanket match that would also
    catch unrelated classes from elsewhere in the markup. Checked against
    every `class="...site-...` in the templates before adding it: all twelve
    existing site-* classes (site-header, site-header-inner, site-logo and
    its four sub-parts, site-footer and site-footer-hearts, site-title-link,
    plus the three nav ones above) already have a rule, so widening it adds
    coverage without adding any new failures.
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
    """Classes inside `_includes/icons/**/*.svg` must resolve to a real rule.

    GitHub issue #396. The test above builds its list from `*.html` and `*.js`,
    so the icon partials — which are `.svg` — have never been looked at. That is
    31 files including the whole `glasses/` set, and a typo'd class in any of
    them renders an unstyled shape and fails nothing. Same shape as the stale
    globs in MANUAL §12: not a scan that matched nothing, but a source list
    that quietly stopped covering the files.

    WHY THIS IS A SEPARATE TEST WITH A DIFFERENT RULE, rather than four more
    paths added to the glob above. Measured before writing: of 41 classes in
    those partials, 10 are styled and **all 31 unstyled ones are BEM
    modifiers whose base is styled** — `glass-icon--rocks` beside
    `.glass-icon`, `nav-icon--food` beside `.nav-icon`. Not one modifier is
    styled anywhere in either stylesheet. So modifiers here are hooks, exactly
    as MANUAL 11.3 describes, and demanding a rule for each would report 31
    failures that are all correct code. The rule that actually catches bugs is
    that the BASE resolves.

    Both stylesheets, because the glasses are cocktails' and the cloche is
    food's, and an icon shared by the chrome is in neither one's alone.

    WHAT IT CANNOT SEE, stated rather than left to be found: a typo in the
    MODIFIER half. `glass-icon--rocsk` has a styled base and passes. That is
    tolerable only because no modifier in these files is styled at all today —
    they carry no rules, so a misspelt one changes nothing. **If a modifier ever
    gains a rule, this limit stops being harmless** and the check needs to
    demand exact matches for modifiers that are styled elsewhere in the set.
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
    """The gap in the rendered tests I wrote to catch exactly this.

    They asserted on the row, the label, the value and the shaded zone -- the
    things AROUND the measurement -- and never on the mark that carries it. So
    when every filled bar vanished, six rendered tests still passed.
    """
    for url in ("/food/reference/internal-temperatures/", "/food/recipes/roast-beef-fillet/"):
        html = page(site, url)
        fragment = chart_of(html) if "recipes" in url else html
        row_count = len(re.findall(r'class="tc-row[ "]', fragment))
        bars = len(re.findall(r'class="tc-out-at"', fragment))
        assert row_count and bars == row_count, (
            f"{url}: {row_count} chart rows but {bars} filled bars — "
            f"every row must draw the figure it is about"
        )


# =============================================================================
# EVERY TEXT CONTROL MUST HAVE A PIECE OF STATE BEHIND IT — GitHub issue #274
# =============================================================================
#
# The fourth instance of one bug: you type into a box, results appear, and the
# clear-all link does not offer itself, so there is no way to dismiss them but
# deleting the text by hand. nameQuery, then isSearching, then two rival
# predicates, then the LEAVE OUT box.
#
# filter-state.test.js generates a case per field from FIELDS and is genuinely
# load-bearing — but it can only prove that the predicate handles every field
# FIELD_SPEC DECLARES. It cannot prove FIELD_SPEC declares every piece of state
# the page actually holds, and that second claim is the one that keeps failing.
# A control with no field is invisible to a sweep over fields.
#
# So this comes at it from the page instead: the ids are read out of the BUILT
# html, and a control this test has never been told about is a failure. Adding
# an input to the index page and no field to FIELD_SPEC now breaks the build
# rather than shipping a dead clear button.
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

    GitHub issues #331 and #667. tests/test_site_config.py checks the gate's
    PARTS exist and tests/test_front_matter.py checks the DATA is well formed.
    This is the only one that checks the gate actually does anything, against a
    real production build -- the same place the swatch-page bug (#276) was
    invisible until someone looked at the output rather than the source.

    TWO FLAGS SINCE 2026-09-02. A recipe publishes only on `awaiting_fix: false`
    AND `proofread: true`. This test used to split the corpus on `awaiting_fix`
    alone, which meant the five recipes that were live unproofread counted as
    "clear" and the test asserted they were PRESENT -- i.e. it asserted the bug
    #667 fixed. The split now asks the gate's own question.

    BOTH DIRECTIONS ON PURPOSE. The held-back half is the feature. The CLEARED
    half is what stops the fix being "hide everything": a plugin that dropped
    every document would satisfy the held-back assertion perfectly and take the
    site down.
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


def test_the_gate_fails_closed_on_a_missing_or_misspelled_flag():
    """A recipe with no `awaiting_fix`, or only the old `awaiting-fix`, does not
    publish. GitHub issue #331, Helen's call 2026-08-18.

    THE ORIGINAL RULE FAILED OPEN: it hid a document only on an explicit `true`,
    so every way of getting the flag wrong ended with the page live -- a missing
    key, the old hyphenated key, a quoted "true". The gate decides what the
    world sees, so it now publishes only on an explicit `false`.

    This builds its own site because the condition cannot exist in the real
    collection: tests/test_front_matter.py forbids both a missing flag and the
    old spelling, so by the time the suite is green there is nothing left to
    observe. Two throwaway recipes are written, built, and removed.

    The CONTROL matters as much as the two subjects. A build that fell over, or
    a gate that hid everything, would satisfy "the flagged ones are absent"
    perfectly -- so a known-good recipe must be present in the same output.
    """
    _require_bundler()
    out = ROOT / "tmp" / "_test_site_failclosed"
    made = []
    body = ('---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
            'source: "test"\nmain_ingredients: ["salt"]\nstar_ingredient: "salt"\n'
            'tags: []\ningredient_groups:\n  - items:\n    - item: salt\n'
            'method:\n  - "Nothing."\nmethod_short:\n  - ""\nmeta:\n  rewritten: true\n'
            '  proofread: true\n{flag}  cooked_before: false\n'
            '---\n')
    # `proofread: true` ON A FIXTURE, DELIBERATELY, and it is not a claim about
    # anything Helen has read -- these two files exist for one build and are
    # deleted in the `finally` below. Since #667 the gate has two legs, and a
    # fixture that fails both proves nothing about either: `proofread: false`
    # here would hold the page back on its own and the awaiting_fix assertion
    # would pass whatever the plugin did with the key it is named for. The one
    # leg under test is the only one allowed to fail.
    try:
        cases = {
            "zzz-gate-no-flag": "",                             # field absent entirely
            "zzz-gate-old-key": "  awaiting-fix: false\n",      # only the old spelling
        }
        for slug, flag in cases.items():
            p = ROOT / "_food_recipes" / f"{slug}.md"
            p.write_text(body.format(t=slug, flag=flag), encoding="utf-8")
            made.append(p)

        result = subprocess.run(
            ["bundle", "exec", "jekyll", "build", "--config", "_config.yml",
             "--destination", str(out)],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]

        published = [s for s in cases if (out / "food" / "recipes" / s / "index.html").exists()]
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
    finally:
        for p in made:
            p.unlink(missing_ok=True)
        shutil.rmtree(out, ignore_errors=True)


# =============================================================================
# THE SECOND LEG OF THE GATE — `proofread`, GitHub issue #667
# =============================================================================
# A page publishes only on `awaiting_fix: false` AND `proofread: true` since
# 2026-09-02. The two tests below are the `proofread` half of what the two
# above do for `awaiting_fix`, and they follow the same fixture discipline for
# the same reason: BOTH STATES ARE WRITTEN INTO THE REAL COLLECTION for one
# build and removed in a `finally`.
#
# That discipline is why `pytest` must never run twice at once on this
# machine -- a concurrent session collects these `zzz-gate-` files as real
# recipes and reports a screenful of bogus failures. It is also why the drink
# fixture below removes `_cocktail_recipes/` itself when it created it: an
# empty directory left behind changes what tests/test_cocktails.py's
# `_load_published` does on the next run.

FOOD_GATE_FIXTURE = (
    '---\ntitle: "{t}"\ntagline: "Temporary fixture, deleted by the test."\n'
    'source: "test"\nmain_ingredients: ["salt"]\nstar_ingredient: "salt"\n'
    'tags: []\ningredient_groups:\n  - items:\n    - item: salt\n'
    'method:\n  - "Nothing."\nmethod_short:\n  - ""\nmeta:\n  rewritten: true\n'
    '  awaiting_fix: false\n  proofread: {proofread}\n  cooked_before: false\n'
    '---\n'
)

# The smallest drink the #669 schema accepts: every key in REQUIRED_TOP_LEVEL,
# one ingredient with a declared generic and an amount, a canonical glass, a
# real mood, and a tagline that is not the "QQ" placeholder (a promoted drink
# may not carry one). Nothing here is a judgement about a real drink -- both
# files exist for one build and are then deleted.
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


def test_an_unproofread_recipe_does_not_reach_the_production_build():
    """`awaiting_fix: false, proofread: false` is held back; `proofread: true`
    publishes. GitHub issue #667, Helen's ruling 2026-09-02: proofread "is the
    very last touch that I, the human, make to the file".

    THE PAIR IS THE TEST. A single held-back fixture is satisfied perfectly by
    a plugin that drops every document, and the `awaiting_fix` leg above cannot
    tell you anything about this one: both recipes here differ in exactly one
    key, so the only thing that can explain one URL existing and the other not
    is the flag under test.

    It builds its own site rather than using `prod_site`, because the two
    states must be manufactured -- the real collection cannot hold a recipe
    whose only defect is being unproofread AND stay the corpus the rest of the
    suite reasons about.
    """
    _require_bundler()
    out = ROOT / "tmp" / "_test_site_proofread_gate"
    made = []
    try:
        cases = {"zzz-gate-unproofread": "false", "zzz-gate-proofread": "true"}
        for slug, value in cases.items():
            p = ROOT / "_food_recipes" / f"{slug}.md"
            p.write_text(FOOD_GATE_FIXTURE.format(t=slug, proofread=value),
                         encoding="utf-8")
            made.append(p)

        result = subprocess.run(
            ["bundle", "exec", "jekyll", "build", "--config", "_config.yml",
             "--destination", str(out)],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]

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
    finally:
        for p in made:
            p.unlink(missing_ok=True)
        shutil.rmtree(out, ignore_errors=True)


# =============================================================================
# THE GARNISH STEP READS AS ENGLISH — #1138 and #1143, 2026-09-17
# =============================================================================

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


def test_the_garnish_step_punctuates_a_list_and_drops_the_article_on_a_plural():
    """`A, B and C`, and no `a` before a plural. Issues #1138 and #1143.

    Helen, 2026-09-17, on the Hurricane: "I think we still have 'Garnish with a
    mint sprig and a fruit wedges and a maraschino cherry.'... 1. If the garnish
    is plural, it should not start with 'a'. 2. If there are more than two
    garnishes, separate all with a comma except for the penultimate pair, which
    get no comma."

    WHY A BUILT PAGE AND NOT A UNIT TEST: the rule is Liquid in
    `_layouts/cocktail.html` and there is no harness that can call it. The
    sentence a reader sees is the only place it can be checked.

    WHY FIXTURES AND NOT REAL DRINKS: no published drink carries three garnishes
    today (measured — five carry two, twenty-four carry one), so the list rule
    has nothing live to bite on and would be a test asserting nothing. The drink
    that provoked the issue is a DRAFT, which a public test may never require
    (#624). `fruit wedges` is deliberately not in garnish.yml: it models the case
    the old list-only rule could not reach, which is a garnish nobody has
    classified yet — where a new spelling always appears first.
    """
    _require_bundler()
    out = ROOT / "tmp" / "_test_site_garnish"
    recipes = ROOT / "_cocktail_recipes"
    created_dir = not recipes.exists()
    made = []

    def lines(items):
        return "".join(f'  - "{g}"\n' for g in items)

    cases = {
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
    try:
        recipes.mkdir(exist_ok=True)
        for slug, (garnishes, _) in cases.items():
            p = recipes / f"{slug}.md"
            p.write_text(GARNISH_DRINK.format(t=slug, garnish=lines(garnishes)),
                         encoding="utf-8")
            made.append(p)

        result = subprocess.run(
            ["bundle", "exec", "jekyll", "build", "--config", "_config.yml",
             "--destination", str(out)],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]

        for slug, (_, expected) in cases.items():
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
    finally:
        for p in made:
            p.unlink(missing_ok=True)
        if created_dir and recipes.is_dir() and not any(recipes.iterdir()):
            recipes.rmdir()
        shutil.rmtree(out, ignore_errors=True)


def test_no_garnish_contains_the_join_separator():
    """The garnish step joins its parts with `|` and splits them back.

    Liquid cannot append to an array, so the step builds one string and splits
    it. A garnish containing the separator would silently become two garnishes.
    Nothing does today; this is what keeps it that way, and it is cheaper than
    choosing a cleverer separator that the next reader has to decode.
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


def test_the_gate_covers_a_promoted_drink():
    """The cocktail collection is gated too, and this proves it on a bare CI
    checkout. GitHub issues #667, #668 and #624.

    #624 IS WHY THIS WRITES ITS OWN DRINKS. `_cocktail_drafts/` is a separate
    private repo, absent in CI, and nothing coordinates a public merge with a
    private one -- so a public test may never REQUIRE private drink data. Two
    throwaway drinks written into `_cocktail_recipes/` need none of it: the
    cocktail leg of the gate is exercised in exactly the checkout where the
    real collection is empty.

    `_cocktail_recipes/` does not exist on disk yet (nothing is promoted), so
    this creates it and, if it did, removes it again. An empty directory left
    behind is not harmless: tests/test_cocktails.py's `_load_published` reads
    its presence.
    """
    _require_bundler()
    out = ROOT / "tmp" / "_test_site_drink_gate"
    recipes = ROOT / "_cocktail_recipes"
    created_dir = not recipes.exists()
    made = []
    try:
        recipes.mkdir(exist_ok=True)
        cases = {"zzz-gate-drink-unproofread": "false",
                 "zzz-gate-drink-proofread": "true"}
        for slug, value in cases.items():
            p = recipes / f"{slug}.md"
            p.write_text(DRINK_GATE_FIXTURE.format(t=slug, proofread=value),
                         encoding="utf-8")
            made.append(p)

        result = subprocess.run(
            ["bundle", "exec", "jekyll", "build", "--config", "_config.yml",
             "--destination", str(out)],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]

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

        # AND THE INDEX AGREES WITH THE GATE. The drinks index reads
        # `site.cocktail_recipes`, which the plugin has already emptied of the
        # held-back drink at :post_read -- so the page cannot list it even by
        # accident. This is the half issue #276 taught: a URL that exists and a
        # listing that mentions it are two separate leaks.
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
    finally:
        for p in made:
            p.unlink(missing_ok=True)
        if created_dir and recipes.is_dir() and not any(recipes.iterdir()):
            recipes.rmdir()
        shutil.rmtree(out, ignore_errors=True)


# =============================================================================
# THE THIRD LEG, DRINKS ONLY — `rewritten`, GitHub issue #1137
# =============================================================================
# Both drink-side flags are parameterised here, where the fixtures above pin all
# but one: the rule is about the COMBINATION of `rewritten` and `made_before`,
# and one of those gates while the other deliberately does not.

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


def test_an_unrewritten_drink_is_held_back_but_an_unmade_one_publishes():
    """`rewritten: true` gates a drink; `made_before` does not. Issue #1137,
    Helen's ruling 2026-09-17.

    HER WORDS: "I want to block cocktails that have not been rewritten. I want
    to allow cocktails that I have not made. I will rewrite these before making
    them." The two flags look alike and answer different questions, which is
    exactly why this test pairs them rather than checking either alone.

    WHY `rewritten` EARNED A LEG. It means the prose on the page is hers rather
    than the source's, and until #1137 it was read by nothing -- so the only
    thing between a source's own wording and the live site was the promotion
    procedure remembering to check. `made_before` stays ungated on her earlier
    ruling (#722, 2026-09-05): "It will be much easier for me to browse drinks I
    want to try from the live site than a local build." #1137 is the other half
    of that sentence -- she reads the drink on the live site in order to MAKE
    it, and what she reads there should be her words.

    FOUR FIXTURES, ONE BUILD, because each row is satisfied on its own by a
    plugin that does nothing or by one that drops everything:

        drink, rewritten,     unmade  -> PUBLISHES (the point of the pairing)
        drink, NOT rewritten, made    -> held      (the new leg)
        drink, NOT rewritten, unmade  -> held      (the leg, not the other flag)
        FOOD,  NOT rewritten          -> PUBLISHES (drinks only; food keeps two)

    The last row is the one a future refactor would most easily break, by
    reading the flags without the collection name -- it would take every
    unrewritten food recipe off the live site, silently.

    It cost nothing on the day it landed: all 47 drinks then live already said
    `rewritten: true` (tmp/rewritten_census.py), so no page went dark.
    """
    _require_bundler()
    out = ROOT / "tmp" / "_test_site_1137_rewritten"
    recipes = ROOT / "_cocktail_recipes"
    created_dir = not recipes.exists()
    made = []
    try:
        recipes.mkdir(exist_ok=True)
        drinks = {
            # slug: (rewritten, made_before)
            "zzz-1137-rewritten-unmade":     ("true",  "false"),
            "zzz-1137-unrewritten-made":     ("false", "true"),
            "zzz-1137-unrewritten-unmade":   ("false", "false"),
        }
        for slug, (rw, mb) in drinks.items():
            p = recipes / f"{slug}.md"
            p.write_text(
                GATE_DRINK_ANY.format(t=slug, rewritten=rw, made_before=mb),
                encoding="utf-8")
            made.append(p)

        food = ROOT / "_food_recipes" / "zzz-1137-food-unrewritten.md"
        food.write_text(
            GATE_FOOD_UNREWRITTEN.format(t="zzz-1137-food-unrewritten"),
            encoding="utf-8")
        made.append(food)

        result = subprocess.run(
            ["bundle", "exec", "jekyll", "build", "--config", "_config.yml",
             "--destination", str(out)],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]

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
    finally:
        for p in made:
            p.unlink(missing_ok=True)
        if created_dir and recipes.is_dir() and not any(recipes.iterdir()):
            recipes.rmdir()
        shutil.rmtree(out, ignore_errors=True)


# =============================================================================
# ONE HEADER AND ONE FOOTER FOR THE WHOLE REPO — GitHub issue #374
# =============================================================================
# Helen, 2026-08-19: "I don't want parity between two footers -- I want one
# footer for the whole site. And one header. Literally the same code and
# assets."
#
# PARITY IS THE THING THIS REPLACES, and the difference is the whole point.
# Parity is two artefacts a human keeps in step, and it had already failed here
# twice by the time this test was written. The tape artwork sat in two
# directories holding byte-identical files, and drifted for five days after
# food's redesign because nothing but a handover note was watching (issue #223).
# The header nav was built from three independently-optional per-site keys, food
# declared all three and cocktails declared none, so cocktails rendered no nav
# whatsoever -- for weeks, with a green suite, because "shared layout" was true
# of the template and false of the output.
#
# Both are invisible to every other test in this suite. The markup is shared,
# the SCSS partial is shared, the classes all have rules, every link resolves:
# each half is individually correct while the two pages disagree. Only the built
# output can see it, and only by looking at two pages at once.

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
    byte-identical across every page OF A SITE, and says the other site's name.

    Not "equivalent", not "both present" -- identical source text. Anything a
    page is allowed to vary is by definition not part of the shared chrome, so
    there is nothing here to normalise away and no tolerance to tune.

    THE NAV ROW JOINED THE WORDMARK ON THE PER-SITE SIDE ON 2026-09-10, and
    this docstring used to say that any exception carved in here "IS a second
    header arriving, and it wants arguing rather than accommodating". It was
    argued: Helen chose, from a header-only candidates page, a row under the
    wordmark that names THE OTHER site -- "[ COCKTAILS ] →" on food, "[ FOOD ]
    →" on cocktails -- because a visitor had no way to know the small glass in
    the corner was a second site. So the row now does the wordmark's one
    per-site job from the other direction: it says where you are not. It is
    still one template and one loop over sites.yml with no per-site key, which
    is what #374 was about; what varies is the output, by the same rule the
    wordmark varies by.

    So the comparison is in two parts. The footer is identical across both
    sites, as before. The nav is identical across pages of ONE site -- the
    index and a recipe, which reach default.html by different routes -- and
    the two sites' rows must each name the other site and neither name its
    own. That last check is what stops the loop quietly showing both, or
    neither, on a site that gained a third entry.
    """
    pages = {
        "/food/": prod_site / "food" / "index.html",
        "/cocktails/": prod_site / "cocktails" / "index.html",
        # A collection document as well as an ordinary page: a recipe reaches
        # default.html through recipe.html, so its chrome arrives by a different
        # route and is worth asserting on rather than assuming.
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

    test_every_class_we_emit_has_a_rule_in_the_stylesheet, above, asks whether a
    class has a rule -- but only in food.css. That is right for the classes only
    food's own pages emit, and it is exactly the wrong question for the chrome,
    which every page in the repo renders. A chrome rule that lives in
    _sass/food/ compiles into food.css, satisfies that test, and is simply
    ABSENT on cocktails.

    Which is what was happening, in three places, when issue #374 went looking:

      - the footer's four link hovers (_sass/food/_footer.scss);
      - the header nav's hover (_sass/food/_recipe-header.scss);
      - .cloche-body, .cloche-heart, .martini-outline, .martini-bowl and
        .martini-liquid, in the same file -- so the two icons in the shared
        header rendered as raw unstyled SVG on every cocktails page.

    Every one of those had a comment explaining that the colour it wanted was
    not in the palette contract, so the rule had to be food-only and cocktails
    would get a plainer version. That reasoning is how a header ends up shared
    in the markup and forked in the cascade, and nothing in this suite could
    see it: the markup is shared, the classes all have rules, every link
    resolves, the build is green.

    Derived from the template and the icon partials rather than from a list, so
    a class added to the chrome tomorrow is covered without anyone remembering.
    """
    layout = ROOT / "_layouts" / "default.html"
    sites = yaml.safe_load((ROOT / "_data" / "sites.yml").read_text(encoding="utf-8")) or {}

    # default.html includes icons/github.svg literally, and icons/<icon>.svg for
    # every site -- so the icon partials' own internal classes are chrome too.
    # That is where five of the eight missing rules were.
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

    # DIVERGENCE ONLY: a class styled by at least one site must be styled by
    # all of them. Deliberately NOT "every chrome class has a rule somewhere" --
    # that is a different claim, it belongs to
    # test_every_class_we_emit_has_a_rule_in_the_stylesheet above, and asserting
    # it here would fire on .nav-icon--food, .nav-icon--martini and
    # .footer-icon--github. Those three are BEM modifier hooks sitting beside
    # bases that ARE styled (MANUAL 11.3), styled by nobody, consistently, on
    # both sites -- which is not a fork and is not what this test is about.
    #
    # (They are nonetheless invisible to the test that should own them, because
    # its source list covers _includes/**/*.html and these live in .svg icon
    # partials. Noted, not fixed here.)
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
    """A page with no site_key renders completely unstyled, and says nothing.

    _layouts/default.html links `assets/css/<this_site.css>.css` inside an
    `{% if this_site %}`, and `this_site` is `site.data.sites[page.site_key]`.
    So a page whose site_key is missing -- or misspelled, or lost when the page
    moved out of the directory whose _config.yml default supplied it -- links NO
    STYLESHEET AT ALL. Not a fallback, not a broken href: the tag simply does
    not render. MANUAL 2.4 records that this is the designed behaviour and
    worth knowing before adding a root-level page.

    IT THEN HAPPENED, IMMEDIATELY, IN THE COMMIT THAT ADDED THE FIRST ONE.
    about.html moved from food/ to the repo root in issue #374, out of the
    `path: "food"` default that had been supplying its site_key. Its front
    matter carries a long comment explaining that site_key must therefore be set
    by hand, and the line itself was never written. The page shipped unstyled,
    and the entire suite -- 17,529 checks including a build of the production
    site and a scan of every link in it -- passed.

    Nothing was looking, because every other check in this file asks about
    something INSIDE a page. This asks whether the page got dressed at all.

    Reads the production build, so a page held back by the awaiting_fix gate is
    correctly not examined: this is a question about what publishes.
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
        # The root redirect is a bare <meta http-equiv="refresh">, deliberately:
        # issue #204 deleted its layout and stylesheet along with the landing
        # page it used to be. It has no <body> content to style.
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
    """The include and exclude pickers must agree on emphasising a real match.

    MANUAL 8.1: these are not two implementations. Both call
    `IS.buildMasterList` and `IS.search`, get back the same ranked results with
    the same `hasWordMatch` flag on each, and differ only in what corpus was fed
    in. So a treatment that one applies and the other does not is drift, not a
    design decision.

    It was drift. Issue #390, found by Helen looking at the two boxes stacked on
    one screen with the same three letters typed into both: SEARCH MAIN
    INGREDIENTS picked out the genuine matches and LEAVE OUT rendered forty
    candidates identically. `makeExcludeButton` took no `wordMatch` argument at
    all, so `r.hasWordMatch` was computed, passed as far as the call site, and
    dropped.

    Nothing could see it. The classes are applied with `classList.add(...)`
    rather than written into a `class="..."` attribute, so
    test_every_class_we_emit_has_a_rule_in_the_stylesheet's scan does not reach
    them (that gap is issue #396's neighbourhood, and is why this test checks
    the stylesheet itself rather than assuming that one does).

    Checks three things, because each fails on its own:
      1. both builders apply a --word-match class;
      2. both call sites pass the flag rather than dropping it;
      3. both classes have a rule in the compiled CSS.
    """
    # COMMENTS STRIPPED BEFORE COUNTING, and this is not fastidiousness: the
    # first version of this test counted `r.hasWordMatch` in the raw source,
    # and the explanatory comment written directly above makeExcludeButton()
    # names it twice. Deleting the argument from the call therefore left the
    # count unchanged and the test green -- a guard defeated by the prose
    # explaining the bug it guards against. Caught by breaking it on purpose,
    # which is the only reason it was caught at all.
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

    # CALL SITES, matched as calls rather than as mentions of a name, and with
    # the two function DEFINITIONS excluded by the lookbehind -- their parameter
    # lists name `wordMatch` and would otherwise read as calls that pass it.
    calls = re.findall(
        r"(?<!function )make(?:Ingredient|Exclude)Button\(([^)]*)\)", js
    )
    dropped = [c for c in calls if "hasWordMatch" not in c and "true" not in c]

    # THE RULE, NOT A COUNT. This asserted "exactly 4 call sites pass the flag"
    # until #387 added a fifth (restoreIndexMemory rebuilds the chosen
    # ingredient's button when you come back to the index), and a correct change
    # turned it red. A magic number makes every new call site a false alarm and
    # teaches whoever meets it to edit the number, which is how a guard stops
    # meaning anything. What actually matters is that NO call site drops the
    # flag -- which is the shape #390 was.
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
          "emphasis lives in _sass/food/_buttons.scss as @mixin "
          "word-match-emphasis($colour); each picker passes its own section "
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
    All three of those conditions were learned from a rule that slipped past a
    pattern, so none of them is defensive tidiness.

    ORDER, BECAUSE @extend WRITES IT BACKWARDS. This was `\\.btn-x[^,{]*\\.active`
    for six weeks and that reads correctly on food, where every active rule is
    authored as `.category--star .btn-star.active` and Sass emits it unchanged.
    Cocktails writes the same idea as `&.is-on` nested in a PLACEHOLDER, so the
    compiled selector is the extender substituted into the placeholder's
    position -- `.is-on.btn-chaos`, chosen class FIRST. A pattern that assumes
    an order silently skipped the one rule that carries the whole active state
    (2026-09-15, #1086, found by printing what the scan actually matched rather
    than trusting that it matched something -- three per-section `background`
    rules did match, so the scan was green and looked alive).

    `:not()`, BECAUSE `.btn-mood:hover:not(.is-on)` IS THE OPPOSITE RULE. It
    contains both class names and means "a button that is NOT chosen" -- the
    resting hover state. Scanning it would let a padding change on HOVER be
    reported as an active-state offence, and worse, would count towards the
    "did this scan match anything" assertion above.
    """
    bare = re.sub(r":not\([^()]*\)", "", selector)
    if f".{chosen}" not in bare:
        return False
    # `(?![-\w])` so `.btn-tag` does not match `.btn-tag-thing`.
    return any(re.search(r"\." + re.escape(b) + r"(?![-\w])", bare)
               for b in buttons)


def test_no_active_filter_button_changes_its_own_width(site):
    """Selecting a filter must not resize it. Issue #389.

    Helen: "filter tags to the right of a selected one move to the right -- they
    should stay in the same position." The cause was `%btn-active-base` setting
    `font-size: 0.74rem` and `letter-spacing: 0.04em`, neither matching the
    resting state it replaced -- so activating re-measured the button and slid
    the rest of the row along. Letter-spacing did most of it: ~0.38px per
    character, about 5.7px on `one-handed food`.

    It was two bugs wearing one rule. Two different resting bases extend that
    placeholder -- .btn-tag/.btn-star at 0.75rem with no letter-spacing, and
    .btn-meta at 0.72rem with 0.02em -- so no single pair of values could have
    agreed with both, and the fix was to declare neither.

    THE POINT OF DOING THIS ON THE COMPILED CSS is that the trap is not the
    placeholder, it is the IDEA that an active state may restyle type. That idea
    can arrive in any of the five rules that extend it, or in a sixth written
    next year, and the symptom -- a few pixels of drift on a row you were not
    looking at -- is one nobody reports twice.

    -webkit-text-stroke is deliberately NOT on the list: it paints outside the
    glyph and occupies no space, which is exactly why it is the right lever for
    a selected state and why it survived the fix (§13.4.2).

    BOTH SITES SINCE 2026-09-15, #1086, AND THAT IS THE SAME LESSON ONE LEVEL
    UP. This read food.css alone for six weeks, because that is where #389
    happened -- so cocktails' own chips were held to the rule by whoever
    remembered it, which for a while was `_sass/cocktails/_cocktail.scss`
    writing "this guard does not reach this selector, so this is enforced by
    construction here" in a comment. A rule enforced by a comment is a rule
    that will be broken by the next person who does not read it. The trigger
    was Helen choosing a filled block for a chosen cocktail chip: the moment
    the two sites' active states were being brought into line, the guard on one
    of them was still site-specific. `.is-on` is cocktails' spelling of
    `.active`; the property list and the reasoning are shared.
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

    The pool sits between a search box and whatever is under it, and it is empty
    for the whole of every session that never types into it. Issue #290 moved
    its gap onto the pool itself, gated on `:not(:empty)`, so that dead air went
    away -- and it did not, because `_sass/food/_search.scss` went on declaring
    `margin-top: $space-lg` on `.search-results` unconditionally.

    THE DIRECTION IS THE WHOLE BUG. A `:not(:empty)` override can only ever ADD
    to the unconditional base underneath it; it cannot take space away. So the
    empty pool kept the larger 1rem and the full one got 0.75rem, which made the
    pool 4px TALLER with nothing in it. Clicking a LEAVE OUT candidate empties
    the pool at the same moment the chosen pill is drawn below it, so the pill
    landed 4px lower than the chip that had just been clicked -- Helen, "if I
    click a chip, it then jumps downwards by a few pixels, but should stay in
    the same place".

    A rule that only fires when the pool has content is fine and is the whole
    design. What this forbids is the unconditional twin, because that is what
    silently decides what "empty" costs.
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

    Takes `rgb(r, g, b)` or `#rrggbb`. Sass emits the former for a colour it
    has computed (a darken() of a root) and the latter for a literal or a
    plain alias -- and on 2026-09-04 LEAVE OUT's two tones became aliases of
    the palette's neutrals, so this stopped seeing three numbers and unpacked
    nothing.
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
    """A matched LEAVE OUT tag must visibly change when you hover it. Issue #403.

    The trap is specific and it is one this palette walked into once already.
    Word-matched candidates REST at $color-exclude-active (issue #390). The pool
    hover therefore cannot be $color-exclude-active: hovering a matched tag
    would change nothing whatsoever -- not the "lightness-only shift reads as
    nothing at small type" of MANUAL 12, which is at least a change, but a
    literal no-op.

    Helen's ask was that these DARKEN, "same as for the include filter", so the
    direction is asserted too and not just the difference. Both values are
    derived ($darken-active and $darken-active-extra off one root), so an edit
    to either step, or a re-rooting of the cobalt, can quietly collapse them.

    Compared on relative luminance rather than on the raw strings, because two
    different strings can still be the same colour and because "darker" is the
    actual claim being made.
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
    # The not-found page. GitHub Pages serves a root 404.html for any URL it
    # cannot find, project sites included, so the file has to be HERE and not
    # in a directory -- 404.html's own front matter says why. Added by the
    # 2026-09-15 design review (#1086); before it, a stale bookmark got
    # GitHub's own page with no way back to either site.
    "404.html",
}


def test_the_built_site_root_holds_nothing_unexpected(prod_site):
    """A file that lands at the site root without anyone deciding it should.

    Jekyll copies the SOURCE DIRECTORY, and `.gitignore` governs what reaches a
    CHECKOUT. Those are different questions, and the gap between them is the
    whole reason this test exists: a file can be correctly ignored by git and
    still be sitting in `_site/`, and a file can be tracked and still be
    excluded from the build. Neither fact tells you the other.

    _config.yml already knew this -- its `*Zone.Identifier` comment says
    ".gitignore already covers these, but that only stops them being committed
    -- Jekyll still reads the working directory" -- and issue #414 was opened
    anyway, claiming two Sublime files were on the live site because they were
    in a local build. They were not: they are untracked, so CI never sees them.
    What they were doing was appearing in the jekyll-prod mockup, which exists
    to show what deploys and was therefore misrepresenting it.

    So this runs against the PRODUCTION build, which is the honest question, and
    it catches the case #414 turned out not to be: a file that really is tracked
    and really would ship.

    Adding a legitimate root file means adding it to EXPECTED_ROOT_FILES, which
    is thirty seconds and forces the question of whether it belongs there.
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


def test_the_cocktail_index_marks_and_styles_everything_it_lights_up(site):
    """Three JS-applied classes on the drinks index, and each must have a rule.

    GitHub issue #579's neighbourhood, and issue #390 is the precedent worth
    naming: on the food side `hasWordMatch` was computed, carried all the way to
    the call site, and dropped -- so one picker marked its genuine matches and
    the other rendered forty candidates identically. Nothing could see it,
    because these classes are applied with classList/className rather than
    written into a `class="..."` attribute, so
    test_every_class_we_emit_has_a_rule_in_the_stylesheet's scan does not reach
    them. Hence checking the compiled stylesheet here rather than assuming one
    does.

    The three:

      btn-pool--word-match  the candidate you actually meant (#549 point 3)
      drink-card-hit        the matched ingredient on a card, which is the one
                            job MANUAL §9.13 gives the card: say why you are
                            here
      drink-name-hit        the matched run of a drink name (#564)
    """
    raw = (ROOT / "assets" / "js" / "cocktail-index.js").read_text(encoding="utf-8")
    js = re.sub(r"//.*$", " ", re.sub(r"/\*.*?\*/", " ", raw, flags=re.S), flags=re.M)

    problems = []
    for cls in ("btn-pool--word-match", "drink-card-hit", "drink-name-hit"):
        if cls not in js:
            problems.append(f"cocktail-index.js never applies .{cls}")

    # The flag has to REACH the chip builder, which is the half #390 lost. Both
    # a family (all) button and a ranked result pass one; a chosen chip passes
    # false, deliberately -- it is already selected and marking it as a match
    # would say something about the query rather than about the chip.
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

    # MATCHED AS A WHOLE CLASS NAME, not as a substring. A plain `in` check is
    # satisfied by `.drink-name-hit-unused`, so renaming a rule out of use would
    # leave this green -- found by breaking it on purpose, which is the only
    # reason it was found. The lookahead is what makes `.drink-card-hit` fail to
    # match `.drink-card-hits` and, more to the point, fail to match a rule that
    # has been renamed to something merely beginning with it.
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


# --- a form control nobody gave a colour --------------------------------------
#
# #654. When the cocktails palette inverted, every element on the page took the
# new colours for free through inheritance -- and the search inputs silently did
# not. Typing into HAS TO HAVE produced BLACK TEXT ON A BLACK GROUND: invisible
# rather than absent, with a green build and a green suite.
#
# WHY INHERITANCE IS NOT A ROUTE HERE. An `<input>` does not inherit `color`. It
# takes the UA stylesheet's `fieldtext`, which is near-black whatever its
# ancestors say. `background`, `font-family` and `font-size` behave the same way
# on form controls: they are set, or they are not set.
#
# EVERY GUARD WE HAD LOOKED IN THE WRONG PLACE, which is the reason for a new one
# rather than a wider old one:
#   - test_every_class_we_emit_has_a_rule_in_the_stylesheet -- the class HAD a
#     rule. It just was not a `color` one.
#   - the contrast measurements -- they read colours they are handed, and nobody
#     hands them a control whose colour is a UA default nobody wrote down.
#   - test_every_published_page_links_a_stylesheet -- the page was fully dressed.
#
# IT WILL BITE AGAIN THE NEXT TIME ANYTHING INVERTS -- a dark mode (#636), a
# print stylesheet, a themed section -- and the failure is always the same shape:
# invisible text, green build. `color` only is the cheap version and is the right
# first one.

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

    THE TOGGLE TRACK IS WHY THIS EXISTS, and it was found by this test failing
    on its first real run. `<button class="cocktail-toggle-track">` on every
    drink page contains one empty `<span class="cocktail-toggle-knob">` and
    nothing else: it is the SWITCH, drawn entirely in background and border, and
    its accessible name comes from `aria-label`, which is never painted. Asking
    it for a `color` is asking the wrong question, and a guard that reports a
    control which cannot be invisible is a guard people learn to skip.

    So: strip the tags and look for a real character. An `aria-label` is
    deliberately NOT counted -- that is the point of the distinction.
    """
    return bool(re.sub(r"<[^>]*>", "", inner_html).strip())

# A `color:` declaration, and not `background-color`, `border-color`,
# `accent-color`, `caret-color` or a `--custom-color` property. The lookbehind is
# what separates them, and getting it wrong in either direction makes this test
# useless rather than merely wrong.
COLOR_DECL = re.compile(r"(?<![-\w])color\s*:")


def _rules(css: str):
    """(selector, body) for every rule in a compiled stylesheet.

    Good enough for this question and deliberately not a parser: at-rules like
    `@media` wrap other rules, and this yields the inner ones with the outer
    selector text attached to the first of them. That can only make the test
    MORE forgiving, never less -- it never invents a `color` that is not there.
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
    """A control whose colour nobody set is a UA default, and UA defaults are dark.

    ASKED OF THE BUILT PAGES AND THE COMPILED CSS, because that is where the two
    halves meet. The class existing in a partial and the rule existing in a
    stylesheet are separately true and jointly insufficient -- the bug was that
    nothing joined them.

    THE MATCH IS DELIBERATELY GENEROUS: a control counts as coloured if ANY
    colouring selector names its id, one of its classes, or its bare tag. That
    over-accepts (a `.btn-tag` rule colouring one page's button satisfies
    another page's) and it still catches the whole of #654, because the failing
    control had no colouring rule anywhere at all. A stricter version needs a
    cascade resolver, which is a different project.

    `_dev/` IS OUT OF SCOPE. Those pages are `output: false` and never ship;
    they are instruments, and #649 above is the guard that covers them.
    """
    pages = [p for p in sorted(site.rglob("*.html"))
             if p.relative_to(site).parts[0] not in {"dev", "_dev"}]
    assert pages, "the build produced no pages outside _dev/."

    # One stylesheet read per sheet, not per page: 550+ pages share two.
    cache = {}

    def colouring_for(html):
        # THE `?v=` CACHE-BUSTER IS WHY THIS DOES NOT ANCHOR ON `.css'`.
        # _layouts/default.html links `...assets/css/cocktails.css?v=1788687397`,
        # and a pattern requiring the quote straight after `.css` matched no
        # page at all -- which this test's own "found nothing" assertion caught
        # on its first run. Kept as a named group so the query string is dropped
        # deliberately rather than by a rsplit that would also survive it.
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

    If it did, this test would pass on the exact bug it exists to catch -- the
    cocktails inputs had a background and no colour. The lookbehind is the whole
    mechanism, and it is one character away from being wrong in either
    direction.
    """
    assert COLOR_DECL.search("color: red")
    assert COLOR_DECL.search("a { color:var(--x) }")
    assert not COLOR_DECL.search("background-color: red")
    assert not COLOR_DECL.search("border-color: red")
    assert not COLOR_DECL.search("accent-color: red")
    assert not COLOR_DECL.search("caret-color: red")
    assert not COLOR_DECL.search("--brand-color: red")


def test_paints_text_skips_the_switch_and_keeps_the_buttons():
    """The refinement's own guard: over-skipping would empty the test silently.

    `_paints_text` is the one place this test decides NOT to look at something,
    which makes it the one place a mistake turns the whole guard green. It was
    added because the toggle track is a real control that genuinely cannot be
    invisible; it must not also excuse a button with words on it.
    """
    # The case that prompted it: the drink page's read/make switch.
    assert not _paints_text('<span class="cocktail-toggle-knob"></span>')
    assert not _paints_text("")
    assert not _paints_text("   \n  ")

    # Everything with a word in it still counts, however it is wrapped.
    assert _paints_text("make it")
    assert _paints_text('<span class="btn-label">clear</span>')
    assert _paints_text('&times; clear')
    assert _paints_text('deal again <span class="universe-again-icon">&#8635;</span>')


def test_a_control_with_no_colouring_rule_is_reported():
    """The whole guard, exercised against a stylesheet that does not colour it.

    Without this, every part of the test could be broken at once -- the scan,
    the selector match, the fallback -- and it would still pass on a repo where
    everything happens to be coloured. This is the #654 bug in miniature: a
    search input, a stylesheet that gives it a background and no colour.
    """
    css = ".drink-search-input { background: #000; border: 1px solid #333; }"
    selectors = _colouring_selectors(css)
    assert selectors == [], (
        "a rule declaring only `background` was read as declaring `color`."
    )

    css_fixed = css + " .drink-search-input { color: #eee; }"
    assert any(".drink-search-input" in s for s in _colouring_selectors(css_fixed))


# --- a mark that is computed, carried, and then styled away -------------------
#
# #653. `cocktail-search.js` returns a `wordMatch` flag per candidate,
# `cocktail-index.js` turns it into `.btn-pool--word-match`, and `_filters.scss`
# gives that class a magenta underline. All three worked. One further rule,
#
#     .drink-search--exclude .btn-pool--word-match { text-decoration: none; }
#
# cancelled it for LEAVE OUT alone, so prefix matches were marked in one picker
# and unmarked in the other for as long as that rule existed. Helen found it by
# putting the two pools side by side with the same three letters typed -- which
# is exactly how #390 was found on the food side, and #390's lesson is the one
# that applies: "one code path" guarantees the same ANSWER and guarantees
# nothing about what either picker DOES with it.
#
# WHY "DOES THE CLASS HAVE A RULE" CANNOT SEE THIS, and it is the general form
# worth having: the class HAD a rule, and a later, more specific rule turning it
# off. A guard asking whether a class is styled cannot see a rule that unstyles
# it. That is why this reads the COMPILED CSS and resolves.
#
# SPECIFICITY, NOT SOURCE ORDER, IS WHAT DECIDES IT.
# `.drink-search--exclude .btn-pool--word-match` is (0,2,0) and the bare
# `.btn-pool--word-match` is (0,1,0), so a sectioned rule beats the base one
# wherever it sits in the file. Reading "the last one wins" would get this right
# by accident today and wrong the moment somebody moves a block.

WORD_MATCH = ".btn-pool--word-match"
PICKER_SECTIONS = ("drink-search--include", "drink-search--exclude")

# `text-decoration` and its longhand. The mark is an underline; a shorthand
# `text-decoration: none` and a longhand `text-decoration-line: none` cancel it
# identically, and only one of the two was ever written here.
DECORATION = re.compile(
    r"(?<![-\w])text-decoration(?:-line)?\s*:\s*([^;}]+)")


def _word_match_decoration(css: str):
    """Effective text-decoration for the mark, per picker section.

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
    """HAS TO HAVE and LEAVE OUT must both still paint the prefix-match mark.

    Helen, 2026-09-02, settling it: "the chip underline rule should be the same
    between has to have and leave out, namely that prefix matching of any word
    gets the pink whereas substring matching does not."
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
    assert base and base != "none", (
        f"the base `{WORD_MATCH}` rule declares text-decoration "
        f"{base!r}. The mark IS the underline; without it the class is emitted "
        f"and paints nothing."
    )

    cancelled = [
        f"{name}: text-decoration {value!r}"
        for name, value in per_section.items()
        if value is not None and value.strip() == "none"
    ]
    assert not cancelled, (
        "One picker cancels the word-match mark that the other one shows. This "
        "is #653 returning: the flag is computed, carried to the call site and "
        "then styled away on one side, so the same three letters typed into "
        "HAS TO HAVE and LEAVE OUT mark different chips.\n  "
        + "\n  ".join(cancelled)
    )


def test_both_pickers_get_the_word_match_class_from_one_builder():
    """The other half of #390's lesson: one answer, and one thing done with it.

    The CSS test above catches the mark being styled away. This catches it never
    being APPLIED to one pool -- which is the same bug entering by the other
    door, and the door food's own guard watches.
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
    """The guard's own guard, against the exact CSS that caused #653.

    Without this the resolver could return `None` for everything and the test
    above would pass on a stylesheet that cancels the mark in both pickers.
    """
    good = (".btn-pool--word-match { text-decoration: underline; }"
            ".drink-search--exclude .btn-pool--word-match { color: #eee; }")
    base, sections = _word_match_decoration(good)
    assert base == "underline"
    assert sections["drink-search--exclude"] is None

    # The rule as it actually stood, and the reason the issue exists.
    bad = good + (".drink-search--exclude .btn-pool--word-match "
                  "{ text-decoration: none; }")
    base, sections = _word_match_decoration(bad)
    assert sections["drink-search--exclude"] == "none", (
        "the resolver did not see a sectioned rule cancelling the mark."
    )

    # The longhand cancels identically and must not slip past.
    longhand = good + (".drink-search--include .btn-pool--word-match "
                       "{ text-decoration-line: none; }")
    _, sections = _word_match_decoration(longhand)
    assert sections["drink-search--include"] == "none"

    # `text-decoration-color` is not the mark going away.
    assert DECORATION.search("text-decoration-color: red") is None


# =============================================================================
# THE SHOPPING LIST'S BUILT DATA — GitHub issue #801
# =============================================================================
# THIS IS THE ONLY PLACE THE AISLE RULE CAN BE CHECKED. The matcher is Ruby
# (_plugins/food_shopping.rb) and runs inside Jekyll, so nothing that reads
# YAML can exercise it; tests/test_food_shopping.py says so where it checks the
# data files instead. A Python reimplementation to make it unit-testable would
# be a second copy of the rule that passes while the site is wrong -- MANUAL
# 11.2's whole complaint. So these read what the build actually emitted.
#
# It caught a real one on the day it was written: `garlic cloves` was landing
# on the spice rack, because `garlic` and `cloves` are the same length and the
# tie went the wrong way.

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
    """The blob covers every row, and every PUBLISHED entry can count people.

    tests/test_food_shopping.py proves every published recipe RESOLVES to a
    number from the two data files. This proves the number reached the page --
    a different claim, and the one that fails if the plugin stops running, is
    renamed, or quietly returns early.

    EVERY RECIPE, DRAFT OR NOT, SINCE #815. The batch box that let a recipe
    off this is gone: Helen ruled that "750 ml of gelato doesn't feed 50" and
    that the estimate belongs in the front matter, so `serves_estimate:` is on
    all 129 files whose `serves:` states no number. A recipe reaching the page
    without a portion count now gets NO BOX at all, which is visible; it used
    to get one that silently did nothing.

    What every recipe DOES need, draft or not, is `k` -- which key its yield
    came from. Without it a `makes:` prints behind the word "serves", which it
    did until 2026-09-07.
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
    """One row, one entry, in the build that actually ships.

    THE DIRECTION THAT MATTERS IS AN EXTRA ENTRY. The blob repeats the row
    gate rather than relaxing it, and it has to: a recipe with no row cannot be
    shortlisted from this page, so an entry for one is dead weight at best --
    and at worst it is a draft's or a held-back recipe's ingredient list
    published on the live index, in a build no local page can reproduce. That
    is #235's exact shape (a link built from `.url` for a document Jekyll never
    writes), one feature along, and only the production build can see it.

    The other direction is the ordinary bug: a row whose recipe contributes
    nothing, which is a shortlist entry the shopping list silently ignores.
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
    """`other` stays small, and what is in it is what is meant to be.

    An unmatched ingredient is not a bug -- it is a heading with things under
    it, and a miss costs a glance rather than an item. But `other` growing is
    the signal that _data/food/aisles.yml needs a keyword, and nothing else
    would ever say so. The ratchet is deliberately loose: it is here to catch a
    keyword table that has stopped being loaded at all, not to police one word.

    THE CROSS-RECIPE LINKS ARE SENT HERE ON PURPOSE and are counted. Five items
    across the collection name another recipe instead of a food, and a pointer
    to a whole other ingredient list has no shelf in a shop.
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

    # MEASURED SEPARATELY, AND HELD TO A LOOSER LINE -- MANUAL 8's own rule
    # about the ingredient picker, which applies here word for word:
    # "Measure production, not your local build. The local build folds in
    # every draft ... a vocabulary entry aimed at one is work done twice."
    # Drafts are absent in CI and in a fresh worktree, so this half only runs
    # on a machine that has cloned them, and it is a catastrophe detector --
    # a table that stopped being read -- rather than a vocabulary treadmill.
    if total["drafts"]:
        share = len(other["drafts"]) / total["drafts"]
        assert share <= 0.15, (
            f"{len(other['drafts'])} of {total['drafts']} DRAFT ingredients "
            f"({share:.0%}) have no aisle. Drafts are allowed a long tail -- "
            "they are unfinished and Helen adds them in batches -- but this is "
            "far enough out to suggest the keyword table is not being read."
        )


def test_water_is_never_on_a_shopping_list(site):
    """`never` is matched on the whole name, and it has to actually fire.

    The cocktails list refuses water through `not_on_cards`; this is food's
    half of the same idea. The second assertion is the interesting one: the
    rule is whole-name, so an ingredient that merely CONTAINS the word is still
    something you buy.
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
    """One truncation rule, two implementations, checked against each other.

    food/index.html derives `data-all-ingredients` in Liquid; the shopping list
    derives its names in Ruby. Both take an item up to its first comma or open
    bracket, and they have to agree or two features disagree about what an
    ingredient is -- the exclusion filter would offer you a word the shopping
    list never uses.

    THE ONE LEGITIMATE DIFFERENCE IS A CROSS-RECIPE LINK. Issue #273 drops
    `[grandma's lemon curd](../…)` from the exclusion index, because it is not
    a single food you can ask to avoid; the shopping list keeps it, because you
    do have to have made the curd. Those are excluded here by the aisle the
    plugin forces them into, which is the same fact stated once.
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


# =============================================================================
# "IF YOU LIKED THIS, HOW ABOUT …" — three related drinks. Issue #927
# =============================================================================
# WHY IT IS CHECKED IN THE PRODUCTION BUILD AND NOT THE LOCAL ONE. The row is
# built by looping `site.cocktail_recipes` in _layouts/cocktail.html, and that
# collection is only the PUBLISHED set in production: `_config_local.yml` sets
# `show_awaiting_fix`, which switches `_plugins/publish_gate.rb` off entirely,
# so a local build's row can legitimately offer a drink that is not live. The
# claim worth guarding -- a live drink page never points at one that is not --
# is only true of, and only visible in, the production build.
#
# AND IT IS THE SAME SHAPE AS #235, the bug the `prod_site` fixture exists for:
# a URL computed for a document that is never written is a correct-looking link
# to a 404. `test_no_link_in_the_production_build_points_at_a_file_that_isnt_there`
# would catch that much on its own; what it cannot see is a row of two, a row
# of four, or a drink offering itself.

RELATED_SECTION = re.compile(r'<ul class="cocktail-related drink-cards">(.*?)</ul>', re.S)
# The NAME's link only. Since 2026-09-11 the items are real cards (#955, and
# the index's own card since #991) and each carries chip links to the filtered
# index as well; those are `<a class="drink-card-mood ...">` and must not count
# as offered drinks.
RELATED_LINK = re.compile(r'<span class="drink-card-tape-word"><a href="([^"]+)">')


def _drink_pages(built_site):
    """Every built drink page, FOUND rather than named.

    MANUAL §12: "you will trust a corpus glob that names files instead of
    finding them" -- a page the corpus cannot see is a page whose row is never
    checked, silently. So this walks the output directory for whatever is
    there, and the caller asserts the count is plausible.
    """
    return sorted((built_site / "cocktails" / "recipes").rglob("index.html"))


def test_every_published_drink_page_offers_three_other_published_drinks(prod_site):
    """#927. Exactly three, never itself, and every one of them a real page.

    THE COUNT IS EXACTLY THREE, not "at most three". The template only emits
    a candidate whose score is above zero, so a drink sharing no mood and no
    ingredient generic with anything would quietly render a row of two, or a
    heading over nothing -- and the failure mode is invisible on any page but
    that drink's. `scripts/related_drinks.py` measured the corpus before the
    feature was written and still does: every drink's THIRD pick shares at
    least 3 today. This is what notices when a new drink, or a vocabulary edit
    that moves moods, changes that -- and that script is where to look when it
    fires, since it names which drink ran out of candidates and what it shares
    with the ones it has.

    NONE OF THEM IS THE PAGE ITSELF. The template excludes `page.url`, and a
    self-link here would be both a dead end and evidence that the exclusion had
    been written against the wrong field.
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
        if len(hrefs) != 3:
            problems.append(f"{url}: {len(hrefs)} related drinks, expected 3")

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


# =============================================================================
# "IF YOU LIKED THIS, HOW ABOUT …" on a RECIPE page — #1005, 2026-09-14
# =============================================================================
# The same claim as the drinks test above, for the same reasons: a live recipe
# page never offers a recipe that is not live, offers exactly three, and never
# itself. `scripts/related_recipes.py` is where to look when it fires.

RELATED_RECIPES_SECTION = re.compile(
    r'<ul class="recipe-list recipe-related">(.*?)</ul>', re.S)
# The TITLE's link only: each row also carries badge links to the filtered
# index, and those must not count as offered recipes.
RELATED_RECIPE_LINK = re.compile(r'<a class="recipe-title-link" href="([^"]+)">')


# --- the search-for-anything box's index, #1050 -------------------------------
# food/search.json and cocktails/search.json are what the box on a recipe or
# drink page searches. Each is generated from the same gated list its index
# renders -- the JSON copies the index's own Liquid rather than paraphrasing it
# -- and this is what notices if the two ever drift: a page in the JSON that
# does not exist is a dropdown result that 404s, and a built page missing from
# the JSON is one the box can never find.

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


def _recipe_pages(built_site):
    return sorted((built_site / "food" / "recipes").rglob("index.html"))


def test_every_published_recipe_page_offers_three_other_published_recipes(prod_site):
    """#1005. Exactly three, never itself, and every one of them a real page.

    The template only emits a candidate scoring above zero (shared tags plus
    shared main ingredients) or sharing the star and a mood, so a recipe
    unlike everything else would quietly render a row of two, or a heading
    over nothing, on its own page and nowhere else. `scripts/related_recipes.py`
    measured the published set the day this was written: every recipe's third
    pick shared at least 1. This is what notices when a promotion or a
    taxonomy edit changes that.
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


# =============================================================================
# HOW MUCH LIQUID IS IN A DRINK -- #1121
# =============================================================================
# Helen: "add total ml next to recipe scaler to help me choose the right number
# of glasses... This means I can vary target units of alcohol myself." Two
# sentences came out of that, and the whole risk is that they are DIFFERENT
# NUMBERS:
#
#   under the scaler   "Approximately 360 ml"   -- the BATCH, and it moves
#   in the footer      "...in a serving of 90 ml." -- ONE GLASS, and it must not
#
# The second guarantee is structural rather than remembered: the moving figure
# lives on `.cocktail-scale-total`, which carries `data-total-ml`, and the units
# line carries no attribute any of this could reach. These tests are what says
# so about BUILT HTML, which is the only place the two sentences meet.
#
# BOTH LINES ARE PRODUCTION, so `prod_site`. The units line went live with #1001
# and the volume line is ungated for the same reason: neither is a price.

SCALE_TOTAL = re.compile(
    r'<p class="cocktail-scale-total" data-total-ml="([^"]*)">(.*?)</p>', re.S)
UNITS_LINE = re.compile(r'<p class="cocktail-units"(.*?)</p>', re.S)
SERVING_OF = re.compile(r"in (?:a serving|each of \d+ servings) of ([\d.]+) ml\.")

# THE DRINKS THAT STATE NO VOLUME, PINNED BY NAME -- see `volume_for` in
# _plugins/cocktail_units.rb for the rule and the argument.
#
# A TOPPED DRINK IS NOT ONE OF THEM, since Helen's ruling of 2026-09-17:
# "Midpoint please, I'll cope on the spot." Five drinks printed nothing for
# half a day because `top_up_ml` is a house range #1076 has shown is a
# stand-in; they now spend its midpoint, which is what the unit count beside
# them has always done, and her "Approximately" carries the span.
#
# WHAT IS LEFT IS A DIFFERENT KIND OF DRINK: one whose excluded pours ARE the
# drink, where a figure would be WRONG rather than rough. The same judgement,
# and the same constant, as `cost.complete`. The Bellini is both topped and
# incomplete, and resolving its top does not rescue it -- six of its eight
# pours are a batch syrup only its method portions.
#
# A RATCHET IN BOTH DIRECTIONS, deliberately. A new name here means a drink
# quietly lost a figure it used to print; a name leaving means one gained a
# figure, which is either a data fix (good -- update this list in that commit)
# or the withholding rule being weakened by accident.
NO_VOLUME_STATED = {
    "caipirinha",
    "pear-apricot-and-rosemary-bellini",
}


def test_the_drinks_that_state_no_volume_are_exactly_the_ones_that_cannot(prod_site):
    """#1121. A figure known to be wrong is worse than no figure.

    The rule is in the plugin; this is the census of what it actually withheld,
    on the built pages, where a Liquid guard that silently inverted would show.
    """
    pages = _drink_pages(prod_site)
    assert len(pages) > 20, (
        f"only {len(pages)} drink pages in the production build -- the corpus "
        "walk is looking in the wrong place."
    )

    silent = {p.parent.name for p in pages
              if not SCALE_TOTAL.search(p.read_text(encoding="utf-8"))}

    assert silent == NO_VOLUME_STATED, (
        "the set of drinks printing no volume has moved.\n"
        f"  newly silent (lost a figure they used to print): "
        f"{sorted(silent - NO_VOLUME_STATED)}\n"
        f"  newly speaking (gained one): {sorted(NO_VOLUME_STATED - silent)}\n"
        "`volume_for` in _plugins/cocktail_units.rb has the rule: a drink says "
        "nothing only when its excluded pours ARE the drink, so a figure would "
        "be wrong rather than rough. A topped drink is NOT such a drink -- it "
        "spends the midpoint of its declared range (Helen, 2026-09-17: "
        "\"Midpoint please, I'll cope on the spot\")."
    )


def test_a_drink_with_no_volume_keeps_the_units_sentence_it_had_before(prod_site):
    """The tail is DROPPED, never guessed, and the old sentence is the fallback.

    Helen's wording is "Roughly X units of alcohol in a serving of Y ml". Where
    Y would be wrong the line falls back to exactly what #753 shipped -- "in a
    serving." -- rather than inventing a figure or a hedge. The Caipirinha is
    the only drink this reaches today. The Bellini has no units line at all (no
    alcohol is recorded in its ingredients), which is a separate, older
    withholding and not this one.
    """
    problems = []
    for page in _drink_pages(prod_site):
        slug = page.parent.name
        if slug not in NO_VOLUME_STATED:
            continue
        units = UNITS_LINE.search(page.read_text(encoding="utf-8"))
        if not units:
            continue
        if SERVING_OF.search(units.group(1)):
            problems.append(f"{slug}: states a serving volume it cannot know")
        elif "in a serving." not in units.group(1) \
                and "servings." not in units.group(1):
            problems.append(f"{slug}: {' '.join(units.group(1).split())}")

    assert not problems, (
        "a drink with no stated volume must keep #753's own sentence:\n  "
        + "\n  ".join(problems)
    )


def test_only_the_scaler_line_carries_a_figure_the_scaler_can_reach(prod_site):
    """THE ONE THING THAT KEEPS THE UNITS LINE STILL.

    cocktail-scale.js writes to `.cocktail-scale-total-figure` and to nothing
    else on this subject; it finds that element by `data-total-ml`. If that
    attribute ever appears on `.cocktail-units`, the per-serving figure becomes
    reachable by the multiple box, which is the bug the layout's own comment
    says to come here for. Cheap to check and impossible to notice by eye.
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

        attr, body = total.group(1), " ".join(total.group(2).split())
        assert re.fullmatch(r"[\d.]+", attr), f"{slug}: data-total-ml={attr!r}"
        figure = float(attr)
        assert figure > 0, f"{slug}: a volume of {figure}"

        # THE PRINTED FIGURE IS THE ATTRIBUTE. The browser multiplies the
        # attribute; the reader reads the text. At x1 they are the same number,
        # and the day they are not, the line lies the moment anyone touches it.
        expected = ("Approximately "
                    f'<span class="cocktail-scale-total-figure">{attr}</span> ml')
        if expected not in " ".join(total.group(0).split()):
            problems.append(f"{slug}: {body!r} does not print {attr} ml")

        # AND WHERE A DRINK IS ONE GLASS, THE FOOTER SAYS THE SAME NUMBER --
        # the batch at x1 IS the serving. A punch divides by `serves:` and is
        # left out of this comparison rather than given a second sum here.
        units = UNITS_LINE.search(html)
        if units and "each of" not in units.group(1):
            said = SERVING_OF.search(units.group(1))
            if said and float(said.group(1)) != figure:
                problems.append(
                    f"{slug}: the scaler says {figure} ml and the units line "
                    f"says {said.group(1)} ml for the same single glass")

    assert not problems, (
        "the two volume figures on a drink page have come apart:\n  "
        + "\n  ".join(problems[:20])
    )


TOP_UP_POUR = re.compile(r'<span class="cocktail-amount">\s*to top\s*</span>')


def _topped_pages(built_site):
    """Every built drink page that prints a `to top` in its amounts."""
    return [p for p in _drink_pages(built_site)
            if TOP_UP_POUR.search(p.read_text(encoding="utf-8"))]


def test_a_topped_drink_spends_the_midpoint_of_its_declared_range(prod_site):
    """Helen, 2026-09-17: "Midpoint please, I'll cope on the spot."

    THE MIDPOINT, NOT EITHER END, and that is the whole of what this checks.
    `top_up_ml` declares 100-150 for soda water; the Tom Collins pours
    60 + 30 + 22.5 = 112.5 ml before it, so the three answers a plausible bug
    could give are 212.5 (`ml_min`), 237.5 (the midpoint) and 262.5 (`ml_max`).
    Read out of costs.yml rather than typed here, so changing the house range
    changes this test's expectation with it -- the claim is about the RULE.

    It is also, quietly, the check that both callers still share one
    expression: the footer's unit count has spent this midpoint since #297, and
    `top_up_ml` in the plugin is now the one place either of them asks.
    """
    costs = yaml.safe_load(
        (ROOT / "_data" / "cocktails" / "costs.yml").read_text(encoding="utf-8"))
    soda = (costs.get("top_up_ml") or {}).get("soda water")
    assert soda, "costs.yml declares no `top_up_ml` for soda water"
    midpoint = (float(soda["ml_min"]) + float(soda["ml_max"])) / 2

    page = prod_site / "cocktails" / "recipes" / "tom-collins" / "index.html"
    assert page.exists(), "the Tom Collins is not in the production build"
    html = page.read_text(encoding="utf-8")

    total = SCALE_TOTAL.search(html)
    assert total, (
        "the Tom Collins prints no volume. Since 2026-09-17 a topped drink "
        "takes the midpoint of its declared range rather than withholding."
    )
    expected = 60 + 30 + 22.5 + midpoint
    assert float(total.group(1)) == expected, (
        f"the Tom Collins totals {total.group(1)} ml; its build is "
        f"60 + 30 + 22.5 = 112.5 and soda water's declared "
        f"{soda['ml_min']}-{soda['ml_max']} ml has midpoint {midpoint}, so it "
        f"should be {expected}. `ml_min` would give "
        f"{112.5 + float(soda['ml_min'])} and `ml_max` "
        f"{112.5 + float(soda['ml_max'])}."
    )


def test_no_topped_drink_is_also_a_punch(prod_site):
    """A PRIMED TRAP, AND THIS IS THE PIN -- `volume_for`'s closing note.

    `serve_ml` divides the whole total by `serves:`, the top included. For a
    bowl that is right about alcohol (it is shared out) and wrong about a top:
    a top fills ONE glass, and four glasses need four tops. scripts/top_up_ml.py
    found the same thing on the same data and said so.

    No topped drink declares `serves:` today, so the two rules have never
    disagreed on a real drink. This is what makes the first topped punch a red
    build rather than a quietly wrong number -- the fix is to add the top after
    the division rather than before it, in `volume_for`, and to ask Helen what
    the scaler's own line should then say.

    READ OFF THE BUILT PAGE, not the front matter: a drink with `serves:` is
    exactly the drink whose units line says "in each of N servings".
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
    """ONE ANCHOR WITH A REAL NUMBER IN IT, checkable by eye.

    52.5 + 15 + 7.5 + 15 = 90 ml, and every other test above checks a
    RELATIONSHIP -- which would all still pass if the plugin's arithmetic were
    wrong in the same way in both places. This is the one that would not.

    If Helen repours the Aviation, this test names itself and the fix is this
    number. It is not a claim about the recipe; it is a claim about the sum.
    """
    page = prod_site / "cocktails" / "recipes" / "aviation" / "index.html"
    assert page.exists(), "the Aviation is not in the production build"
    html = page.read_text(encoding="utf-8")

    total = SCALE_TOTAL.search(html)
    assert total, "no volume line on the Aviation"
    assert total.group(1) == "90", (
        f"the Aviation totals {total.group(1)} ml; its amounts are "
        "52.5 + 15 + 7.5 + 15 = 90"
    )
    assert "Approximately" in total.group(2), (
        "Helen's wording is 'Approximately X ml' (#1121, §13.12: the voice is "
        f"hers). The line now reads: {' '.join(total.group(2).split())!r}"
    )

    units = UNITS_LINE.search(html)
    assert units, "no units line on the Aviation"
    assert "of alcohol in a serving of 90 ml." in " ".join(units.group(1).split()), (
        "Helen's wording is 'Roughly X units of alcohol in a serving of Y ml' "
        f"(#1121). The line now reads: {' '.join(units.group(1).split())!r}"
    )
