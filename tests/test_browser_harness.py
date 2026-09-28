"""The browser harness has one Playwright version, wherever it is installed.

Since 2026-09-15 Playwright is pinned twice: in .devcontainer/Dockerfile, which
bakes it into the image under /opt/playwright, and in scripts/browser/install.sh,
which installs it into tmp/browser/ outside the image. Helen asked for the
image copy ("shall I pre-install Playwright (and its dependencies) into this
Docker image?") so fresh worktrees stop downloading a browser. Two pins drift
silently -- a screenshot taken on one version and compared with one taken on
the other is not the same measurement -- so this file refuses the drift.
"""
from __future__ import annotations

import pathlib
import re

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / ".devcontainer" / "Dockerfile"
BROWSER = ROOT / "scripts" / "browser"
REQUIREMENTS = ROOT / "requirements-test.txt"


def _dockerfile_pin() -> str:
    pins = re.findall(r"playwright@(\d+\.\d+\.\d+)", DOCKERFILE.read_text(encoding="utf-8"))
    assert len(pins) == 1, f"expected one playwright@X.Y.Z in the Dockerfile, found {pins!r}"
    return pins[0]


def _install_pin() -> str:
    pins = re.findall(r"^version=(\d+\.\d+\.\d+)$",
                      (BROWSER / "install.sh").read_text(encoding="utf-8"), re.M)
    assert len(pins) == 1, f"expected one version=X.Y.Z in install.sh, found {pins!r}"
    return pins[0]


def test_the_image_and_install_sh_pin_the_same_playwright():
    assert _dockerfile_pin() == _install_pin(), (
        f"the Dockerfile pins playwright {_dockerfile_pin()} and "
        f"scripts/browser/install.sh pins {_install_pin()} -- bump both, then "
        "rebuild the devcontainer image"
    )


def _pip_pin() -> str:
    pins = re.findall(r"^playwright==(\d+\.\d+\.\d+)\s*$",
                      REQUIREMENTS.read_text(encoding="utf-8"), re.M)
    assert len(pins) == 1, f"expected one playwright== pin in requirements-test.txt, found {pins!r}"
    return pins[0]


def test_the_python_binding_and_the_npm_harness_are_the_same_playwright():
    """THE THIRD PIN, added 2026-09-28, and the reason the version moved.

    requirements-test.txt gained `playwright` for #1200's headless smoke test.
    It was first pinned at 1.47.0 to sit beside the npm 1.47.2 in the image --
    and PyPI HAS NO 1.47.2 (checked against the index that day: 1.47.0, then
    1.48.0). So the two lines could not be made to agree, each resolved a
    different Chromium revision, and the image carried two browsers for no
    reason anybody chose.

    Moving both to 1.63.0, which exists on npm and PyPI alike, collapses that
    into one number and one browser. This test is what stops them drifting
    apart again -- and it is why `playwright` sits in dependabot.yml's ignore
    list, since a bot can only ever move one of the four places the number
    lives (here, both Dockerfile lines, and install.sh).

    Read as an EXACT match, not a major or minor one: a screenshot taken on one
    build and compared with one taken on another is not the same measurement,
    which is the same argument the sibling test above makes for the npm pair.
    """
    assert _pip_pin() == _dockerfile_pin(), (
        f"requirements-test.txt pins playwright {_pip_pin()} and the image's "
        f"npm install pins {_dockerfile_pin()}. They must match, or the pip "
        "binding and the screenshot harness resolve different Chromium "
        "revisions and the image carries two browsers. Bump all four places "
        "together -- requirements-test.txt, both Dockerfile lines, and "
        "scripts/browser/install.sh -- then rebuild the image."
    )


def test_the_dockerfile_installs_chromium_with_its_system_dependencies():
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "playwright install --with-deps chromium" in text, (
        "Helen asked for Playwright's dependencies in the image too; "
        "`--with-deps` is what installs Chromium's system libraries"
    )


@pytest.mark.parametrize("script", ["shoot.sh", "crop.sh"])
def test_the_harness_finds_playwright_through_env_sh(script):
    text = (BROWSER / script).read_text(encoding="utf-8")
    assert ". scripts/browser/env.sh" in text, (
        f"{script} must source env.sh, which prefers tmp/browser/ and falls "
        "back to the image's /opt/playwright"
    )
    assert "tmp/browser/node_modules" not in text and "ms-playwright" not in text, (
        f"{script} names a Playwright location itself, so it would ignore the "
        "image's copy -- that belongs in env.sh alone"
    )
