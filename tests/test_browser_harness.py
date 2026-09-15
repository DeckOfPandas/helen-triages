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
