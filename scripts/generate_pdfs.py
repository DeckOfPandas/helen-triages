#!/usr/bin/env python3
"""Render every built recipe and drink page to a PDF sitting beside it (#86,
#1005).

    python3 scripts/generate_pdfs.py                 # against ./_site
    python3 scripts/generate_pdfs.py --site _site_prod --jobs 8
    python3 scripts/generate_pdfs.py --chrome /path/to/chrome

--site is the built site directory (default `_site`), --jobs the number of
parallel renders (default 4), and --chrome a browser that is not on PATH as
google-chrome or chromium.

It runs against a finished build, after `jekyll build` and before the Pages
artifact is uploaded, and writes into the build directly, so Jekyll never sees
the PDFs. `_site/food/recipes/beef-wellington/index.html` gets
`_site/food/recipes/beef-wellington.pdf` beside it, and a drink under
`cocktails/recipes/` likewise; that is the URL `_includes/page-print.html`
links to. Scratch (the Chrome profiles and the staging symlink) goes in the
repo's own `tmp/`.

The rules:

  - Headless Chrome is the renderer, so the PDF and the browser's own Print
    are the same document, through the same print stylesheet.
  - No Chrome is a failure, never a skip, and so are a collection with no
    pages and a render that writes nothing: a deploy that quietly stopped
    producing PDFs would leave every "pdf" link on the site a 404.
  - Pages are served from a local HTTP server that mirrors the deployed shape,
    not opened as file:// URLs. The site is served under a baseurl, so every
    asset URL in the built HTML is absolute; opened as a file they all miss
    and the PDF comes out unstyled.
"""
from __future__ import annotations

import argparse
import http.server
import functools
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Scratch goes in the repo's own tmp/, never the machine's /tmp (CLAUDE.md).
# Gitignored, so it may not exist on a fresh CI checkout.
SCRATCH = ROOT / "tmp"

# Long enough for decorations.js to fetch and inject every SVG: they arrive
# over HTTP after load, and a render that does not wait prints without them.
# Chrome exits as soon as the page is idle, so this is a ceiling, not a delay
# every page pays.
VIRTUAL_TIME_BUDGET_MS = 15000


