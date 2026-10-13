"""One headless-Chromium smoke test of both indexes, a recipe and a drink (#1200).

Nothing else in the suite executes a built page: the stub-DOM harness
(`tests/js/`) cannot see a `<script>` tag missing from the page, a script that
throws on a real DOM, or a layout that overflows. This checks console errors,
sideways overflow at the harness's two widths, and that each index lists rows
and a filter click changes its count. Pixel comparison, a11y and other
browsers are #1102. The pages come from conftest's `prod_site` build.

Every test takes the `chromium` fixture, which skips when Chromium cannot
LAUNCH, never on whether playwright imports: CI installs the binding and no
browser, so an import-based skip would run there, fail, and gate the deploy
(DECISIONS §10, #1127). conftest names the skip at the end of the run and
test_suite_hygiene.py holds the tests to the fixture. `HT_REQUIRE_BROWSER=1`
turns the skip into a failure.
"""
from __future__ import annotations

import functools
import http.server
import os
import pathlib
import threading
import urllib.parse

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASEURL = "/helen-triages"

# Where Chromium is, in scripts/browser/env.sh's order. This search wins over
# the image's own PLAYWRIGHT_BROWSERS_PATH: a worktree's install.sh copy exists
# because the image is older than the pin, which is when the image's path is
# the wrong one. Neither directory: the variable is left alone, which is right
# on a host whose `playwright install` used its default.
BROWSER_DIRS = (
    ROOT / "tmp" / "browser" / "ms-playwright",
    pathlib.Path("/opt/playwright/ms-playwright"),
)

# The harness's own viewports (scripts/browser/shoot.js), not re-invented.
VIEWPORTS = {
    360: dict(viewport={"width": 360, "height": 780}, device_scale_factor=2,
              is_mobile=True, has_touch=True),
    1280: dict(viewport={"width": 1280, "height": 900}, device_scale_factor=1),
}

# Each index script's LAST statement is `window.addEventListener('pagehide',
# <this>)` -- MANUAL §10.2 calls it the canary. Seeing it registered means the
# script ran top to bottom, which a list merely being present cannot show: the
# rows are rendered by Liquid and are there with no script at all.
INDEXES = {
    "food": dict(url="/food/", canary="saveIndexMemory",
                 rows=".recipe-list > li", count="#recipe-count-n",
                 filters=".btn-tag, .btn-star"),
    "cocktails": dict(url="/cocktails/", canary="saveDrinksMemory",
                      rows=".drink-cards > li.drink-card", count="#drink-count-n",
                      filters=".btn-mood"),
}

RECORD_PAGEHIDE = """
window.__pagehide = [];
const add = window.addEventListener;
window.addEventListener = function (type, fn, opts) {
  if (type === 'pagehide') window.__pagehide.push(fn && fn.name);
  return add.call(this, type, fn, opts);
};
"""


def browsers_path(dirs=BROWSER_DIRS):
    """The PLAYWRIGHT_BROWSERS_PATH to launch with, or None to leave it alone."""
    for candidate in dirs:
        if candidate.is_dir():
            return str(candidate)
    return None


def _no_browser(reason):
    if os.environ.get("HT_REQUIRE_BROWSER"):
        pytest.fail(f"HT_REQUIRE_BROWSER is set and there is no browser: {reason}")
    pytest.skip(f"no launchable Chromium, so no browser smoke test: {reason}")


