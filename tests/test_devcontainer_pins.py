"""requirements-test.txt is the single source; the Dockerfile's copy must agree.

`.devcontainer/Dockerfile` repeats the pins by hand because it cannot `COPY
requirements-test.txt`: its build context is `.devcontainer/`, not the repo
root. The narrow context has to stay, because the image stamp (#1180) hashes
every file in the context, and with the repo as context editing a recipe would
rebuild the container. So the two copies are held together by this test (#1203).

Exact pins, not floors: with `>=`, CI and the image each install whatever is
newest on the day, and no file records the version the suite is green on.
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
    """If these disagree, a green suite in the container says nothing about a
    green suite in CI, and vice versa."""
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
    """`devcontainer.json` and the README name the bundle-cache volume `run.sh`
    assigns, and no other (#1203).

    With two names, which cache is used, and so whether `bundle install` runs
    from scratch, depends on how the container was started.
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
    """The container and CI run the JS suite on one Node major (#1203): the
    version a test passed under is part of what the pass means, and CI's run
    gates the deploy.

    Read as majors, because the two sources cannot express the same precision:
    NodeSource ships a `setup_NN.x` script and setup-node takes `"NN"`.
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
