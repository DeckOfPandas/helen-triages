"""scripts/browser/: one Playwright version, and wrappers that refuse before a
browser is needed.

The wrappers are this site's layer over the kit's tools/dev/: the
per-worktree port, the /helen-triages base URL and the default page set. The
measuring, and its own argument checks, are the kit's (tests/kit/).
"""
from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parents[1]
BROWSER = ROOT / "scripts" / "browser"
WRAPPERS = ["shoot.sh", "crop.sh", "click-crop.sh", "styles.sh", "gaps.sh"]


def test_install_sh_pins_the_playwright_the_image_carries():
    """install.sh is the fallback outside the image; a shot on one release
    compared with one on another is not the same measurement."""
    pins = re.findall(r"^version=(\d+\.\d+\.\d+)$", (BROWSER / "install.sh").read_text(encoding="utf-8"), re.M)
    image = re.search(r"^PLAYWRIGHT_VERSION=(\S+)", (ROOT / ".devcontainer" / "kit.env").read_text(encoding="utf-8"), re.M)
    assert len(pins) == 1 and image, (pins, image)
    assert pins[0] == image.group(1), (
        f"scripts/browser/install.sh pins {pins[0]} and kit.env's PLAYWRIGHT_VERSION is {image.group(1)}")


@pytest.mark.parametrize("script", WRAPPERS + ["capture.sh"])
def test_every_wrapper_finds_playwright_through_env_sh(script):
    """env.sh prefers tmp/browser/ and falls back to the image's copy; a
    wrapper naming a location itself would skip one of the two."""
    text = (BROWSER / script).read_text(encoding="utf-8")
    assert ". scripts/browser/env.sh" in text or ". scripts/browser/_site.sh" in text, script
    assert "tmp/browser/node_modules" not in text and "ms-playwright" not in text, script


@pytest.mark.parametrize("script", WRAPPERS[1:])
def test_the_page_wrappers_measure_with_the_kits_tools(script):
    text = (BROWSER / script).read_text(encoding="utf-8")
    assert "node tools/dev/" in text, f"{script} no longer hands off to tools/dev/"


@pytest.mark.parametrize("args", [
    ["crop.sh"],
    ["crop.sh", "food/", "h1", "x"],
    ["crop.sh", "/food/../x/", "h1", "x"],
    ["crop.sh", "/food/", "h1", "x", "1280", ".box"],
    ["click-crop.sh", "/food/", ".a", ".b"],
    ["click-crop.sh", "http://evil/", ".a", ".b", "x"],
    ["styles.sh", "/food/"],
    ["styles.sh", "food/", "h1"],
    ["gaps.sh"],
    ["gaps.sh", "/a/://b/"],
    ["shoot.sh"],
    ["shoot.sh", "x", "food/"],
])
def test_the_wrappers_refuse_bad_arguments_before_needing_a_browser(args):
    done = subprocess.run(["sh", f"scripts/browser/{args[0]}", *args[1:]], cwd=ROOT,
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 2, (args, done.stderr)
