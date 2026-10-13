"""The browser harness has one Playwright version, wherever it is installed.

Playwright's version is written in .devcontainer/Dockerfile, which bakes it
into the image under /opt/playwright, in scripts/browser/install.sh, which
installs it into tmp/browser/ outside the image, and in requirements-test.txt
for the Python binding. Pins drift silently, and a screenshot taken on one
version compared with one taken on another is not the same measurement, so
this file refuses the drift.
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
    """The pip binding (#1200) and the npm harness pin one exact version, so
    they resolve one Chromium revision and the image carries one browser.

    npm and PyPI do not publish the same patch releases, so pick a version
    both have. `playwright` is in dependabot.yml's ignore list because a bot
    moves only one of the places the number lives: requirements-test.txt,
    both Dockerfile lines, and install.sh.
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
