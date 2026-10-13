"""guard-main-branch.py and guard-destructive-git.py, broken on purpose.

A guard is proved by breaking the thing on purpose (#1198, DECISIONS §11).
Each hook is fed the JSON the harness feeds it, on stdin, with the subprocess's
`cwd` set to a throwaway `git init` repository. A real repository, not a mock:
what is proved is that the hook agrees with git. The nested-repository case
(`git -C _food_drafts ...`) is tested for both hooks, because a hook that asks
the outer repository gives the wrong answer silently.

`cwd` is always a throwaway repo, never this worktree. `guard-destructive-git.py`
reads `git stash list` in the process's own directory, and the stash stack is
shared between the primary checkout and every worktree, so a stash test run
here would pass or fail on another session's work.

Not `git worktree add`: an interrupted test would leave an entry only
`git worktree prune` clears, which is Helen's.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

pytestmark = pytest.mark.shared

HOOKS = pathlib.Path(__file__).resolve().parents[1] / ".claude" / "hooks"

# A committer for the throwaway repos, passed per invocation with `git -c` so
# nothing is written to a config file anywhere.
IDENTITY = [
    "-c", "user.name=Guard Test",
    "-c", "user.email=guard-test@example.invalid",
    "-c", "commit.gpgsign=false",
]


def _git(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60,
    )


def _repo(where: pathlib.Path, branch: str = "main") -> pathlib.Path:
    """A throwaway git repo on `branch` with one commit and one tracked file.

    Skips rather than fails if git cannot make it: a missing or ancient git is
    a fact about the machine, not a regression in the hook under test.
    """
    where.mkdir(parents=True, exist_ok=True)
    made = _git(where, "init", "--quiet", f"--initial-branch={branch}")
    if made.returncode != 0:
        pytest.skip(f"could not git init a probe repo: {made.stderr.strip()}")

    (where / "tracked.txt").write_text("first\n", encoding="utf-8")
    _git(where, "add", "--", "tracked.txt")
    committed = _git(where, *IDENTITY, "commit", "--quiet", "-m", "first")
    if committed.returncode != 0:
        pytest.skip(f"could not commit in a probe repo: {committed.stderr.strip()}")

    on = _git(where, "branch", "--show-current").stdout.strip()
    if on != branch:
        pytest.skip(f"probe repo is on {on!r}, not {branch!r}")
    return where


def _dirty(repo: pathlib.Path) -> None:
    """Make `tracked.txt` modified, so there is something real to lose."""
    (repo / "tracked.txt").write_text("edited, uncommitted\n", encoding="utf-8")


def _decision(hook: str, command: str, cwd: pathlib.Path) -> str | None:
    """The hook's `permissionDecisionReason`, or None if it allowed the call."""
    result = subprocess.run(
        ["python3", str(HOOKS / hook)],
        input=json.dumps({"tool_input": {"command": command}}),
        cwd=cwd, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    if not result.stdout.strip():
        return None
    payload = json.loads(result.stdout)
    output = payload["hookSpecificOutput"]
    if output.get("permissionDecision") != "deny":
        return None
    assert output["hookEventName"] == "PreToolUse"
    return output["permissionDecisionReason"]


# ---- guard-main-branch.py: the hook that protects `main` ----

COMMIT_AND_MERGE = [
    "git commit -F tmp/commit-msg.txt",
    "git commit --amend -F tmp/commit-msg.txt",
    "git commit -a -F tmp/commit-msg.txt",
    "git merge origin/main",
    "git merge --no-ff some-branch",
    # The credential-helper spelling every `git-*-agent.sh` wrapper uses. It
    # must not become a way past this hook: lowercase `-c` is allowed by
    # guard-unanalyzable-bash.py precisely so those wrappers work.
    "git -c credential.helper=scripts/git-credential-agent-token.sh commit -F tmp/m.txt",
]


@pytest.mark.parametrize("command", COMMIT_AND_MERGE)
@pytest.mark.parametrize("protected", ["main", "master"])
def test_main_branch_guard_refuses_writing_history_to_a_protected_branch(
    tmp_path, command, protected,
):
    repo = _repo(tmp_path / protected, branch=protected)
    reason = _decision("guard-main-branch.py", command, repo)
    assert reason is not None, f"allowed {command!r} on {protected}"
    assert protected in reason, reason
    assert "checkout -b" in reason, "the refusal does not say what to do instead"


@pytest.mark.parametrize("command", COMMIT_AND_MERGE)
def test_main_branch_guard_allows_the_same_commands_on_a_working_branch(
    tmp_path, command,
):
    """The whole workflow is committing on a branch. A guard that fired here
    would be a guard nothing could be done around except turning it off."""
    repo = _repo(tmp_path / "branch", branch="worktree-probe")
    assert _decision("guard-main-branch.py", command, repo) is None, command


@pytest.mark.parametrize("command", [
    # Everything else on `main` is untouched: reading, fetching, branching,
    # checking out, pushing an existing commit.
    "git status",
    "git log --oneline -5",
    "git diff",
    "git show HEAD",
    "git fetch origin",
    "git branch --show-current",
    "git checkout -b chore/1198-guard-tests",
    "sh scripts/git-push-agent.sh branch:branch",
    "sh scripts/git-fetch-main.sh",
    # Writing about the verbs: commit messages in this repository discuss them.
    "git log --grep 'git commit on main'",
    'git add -- tmp/notes-about-git-merge.txt',
])
def test_main_branch_guard_leaves_everything_else_on_main_alone(tmp_path, command):
    repo = _repo(tmp_path / "main-other", branch="main")
    assert _decision("guard-main-branch.py", command, repo) is None, command


def test_main_branch_guard_asks_the_nested_repo_not_the_outer_one(tmp_path):
    """Outer on a working branch, nested on `main`: the answer must come from
    the nested repository.

    A hook that recognises `git -C <nested> commit` as a commit and then
    checks the outer repository's branch lets a commit onto a drafts repo's
    own `main`.
    """
    outer = _repo(tmp_path / "outer", branch="worktree-probe")
    _repo(outer / "_food_drafts", branch="main")

    reason = _decision("guard-main-branch.py",
                       "git -C _food_drafts commit -F tmp/commit-msg.txt", outer)
    assert reason is not None, (
        "a commit onto a nested repo's `main` was allowed because the outer "
        "repo is on a branch -- the 2026-09-10 hole, reopened"
    )
    assert "_food_drafts" in reason, (
        f"the refusal does not name which repository it is about:\n{reason}"
    )


def test_main_branch_guard_reads_a_cd_and_a_dash_c_as_composing(tmp_path):
    """`cd a && git -C b commit` runs in `a/b`, not `a` and not `b`.

    Resolving the `-C` path against the worktree root finds a directory that
    does not exist, falls back to cwd, and allows the commit. Tested at the
    hook even though guard-unanalyzable-bash.py refuses a leading `cd`: the
    two hooks are independent, and this one must be correct alone.
    """
    outer = _repo(tmp_path / "outer", branch="worktree-probe")
    middle = outer / "middle"
    _repo(middle, branch="worktree-probe")
    _repo(middle / "_cocktail_drafts", branch="main")

    reason = _decision(
        "guard-main-branch.py",
        "cd middle && git -C _cocktail_drafts commit -F tmp/commit-msg.txt",
        outer,
    )
    assert reason is not None, "the cd and the -C did not compose"
    assert "_cocktail_drafts" in reason, reason


def test_a_leading_cd_into_a_nested_repo_is_refused_by_the_other_guard(tmp_path):
    """The `if` gate is not a hole, because another guard closes it.

    Both git guards are wired with `"if": "Bash(git *)"`, a prefix match, so
    neither ever sees `cd _food_drafts && git commit`.
    guard-unanalyzable-bash.py has no `if`, runs on every Bash call, and
    refuses the leading `cd` and the `&&`. If the gate or that guard changes,
    this test or the wiring test goes red.
    """
    repo = _repo(tmp_path / "outer", branch="worktree-probe")
    reason = _decision(
        "guard-unanalyzable-bash.py",
        "cd _food_drafts && git commit -F tmp/commit-msg.txt",
        repo,
    )
    assert reason is not None, (
        "a leading `cd` into a nested repo reaches git unexamined: the git "
        "guards are gated to `Bash(git *)` and cannot see this shape"
    )


def test_main_branch_guard_says_nothing_when_there_is_no_repository(tmp_path):
    """A hook must never break a tool call. Outside a repo there is no branch to
    read, and the answer is silence, not a crash and not a refusal."""
    nowhere = tmp_path / "not-a-repo"
    nowhere.mkdir()
    assert _decision("guard-main-branch.py",
                     "git commit -F tmp/commit-msg.txt", nowhere) is None


# ---- guard-destructive-git.py: the hook that protects uncommitted work ----

DESTRUCTIVE = [
    ("git reset --hard", "git reset --hard"),
    ("git reset --hard HEAD~1", "git reset --hard"),
    ("git checkout -- tracked.txt", "git checkout -- <paths>"),
    ("git checkout .", "git checkout ."),
    ("git clean -fd", "git clean -f"),
    ("git clean --force", "git clean -f"),
    ("git restore tracked.txt", "git restore"),
    ("git restore --staged --worktree tracked.txt", "git restore"),
    # The bare-path form reads more innocently and discards just as thoroughly.
    ("git checkout tracked.txt", "git checkout <path>"),
    # A compound line with redirection and a fallback, which no
    # prefix-matching deny pattern reaches.
    ("git checkout -- tracked.txt 2>/dev/null || true", "git checkout -- <paths>"),
]


@pytest.mark.parametrize("command,label", DESTRUCTIVE)
def test_destructive_guard_refuses_a_discard_over_uncommitted_work(
    tmp_path, command, label,
):
    repo = _repo(tmp_path / "dirty")
    _dirty(repo)
    reason = _decision("guard-destructive-git.py", command, repo)
    assert reason is not None, f"allowed {command!r} over a dirty tree"
    assert label in reason, f"named the wrong command:\n{reason}"


@pytest.mark.parametrize("command,_label", DESTRUCTIVE)
def test_destructive_guard_allows_the_same_command_on_a_clean_tree(
    tmp_path, command, _label,
):
    """Deliberate: it is the combination with a dirty tree that is dangerous.
    A guard that fires on harmless invocations is one you learn to route
    around."""
    repo = _repo(tmp_path / "clean")
    assert _decision("guard-destructive-git.py", command, repo) is None, command


def test_destructive_guard_names_what_would_be_lost(tmp_path):
    """The refusal names what would be lost. One that does not is a refusal
    Helen cannot act on, and she is the one being asked."""
    repo = _repo(tmp_path / "named")
    _dirty(repo)
    (repo / "untracked.md").write_text("new and unsaved\n", encoding="utf-8")

    reason = _decision("guard-destructive-git.py", "git reset --hard", repo)
    assert reason is not None
    assert "tracked.txt" in reason, f"the modified file is not named:\n{reason}"
    assert "untracked.md" in reason, f"the untracked file is not named:\n{reason}"
    assert "2 uncommitted change" in reason, reason
    assert "git stash -u" in reason, "the reversible alternative is not offered"


@pytest.mark.parametrize("command", [
    # `--staged` without `--worktree` only unstages: the working tree is
    # untouched, so there is nothing to lose.
    "git restore --staged tracked.txt",
    "git restore -S tracked.txt",
    # The reversible answer the refusal itself recommends.
    "git stash -u",
    "git stash push -u -m probe",
    # Applies and then drops, so content lands in the tree rather than
    # vanishing, and git keeps the stash on a conflict.
    "git stash pop",
    # Reading is always fine, dirty or not.
    "git status",
    "git diff",
    "git add -- tracked.txt",
    "git checkout -b chore/1198-guard-tests",
    # Writing about the commands: a commit message or a grep that names one
    # must not be refused.
    "git commit -F tmp/msg-about-git-reset-hard.txt",
    "git log --grep 'git reset --hard'",
    'grep -rn "git clean -fd" model_instructions/',
])
def test_destructive_guard_leaves_the_safe_and_the_merely_mentioned_alone(
    tmp_path, command,
):
    repo = _repo(tmp_path / "safe")
    _dirty(repo)
    assert _decision("guard-destructive-git.py", command, repo) is None, command


def test_destructive_guard_asks_the_nested_repo_not_the_outer_one(tmp_path):
    """Outer clean, nested dirty: `git -C <nested> reset --hard` is judged by
    the nested tree.

    The flag pattern must allow a flag with a value. One that matches `-C `
    and not `_food_drafts` never recognises the command as a reset at all, so
    it is not judged and allowed but never looked at.
    """
    outer = _repo(tmp_path / "outer")
    nested = _repo(outer / "_food_drafts")
    _dirty(nested)

    reason = _decision("guard-destructive-git.py",
                       "git -C _food_drafts reset --hard", outer)
    assert reason is not None, (
        "a reset aimed at a dirty nested repo was allowed because the outer "
        "tree is clean -- the 2026-09-10 hole, reopened"
    )
    assert "_food_drafts" in reason, reason
    assert "tracked.txt" in reason, f"the nested loss is not named:\n{reason}"


def test_destructive_guard_stops_a_stash_drop_whatever_the_tree_looks_like(tmp_path):
    """A second kind of loss, with its own gate. `git stash drop` destroys the
    stash list, which is as gone on a clean tree as on a dirty one, so the
    clean-tree check that allows everything else must not allow it.

    A throwaway repo, so this is our stash and not the shared stack.
    """
    repo = _repo(tmp_path / "stash")
    _dirty(repo)
    stashed = _git(repo, *IDENTITY, "stash", "push", "-u", "-m", "probe-stash")
    if stashed.returncode != 0:
        pytest.skip(f"could not stash in a probe repo: {stashed.stderr.strip()}")

    entries = _git(repo, "stash", "list").stdout.strip()
    assert "probe-stash" in entries, entries
    # The tree is now clean: the condition under which every other command
    # here is allowed.
    assert not _git(repo, "status", "--porcelain").stdout.strip()

    for command in ("git stash drop", "git stash clear", "git stash drop 'stash@{0}'"):
        reason = _decision("guard-destructive-git.py", command, repo)
        assert reason is not None, f"allowed {command!r} with a stash to lose"
        assert "probe-stash" in reason, (
            f"the refusal does not name the stash it would destroy:\n{reason}"
        )


def test_destructive_guard_allows_a_stash_drop_when_nothing_is_stashed(tmp_path):
    """Nothing to lose, so nothing to stop."""
    repo = _repo(tmp_path / "no-stash")
    for command in ("git stash drop", "git stash clear"):
        assert _decision("guard-destructive-git.py", command, repo) is None, command


def test_destructive_guard_says_nothing_when_there_is_no_repository(tmp_path):
    nowhere = tmp_path / "not-a-repo"
    nowhere.mkdir()
    assert _decision("guard-destructive-git.py", "git reset --hard", nowhere) is None


# ---- Wiring ----
# A hook that exists but is not wired guards nothing, and the suite would not
# notice: every test above runs the file directly.

def _pre_tool_use_hooks() -> list[dict]:
    settings = json.loads((HOOKS.parent / "settings.json").read_text(encoding="utf-8"))
    return [
        hook
        for entry in settings["hooks"]["PreToolUse"]
        if entry.get("matcher") == "Bash"
        for hook in entry["hooks"]
    ]


@pytest.mark.parametrize("name", [
    "guard-main-branch.py",
    "guard-destructive-git.py",
])
def test_both_git_guards_are_wired_as_bash_pretooluse_hooks(name):
    wired = [
        hook for hook in _pre_tool_use_hooks()
        if hook["command"].endswith(f'/.claude/hooks/{name}"')
    ]
    assert wired, f"{name} exists but no PreToolUse hook runs it"
    assert len(wired) == 1, f"{name} is wired {len(wired)} times"
    assert wired[0]["if"] == "Bash(git *)", (
        f"{name} is gated on {wired[0].get('if')!r}. Both git guards are "
        "deliberately gated to git commands; changing that changes which "
        "shapes they can see, and "
        "test_a_leading_cd_into_a_nested_repo_is_refused_by_the_other_guard "
        "records what the gate lets past."
    )
