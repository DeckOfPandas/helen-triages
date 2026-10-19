"""Links between the site's own HTML pages -- #220.

Scans every `<a href>` in food/**/*.html, cocktails/**/*.html, the root
*.html pages, _layouts/ and _includes/, and checks the path against the
published pages and the fragment against the ids its target can emit.
Run: pytest tests/test_page_links.py

Published pages are derived from each page's `permalink:` (or Jekyll's
default, `/:path:output_ext`) and from `_config.yml`'s `collections:`. An
`output: false` collection and a `published: false` page are not targets.

A wrong fragment does not 404: the page loads and lands at the top. So
fragments are checked, a bare `href="#top"` included, and ids are resolved
across `{% include %}` edges and the layout chain (`_ids_visible_from`).

Skipped: a scheme, `//`, `mailto:`, and `.pdf` links, which
tests/test_site_config.py::test_pdf_link_points_where_the_pdfs_are_written
holds at both ends.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import pytest
import yaml

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

# The two site page directories, plus every ordinary page at the repo root.
# The root level is globbed, not listed: a page this corpus cannot see is not
# a link target, and its own outbound links go unscanned (#374).
#
# A `published: false` page is dropped from both sides. Jekyll gives it no
# URL, so its relative hrefs have no base to resolve against (#400), and it
# must not count as a target: a link into it would 404 in production.
_PUBLISHED_FALSE = re.compile(
    r"\A---\n(?:.*\n)*?published:\s*false\s*(?:#.*)?\n(?:.*\n)*?---\n", re.M)


def _is_published(path):
    return not _PUBLISHED_FALSE.match(path.read_text(encoding="utf-8"))


PAGE_FILES = [
    p for p in (
        sorted(ROOT.glob("food/**/*.html"))
        + sorted(ROOT.glob("cocktails/**/*.html"))
        + sorted(ROOT.glob("*.html"))
    ) if _is_published(p)
]
UNPUBLISHED_PAGE_FILES = [
    p for p in (
        sorted(ROOT.glob("food/**/*.html"))
        + sorted(ROOT.glob("cocktails/**/*.html"))
        + sorted(ROOT.glob("*.html"))
    ) if not _is_published(p)
]
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

# Permalinks of the `published: false` pages: real locally, absent from a
# production build. Only test_site_nav_links_resolve_to_real_pages reads this,
# to check a `local_only` footer link (#529). It is never a link target.
UNPUBLISHED_PAGES: set[str] = {page_url(f) for f in UNPUBLISHED_PAGE_FILES}


def _collection_pages() -> dict[str, Path]:
    """url -> source file, for every PUBLISHED collection document.

    Read from _config.yml, so a collection added later is picked up. An
    `output: false` collection (the drafts) is excluded: its pages get no
    public URL, so a link to one 404s in production though the file exists.
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
    has a computed target and is skipped: those includes are SVG icons, which
    carry no id and no href.
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

    Floods outward because a fragment link written in a partial or a layout
    can target an id that lives only in the page that includes it. `start` is
    the file a `#fragment` link was found in, or the target page's file for a
    `path/#fragment` link.
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

