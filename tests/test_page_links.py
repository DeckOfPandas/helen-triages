"""Links between the site's own HTML pages -- GitHub issue #220.

WHY THIS FILE EXISTS. tests/test_taxonomy.py's link tests are thorough -- four
separate tests, each written after a real bug -- but every one of them reads
`_food_recipes/*.md` front matter. Not one looks at an `href` written into an
HTML template. Two real bugs got through that gap:

  1. food/reference/index.html linked to `internal-temperatures/` for a day
     after that page was deleted. (That page is gone too now, so this exact
     link is history -- but it is why this file exists.)
  2. food/reference/cooking-methods.html linked to `../temperatures/#steak`
     and `../temperatures/#fish`, twice each. Those fragments never existed --
     the real ids are `#beef-steak` and `#fish-salmon`. A wrong fragment does
     not 404: the page loads and the browser lands at the top, so the symptom
     reads as "the scroll doesn't work", not "the link is broken".

WHAT THIS FILE SCANS. Every `<a href="...">` in food/**/*.html,
cocktails/**/*.html, _layouts/*.html, _includes/**/*.html and the root
index.html. `<link>` tags (stylesheet, favicon) are not `<a>` tags and are not
in scope -- this is about navigation between the site's own pages.

WHAT "PUBLISHED" MEANS, AND WHERE IT COMES FROM. Derived, not hardcoded, from
the same two places Jekyll itself reads:
  - an ordinary page's own front matter `permalink:` (falling back to
    Jekyll's own default, `/:path:output_ext`, for the couple of pages that
    don't set one -- food/swatch.html, food/swatch-scribbles.html);
  - `_config.yml`'s `collections:` block, which gives each collection's
    `permalink:` pattern and whether it publishes at all (`output: true`) --
    `_food_drafts/` is `output: false` and is correctly NOT a valid link
    target, the same rule test_taxonomy.py's PUBLISHED set already applies to
    markdown links.
A page added tomorrow, in either form, is covered tomorrow without this file
changing.

PURE-FRAGMENT LINKS (`href="#top"`). Checked here, not skipped. Bug #2 above
is a same-page-shaped mistake wearing a cross-page hyperlink -- nothing stops
the identical typo happening in a same-page `href="#top"`, and the symptom
(loads fine, scrolls nowhere) is identical either way. There is no principled
reason to check a fragment only when it happens to follow a path.

IDS INSIDE AN INCLUDE, AND INSIDE A LOOP. `_includes/food/method_table.html`
emits `<h2 ... id="{{ include.id }}">` -- a Liquid parameter, not a literal,
so scanning that file's own text finds no id there at all. Every call site
passes a literal (`id="beef"`, `id="chicken"`, ...), so this file resolves
that id by reading the literal argument at each `{% include %}` call site
instead of trying to read the partial in isolation. The reverse problem
happens too: that same partial's own `href="#top"` targets an id that lives
not in its own text but in whichever page includes it
(food/reference/cooking-methods.html's `<article id="top">`). So id
resolution for any one file floods outward along both `{% include %}` edges
(in either direction) and the `layout:` chain, rather than looking at a
single file's text alone -- see `_ids_visible_from()`.

There is no id generated inside a genuine `{% for %}` loop that this file
checks statically anywhere in this codebase today (checked by hand against
every `id="..."` in the templates). The one place a link fragment IS built
from a loop-like indirection -- `_includes/food/doneness_chart.html`'s
`#{{ _anchor }}`, where `_anchor` comes from a recipe's `internal_temp_ref`
resolving into `_data/food/internal_temperatures.yml`'s `chart_anchor:`
field -- is handled by a separate, narrower test
(`test_chart_anchor_fragments_exist_on_the_temperatures_page`) that reads
every declared `chart_anchor:` value directly from the data file, rather than
by simulating the recipe -> data lookup here.

EXTERNAL LINKS, `mailto:`, AND THE PDF LINK. A scheme (`http:`, `mailto:`) or
a protocol-relative `//` is skipped -- genuinely out of this site's control.
`.pdf` links (recipe.html's own "pdf" button) are skipped too: the target
isn't an HTML page Jekyll publishes, and the two ends of that link (the href
here, and the directory scripts/generate_pdfs.py writes into) are already
guarded by tests/test_site_config.py::test_pdf_link_points_where_the_pdfs_are_written.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import pytest
import yaml

# Suite marker, so `pytest -m shared` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.shared

ROOT = Path(__file__).resolve().parent.parent

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


# --- the corpus of files whose <a href> we check ----------------------------

PAGE_FILES = (
    sorted(ROOT.glob("food/**/*.html"))
    + sorted(ROOT.glob("cocktails/**/*.html"))
    + [ROOT / "index.html"]
)
LAYOUT_FILES = sorted(ROOT.glob("_layouts/*.html"))
INCLUDE_FILES = sorted(ROOT.glob("_includes/**/*.html"))
ALL_TEMPLATE_FILES = PAGE_FILES + LAYOUT_FILES + INCLUDE_FILES


# --- what the site publishes, and at what URL --------------------------------

def _default_page_url(path: Path) -> str:
    """Jekyll's own fallback for a page with no `permalink:`: `/:path:output_ext`."""
    rel = path.relative_to(ROOT).with_suffix("")
    return "/" + str(rel).replace("\\", "/") + ".html"


