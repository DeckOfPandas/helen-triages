"""CI and the container run the suite on the same versions.

CI installs from requirements-test.txt and sets up its own Node; the container
is the kit's image built from .devcontainer/kit.env and requirements.txt, with
pytest pinned in the kit's Dockerfile. A green suite in one says something
about the other only while these agree, and CI's run gates the deploy (#1203).
Exact pins, not floors: with `>=` each side installs whatever is newest.
"""
from __future__ import annotations

import pathlib
import re

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-test.txt"
IMAGE_REQUIREMENTS = ROOT / ".devcontainer" / "requirements.txt"
KIT_ENV = ROOT / ".devcontainer" / "kit.env"
DOCKERFILE = ROOT / ".devcontainer" / "Dockerfile"
WORKFLOW = ROOT / ".github" / "workflows" / "build-and-deploy.yml"
PIN = re.compile(r"^([A-Za-z0-9._-]+)==([0-9][0-9A-Za-z.]*)\s*$")


def _pins(path: pathlib.Path) -> dict[str, str]:
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        match = PIN.match(line)
        assert match, f"{path.name}: {line!r} is not an exact `name==version` pin"
        pins[match.group(1).lower()] = match.group(2)
    return pins


def _kit_env(key: str) -> str:
    match = re.search(rf"^{key}=\"?([^\"\s#]+)", KIT_ENV.read_text(encoding="utf-8"), re.M)
    assert match, f".devcontainer/kit.env sets no {key}"
    return match.group(1)


def test_ci_installs_from_the_requirements_file_rather_than_its_own_list():
    assert "pip install -r requirements-test.txt" in WORKFLOW.read_text(encoding="utf-8"), (
        "the workflow no longer installs from requirements-test.txt; a list of its own "
        "would be one more hand-kept copy of these pins")


def test_ci_runs_the_pytest_the_image_installs():
    image = re.search(r'"pytest==([0-9.]+)"', DOCKERFILE.read_text(encoding="utf-8"))
    assert image, "the kit's Dockerfile no longer pins pytest"
    assert _pins(REQUIREMENTS)["pytest"] == image.group(1), (
        f"requirements-test.txt pins pytest {_pins(REQUIREMENTS)['pytest']} and the kit's "
        f"image installs {image.group(1)}: follow the image (the kit owns it)")


def test_ci_and_the_image_pin_the_same_pyyaml():
    assert _pins(REQUIREMENTS)["pyyaml"] == _pins(IMAGE_REQUIREMENTS)["pyyaml"], (
        "requirements-test.txt and .devcontainer/requirements.txt pin different PyYAML")


def test_ci_and_the_image_pin_the_same_playwright():
    assert _pins(REQUIREMENTS)["playwright"] == _kit_env("PLAYWRIGHT_VERSION"), (
        "requirements-test.txt's playwright and kit.env's PLAYWRIGHT_VERSION differ, so CI's "
        "binding and the image's browsers are different releases")


def test_ci_and_the_container_run_one_node_major():
    workflow = re.search(r'node-version:\s*"?(\d+)', WORKFLOW.read_text(encoding="utf-8"))
    assert workflow, "no node-version in the workflow's setup-node step"
    assert workflow.group(1) == _kit_env("NODE_MAJOR"), (
        f"CI runs Node {workflow.group(1)} and kit.env's NODE_MAJOR is {_kit_env('NODE_MAJOR')}")
