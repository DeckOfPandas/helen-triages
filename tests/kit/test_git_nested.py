"""scripts/git-nested.sh: git inside a nested clone, from a fixed list of verbs."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from .test_wrappers import CONF, ok, project, refused, run  # noqa: F401  (project is a fixture)

NESTED_CONF = CONF + 'NESTED_DIRS="_drafts _other"\n'
SAFE = ["-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", "_drafts"]


def nested(project: Path, *args: str):
    return run(project, "git-nested.sh", *args, conf=NESTED_CONF)


@pytest.mark.parametrize("args,tail", [
    (["status", "--short"], ["status", "--short"]),
    (["diff", "--stat", "main"], ["diff", "--no-ext-diff", "--no-textconv", "--stat", "main"]),
    (["log", "--oneline", "-5", "HEAD~2"], ["log", "--no-ext-diff", "--no-textconv", "--oneline", "-5", "HEAD~2"]),
    (["show", "--stat", "HEAD^"], ["show", "--no-ext-diff", "--no-textconv", "--stat", "HEAD^"]),
    (["branch", "--show-current"], ["branch", "--show-current"]),
    (["checkout", "-b", "tidy/x"], ["checkout", "-b", "tidy/x"]),
    (["add", "--", ".", "a/b.md"], ["add", "--", ".", "a/b.md"]),
    (["commit", "-F", "tmp/body.md"], ["commit", "-F", "../tmp/body.md"]),
])
def test_accepted_calls_run_with_hooks_off(project, args, tail):
    out = ok(nested(project, "_drafts", *args))
    assert out == ["git", *SAFE, *tail]


@pytest.mark.parametrize("args", [
    ["_drafts"],
    ["elsewhere", "status"],
    ["../x", "status"],
    ["_drafts", "push"],
    ["_drafts", "reset", "--hard"],
    ["_drafts", "stash", "drop"],
    ["_drafts", "status", "--ignored"],
    ["_drafts", "diff", "--output=/etc/x"],
    ["_drafts", "diff", "--no-index", "a", "b"],
    ["_drafts", "diff", "--ext-diff"],
    ["_drafts", "diff", "/etc/passwd"],
    ["_drafts", "diff", "../x"],
    ["_drafts", "log", "-1000"],
    ["_drafts", "branch", "-D", "x"],
    ["_drafts", "checkout", "main"],
    ["_drafts", "checkout", "-b", "main"],
    ["_drafts", "checkout", "--", "a"],
    ["_drafts", "add", "."],
    ["_drafts", "add", "--", "--chmod=+x"],
    ["_drafts", "commit", "-a"],
    ["_drafts", "commit", "-F", "notes.txt"],
    ["_drafts", "commit", "-F", "tmp/missing.md"],
    ["_drafts", "commit", "-F", "tmp/body.md", "--amend"],
])
def test_refusals(project, args):
    assert refused(nested(project, *args))


def test_refused_with_no_nested_dirs(project):
    assert refused(run(project, "git-nested.sh", "_drafts", "status"))


@pytest.mark.parametrize("value", ['"../x"', '".git"', '"-x"', '"a/b"',
                                   '"_x:nope"', '"../x:site"', '":site"'])
def test_bad_nested_dirs_are_refused(project, value):
    assert refused(run(project, "git-nested.sh", "x", "status", conf=CONF + f"NESTED_DIRS={value}\n"))


def test_a_folder_may_name_the_repo_it_clones(project):
    conf = CONF + 'NESTED_DIRS="_drafts:drafts _other"\n'
    out = ok(run(project, "git-nested.sh", "_drafts", "status", conf=conf))
    assert out == ["git", *SAFE, "status"]
    assert refused(run(project, "git-nested.sh", "_drafts:drafts", "status", conf=conf))


# --- for real, against a nested repo ------------------------------------------------

def live(project: Path, *args: str):
    (project / "scripts" / "github.conf").write_text(NESTED_CONF)
    return subprocess.run(["sh", "scripts/git-nested.sh", "_drafts", *args], cwd=project,
                          capture_output=True, text=True, timeout=30,
                          env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(project),
                               "GIT_CEILING_DIRECTORIES": str(project.parent),
                               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


@pytest.fixture
def clone(project: Path) -> Path:
    drafts = project / "_drafts"
    drafts.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=drafts, check=True)
    (drafts / "a.md").write_text("a\n")
    return drafts


def test_a_missing_clone_is_refused(project):
    assert refused(live(project, "status"))


def test_commit_on_main_is_refused(project, clone):
    assert live(project, "add", "--", "a.md").returncode == 0
    assert refused(live(project, "commit", "-F", "tmp/body.md"))


def test_commit_on_a_branch_runs_no_hook(project, clone):
    hook = clone / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\ntouch ../hook-ran\n")
    hook.chmod(0o755)
    assert live(project, "checkout", "-b", "work").returncode == 0
    assert live(project, "add", "--", "a.md").returncode == 0
    done = live(project, "commit", "-F", "tmp/body.md")
    assert done.returncode == 0, done.stderr
    assert not (project / "hook-ran").exists()
    log = live(project, "log", "--oneline", "-1")
    assert "hello" in log.stdout
