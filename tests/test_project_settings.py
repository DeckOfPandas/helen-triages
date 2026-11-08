"""helen-triages' own settings and test plumbing, beside the kit's.

The kit's tests (tests/kit/) hold everything the kit ships; these hold the
rulings that are this project's (DECISIONS §11): no host-only runtime, the
retired /workspace/.node-runtime, the dead `.gh-runtime` merge deny kept, and
conftest's tmp_path.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
PERMISSIONS = SETTINGS["permissions"]


def test_no_allow_rule_names_a_host_only_runtime():
    """Claude runs only in the container, where gh and node are on PATH; a rule
    naming the host checkout's runtimes grants nothing and reads as if it did."""
    for rule in PERMISSIONS["allow"]:
        assert ".gh-runtime" not in rule and ".node-runtime" not in rule, rule


def test_the_node_runtime_is_retired():
    assert not any(".node-runtime" in d for d in PERMISSIONS.get("additionalDirectories", []))
    assert not any(".node-runtime" in rule for rule in PERMISSIONS["deny"])


def test_the_dead_gh_runtime_merge_deny_stays():
    """A deny on a dead path costs nothing, and removing a rail is not pruning."""
    assert "Bash(.gh-runtime/bin/gh pr merge *)" in PERMISSIONS["deny"]


def test_tmp_path_is_this_repos_and_git_cannot_climb_out_of_it(tmp_path):
    """conftest's `tmp_path`: under this repo's tmp/, never the system /tmp,
    and git run inside it finds no repository above it."""
    assert (ROOT / "tmp") in tmp_path.parents, tmp_path
    probe = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=tmp_path,
                           capture_output=True, text=True)
    assert probe.returncode != 0, (
        f"git found {probe.stdout.strip()} from inside tmp_path, so a "
        "'no repository here' test would be judged by this worktree")
