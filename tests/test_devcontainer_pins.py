"""requirements-test.txt is the single source; the Dockerfile's copy must agree.

WHY THE DUPLICATION EXISTS AND IS NOT GOING AWAY. `.devcontainer/Dockerfile`
installs the Python test dependencies by hand instead of `COPY
requirements-test.txt`, because its build context is `.devcontainer/` itself,
not the repo root, so the file is not reachable from the build.

#1203 asked for "pin exact versions in one file and have the Dockerfile read
it". The second half cannot be done the obvious way: widening the build context
to the repo root would break the image stamp (#1180), which hashes every file in
the context to decide whether to rebuild -- with the repo as context, editing a
recipe would trigger a container rebuild. The narrow context is load-bearing.

So the fix is the other shape, and this repository already has the precedent two
blocks up in that same Dockerfile: the Playwright version is pinned there AND in
`scripts/browser/install.sh`, and `tests/test_browser_harness.py` fails if they
differ. A "keep in sync by hand" comment is a hope. A test is the sync.

WHAT DRIFTED, MEASURED 2026-09-28. Both files said `>=`, not `==`:
`requirements-test.txt` said `pytest>=8.0` and `PyYAML>=6.0`, and the Dockerfile
repeated those floors. So CI installed whatever was newest on the day it ran,
the image installed whatever was newest when it was last built, and the two
could differ indefinitely with nothing noticing. The image in use carried pytest
9.1.1 under a floor of 8.0, and no file anywhere recorded the version the suite
was actually green on. A floor says "at least this works"; a pin says "this
works", and only the second is a fact somebody measured.
"""
from __future__ import annotations

import pathlib
import re

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-test.txt"
DOCKERFILE = ROOT / ".devcontainer" / "Dockerfile"
WORKFLOW = ROOT / ".github" / "workflows" / "build-and-deploy.yml"

# `name==version`, ignoring comments and blank lines.
PIN = re.compile(r"^([A-Za-z0-9._-]+)==([0-9][0-9A-Za-z.]*)\s*$")


def _required() -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN.match(line)
        assert match, (
            f"requirements-test.txt line {line!r} is not an exact pin. Every "
            "dependency here is pinned with `==` on purpose (#1203): a floor "
            "lets CI and the container image drift apart silently, which is "
            "what this file was for weeks."
        )
        pins[match.group(1).lower()] = match.group(2)
    assert pins, "requirements-test.txt declares no pins at all"
    return pins


def _dockerfile_pins() -> dict[str, str]:
    """Every `"name==version"` quoted argument in the Dockerfile's pip install."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    return {
        name.lower(): version
        for name, version in re.findall(
            r'"([A-Za-z0-9._-]+)==([0-9][0-9A-Za-z.]*)"', text
        )
    }


def test_requirements_are_all_exact_pins():
    """The assertion lives in the helper, so this is the test that names it."""
    pins = _required()
    assert "pytest" in pins, f"no pytest pin among {sorted(pins)}"


def test_the_image_installs_what_this_file_pins():
    """THE POINT OF THE FILE. If these disagree, a green suite in the container
    says nothing about a green suite in CI, and vice versa."""
    required = _required()
    installed = _dockerfile_pins()

    missing = sorted(set(required) - set(installed))
    assert not missing, (
        f"requirements-test.txt pins {missing} and .devcontainer/Dockerfile "
        "does not install them. The Dockerfile cannot COPY that file (its build "
        "context is .devcontainer/), so the pins are repeated by hand -- add "
        "them to the `pip install` line, then rebuild the image."
    )

    wrong = {
        name: (version, installed[name])
        for name, version in required.items()
        if installed[name] != version
    }
    assert not wrong, (
        "the Dockerfile pins a different version from requirements-test.txt: "
        + "; ".join(
            f"{name} wants {want} but the image installs {got}"
            for name, (want, got) in sorted(wrong.items())
        )
        + ". requirements-test.txt is the single source -- edit the Dockerfile "
        "to match it, then rebuild the image."
    )


def test_ci_installs_from_the_requirements_file_rather_than_its_own_list():
    """CI's advantage over the image is that it CAN read the file. It should, so
    that exactly one of the two places needs a hand-maintained copy."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pip install -r requirements-test.txt" in text, (
        "the workflow no longer installs from requirements-test.txt. If it "
        "grew its own package list, there would be three copies of these pins "
        "and two of them hand-maintained."
    )


def test_every_way_of_starting_the_container_names_one_bundle_cache():
    """#1203: there were TWO bundle-cache volume names, so which one got used --
    and therefore whether `bundle install` had to run from scratch -- depended on
    how the container was started. `devcontainer.json` said
    `helen-triages-bundle-cache`; `run.sh` said
    `helen-triages-bundle-cache-helen-triages`.

    The README made it worse by claiming `devcontainer.json` is "set up to match
    Phase 1 above (same volumes, same env)", which was not true. Aligned onto
    `run.sh`'s name rather than the shorter one, because run.sh is the primary
    path in the README and its volume is the populated one; the VS Code path
    already runs `bundle install` as its `postCreateCommand`, so it refills for
    free.
    """
    run_sh = (ROOT / ".devcontainer" / "run.sh").read_text(encoding="utf-8")
    declared = re.search(r"^BUNDLE_VOLUME=(\S+)", run_sh, re.M)
    assert declared, "run.sh no longer assigns BUNDLE_VOLUME"
    name = declared.group(1)

    others = {
        ".devcontainer/devcontainer.json": ROOT / ".devcontainer" / "devcontainer.json",
        ".devcontainer/README.md": ROOT / ".devcontainer" / "README.md",
    }
    for label, path in others.items():
        text = path.read_text(encoding="utf-8")
        # Every mention of a bundle-cache volume, so a stale short name is caught
        # rather than merely joined by a correct one.
        mentions = set(re.findall(r"helen-triages-bundle-cache[A-Za-z0-9._-]*", text))
        assert mentions, f"{label} names no bundle-cache volume at all"
        assert mentions == {name}, (
            f"{label} names {sorted(mentions)} but run.sh uses {name!r}. Two "
            "names means the cache that gets used depends on how the container "
            "was started, and one of them is always cold."
        )


def test_the_container_and_ci_agree_on_a_node_major():
    """#1203: the container installed Node 22 while CI's setup-node said 24, so
    the JS suite ran on two majors -- one of them in the gate that decides
    whether the site deploys -- for weeks with no difference showing. That is
    luck, and the version a test passed under is part of what the pass means.

    Read as MAJORS, because the two sources cannot express the same precision:
    NodeSource ships a `setup_24.x` script and setup-node takes `"24"`.
    """
    docker = re.search(r"deb\.nodesource\.com/setup_(\d+)\.x",
                       DOCKERFILE.read_text(encoding="utf-8"))
    assert docker, "no NodeSource setup_NN.x line in .devcontainer/Dockerfile"

    workflow = re.search(r'node-version:\s*"?(\d+)',
                         WORKFLOW.read_text(encoding="utf-8"))
    assert workflow, "no node-version in the workflow's setup-node step"

    assert docker.group(1) == workflow.group(1), (
        f".devcontainer/Dockerfile installs Node {docker.group(1)} and CI uses "
        f"Node {workflow.group(1)}. Pin both to one major: the JS suite's pass "
        "means less when the two run different runtimes, and CI's is the one "
        "that gates the deploy."
    )
