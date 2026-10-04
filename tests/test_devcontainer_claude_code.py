"""Claude Code's version in the devcontainer image -- `.devcontainer/claude_code_latest.py`.

`run.sh` asks npm for the newest version on every launch and rebuilds the image
when it differs from the one the image was built with. Two things here can go
wrong quietly, and each has a test:

  * The lookup's answer goes into a `RUN` line and an image label, so anything
    that is not three plain numbers must come back as "don't know", never as
    text for the build to interpolate.
  * The Dockerfile, `run.sh` and the label have to agree on one argument name.
    If they drift, the build still succeeds -- on the default, from cache --
    and the image silently stops following releases, which is exactly the state
    this replaced.

Nothing here touches the network or Docker: the lookup's parser is driven with
bytes, and the wiring is read off the committed files.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEVCONTAINER = ROOT / ".devcontainer"
MODULE = DEVCONTAINER / "claude_code_latest.py"


@pytest.fixture(scope="module")
def lookup():
    assert MODULE.is_file(), (
        f"{MODULE} is missing. run.sh survives that (it treats a failed lookup "
        f"as 'keep the image you have'), so the image would just stop updating."
    )
    spec = importlib.util.spec_from_file_location("claude_code_latest", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_registry_answer_yields_its_version(lookup):
    body = b'{"name": "@anthropic-ai/claude-code", "version": "2.1.289"}'
    assert lookup.parse_version(body) == "2.1.289"


@pytest.mark.parametrize("body", [
    b"",                                            # nothing came back
    b"<html>502 Bad Gateway</html>",                # a proxy's error page
    b'{"name": "@anthropic-ai/claude-code"}',       # no version field
    b'{"version": 2}',                              # not a string
    b'["2.1.289"]',                                 # not an object
    b'{"version": "latest"}',
    b'{"version": "2.1.289-beta.1"}',
    b'{"version": "2.1.289 && curl example.com"}',
    b'{"version": "2.1.289\\n"}',
])
def test_anything_but_three_plain_numbers_is_dont_know(lookup, body):
    """The value is interpolated into a RUN line, so the shape check is the guard."""
    assert lookup.parse_version(body) is None


def test_an_unreachable_registry_is_dont_know_not_an_error(lookup):
    """Offline must not stop a container starting. Port 9 on localhost refuses
    at once, so this never leaves the machine."""
    assert lookup.latest_version("http://127.0.0.1:9/", timeout=1) is None


def test_the_dockerfile_installs_the_version_it_is_given():
    dockerfile = (DEVCONTAINER / "Dockerfile").read_text(encoding="utf-8")
    code = [line.strip() for line in dockerfile.splitlines()
            if line.strip() and not line.strip().startswith("#")]
    assert "ARG CLAUDE_CODE_VERSION=latest" in code
    installs = [line for line in code if "@anthropic-ai/claude-code" in line]
    assert installs == ['RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}"'], (
        f"expected one Claude Code install, taking its version from the build "
        f"argument; found {installs!r}. A second install, or one with no "
        f"version, is a cached layer that never moves."
    )
    assert "ENV DISABLE_AUTOUPDATER=1" in code, (
        "without it the CLI tries to update itself into root's npm folder and "
        "opens every session with a warning that it could not"
    )


def test_claude_code_is_the_last_install_in_the_dockerfile():
    """It changes most days, and every layer after a changed one is rebuilt."""
    dockerfile = (DEVCONTAINER / "Dockerfile").read_text(encoding="utf-8")
    runs = [line.strip() for line in dockerfile.splitlines()
            if line.strip().startswith("RUN ")]
    assert "@anthropic-ai/claude-code" in runs[-1], (
        f"the last RUN is {runs[-1]!r}. Whatever sits below the Claude Code "
        f"install is re-run on every new release."
    )


def test_run_sh_passes_and_records_the_same_version():
    run_sh = (DEVCONTAINER / "run.sh").read_text(encoding="utf-8")
    assert "python3 .devcontainer/claude_code_latest.py || true" in run_sh, (
        "the lookup must be allowed to fail: run.sh is `set -e`, and a bare "
        "call would stop the container starting whenever npm is unreachable"
    )
    assert '--build-arg "CLAUDE_CODE_VERSION=$CLAUDE_CODE_VERSION"' in run_sh
    assert '--label "$CLAUDE_CODE_LABEL=$CLAUDE_CODE_VERSION"' in run_sh, (
        "the label is what the next launch compares against; build with one "
        "value and record another and it rebuilds every time, or never"
    )
    assert re.search(r'\[ "\$IMAGE_CLAUDE_CODE" != "\$CLAUDE_CODE_VERSION" \]', run_sh)


def test_the_lookup_is_not_a_build_input():
    """The image never uses it, so editing it should cost no rebuild."""
    ignored = (DEVCONTAINER / ".dockerignore").read_text(encoding="utf-8").split()
    assert "claude_code_latest.py" in ignored