def page_url(path: Path) -> str:
    permalink = front_matter(path).get("permalink")
    return permalink if permalink else _default_page_url(path)


PAGE_URL_BY_FILE: dict[Path, str] = {f: page_url(f) for f in PAGE_FILES}


def _collection_pages() -> dict[str, Path]:
    """url -> source file, for every PUBLISHED collection document.

    Reads _config.yml directly rather than assuming food_recipes/
    cocktail_recipes -- a collection added later is picked up the same way.
    `output: false` (food_drafts) is deliberately excluded: those pages get
    no public URL, so a link to one would 404 in production even though the
    file exists on disk, exactly the rule test_taxonomy.py's PUBLISHED set
    already applies to markdown-to-markdown links.
    """
    config = yaml.safe_load((ROOT / "_config.yml").read_text(encoding="utf-8")) or {}
    pages: dict[str, Path] = {}
    for name, spec in (config.get("collections") or {}).items():
        spec = spec or {}
        if not spec.get("output"):
            continue
        permalink = spec.get("permalink")
        source_dir = ROOT / f"_{name}"
        if not permalink or not source_dir.is_dir():
            continue
        for f in sorted(source_dir.glob("*.md")):
            pages[permalink.replace(":path", f.stem)] = f
    return pages


PAGES: dict[str, Path] = {url: f for f, url in PAGE_URL_BY_FILE.items()}
PAGES.update(_collection_pages())


# --- resolving ids, including ones behind an {% include %} or a layout ------

INCLUDE_TAG = re.compile(
    r"\{%-?\s*include\s+([\w./-]+\.html)((?:\s+[\w.-]+\s*=\s*"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s%}]+))*)\s*-?%\}",
    re.S,
)
PARAM = re.compile(r'([\w.-]+)\s*=\s*"([^"]*)"')
STATIC_ID = re.compile(r'id="([^"{}]+)"')
PASSTHROUGH_ID = re.compile(r'id="\{\{\s*include\.(\w+)\s*\}\}"')


def _includes_of(path: Path) -> list[tuple[Path, dict]]:
    """(partial file, literal call-site params) for every {% include x.html
    ... %} in `path` whose target is a literal path. `{% include {{ var }} %}`
    (default.html's site-icon/switch-icon includes) has a computed target and
    is skipped -- it never carries an id or an href in this codebase, only an
    SVG partial.
    """
    text = path.read_text(encoding="utf-8")
    out = []
    for m in INCLUDE_TAG.finditer(text):
        partial = ROOT / "_includes" / m.group(1)
        if partial.exists():
            out.append((partial, dict(PARAM.findall(m.group(2) or ""))))
    return out


def _own_layout(path: Path) -> Path | None:
    layout = front_matter(path).get("layout")
    if not layout:
        return None
    candidate = ROOT / "_layouts" / f"{layout}.html"
    return candidate if candidate.exists() else None


def _build_parents_map(files: list[Path]) -> dict[Path, list[tuple[Path, dict]]]:
    parents: dict[Path, list[tuple[Path, dict]]] = {}
    for f in files:
        for partial, params in _includes_of(f):
            parents.setdefault(partial, []).append((f, params))
    return parents


PARENTS_MAP = _build_parents_map(ALL_TEMPLATE_FILES)


