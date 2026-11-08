"""The session-start lines about place: the image's nested-clone warning
(.devcontainer/session-place.py) and the kit line in session-ground-truth.py."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLACE = ROOT / ".devcontainer" / "session-place.py"
GROUND_TRUTH = ROOT / ".claude" / "hooks" / "session-ground-truth.py"
GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *GIT_ID, *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def new_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    (path / "f").write_text("x\n")
    git(path, "add", "f")
    git(path, "commit", "-q", "-m", "one")
    return path


def place(cwd: Path, root: Path) -> str | None:
    done = subprocess.run(["python3", str(PLACE), str(root)], input=json.dumps({"cwd": str(cwd)}),
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    if not done.stdout.strip():
        return None
    return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = new_repo(tmp_path / "workspace")
    git(root, "worktree", "add", "-q", "-b", "wt", ".claude/worktrees/wt")
    (root / "src").mkdir()
    new_repo(root / "drafts")
    return root


def test_quiet_at_the_root_in_a_subfolder_and_in_a_worktree(workspace):
    assert place(workspace, workspace) is None
    assert place(workspace / "src", workspace) is None
    assert place(workspace / ".claude" / "worktrees" / "wt", workspace) is None


def test_warns_in_a_nested_clone(workspace):
    message = place(workspace / "drafts", workspace)
    assert message and "nested clone" in message and "do not run here" in message
    assert str(workspace / "drafts") in message


def test_warns_outside_the_project(workspace, tmp_path):
    message = place(tmp_path, workspace)
    assert message and "outside the project" in message


def test_the_image_wires_the_warning_into_managed_settings():
    dockerfile = (ROOT / ".devcontainer" / "Dockerfile").read_text()
    assert "COPY managed-settings.json /etc/claude-code/managed-settings.json" in dockerfile
    copied = re.search(r"^COPY session-place\.py (\S+)$", dockerfile, re.MULTILINE).group(1)
    managed = json.loads((ROOT / ".devcontainer" / "managed-settings.json").read_text())
    commands = [h["command"] for group in managed["hooks"]["SessionStart"] for h in group["hooks"]]
    assert commands == [f"python3 {copied} /workspace"]


def test_the_image_files_are_in_the_build_stamp():
    ignored = (ROOT / ".devcontainer" / ".dockerignore").read_text().split()
    assert "managed-settings.json" not in ignored and "session-place.py" not in ignored


# --- the kit line ---------------------------------------------------------------------------

def kit_line(cwd: Path) -> str:
    done = subprocess.run(["python3", str(GROUND_TRUTH)], input=json.dumps({"cwd": str(cwd)}),
                          capture_output=True, text=True, cwd=cwd, timeout=30)
    report = json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
    return next(line.strip() for line in report.splitlines() if line.strip().startswith("kit:"))


def test_kit_line_in_the_kit(tmp_path):
    repo = new_repo(tmp_path / "kit")
    (repo / "kit").mkdir()
    (repo / "kit" / "manifest").write_text("")
    assert kit_line(repo) == "kit: this repo is the kit"


def test_kit_line_never_synced(tmp_path):
    assert "never synced" in kit_line(new_repo(tmp_path / "p"))


@pytest.fixture
def synced(tmp_path: Path) -> tuple[Path, Path, str]:
    """A project locked at the kit's first commit, the kit since moved on twice."""
    upstream = new_repo(tmp_path / "upstream")
    first = git(upstream, "rev-parse", "HEAD")
    project = new_repo(tmp_path / "project")
    (project / ".claude" / "kit").mkdir(parents=True)
    (project / ".claude" / "kit" / "kit.lock").write_text(json.dumps(
        {"kit_repo": "no-such-repo", "kit_commit": first, "files": {}}))
    return project, upstream, first


def test_kit_line_without_a_clone(synced):
    project, _, first = synced
    assert kit_line(project) == (f"kit: synced at {first[:12]}; no tmp/kit clone to compare with "
                                 "-- /kit-sync clones one")


def test_kit_line_counts_commits_behind(synced):
    project, upstream, first = synced
    git(project, "clone", "-q", str(upstream), "tmp/kit")
    assert kit_line(project) == f"kit: up to date (synced at {first[:12]}; as last fetched)"
    for n in ("two", "three"):
        (upstream / "f").write_text(n)
        git(upstream, "commit", "-q", "-am", n)
    git(project / "tmp" / "kit", "fetch", "-q")
    assert kit_line(project) == f"kit: 2 commits behind (synced at {first[:12]}; as last fetched) -- /kit-sync"


def test_kit_line_in_a_worktree_uses_the_main_checkouts_clone(synced):
    project, upstream, first = synced
    git(project, "clone", "-q", str(upstream), "tmp/kit")
    git(project, "add", ".claude/kit/kit.lock")
    git(project, "commit", "-q", "-m", "lock")
    git(project, "worktree", "add", "-q", "-b", "wt", "wt")
    assert kit_line(project / "wt") == f"kit: up to date (synced at {first[:12]}; as last fetched)"
