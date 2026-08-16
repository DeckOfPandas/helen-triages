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

import pathlib
import re
import shutil
import subprocess

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "tmp" / "_test_site"


@pytest.fixture(scope="session")
def site() -> pathlib.Path:
    """Build once per run, into the project's own tmp/ (never /tmp — CLAUDE.md).

    Uses the local config as well as the production one, so drafts build and the
    output matches what Helen actually looks at.
    """
    if shutil.which("bundle") is None:
        pytest.skip("no bundler on this machine; skipping rendered-output tests")

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
    if shutil.which("bundle") is None:
        pytest.skip("no bundler on this machine; skipping rendered-output tests")

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