@pytest.fixture(scope="session")
def chromium():
    """One Chromium for the session, or a skip that says why there is none."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        _no_browser(f"the playwright package is not installed ({exc})")

    path = browsers_path()
    saved = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if path:
        # The driver is a subprocess that copies the environment when it
        # starts, so the variable is needed for exactly as long as the start.
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = path
    try:
        pw = sync_playwright().start()
    finally:
        if path:
            if saved is None:
                del os.environ["PLAYWRIGHT_BROWSERS_PATH"]
            else:
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = saved
    try:
        browser = pw.chromium.launch()
    except Exception as exc:  # the launch error IS the reason
        pw.stop()
        _no_browser(str(exc).strip().splitlines()[0])
    yield browser
    browser.close()
    pw.stop()


class _BaseurlHandler(http.server.SimpleHTTPRequestHandler):
    """Serve the build at BASEURL, as serve.sh's symlink does, so every
    relative_url on the page resolves. Anything outside BASEURL is a 404."""

    def translate_path(self, path):
        clean = urllib.parse.urlsplit(path).path
        if not clean.startswith(BASEURL + "/"):
            return str(pathlib.Path(self.directory) / "\0-outside-baseurl")
        return super().translate_path(clean[len(BASEURL):])

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def served(prod_site):
    handler = functools.partial(_BaseurlHandler, directory=str(prod_site))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}{BASEURL}"
    server.shutdown()
    server.server_close()


def _first_page(prod_site, folder):
    pages = sorted((prod_site / folder / "recipes").glob("*/index.html"))
    assert pages, f"the production build has no pages under {folder}/recipes/"
    return "/" + str(pages[0].parent.relative_to(prod_site)) + "/"


class _Visit:
    """A page opened in a fresh context, collecting everything that went wrong."""

    def __init__(self, browser, base, url, width):
        self.url = url
        self.width = width
        self.context = browser.new_context(**VIEWPORTS[width])
        self.context.add_init_script(RECORD_PAGEHIDE)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("console", lambda m: m.type == "error"
                     and self.errors.append(f"console: {m.text}"))
        self.page.on("pageerror", lambda e: self.errors.append(f"uncaught: {e}"))
        self.page.goto(base + url, wait_until="load")

    def wait_for_script(self, canary):
        try:
            self.page.wait_for_function(
                "name => window.__pagehide.includes(name)", arg=canary,
                timeout=10_000)
        except Exception:
            pytest.fail(
                f"{self.url}: the index script never reached its last line -- "
                f"`pagehide` -> {canary} was not registered within 10s. A "
                f"<script> tag missing from the page, or a throw above the "
                f"canary. Errors seen:\n  " + ("\n  ".join(self.errors) or "none"))

    def overflow(self):
        # shoot.js's measure, deliberately: mobile emulation GROWS innerWidth
        # to fit the widest content, so `scrollWidth <= innerWidth` is true of
        # an overflowing phone page. Compare against the width asked for.
        return self.page.evaluate("""(vw) => {
          const docW = Math.max(document.documentElement.scrollWidth, window.innerWidth);
          if (docW <= vw) return null;
          const wide = [];
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            if (r.width > 0 && (r.right > vw + 1 || r.left < -1))
              wide.push(`<${el.tagName.toLowerCase()} class="${String(el.getAttribute('class') || '').slice(0, 60)}"> right=${Math.round(r.right)}`);
          }
          return {docW, wide: wide.slice(0, 5)};
        }""", self.width)

    def close(self):
        self.context.close()


@pytest.fixture
def visit(chromium, served):
    opened = []

    def _open(url, width=1280):
        v = _Visit(chromium, served, url, width)
        opened.append(v)
        return v
    yield _open
    for v in opened:
        v.close()


PAGES = ("food index", "cocktails index", "a recipe", "a drink")


def _url_of(which, prod_site):
    if which == "a recipe":
        return _first_page(prod_site, "food")
    if which == "a drink":
        return _first_page(prod_site, "cocktails")
    return INDEXES[which.split()[0]]["url"]


@pytest.mark.parametrize("width", sorted(VIEWPORTS))
@pytest.mark.parametrize("which", PAGES)
def test_the_page_runs_clean_and_fits(chromium, visit, prod_site, which, width):
    url = _url_of(which, prod_site)
    v = visit(url, width)
    v.page.wait_for_load_state("networkidle")
    for name, index in INDEXES.items():
        if url == index["url"]:
            v.wait_for_script(index["canary"])

    assert not v.errors, (
        f"{url} at {width}px reported {len(v.errors)} error(s) in a real "
        f"browser:\n  " + "\n  ".join(v.errors)
    )
    # Measure the settled page (#1295). assets/js/card-name-fit.js fits the
    # card names at load and again on `document.fonts.ready`; `networkidle`
    # and the canary say nothing about that second pass, so wait for the
    # fonts, then two frames for the refit to lay out. Not proven to be the
    # cause of the intermittent overflow: if this flakes with the wait in
    # place, the overflow is real and the fitting is what to fix.
    v.page.evaluate("""() => document.fonts.ready.then(() => new Promise(
        done => requestAnimationFrame(() => requestAnimationFrame(done))))""")
    wide = v.overflow()
    assert wide is None, (
        f"{url} is {wide['docW']}px wide in a {width}px viewport -- it scrolls "
        f"sideways. Widest elements:\n  " + "\n  ".join(wide["wide"])
    )


def _visible(page, selector):
    return page.evaluate(
        "s => [...document.querySelectorAll(s)].filter(e => e.checkVisibility()).length",
        selector)


@pytest.mark.parametrize("name", sorted(INDEXES))
def test_the_index_lists_rows_and_a_filter_changes_the_count(chromium, visit, name):
    index = INDEXES[name]
    v = visit(index["url"])
    v.wait_for_script(index["canary"])

    rows = _visible(v.page, index["rows"])
    assert rows > 0, (
        f"{index['url']}: its script ran to the end and no row of "
        f"{index['rows']!r} is visible"
    )

    count = v.page.locator(index["count"])
    before = count.inner_text()
    buttons = v.page.locator(index["filters"])
    tried = []
    changed = None
    for i in range(buttons.count()):
        button = buttons.nth(i)
        if not button.is_visible():
            continue
        label = button.inner_text().strip()
        button.click()
        assert button.get_attribute("aria-pressed") == "true", (
            f"{index['url']}: clicking {label!r} did not mark it pressed")
        after = count.inner_text()
        if after != before:
            changed = (label, after)
            break
        tried.append(label)
        button.click()           # un-choose it and try the next
    assert changed, (
        f"{index['url']}: no filter changed the survivor count from {before} "
        f"(tried {len(tried)}: {', '.join(tried[:8])})"
    )
    assert not v.errors, (
        f"{index['url']}: clicking {changed[0]!r} produced error(s):\n  "
        + "\n  ".join(v.errors)
    )
