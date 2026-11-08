"""scripts/git-diff-main-checkout.sh, against a real repo with one worktree."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]


@pytest.fixture
def worktree(tmp_path: Path, kit_root: Path) -> Path:
    main = tmp_path / "main"
    main.mkdir()
    shutil.copy(kit_root / "scripts" / "git-diff-main-checkout.sh", main / "diff.sh")
    (main / "a.txt").write_text("one\n")
    (main / "b.txt").write_text("one\n")
    subprocess.run([*GIT, "init", "-q"], cwd=main, check=True)
    subprocess.run([*GIT, "add", "."], cwd=main, check=True)
    subprocess.run([*GIT, "commit", "-qm", "x"], cwd=main, check=True)
    subprocess.run([*GIT, "worktree", "add", "-q", str(tmp_path / "wt")], cwd=main, check=True)
    (main / "a.txt").write_text("two\n")
    (main / "b.txt").write_text("two\n")
    (tmp_path / "wt" / "tmp").mkdir()
    return tmp_path / "wt"


def run(worktree: Path, *args: str):
    return subprocess.run(["sh", "diff.sh", *args], cwd=worktree, capture_output=True, text=True,
                          env={"PATH": "/usr/local/bin:/usr/bin:/bin",
                               "GIT_CEILING_DIRECTORIES": str(worktree.parent)})


def test_shows_the_main_checkouts_changes(worktree):
    done = run(worktree)
    assert done.returncode == 0, done.stderr
    assert "+two" in done.stdout and "a.txt" in done.stdout and "b.txt" in done.stdout


def test_stat_and_pathspec(worktree):
    done = run(worktree, "--stat", "a.txt")
    assert done.returncode == 0, done.stderr
    assert "a.txt" in done.stdout and "b.txt" not in done.stdout


def test_patch_applies_in_the_worktree(worktree):
    done = run(worktree, "--patch", "tmp/main.patch")
    assert done.returncode == 0, done.stderr
    subprocess.run(["git", "apply", "tmp/main.patch"], cwd=worktree, check=True)
    assert (worktree / "a.txt").read_text() == "two\n"


@pytest.mark.parametrize("args", [
    ["/etc/passwd"], ["../x"], ["-p"], ["a;b"], ["--stat", "--output=x"],
    ["--patch"], ["--patch", "out.patch"], ["--patch", "tmp/../x.patch"], ["--patch", "/tmp/x.patch"],
])
def test_refusals(worktree, args):
    done = run(worktree, *args)
    assert done.returncode == 2 and "refused" in done.stderr


def test_patch_refuses_a_symlink(worktree):
    (worktree / "tmp" / "link.patch").symlink_to("/dev/null")
    done = run(worktree, "--patch", "tmp/link.patch")
    assert done.returncode == 2 and "symlink" in done.stderr
