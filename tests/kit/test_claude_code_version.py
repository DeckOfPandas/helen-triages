"""Claude Code's version in the image: .devcontainer/claude_code_latest.py and its wiring.

run.sh asks npm for the newest version on every launch and rebuilds when it
differs from the image's label. The answer lands in a RUN line and a label, so
anything but three plain numbers must come back as "don't know". And the
Dockerfile, run.sh and the label must agree on one argument name: if they
drift, the build still succeeds, from cache, and the image stops following
releases. Nothing here touches the network or Docker.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def lookup():
    path = Path(__file__).resolve().parents[2] / ".devcontainer" / "claude_code_latest.py"
    spec = importlib.util.spec_from_file_location("claude_code_latest", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_registry_answer_yields_its_version(lookup):
    assert lookup.parse_version(b'{"name": "@anthropic-ai/claude-code", "version": "2.1.289"}') == "2.1.289"


@pytest.mark.parametrize("body", [
    b"",
    b"<html>502 Bad Gateway</html>",
    b'{"name": "@anthropic-ai/claude-code"}',
    b'{"version": 2}',
    b'["2.1.289"]',
    b'{"version": "latest"}',
    b'{"version": "2.1.289-beta.1"}',
    b'{"version": "2.1.289 && curl example.com"}',
    b'{"version": "2.1.289\\n"}',
])
def test_anything_but_three_plain_numbers_is_dont_know(lookup, body):
    assert lookup.parse_version(body) is None


def test_an_unreachable_registry_is_dont_know_not_an_error(lookup):
    # Port 9 on localhost refuses at once, so this never leaves the machine.
    assert lookup.latest_version("http://127.0.0.1:9/", timeout=1) is None


def test_the_dockerfile_installs_the_version_it_is_given_last(kit_root):
    dockerfile = (kit_root / ".devcontainer" / "Dockerfile").read_text()
    code = [line.strip() for line in dockerfile.splitlines() if line.strip() and not line.strip().startswith("#")]
    assert "ARG CLAUDE_CODE_VERSION=latest" in code
    installs = [line for line in code if "@anthropic-ai/claude-code" in line]
    assert installs == ['RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}"'], installs
    assert "ENV DISABLE_AUTOUPDATER=1" in code
    runs = [line for line in code if line.startswith("RUN ")]
    assert "@anthropic-ai/claude-code" in runs[-1], "every layer after the install reruns on each release"


def test_run_sh_builds_labels_and_compares_one_version(kit_root):
    run_sh = (kit_root / ".devcontainer" / "run.sh").read_text()
    assert 'python3 "$HERE/claude_code_latest.py" || true' in run_sh, "a failed lookup must not stop run.sh"
    assert '--build-arg "CLAUDE_CODE_VERSION=$CLAUDE_CODE_VERSION"' in run_sh
    assert '--label "$VERSION_LABEL=$CLAUDE_CODE_VERSION"' in run_sh
    assert 'IMAGE_VERSION="$(label "$VERSION_LABEL")"' in run_sh
    assert re.search(r'\[ "\$IMAGE_VERSION" != "\$CLAUDE_CODE_VERSION" \]', run_sh)


def test_the_lookup_is_not_a_build_input(kit_root):
    assert "claude_code_latest.py" in (kit_root / ".devcontainer" / ".dockerignore").read_text().split()
