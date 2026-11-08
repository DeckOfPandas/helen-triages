"""kit/manifest names every file the kit tracks, once. Kit repo only: a
project has no manifest, only the kit.lock a sync writes from it."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from .conftest import load_tool

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "kit" / "manifest"
sync = load_tool("sync")
build = load_tool("build")


@pytest.fixture
def owned() -> tuple[dict[str, dict[str, str | None]], list[str]]:
    """(each kind -> {path: template}, every tracked file)."""
    if not MANIFEST.is_file():
        pytest.skip("this is a project: kit/manifest lives in the kit only")
    files = [f for f in subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                                       text=True, check=True).stdout.split("\0") if f]
    return sync.expand(sync.read_manifest(MANIFEST.read_text(encoding="utf-8")), files), files


def test_every_tracked_file_has_an_owner(owned):
    owned, files = owned
    named = set().union(*owned.values())
    missing = sorted(set(files) - named)
    assert not missing, f"kit/manifest doesn't say who owns: {missing}"


def test_project_templates_exist(owned):
    owned, _ = owned
    assert owned["project"], "no project paths read from kit/manifest -- parsing broke?"
    for path, template in owned["project"].items():
        assert (ROOT / (template or path)).is_file(), f"{path}'s template {template or path} is missing"


def test_generated_paths_are_what_the_builder_writes(owned):
    owned, _ = owned
    assert set(owned["generated"]) == {str(build.SETTINGS), str(build.DEVCONTAINER)}


def test_the_builders_inputs_are_kit_or_project_owned(owned):
    owned, _ = owned
    assert str(build.KIT_SETTINGS) in owned["kit"] and str(build.DEVCONTAINER_TEMPLATE) in owned["kit"]
    assert str(build.PROJECT_SETTINGS) in owned["project"] and str(build.KIT_ENV) in owned["project"]


def test_what_a_project_needs_to_sync_and_check_ships(owned):
    owned, _ = owned
    for path in ("tools/kit/sync.py", "tools/kit/build.py", "tests/kit/test_kit_lock.py",
                 ".claude/kit/RULES.md", ".claude/skills/kit-sync/SKILL.md"):
        assert path in owned["kit"], f"{path} is not shipped to projects"


@pytest.mark.parametrize("line,message", [
    ("kit", "is not `<kind> <path>`"),
    ("owned scripts/", "is not `<kind> <path>`"),
    ("kit a b", "is not `<kind> <path>`"),
    ("kit /etc/passwd", "relative path"),
    ("kit ../x", "relative path"),
])
def test_a_bad_manifest_line_is_refused(line, message):
    with pytest.raises(sync.SyncError, match=message):
        sync.read_manifest(line)


def test_a_path_claimed_twice_is_refused():
    with pytest.raises(sync.SyncError, match="twice"):
        sync.expand(sync.read_manifest("kit scripts/\nproject scripts/a.sh"), ["scripts/a.sh"])
