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
    html = page(site, "/food/reference/temperatures/")
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
        ("/food/reference/temperatures/", data["pork"]["roasting"]),
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


def test_every_chart_row_draws_its_filled_bar(site):
    """The gap in the rendered tests I wrote to catch exactly this.

    They asserted on the row, the label, the value and the shaded zone -- the
    things AROUND the measurement -- and never on the mark that carries it. So
    when every filled bar vanished, six rendered tests still passed.
    """
    for url in ("/food/reference/temperatures/", "/food/recipes/roast-beef-fillet/"):
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
    """Flagged recipes are absent from the production build; unflagged are present.

    GitHub issue #331. tests/test_site_config.py checks the gate's PARTS exist
    and tests/test_front_matter.py checks the DATA is well formed. This is the
    only one that checks the gate actually does anything, against a real
    production build -- the same place the swatch-page bug (#276) was invisible
    until someone looked at the output rather than the source.

    BOTH DIRECTIONS ON PURPOSE. The flagged half is the feature. The UNFLAGGED
    half is what stops the fix being "hide everything": a plugin that dropped
    every document would satisfy the flagged assertion perfectly and take the
    site down, and with no recipe currently flagged that would be the only
    assertion running.
    """
    import yaml as _yaml
    import re as _re

    flagged, clear = [], []
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        fm = _re.match(r"\A---\n(.*?)\n---", raw, _re.S)
        meta = (_yaml.safe_load(fm.group(1)) or {}).get("meta", {}) or {}
        (flagged if meta.get("awaiting_fix") is True else clear).append(path.stem)

    assert clear, (
        "No unflagged recipes at all -- this test would pass while checking "
        "nothing, which is what tests/test_suite_hygiene.py exists to prevent."
    )

    published = [s for s in flagged if (prod_site / "food" / "recipes" / s / "index.html").exists()]
    assert not published, (
        "Recipe(s) flagged `meta.awaiting_fix: true` were PUBLISHED anyway:\n  "
        + "\n  ".join(published)
        + "\n\nThe gate has failed open. Check _plugins/hide_awaiting_fix.rb "
          "still reads `awaiting_fix`, that _config.yml sets "
          "`show_awaiting_fix: false`, and that the build is not running in "
          "Jekyll's safe mode, which ignores _plugins/ without warning."
    )

    vanished = [s for s in clear if not (prod_site / "food" / "recipes" / s / "index.html").exists()]
    assert not vanished, (
        "Unflagged recipe(s) missing from the production build:\n  "
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
            '  proofread: false\n{flag}  cooked_before: false\n'
            '  date_last_edited: "2026-08-18"\n---\n')
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
            + "\n\n_plugins/hide_awaiting_fix.rb must publish only on an "
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