# Href shapes this scanner cannot trace to a literal, each with what checks it
# instead. A new untraceable href that is not listed fails
# test_no_link_shape_is_silently_unresolved. Remove an entry when its shape
# leaves the templates: a stale one trusts whatever emits that shape next.
# `<x>_site.home` and `link.url` are values out of _data/sites.yml, which
# test_site_nav_links_resolve_to_real_pages checks against the published pages.
# A document's `.url` is computed by Jekyll from its own permalink.
TRUSTED_DYNAMIC = (
    re.compile(r"^\{\{\s*this_site\.home\s*\|\s*default:\s*'/'\s*\|\s*relative_url\s*\}\}$"),
    re.compile(r"^\{\{\s*nav_site\.home\s*\|\s*relative_url\s*\}\}$"),
    # The head of the footer reference column (#1149, _layouts/default.html).
    re.compile(r"^\{\{\s*ref_site\.home\s*\|\s*relative_url\s*\}\}$"),
    # The back arrow on a recipe or drink page (#387,
    # _includes/back-to-index.html).
    re.compile(r"^\{\{\s*back_site\.home\s*\|\s*relative_url\s*\}\}$"),
    # The see-shortlist link (#1011, _includes/page-actions.html). The query
    # does not change the page fetched, and `#results` is an id both indexes
    # carry (test_the_search_box_searches_for_anything_on_a_local_build,
    # tests/test_site_config.py).
    re.compile(r"^\{\{\s*actions_site\.home\s*\|\s*relative_url\s*\}\}\?shortlist=1#results$"),
    # The footer's reference links.
    re.compile(r"^\{\{\s*link\.url\s*\|\s*relative_url\s*\}\}$"),
    re.compile(r"^\{\{\s*(?:recipe|cocktail)\.url\s*\|\s*relative_url\s*\}\}$"),
    # The related-drinks row on a drink page (#927, _layouts/cocktail.html).
    # Also checked on the production build, since the row is chosen by a
    # score: test_every_published_drink_page_offers_four_other_published_drinks
    # in tests/test_rendered_pages.py.
    re.compile(r"^\{\{\s*rel\.url\s*\|\s*relative_url\s*\}\}$"),
    # The related-recipes row on a recipe page (#1005, _layouts/recipe.html),
    # checked on the production build by
    # test_every_published_recipe_page_offers_three_other_published_recipes.
    re.compile(r"^\{\{\s*_rel\.url\s*\|\s*relative_url\s*\}\}$"),
    # A card on the cocktails index. A draft's card is emitted only under
    # `site.show_drafts`, which only _config_local.yml sets, so its href never
    # reaches a production build.
    re.compile(r"^\{\{\s*drink\.url\s*\|\s*relative_url\s*\}\}$"),
    # A drink's source link (_layouts/cocktail.html). Unlike the rest, this is
    # unchecked, not checked elsewhere: `source_url` is an external address in
    # front matter, out of scope as a literal `http://` href is. A dead one
    # rots silently; checking it would take a network call.
    re.compile(r"^\{\{\s*page\.source_url\s*\}\}$"),
    # A drink page's mood chips, linking to the cocktails index filtered by
    # that mood. `index_home` is `site.data.sites[page.site_key].home`. The
    # `?mood=` query does not change the page fetched, and a stale mood is a
    # taxonomy question for tests/test_cocktails.py. `chip` is "mood" or
    # "hassle", and `filter-` plus either is an id on the index
    # (test_filter_sections_carry_the_id_their_badges_and_chips_link_to,
    # tests/test_site_config.py).
    re.compile(r"^\{\{\s*index_home\s*\|\s*relative_url\s*\}\}\?mood="
               r"\{\{\s*m\s*\|\s*url_encode\s*\}\}#filter-\{\{\s*chip\s*\}\}$"),
    # A drink page's SHIP IT? word, linking to the index filtered to that ship
    # value (#1412). Same `index_home`; `?ship=` does not change the page
    # fetched, a value no card carries is dropped by cocktail-index.js, and
    # `#results` is the count line's id on the index.
    re.compile(r"^\{\{\s*index_home\s*\|\s*relative_url\s*\}\}\?ship="
               r"\{\{\s*page_ship\s*\|\s*url_encode\s*\}\}#results$"),
)


