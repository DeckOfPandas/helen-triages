"""guard-git-output.py: the diff options that write, read outside, or run a program."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from .conftest import denied, run_hook

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]


@pytest.fixture
def hook(kit_root: Path) -> Path:
    return kit_root / ".claude" / "hooks" / "guard-git-output.py"


@pytest.mark.parametrize("command", [
    "git diff --output=CLAUDE.md",
    "git diff --output CLAUDE.md",
    "git diff HEAD~1 --output=/etc/x",
    "git diff -- --output=x",
    "git log -p --output=tmp/x",
    "git show HEAD --output=x",
    "git whatchanged --output=x",
    "git diff-tree -p HEAD --output=x",
    "git diff --no-index a /etc/passwd",
    "git diff --ext-diff",
    "git diff --textconv HEAD",
    "git -c core.pager=cat diff --output=x",
    "git --no-pager log --output=x",
    "/usr/bin/git diff --output=x",
    # Abbreviations a later git may accept.
    "git diff --outp=x",
    "git diff --ou=x",
    "git diff --no-ind a b",
    "git diff --ext",
    "git diff --textc",
    # Unbalanced quotes fall back to whitespace splitting, not to passing.
    "git diff --output=x 'unterminated",
])
def test_refuses(hook, tmp_path, command):
    assert denied(run_hook(hook, command, tmp_path)), command


@pytest.mark.parametrize("command", [
    "git diff",
    "git diff --stat main",
    "git diff --text HEAD",
    "git diff --output-indicator-new=+ HEAD",
    "git diff --no-ext-diff HEAD",
    "git diff --no-textconv HEAD",
    "git diff main > tmp/changes.patch",
    "git log --oneline -5",
    "git show HEAD:README.md",
    "git status --short",
    "git commit -F tmp/msg-about-git-diff-output.txt",
    "grep -rn -- '--output' .claude/hooks/",
    "sh scripts/git-diff-main-checkout.sh --patch tmp/x.patch",
])
def test_passes(hook, tmp_path, command):
    assert not denied(run_hook(hook, command, tmp_path)), command


def test_the_refusal_says_what_to_do_instead(hook, tmp_path):
    reason = run_hook(hook, "git diff --output=x", tmp_path)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "> tmp/changes.patch" in reason


def test_every_spelling_this_git_writes_with_is_refused(hook, tmp_path):
    """Ask the installed git which spellings really write, and check each is refused."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.txt").write_text("one\n")
    subprocess.run([*GIT, "init", "-q"], cwd=repo, check=True)
    subprocess.run([*GIT, "add", "."], cwd=repo, check=True)
    subprocess.run([*GIT, "commit", "-qm", "x"], cwd=repo, check=True)
    (repo / "a.txt").write_text("two\n")
    writers = []
    for spelling in ("--output=out", "--outpu=out", "--outp=out", "--out=out", "--ou=out", "--o=out"):
        subprocess.run(["git", "diff", spelling], cwd=repo, capture_output=True)
        if (repo / "out").exists():
            writers.append(spelling)
            (repo / "out").unlink()
    assert "--output=out" in writers
    for spelling in writers:
        assert denied(run_hook(hook, f"git diff {spelling}", tmp_path)), spelling


def test_wired_into_settings_without_an_if(kit_root):
    settings = json.loads((kit_root / ".claude" / "settings.json").read_text())
    hooks = [h for group in settings["hooks"]["PreToolUse"] if group.get("matcher") == "Bash"
             for h in group["hooks"]]
    wired = [h for h in hooks if h["command"].endswith('/.claude/hooks/guard-git-output.py"')]
    assert wired and "if" not in wired[0]