@lru_cache(maxsize=None)
def _ids_visible_from(start: Path) -> frozenset:
    """Every id reachable from `start` -- its own static ids, plus its
    layout's, plus anything it {% include %}s, plus (the reverse direction)
    anything that {% include %}s IT, with `id="{{ include.X }}"` resolved
    against that specific call site's literal params.

    Floods outward rather than looking at one file alone, because a fragment
    link written inside a partial or a layout targets an id that may not live
    in that file's own text at all (method_table.html's own `href="#top"`
    targets `<article id="top">`, which is only in the page that includes
    it). Used both to check a same-file `#fragment` link (start = the file
    the link was found in) and to check a cross-page `path/#fragment` link
    (start = the target page's own file).
    """
    seen: set[Path] = set()
    ids: set[str] = set()
    stack = [start]
    while stack:
        f = stack.pop()
        if f in seen or not f.exists():
            continue
        seen.add(f)
        text = f.read_text(encoding="utf-8")
        ids |= set(STATIC_ID.findall(text))
        layout = _own_layout(f)
        if layout is not None:
            stack.append(layout)
        for partial, _params in _includes_of(f):
            stack.append(partial)
        for parent, params in PARENTS_MAP.get(f, []):
            stack.append(parent)
            for m in PASSTHROUGH_ID.finditer(text):
                if m.group(1) in params:
                    ids.add(params[m.group(1)])
    return frozenset(ids)


# --- turning a raw href="..." into a literal target, where possible ---------

A_HREF = re.compile(r'<a\b[^>]*?\bhref="([^"]*)"', re.I | re.S)
EXTERNAL = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)")
LIQUID_RELATIVE = re.compile(r"^\{\{\s*'([^']+)'\s*\|.*?relative_url\s*\}\}(.*)$", re.S)
ASSIGN_REF = re.compile(r"^\{\{\s*(\w+)\s*\}\}(.*)$", re.S)
ASSIGN_LITERAL = re.compile(
    r'\{%-?\s*assign\s+(\w+)\s*=\s*"([^"]+)"\s*\|[^%]*?relative_url[^%]*?-?%\}', re.S
)

# Header nav hrefs are built from `this_site`/`sibling_site` (Liquid
# variables read from _data/sites.yml, resolved per page), and the two
# per-item loop links are built from Jekyll's own `.url` on each document.
# Neither is a literal this scanner can read out of the template text, so
# both are resolved a different way instead of being silently skipped:
#   - this_site.home / this_site.about_url / sibling_site.home ->
#     test_site_nav_links_resolve_to_real_pages, which reads sites.yml
#     directly.
#   - recipe.url / cocktail.url -> not checked at all, deliberately: Jekyll
#     computes `.url` from the document's own permalink, so it is correct by
#     construction and there is nothing for a link-shape test to add.
# A new href this scanner can't trace to a literal, and that isn't one of
# these, fails test_no_link_shape_is_silently_unresolved instead of quietly
# passing.
TRUSTED_DYNAMIC = (
    re.compile(r"^\{\{\s*this_site\.home\s*\|\s*default:\s*'/'\s*\|\s*relative_url\s*\}\}$"),
    re.compile(r"^\{\{\s*sibling_site\.home\s*\|\s*relative_url\s*\}\}$"),
    re.compile(r"^\{\{\s*this_site\.about_url\s*\|\s*relative_url\s*\}\}$"),
    # The footer's reference links, added 2026-08-16. Same shape and same
    # treatment as the three above: the value lives in _data/sites.yml, so this
    # scanner cannot read it out of the template, and
    # test_site_nav_links_resolve_to_real_pages checks every one of them
    # against the published-page set instead.
    re.compile(r"^\{\{\s*link\.url\s*\|\s*relative_url\s*\}\}$"),
    re.compile(r"^\{\{\s*(?:recipe|cocktail)\.url\s*\|\s*relative_url\s*\}\}$"),
    # _layouts/cocktail.html's source link, added 2026-08-16 with the cocktail
    # schema. DIFFERENT REASON FROM EVERY OTHER ENTRY ABOVE, and worth saying
    # so plainly rather than letting it inherit their justification: the others
    # are internal links this scanner cannot read but something else checks.
    # `source_url` is an EXTERNAL address typed into a drink's front matter --
    # a magazine, a bar's site, a video. It is out of scope for exactly the
    # reason _scan() already skips a literal `http://` href: it points
    # somewhere this site does not control.
    #
    # So it is UNCHECKED, not checked elsewhere. Nothing here or anywhere else
    # verifies a source_url resolves, and a dead one will rot silently. If that
    # ever matters, the answer is a link-rot checker run deliberately and
    # offline, not a rule in this file -- which asserts about the site's own
    # pages and would have to make a network call to say anything at all.
    re.compile(r"^\{\{\s*page\.source_url\s*\}\}$"),
)