def _assigns(path: Path) -> dict[str, str]:
    """{% assign name = "literal" | ... relative_url ... %} in `path`: an
    href built one hop away from its literal.
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
    """The whole-corpus guard: every test below only means something if
    there was something to scan, and a scan that finds nothing passes.
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
    """Guards the scanner, not the content. An href it cannot trace to a
    literal path is either on TRUSTED_DYNAMIC, where each entry says what
    checks it instead, or it is new: a link the scanner cannot see is a link
    it cannot catch breaking.
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
    """Every link _data/sites.yml feeds the header nav and the footer
    reference block points at a real page. TRUSTED_DYNAMIC only records that
    those href shapes are accounted for; this checks where the values point.

    The header emits one icon per site on every page (#374), so a broken
    `home` on one site is a dead link on every page of the other.
    """
    path = ROOT / "_data" / "sites.yml"
    sites = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    assert sites, f"{path} declares no sites -- nothing for the header nav to link to."

    icons_dir = ROOT / "_includes" / "icons"

    problems = []
    for key, site in sites.items():
        site = site or {}
        home = site.get("home") or "/"
        if home not in PAGES:
            problems.append(f"sites.yml: {key}.home = {home!r}, no published page there")

        # The shared nav gives every site a slot, so a missing `icon` renders
        # `{% include icons/.svg %}`, a build failure. Caught here so the
        # message names the site.
        icon = site.get("icon")
        if not icon:
            problems.append(
                f"sites.yml: {key} declares no `icon`. The header nav "
                f"(_layouts/default.html) emits one icon per site on every page, "
                f"so this is not optional -- it builds an include path from it."
            )
        elif not (icons_dir / f"{icon}.svg").exists():
            problems.append(
                f"sites.yml: {key}.icon = {icon!r}, but "
                f"_includes/icons/{icon}.svg does not exist"
            )

        # The footer reference block. A site with no links is fine; a listed
        # link has to go somewhere real. `local_only: true` inverts the check,
        # it does not skip it (#529): the template drops such a link unless
        # `show_local_reference_links` is set, so it must point at a page in
        # UNPUBLISHED_PAGES, and an ordinary one at a page in PAGES. Otherwise
        # production links a 404, or a page that now exists goes unlinked.
        for entry in site.get("reference_links") or []:
            entry = entry or {}
            url = entry.get("url")
            if entry.get("local_only"):
                if url in PAGES:
                    problems.append(
                        f"sites.yml: {key}.reference_links entry "
                        f"{entry.get('text')!r} is local_only, but {url!r} IS "
                        f"published -- drop the flag, or the page is linked "
                        f"nowhere it can be reached"
                    )
                elif url not in UNPUBLISHED_PAGES:
                    problems.append(
                        f"sites.yml: {key}.reference_links entry "
                        f"{entry.get('text')!r} is local_only and points at "
                        f"{url!r}, which no page serves at all -- not published, "
                        f"and not `published: false` either"
                    )
            elif url not in PAGES:
                problems.append(
                    f"sites.yml: {key}.reference_links entry {entry.get('text')!r} "
                    f"points at {url!r}, which no published page serves"
                )

        # Keys no template reads (#374). Asserted absent, because setting one
        # looks like configuration and does nothing.
        for retired, why in RETIRED_SITE_KEYS.items():
            if retired in site:
                problems.append(
                    f"sites.yml: {key}.{retired} is retired -- {why} "
                    f"Nothing reads it, so setting it changes nothing."
                )

    assert not problems, "Header nav link(s) resolve nowhere:\n  " + "\n  ".join(problems)


# Per-site keys _data/sites.yml must not carry, each with what replaced it
# (#374): the header and the footer are one artefact for the whole repo.
RETIRED_SITE_KEYS = {
    "home_icon": "renamed `icon`; the nav gives every site a slot, not just this one.",
    "switch_site": "the nav loops every site in this file, so there is nothing to switch to.",
    "switch_icon": "see switch_site; one `icon` per site covers both roles.",
    "about_url": "there is one about page, at the literal /about/.",
    "footer_svg": "the footer hearts are chrome, named in assets/js/decorations.js.",
    "tape": "one tape set for the repo, at assets/img/chrome/tape/.",
    "tape_count": "moved to _data/chrome.yml, which is chrome config rather than site identity.",
}


def test_chart_anchor_fragments_exist_on_the_temperatures_page():
    """Every `chart_anchor:` value in _data/food/internal_temperatures.yml
    is an id on the temperatures page.

    _includes/food/doneness_chart.html links a recipe to
    /food/reference/internal-temperatures/#<chart_anchor>, a fragment that is
    a literal in no template, so the generic scanner cannot see it. The
    declared values are checked directly, not through a recipe.
    """
    path = ROOT / "_data" / "food" / "internal_temperatures.yml"
    anchors = sorted(set(re.findall(r"chart_anchor:\s*(\S+)", path.read_text(encoding="utf-8"))))
    assert anchors, f"No chart_anchor: values found in {path} -- has the field been renamed?"

    temps_page = PAGES.get("/food/reference/internal-temperatures/")
    assert temps_page, "/food/reference/internal-temperatures/ is not a published page any more."

    ids = _ids_visible_from(temps_page)
    missing = [a for a in anchors if a not in ids]
    assert not missing, (
        f"_data/food/internal_temperatures.yml declares chart_anchor value(s) "
        f"{missing} with no matching id=\"...\" on food/reference/internal-temperatures.html.\n"
        f"_includes/food/doneness_chart.html links every wired recipe's 'more "
        f"temperatures' straight to that fragment, so a wrong or renamed anchor "
        f"here is a silent do-nothing link on a live recipe page, not a 404."
    )


# A quoted `../slug/` or `/food/...` in a script or a data file becomes a link
# only at runtime, so every scan above is blind to it.
JS_PATH_LITERAL = re.compile(r"""['"](\.\./[a-z0-9\-/]+/|/food/[a-z0-9\-/]+/)""")


def test_links_built_outside_templates_still_resolve():
    """A URL that is not an `<a href>` in a template is still a URL, and rots.

    A link built by string concatenation in assets/js/, or carried as raw HTML
    in a _data/ file and emitted inside a JSON blob, is an `<a href>` in no
    template and in no built page, so the template scan here and the
    built-html scan in tests/test_rendered_pages.py both miss it (#384).

    Blunt on purpose: quoted path-shaped literals, each checked against the
    published pages, with no reading of the code around them.
    """
    sources = sorted((ROOT / "assets" / "js").glob("*.js")) + \
              sorted((ROOT / "_data").rglob("*.yml"))
    assert sources, (
        "No scripts or data files found -- either they moved or these globs "
        "went stale, and a scan that finds nothing passes."
    )

    problems = []
    checked = 0
    for path in sources:
        for raw in JS_PATH_LITERAL.findall(path.read_text(encoding="utf-8")):
            checked += 1
            if raw.startswith("/food/"):
                target = raw
            else:
                # `../slug/` is resolved as if on a /food/reference/<page>/
                # URL. A script building relative links from any other page
                # needs its own case here.
                target = "/food/reference/" + raw[len("../"):]
            if target not in PAGES:
                problems.append(f"{path.name}: '{raw}' -> {target}, no published page there")

    assert checked, (
        "No path-shaped literals found in any script. Either none builds a URL "
        "any more -- in which case delete this test -- or the pattern stopped "
        "matching, which would leave it green and useless."
    )
    assert not problems, (
        "Link(s) built in JavaScript point at pages that do not exist:\n  "
        + "\n  ".join(problems)
        + "\n\nThese are invisible to the template and built-html scanners in "
          "this file, so nothing else will catch them. Keep them relative "
          "(`../slug/`) rather than root-relative: a script has no Liquid, and "
          "a literal /food/... drops the baseurl and 404s in production while "
          "working on localhost."
    )
