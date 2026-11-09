"""The .claude/hooks guards: what each refuses and what it lets through."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from .conftest import denied, run_hook


@pytest.fixture
def hooks(kit_root: Path) -> Path:
    return kit_root / ".claude" / "hooks"


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    return tmp_path


# --- guard-main-branch --------------------------------------------------------------

@pytest.mark.parametrize("command", ["git commit -m x", "git -c a=b commit -F tmp/m", "git merge feat"])
def test_commit_on_main_is_refused(hooks, repo, command):
    assert denied(run_hook(hooks / "guard-main-branch.py", command, repo))


@pytest.mark.parametrize("command", ["git status", "git push x", 'echo "git commit"', "git log"])
def test_other_commands_on_main_pass(hooks, repo, command):
    assert not denied(run_hook(hooks / "guard-main-branch.py", command, repo))


def test_commit_on_a_branch_passes(hooks, repo):
    git(repo, "checkout", "-q", "-b", "feat")
    assert not denied(run_hook(hooks / "guard-main-branch.py", "git commit -m x", repo))


def test_commit_aimed_at_a_nested_repo_on_main(hooks, repo):
    git(repo, "checkout", "-q", "-b", "feat")
    nested = repo / "nested"
    nested.mkdir()
    git(nested, "init", "-q", "-b", "main")
    assert denied(run_hook(hooks / "guard-main-branch.py", "git -C nested commit -m x", repo))


# --- guard-destructive-git -------------------------------------------------------------

DESTRUCTIVE = ["git reset --hard", "git checkout -- a.txt", "git checkout .", "git clean -fd",
               "git restore a.txt", "git checkout a.txt"]


@pytest.mark.parametrize("command", DESTRUCTIVE)
def test_destructive_on_dirty_tree_is_refused(hooks, repo, command):
    (repo / "a.txt").write_text("work")
    assert denied(run_hook(hooks / "guard-destructive-git.py", command, repo))


@pytest.mark.parametrize("command", DESTRUCTIVE[:4])
def test_destructive_on_clean_tree_passes(hooks, repo, command):
    assert not denied(run_hook(hooks / "guard-destructive-git.py", command, repo))


@pytest.mark.parametrize("command", ["git restore --staged a.txt", "git stash -u", 'git commit -m "git reset --hard"'])
def test_safe_forms_pass_on_dirty_tree(hooks, repo, command):
    (repo / "a.txt").write_text("work")
    assert not denied(run_hook(hooks / "guard-destructive-git.py", command, repo))


def test_stash_drop_with_no_stashes_passes(hooks, repo):
    assert not denied(run_hook(hooks / "guard-destructive-git.py", "git stash drop", repo))


def stash_something(repo: Path) -> None:
    (repo / "a.txt").write_text("one")
    git(repo, "add", "a.txt")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "one")
    (repo / "a.txt").write_text("two")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "stash", "push", "-q", "-m", "kept")


@pytest.mark.parametrize("command", ["git stash drop", "git stash clear"])
def test_stash_drop_with_stashes_is_refused(hooks, repo, command):
    stash_something(repo)
    assert denied(run_hook(hooks / "guard-destructive-git.py", command, repo))


def test_stash_drop_asks_the_repo_it_targets(hooks, repo):
    nested = repo / "nested"
    nested.mkdir()
    git(nested, "init", "-q", "-b", "main")
    stash_something(nested)
    guard = hooks / "guard-destructive-git.py"
    assert denied(run_hook(guard, "git -C nested stash drop", repo))
    assert not denied(run_hook(guard, "git stash drop", repo))
    stash_something(repo)
    other = repo / "other"
    other.mkdir()
    git(other, "init", "-q", "-b", "main")
    assert not denied(run_hook(guard, "git -C other stash drop", repo))


# --- guard-token-expansion -------------------------------------------------------------------

@pytest.mark.parametrize("command", [
    "echo $AGENT_GH_TOKEN",
    'echo "${AGENT_GH_TOKEN:+set}"',
    "printf '%s' ${#GH_TOKEN}",
    "ls | echo $MY_SECRET",
    "x=${AGENT_GH_TOKEN:-none}",
    "git clone https://bot:$AGENT_GH_TOKEN@github.com/a/b",
    "sh scripts/gh-read.sh repos/a/b --jq env",
    "printenv",
    "env",
    "env -0",
    "cat /proc/self/environ",
    "grep x ghp_" + "a" * 36,
])
def test_token_exposures_are_refused(hooks, tmp_path, command):
    assert denied(run_hook(hooks / "guard-token-expansion.py", command, tmp_path))


@pytest.mark.parametrize("command", [
    "echo '$AGENT_GH_TOKEN'",
    'GH_TOKEN="$AGENT_GH_TOKEN" gh issue list',
    "env FOO=1 ls",
    "echo $HOME",
    "sh scripts/gh-read.sh repos/a/b --fields state",
    "printf 'a ghp_ token'",
])
def test_harmless_forms_pass(hooks, tmp_path, command):
    assert not denied(run_hook(hooks / "guard-token-expansion.py", command, tmp_path))


def test_token_in_a_script_the_command_runs(hooks, tmp_path):
    (tmp_path / "tmp").mkdir()
    (tmp_path / "tmp" / "x.sh").write_text("git push https://u:${AGENT_GH_TOKEN}@github.com/a/b\n")
    assert denied(run_hook(hooks / "guard-token-expansion.py", "sh tmp/x.sh", tmp_path))


# --- session-ground-truth -----------------------------------------------------------------------

def test_ground_truth_reports_branch(hooks, repo):
    done = subprocess.run(
        ["python3", str(hooks / "session-ground-truth.py")],
        input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True, cwd=repo,
    )
    report = json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "branch: main -- DO NOT COMMIT" in report
    assert "sandbox:" in report and "tree: clean" in report


def _ground_truth(hooks: Path, repo: Path) -> str:
    done = subprocess.run(
        ["python3", str(hooks / "session-ground-truth.py")],
        input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True, cwd=repo,
    )
    return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]


def test_ground_truth_names_an_absent_nested_clone_and_how_to_clone_it(hooks, repo):
    (repo / "scripts").mkdir()
    (repo / "scripts" / "github.local.conf").write_text(
        'GH_REPOS="site drafts"\nNESTED_DIRS="_drafts:drafts _scratch"  # second has no repo\n')
    report = _ground_truth(hooks, repo)
    assert "nested: _drafts ABSENT" in report
    assert "sh scripts/git-clone-agent.sh drafts _drafts" in report
    assert "_scratch" not in report


def test_ground_truth_names_an_absent_clone_inside_a_clone(hooks, repo):
    (repo / "scripts").mkdir()
    (repo / "scripts" / "github.local.conf").write_text(
        'GH_REPOS="site drafts"\nNESTED_DIRS="site:site site/_drafts:drafts"\n')
    (repo / "site").mkdir()
    git(repo / "site", "init", "-q")
    report = _ground_truth(hooks, repo)
    assert "nested: site/_drafts ABSENT" in report
    assert "sh scripts/git-clone-agent.sh drafts site/_drafts" in report


def test_ground_truth_is_quiet_when_every_nested_clone_is_there(hooks, repo):
    (repo / "scripts").mkdir()
    (repo / "scripts" / "github.local.conf").write_text('NESTED_DIRS="_drafts:drafts"\n')
    (repo / "_drafts").mkdir()
    git(repo / "_drafts", "init", "-q")
    assert "nested:" not in _ground_truth(hooks, repo)


# --- analysable commands, sed, awk, inline programs ------------------------------------------

@pytest.mark.parametrize("hook,command", [
    ("guard-sed.py", "sed -i s/a/b/ f"),
    ("guard-sed.py", "cat f | /usr/bin/sed x"),
    ("guard-awk.py", "gawk '{print}' f"),
    ("guard-inline-script.py", "python3 -c 'print(1)'"),
    ("guard-inline-script.py", "node -e 'x'"),
    ("guard-unanalyzable-bash.py", "ls | wc -l"),
    ("guard-unanalyzable-bash.py", "a && b"),
    ("guard-unanalyzable-bash.py", "echo $(id)"),
    ("guard-unanalyzable-bash.py", 'echo "$(id)"'),
    ("guard-unanalyzable-bash.py", "cd x"),
    ("guard-unanalyzable-bash.py", "git -C x status"),
    ("guard-unanalyzable-bash.py", "FOO=1 ls"),
    ("guard-unanalyzable-bash.py", "ls *.md"),
    ("guard-unanalyzable-bash.py", "cat <<EOF"),
    ("guard-unanalyzable-bash.py", "a || b"),
    ("guard-unanalyzable-bash.py", "curl https://x/y?a=1&b=2"),
    ("guard-unanalyzable-bash.py", "(cd x)"),
    ("guard-unanalyzable-bash.py", "sh scripts/gh-read.sh repos/o/r --jq '[.a] | @tsv'"),
    ("guard-unanalyzable-bash.py", 'grep "$[a]" f'),
    ("guard-unanalyzable-bash.py", "curl --proto =https --output tmp/x https://x"),
    ("guard-unanalyzable-bash.py", "ls =python3"),
    # Both reached the human as prompts: the checker reads `|=name` inside quotes.
    ("guard-unanalyzable-bash.py", 'grep -rnE "proto|=cmd|lone" tests/x.py'),
    ("guard-unanalyzable-bash.py", "grep -n -E 'proto|equals|=https' tests/x.py"),
])
def test_guard_refusals(hooks, tmp_path, hook, command):
    assert denied(run_hook(hooks / hook, command, tmp_path))


@pytest.mark.parametrize("hook,command", [
    ("guard-sed.py", 'git commit -m "no sed here"'),
    ("guard-sed.py", "cat processed.txt"),
    ("guard-awk.py", "python3 guard-awk.py"),
    ("guard-inline-script.py", "python3 tmp/x.py"),
    ("guard-inline-script.py", "git -c a=b status"),
    ("guard-unanalyzable-bash.py", "git status 2>&1"),
    ("guard-unanalyzable-bash.py", "grep 'a|b' f"),
    ("guard-unanalyzable-bash.py", "git -c credential.helper=x push"),
    ("guard-unanalyzable-bash.py", "curl --proto '=https' --output tmp/x https://x"),
    ("guard-unanalyzable-bash.py", "git log --format=%h --since=yesterday"),
    ("guard-unanalyzable-bash.py", "grep -n 'a = b' f"),
    ("guard-unanalyzable-bash.py", 'test "$a" = b'),
    ("guard-unanalyzable-bash.py", "grep -n 'proto=https' f"),
    ("guard-unanalyzable-bash.py", "grep -n -E 'a|= b' f"),
    ("guard-unanalyzable-bash.py", "echo '$(not run)'"),
    ("guard-unanalyzable-bash.py", "python3 -m json.tool f > /dev/null"),
    ("guard-unanalyzable-bash.py", "sh scripts/gh-read.sh 'repos/o/r?a=1&b=2' --fields a,b"),
])
def test_guard_passes(hooks, tmp_path, hook, command):
    assert not denied(run_hook(hooks / hook, command, tmp_path))


def test_cd_and_git_dash_c_refusals_say_what_to_do_instead(hooks, tmp_path):
    for command in ("cd /workspace", "git -C ../.. diff"):
        reason = run_hook(hooks / "guard-unanalyzable-bash.py", command, tmp_path)[
            "hookSpecificOutput"]["permissionDecisionReason"]
        assert "scripts/" in reason and "validated arguments" in reason, command