def _assigns(path: Path) -> dict[str, str]:
    """{% assign name = "literal" | ... relative_url ... %} in `path` --
    index.html builds its redirect target this way (`redirect_url`), one hop
    away from the href itself.
    """
    return dict(ASSIGN_LITERAL.findall(path.read_text(encoding="utf-8")))


def _literal_target(raw: str, assigns: dict[str, str]) -> str | None:
    """The literal href string `raw` resolves to, or None if this scanner
    cannot trace it back to one (see TRUSTED_DYNAMIC above for what that
    covers instead)."""
    raw = raw.strip()
    m = LIQUID_RELATIVE.match(raw)
    if m:
        return m.group(1) + m.group(2)
    if raw.startswith("../") or raw.startswith("#"):
        return raw
    m2 = ASSIGN_REF.match(raw)
    if m2 and m2.group(1) in assigns:
        return assigns[m2.group(1)] + m2.group(2)
    return None


# --- the scan itself ----------------------------------------------------------

def _scan() -> dict:
    problems = {"bad_path": [], "bad_fragment": [], "unresolved": []}
    scanned = 0
    for f in ALL_TEMPLATE_FILES:
        text = f.read_text(encoding="utf-8")
        assigns = _assigns(f)
        source_label = str(f.relative_to(ROOT))
        source_url = PAGE_URL_BY_FILE.get(f)  # None for a layout/include

        for raw in A_HREF.findall(text):
            if ".pdf" in raw or EXTERNAL.match(raw.strip()) or raw.strip().startswith("mailto:"):
                continue
            scanned += 1

            target = _literal_target(raw, assigns)
            if target is None:
                if not any(p.match(raw.strip()) for p in TRUSTED_DYNAMIC):
                    problems["unresolved"].append(f'{source_label}: href="{raw}"')
                continue

            if target.startswith("#"):
                frag = target[1:]
                if frag and frag not in _ids_visible_from(f):
                    problems["bad_fragment"].append(
                        f'{source_label}: href="{raw}" -- no id="{frag}" reachable '
                        f"from this file"
                    )
                continue

            base = source_url or "/"
            split = urlsplit(urljoin(base, target))
            path, fragment = split.path, split.fragment

            if path not in PAGES:
                problems["bad_path"].append(
                    f'{source_label}: href="{raw}" -> {path!r}, no published page there'
                )
                continue

            if fragment and "{" not in fragment:
                if fragment not in _ids_visible_from(PAGES[path]):
                    problems["bad_fragment"].append(
                        f'{source_label}: href="{raw}" -> {path}#{fragment}, no '
                        f'id="{fragment}" on that page'
                    )

    problems["_scanned"] = scanned
    return problems


_PROBLEMS = _scan()


# --- the tests -----------------------------------------------------------------

def test_the_scanned_link_corpus_is_not_empty():
    """The whole-corpus guard tests/test_suite_hygiene.py enforces: every
    test below only means something if there was something to scan. If this
    ever legitimately hits zero -- every <a href> removed from every page,
    layout and include at once -- delete the checks below with it, rather
    than letting them pass while checking nothing.
    """
    assert PAGES, (
        "No published pages were derived from front matter permalink: or "
        "_config.yml's collections:. Either the site has no pages any more, "
        "or the derivation above has stopped finding them -- check which "
        "before trusting anything below."
    )
    assert _PROBLEMS["_scanned"] > 0, (
        "No <a href=...> found across food/**/*.html, cocktails/**/*.html, "
        "_layouts/*.html, _includes/**/*.html or index.html. Either the site "
        "has genuinely gone link-free, or A_HREF has stopped matching -- "
        "check which before trusting the green below."
    )


def test_internal_links_point_at_a_published_page():
    problems = _PROBLEMS["bad_path"]
    assert not problems, (
        "Internal link(s) point at a page nothing publishes:\n  "
        + "\n  ".join(problems)
        + "\n\nEither the target was renamed or deleted and this link was "
          "never updated, or it is missing its trailing slash -- every page "
          "on this site is directory-style (/a/b/), and '/a/b' without the "
          "slash is a different, unpublished path."
    )


def test_internal_link_fragments_exist_on_their_target():
    problems = _PROBLEMS["bad_fragment"]
    assert not problems, (
        "Internal link(s) point at a #fragment their target page never "
        "emits:\n  " + "\n  ".join(problems)
        + "\n\nA wrong fragment does not 404 -- the page loads and the "
          "browser lands at the top, so this reads as a missing scroll, not "
          "a broken link. Fix the fragment in the href, or the id it's "
          "supposed to point at."
    )


