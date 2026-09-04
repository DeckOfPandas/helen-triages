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
    globs in HANDOVER §12: not a scan that matched nothing, but a source list
    that quietly stopped covering the files.

    WHY THIS IS A SEPARATE TEST WITH A DIFFERENT RULE, rather than four more
    paths added to the glob above. Measured before writing: of 41 classes in
    those partials, 10 are styled and **all 31 unstyled ones are BEM
    modifiers whose base is styled** — `glass-icon--rocks` beside
    `.glass-icon`, `nav-icon--food` beside `.nav-icon`. Not one modifier is
    styled anywhere in either stylesheet. So modifiers here are hooks, exactly
    as HANDOVER 11.3 describes, and demanding a rule for each would report 31
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
          "HANDOVER 11.3. A base with no rule at all is a typo or a deletion "
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
            '  date_last_edited: "2026-08-18"\n---\n')
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
    '  date_last_edited: "2026-09-02"\n---\n'
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
    'meta:\n  ship: "yes"\n  date_last_edited: "2026-09-02"\n'
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
    """The nav row and the whole footer are byte-identical across both sites.

    Not "equivalent", not "both present" -- identical source text. Anything a
    page is allowed to vary is by definition not part of the shared chrome, so
    there is nothing here to normalise away and no tolerance to tune. If this
    test ever needs an exception carved into it, that exception IS a second
    header arriving, and it wants arguing rather than accommodating.

    The wordmark is deliberately OUT of scope: `[ FOOD ]` versus
    `[ COCKTAILS ]`, and the home link under it, say where you are, which is the
    one job the chrome still does per-site. It lives in .site-title-link, above
    the nav row this test reads, so the two are already separated in the markup.
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

        reference_url, reference = next(iter(chromes.items()))
        for url, chrome in chromes.items():
            if chrome[block] == reference[block]:
                continue
            raise AssertionError(
                f"The {block} differs between {reference_url} and {url}.\n\n"
                f"{reference_url}:\n{reference[block]}\n\n"
                f"{url}:\n{chrome[block]}\n\n"
                f"There is ONE header and ONE footer in this repo (issue #374). "
                f"A difference here means something in _layouts/default.html has "
                f"started branching on site_key again, or a value it reads out of "
                f"_data/sites.yml has become per-site when it should be in "
                f"_data/chrome.yml. Both are how the two drifted apart before."
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
    # bases that ARE styled (HANDOVER 11.3), styled by nobody, consistently, on
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
    not render. HANDOVER 2.4 records that this is the designed behaviour and
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

    HANDOVER 8.1: these are not two implementations. Both call
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
        + "\n\nThey share one code path and one set of ranked results (HANDOVER "
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
    """
    css = (site / "assets" / "css" / "food.css").read_text(encoding="utf-8")

    # Rules whose selector says "a filter button in its selected state".
    blocks = re.findall(r"([^{}]+)\{([^{}]*)\}", css)
    active = [(sel.strip(), body) for sel, body in blocks
              if re.search(r"\.btn-(?:tag|star|meta|ingredient|exclude)[^,{]*\.active", sel)]
    assert active, (
        "No active filter-button rules found in the compiled CSS. Either the "
        "class naming changed or this pattern went stale -- and a scan that "
        "matches nothing passes while checking nothing."
    )

    offenders = []
    for sel, body in active:
        for decl in body.split(";"):
            prop = decl.split(":")[0].strip().lower()
            if prop in LAYOUT_PROPERTIES:
                offenders.append(f"{sel} declares {decl.strip()}")

    assert not offenders, (
        "Active filter-button rule(s) declare a property that changes the "
        "button's size:\n  " + "\n  ".join(sorted(set(offenders)))
        + "\n\nThe button grows or shrinks the moment it is selected, and every "
          "button after it on the row moves (issue #389). A selected state may "
          "change colour, .tag-shape fill and -webkit-text-stroke, none of "
          "which occupies space. If a metric genuinely must change, change the "
          "RESTING state to match so the two agree."
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
        "passes while checking nothing (HANDOVER 12)."
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
    nothing at small type" of HANDOVER 12, which is at least a change, but a
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
                            job HANDOVER §9.13 gives the card: say why you are
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
          "HANDOVER §9.13 says a card must never be, and a candidate pool that "
          "marks nothing is issue #390 on the other index."
    )