def _chrome(explicit: str | None = None) -> str:
    """The Chrome binary, or exit non-zero saying so.

    `explicit` is --chrome, for a browser that is not on PATH under one of the
    usual names: WSL has no Linux Chrome unless one is installed.
    """
    if explicit:
        found = shutil.which(explicit) or (explicit if Path(explicit).exists() else None)
        if not found:
            sys.exit(f"--chrome {explicit!r} is not on PATH and is not a file.")
        return found
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit(
        "No Chrome/Chromium on PATH, so no PDFs can be built.\n"
        "This runs on the GitHub ubuntu runner, which ships Google Chrome. If "
        "the image has dropped it, install it in the workflow rather than "
        "letting this step be skipped -- every 'pdf' link on the site expects "
        "the file to be there."
    )


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler without a line of log per asset request."""

    def log_message(self, *args):    # noqa: D102 - silencing, not logging
        pass


def _serve(directory: Path) -> tuple[socketserver.TCPServer, int]:
    """Start a background HTTP server on a free port, return it and the port."""
    handler = functools.partial(_QuietHandler, directory=str(directory))
    # Port 0 lets the OS pick a free one -- a fixed port would collide with
    # whatever else a runner (or a laptop) happens to have listening.
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def _render(chrome: str, url: str, out: Path) -> tuple[Path, str | None]:
    """Render one URL. Returns (out, error message or None)."""
    # Its own profile directory per render: parallel Chromes sharing one
    # profile fight over the lock file and some of them exit having written
    # nothing at all.
    with tempfile.TemporaryDirectory(prefix="htf-pdf-", dir=SCRATCH) as profile:
        result = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--user-data-dir={profile}",
                # The browser's own URL/date stamp along the top and bottom of
                # every sheet. It is useful when you hit Print yourself and
                # noise on a file you meant to keep or send.
                "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw",
                f"--virtual-time-budget={VIRTUAL_TIME_BUDGET_MS}",
                f"--print-to-pdf={out}",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    if result.returncode != 0:
        return out, f"chrome exited {result.returncode}: {result.stderr.strip()[:300]}"
    # Chrome can exit 0 having written nothing (a navigation failure is not an
    # error to it). An empty or missing file is the symptom that would
    # otherwise reach the site as a broken link.
    if not out.exists() or out.stat().st_size == 0:
        return out, "chrome exited 0 but wrote no PDF"
    return out, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="_site", help="built site directory")
    parser.add_argument("--jobs", type=int, default=4, help="parallel renders")
    parser.add_argument(
        "--chrome",
        help="browser to render with, if it is not on PATH as google-chrome/chromium",
    )
    args = parser.parse_args()

    site = (ROOT / args.site).resolve()
    if not site.is_dir():
        sys.exit(f"{site} does not exist -- run `jekyll build` first.")

    SCRATCH.mkdir(exist_ok=True)
    chrome = _chrome(args.chrome)

    # Each collection is checked for emptiness on its own: a build that lost
    # one collection's pages would otherwise be hidden by the other still
    # rendering, and every pdf link on that site would 404.
    recipes = []
    for collection in ("food/recipes", "cocktails/recipes"):
        pages = sorted(site.glob(f"{collection}/*/index.html"))
        if not pages:
            sys.exit(
                f"No pages found under {site}/{collection}/. Either the build "
                f"did not run or the permalink has changed -- silently "
                f"producing zero PDFs would leave every 'pdf' link broken."
            )
        recipes.extend(pages)

    # Read the baseurl off the build, not out of _config.yml. Every page
    # states it (_layouts/default.html emits `<meta name="base-url">`), so
    # this script cannot disagree with the site it is rendering, and it needs
    # nothing outside the standard library.
    baseurl_match = re.search(
        r'<meta name="base-url" content="([^"]*)"',
        recipes[0].read_text(encoding="utf-8"),
    )
    if not baseurl_match:
        sys.exit(
            f"{recipes[0]} has no <meta name=\"base-url\">. _layouts/"
            f"default.html emits it for assets.js; if it has been renamed, "
            f"this script needs to follow, or every asset URL below misses "
            f"and the PDFs come out unstyled."
        )
    baseurl = baseurl_match.group(1).strip("/")

    # Mirror the deployed shape: the built site has to sit under its baseurl
    # for the absolute asset URLs to resolve. A symlink, not a copy;
    # SimpleHTTPRequestHandler follows it.
    stage_root = Path(tempfile.mkdtemp(prefix="htf-pdf-root-", dir=SCRATCH))
    stage = stage_root
    if baseurl:
        (stage / baseurl).symlink_to(site)
        prefix = f"/{baseurl}"
    else:
        (stage / "site").symlink_to(site)
        stage = stage / "site"
        prefix = ""

    httpd, port = _serve(stage)
    try:
        jobs = []
        for page in recipes:
            # The URL is the page's own path under the build, so neither
            # collection's prefix is written here a second time.
            rel = page.parent.relative_to(site).as_posix()
            slug = page.parent.name
            url = f"http://127.0.0.1:{port}{prefix}/{rel}/"
            jobs.append((url, page.parent.parent / f"{slug}.pdf"))

        print(f"rendering {len(jobs)} recipe PDFs with {args.jobs} workers")
        failures = []
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(_render, chrome, url, out) for url, out in jobs]
            for future in futures:
                out, error = future.result()
                if error:
                    failures.append(f"{out.name}: {error}")
    finally:
        httpd.shutdown()
        # Only the symlink and its directory -- shutil.rmtree does not follow
        # symlinks, so _site itself is never at risk here.
        shutil.rmtree(stage_root, ignore_errors=True)

    if failures:
        print(f"\n{len(failures)} of {len(jobs)} failed:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    total = sum(out.stat().st_size for _, out in jobs)
    print(f"wrote {len(jobs)} PDFs, {total / 1_000_000:.1f} MB total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