def test_no_link_shape_is_silently_unresolved():
    """Guards the scanner itself, not the content. A href this test cannot
    trace back to a literal path is either explicitly trusted above
    (TRUSTED_DYNAMIC, each checked a different way -- see
    test_site_nav_links_resolve_to_real_pages and
    test_chart_anchor_fragments_exist_on_the_temperatures_page) or it is new,
    and a link this test cannot see is a link it cannot catch breaking --
    exactly the "found nothing, so nothing failed" trap
    tests/test_suite_hygiene.py exists to catch, wearing a per-item mask.
    """
    problems = _PROBLEMS["unresolved"]
    assert not problems, (
        "href value(s) this scanner cannot resolve to a literal path, and "
        "that are not on the TRUSTED_DYNAMIC allow-list:\n  "
        + "\n  ".join(problems)
        + "\n\nEither teach _literal_target() to trace it, or -- if it is "
          "provably always correct the way recipe.url/cocktail.url are "
          "(Jekyll computes those from the document's own permalink) -- add "
          "it to TRUSTED_DYNAMIC with a comment saying why, and how it's "
          "checked instead."
    )


def test_site_nav_links_resolve_to_real_pages():
    """_layouts/default.html's header nav builds its hrefs from
    _data/sites.yml (this_site.home, this_site.about_url, sibling_site.home)
    rather than a literal path in the template -- TRUSTED_DYNAMIC above only
    records that this shape is accounted for, it does not check where the
    values actually point. This reads sites.yml directly and checks each one.
    """
    path = ROOT / "_data" / "sites.yml"
    sites = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    assert sites, f"{path} declares no sites -- nothing for the header nav to link to."

    problems = []
    for key, site in sites.items():
        site = site or {}
        home = site.get("home") or "/"
        if home not in PAGES:
            problems.append(f"sites.yml: {key}.home = {home!r}, no published page there")

        about = site.get("about_url")
        if about and about not in PAGES:
            problems.append(f"sites.yml: {key}.about_url = {about!r}, no published page there")

        # The footer reference block (2026-08-16). Absent is fine -- cocktails
        # has none yet, and the template renders nothing rather than an empty
        # heading -- but a link that IS listed has to go somewhere real.
        for entry in site.get("reference_links") or []:
            url = (entry or {}).get("url")
            if url not in PAGES:
                problems.append(
                    f"sites.yml: {key}.reference_links entry {entry.get('text')!r} "
                    f"points at {url!r}, which no published page serves"
                )

        switch = site.get("switch_site")
        if switch:
            sibling_home = (sites.get(switch) or {}).get("home")
            if not sibling_home or sibling_home not in PAGES:
                problems.append(
                    f"sites.yml: {key}.switch_site = {switch!r}, but "
                    f"sites.yml[{switch!r}].home = {sibling_home!r} has no published page"
                )
    assert not problems, "Header nav link(s) resolve nowhere:\n  " + "\n  ".join(problems)


def test_chart_anchor_fragments_exist_on_the_temperatures_page():
    """_includes/food/doneness_chart.html links a recipe's 'more temperatures'
    line to /food/reference/temperatures/#<chart_anchor>, where chart_anchor
    comes from that recipe's own internal_temp_ref resolving into
    _data/food/internal_temperatures.yml -- a fragment this test's generic
    scanner deliberately does not try to compute (it isn't a literal in any
    template, and simulating the recipe -> data_ref -> chart_anchor lookup
    here would just be a second, weaker copy of what recipe.html itself
    does). Simpler and just as strong: every chart_anchor: value the data
    file actually declares must be a real id on the temperatures page, full
    stop -- checked directly, not through a recipe at all.
    """
    path = ROOT / "_data" / "food" / "internal_temperatures.yml"
    anchors = sorted(set(re.findall(r"chart_anchor:\s*(\S+)", path.read_text(encoding="utf-8"))))
    assert anchors, f"No chart_anchor: values found in {path} -- has the field been renamed?"

    temps_page = PAGES.get("/food/reference/temperatures/")
    assert temps_page, "/food/reference/temperatures/ is not a published page any more."

    ids = _ids_visible_from(temps_page)
    missing = [a for a in anchors if a not in ids]
    assert not missing, (
        f"_data/food/internal_temperatures.yml declares chart_anchor value(s) "
        f"{missing} with no matching id=\"...\" on food/reference/temperatures.html.\n"
        f"_includes/food/doneness_chart.html links every wired recipe's 'more "
        f"temperatures' straight to that fragment, so a wrong or renamed anchor "
        f"here is a silent do-nothing link on a live recipe page, not a 404."
    )
