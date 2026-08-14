#!/usr/bin/env python3
"""Render every built recipe page to a PDF sitting beside it. GitHub issue #86.

Runs against a FINISHED BUILD, after `jekyll build` and before the Pages
artifact is uploaded, and writes into _site/ directly -- Jekyll never sees the
PDFs, so there is no collection, no permalink and no front matter to keep in
step. `_site/food/recipes/beef-wellington/index.html` gets
`_site/food/recipes/beef-wellington.pdf` next to it, which is the URL
_layouts/recipe.html links to.

    python3 scripts/generate_pdfs.py                 # against ./_site
    python3 scripts/generate_pdfs.py --site _site_prod --jobs 8

WHY HEADLESS CHROME AND NOTHING ELSE. A PDF library in the page was the
obvious alternative and is the wrong shape for this repo twice over: it means
vendoring a few hundred KB of third-party JavaScript into assets/js/ (where
test_palette_is_the_only_place_hex_colours_are_written would fail on its
colour literals -- the suite correctly noticing that nothing here is built
that way), and it means a second renderer that would have to be taught the
print stylesheet all over again. Chrome already has that stylesheet. The PDF
and the browser's own Print are the same document by construction, not by
being kept in sync.

It costs nothing to install: Google Chrome ships with the GitHub ubuntu
runner image (checked against actions/runner-images before this was written,
not assumed). If that ever stops being true this script fails loudly rather
than skipping -- see _chrome() below. That is deliberate: a deploy that
quietly stops producing PDFs would leave every "pdf" link on the site
pointing at a 404, and nothing else would notice.

WHY A LOCAL SERVER RATHER THAN file:// URLs. The site is served from a
baseurl (/helen-triages/), so every asset URL in the built HTML is absolute
from the domain root. Opened as a file, all of them miss, and the PDF comes
out unstyled -- which looks enough like "a plain document" to pass a glance.
Serving a directory that mirrors the deployed shape makes the rendered page
identical to the real one, decorations and all.
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

# Scratch goes in the repo's own tmp/, never the machine's /tmp -- CLAUDE.md is
# explicit about it, and a script that quietly ignored that rule whenever
# somebody ran it locally would be the worst place to break it. Gitignored, so
# it may not exist on a fresh CI checkout.
SCRATCH = ROOT / "tmp"

# Long enough for decorations.js to fetch and inject every SVG (the
# highlighters behind the amounts, the annotation arrows, the tag shapes) --
# they arrive over HTTP after load, so a render that does not wait for them
# produces a PDF missing exactly the hand-drawn character the print stylesheet
# went to the trouble of keeping. Chrome exits as soon as the page is idle, so
# this is a ceiling, not a delay every page pays.
VIRTUAL_TIME_BUDGET_MS = 15000


def _chrome(explicit: str | None = None) -> str:
    """The Chrome binary, or exit non-zero saying so.

    `explicit` is --chrome, for a browser that is not on PATH under one of the
    usual names. That is the normal case on this machine rather than an exotic
    one: WSL has no Linux Chrome unless you install one, and the Windows
    install next door is chrome.exe.
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

    recipes = sorted(site.glob("food/recipes/*/index.html"))
    if not recipes:
        sys.exit(
            f"No recipe pages found under {site}/food/recipes/. Either the "
            f"build did not run or the permalink has changed -- silently "
            f"producing zero PDFs would leave every 'pdf' link broken."
        )

    # Read the baseurl off the BUILD rather than out of _config.yml. Every page
    # states it, because assets.js needs it (_layouts/default.html emits
    # `<meta name="base-url">`), so taking it from here means this script
    # cannot disagree with the site it is rendering -- which parsing the config
    # separately would eventually let it do. Nothing needs installing to read
    # it either, which keeps this script to Python's standard library and the
    # workflow to no setup step at all.
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

    # Mirror the deployed shape: the built site has to sit UNDER its baseurl
    # for the absolute asset URLs in the HTML to resolve. A symlink rather
    # than a copy -- 90-odd pages plus artwork is not worth duplicating, and
    # SimpleHTTPRequestHandler follows it happily.
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
            slug = page.parent.name
            url = f"http://127.0.0.1:{port}{prefix}/food/recipes/{slug}/"
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
