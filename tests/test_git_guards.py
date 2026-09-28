"""guard-main-branch.py and guard-destructive-git.py, broken on purpose.

WHY THIS FILE EXISTS. Eight hooks live in `.claude/hooks/`. Until now five had
tests -- `guard-sed.py` and `guard-awk.py` in `test_text_tool_guards.py`,
`guard-unanalyzable-bash.py`, `guard-token-expansion.py` and
`session-ground-truth.py` in `test_agent_wrappers.py` -- and the two that guard
the repository's two stated disasters had none between them. The sed and awk
guards had six tests; the hook that stops a commit landing on `main` and the
hook that stops uncommitted work being discarded had zero. #1198.

DECISIONS §11 (2026-09-09, 2026-09-10) records the rule these tests apply: a
guard is proved by breaking the thing on purpose. Both of these hooks have
history that makes the point -- each shipped with a hole that was found only by
aiming a real command at a real repository, and both holes were in the
nested-repository case:

  * guard-main-branch.py matched `git -C _food_drafts commit` as a commit and
    then asked the WRONG repository which branch it was on.
  * guard-destructive-git.py's flag pattern did not allow for a flag with a
    value, so `git -C _food_drafts reset --hard` was never recognised at all.

So the nested case is not an edge here, it is the case with form, and it is
tested for both hooks below.

HOW THESE TESTS WORK. Each hook is fed the same JSON the harness feeds it, on
stdin, with the subprocess's `cwd` set to a throwaway `git init` repository --
because both hooks ask git about a directory, and `guard-main-branch.py` reads
`Path.cwd()` to find it. A real repository rather than a mock: the thing being
proved is that the hook agrees with git, and a mock would only prove it agrees
with the mock.

`cwd` IS ALWAYS A THROWAWAY REPO, NEVER THIS WORKTREE, AND THAT IS LOAD-BEARING
FOR THE STASH TESTS. `guard-destructive-git.py` reads `git stash list` in the
process's own directory, and the stash stack is shared between this repo's
primary checkout and every worktree -- another session may push or pop it while
this suite runs. A stash test run in this worktree would therefore pass or fail
on someone else's work. In a throwaway repo the stash list is ours alone.

Deliberately NOT `git worktree add`: that would mutate this repo's worktree
list, and an interrupted test would leave an entry only `git worktree prune`
clears -- which is Helen's, not a test's (CLAUDE.md, normal workflow). Same
reasoning as `test_agent_wrappers.py`'s probe repo.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

pytestmark = pytest.mark.shared

HOOKS = pathlib.Path(__file__).resolve().parents[1] / ".claude" / "hooks"

# A committer for the throwaway repos. Passed per-invocation with `git -c`, so
# nothing is written to a config file anywhere -- CLAUDE.md forbids touching
# global git config, and a test that needed it would be the wrong test.
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


# =============================================================================
# guard-main-branch.py -- the hook that protects `main`
# =============================================================================

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
    # Everything else on `main` is untouched, and CLAUDE.md says so in as many
    # words: "reading, fetching, branching, checking out, pushing an existing
    # commit".
    "git status",
    "git log --oneline -5",
    "git diff",
    "git show HEAD",
    "git fetch origin",
    "git branch --show-current",
    "git checkout -b chore/1198-guard-tests",
    "sh scripts/git-push-agent.sh branch:branch",
    "sh scripts/git-fetch-main.sh",
    # Writing ABOUT the verbs. Commit messages in this repository discuss them
    # constantly -- this file's own introducing commit does.
    "git log --grep 'git commit on main'",
    'git add -- tmp/notes-about-git-merge.txt',
])
def test_main_branch_guard_leaves_everything_else_on_main_alone(tmp_path, command):
    repo = _repo(tmp_path / "main-other", branch="main")
    assert _decision("guard-main-branch.py", command, repo) is None, command


def test_main_branch_guard_asks_the_nested_repo_not_the_outer_one(tmp_path):
    """THE CASE WITH FORM. Four commits went onto `_cocktail_drafts`' own `main`
    on 2026-08-17, and in 2026-09-10 the hook recognised `git -C <nested>
    commit` as a commit and then checked the OUTER repository's branch.

    Outer on a working branch, nested on `main`: the answer must come from the
    nested one. `git -C` is the only remaining way to reach a nested repo, since
    guard-unanalyzable-bash.py refuses a leading `cd` (proved below).
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

    The hook's docstring says the two compose, and its own first fix for the
    `-C` hole did not -- it resolved the `-C` path against the worktree root, so
    this exact shape resolved to a directory that does not exist, fell back to
    cwd, and allowed the commit. Tested at the hook even though
    guard-unanalyzable-bash.py refuses a leading `cd` today: the two hooks are
    independent, and this one should not depend on the other for correctness.
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
    """The `if` gate is not a hole, and this is why it needs saying.

    Both git guards are wired with `"if": "Bash(git *)"`, which is a PREFIX
    match -- so neither of them ever sees `cd _food_drafts && git commit`. That
    would be a hole if nothing else caught it. guard-unanalyzable-bash.py has no
    `if`, runs on every Bash call, and refuses a leading `cd` and `&&` chaining
    both. So the composition is closed even though neither hook closes it alone,
    and that is worth a test rather than a comment: if the `if` gate or the
    unanalyzable guard changes, exactly one of these two tests should go red.
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


# =============================================================================
# guard-destructive-git.py -- the hook that protects uncommitted work
# =============================================================================

DESTRUCTIVE = [
    ("git reset --hard", "git reset --hard"),
    ("git reset --hard HEAD~1", "git reset --hard"),
    ("git checkout -- tracked.txt", "git checkout -- <paths>"),
    ("git checkout .", "git checkout ."),
    ("git clean -fd", "git clean -f"),
    ("git clean --force", "git clean -f"),
    ("git restore tracked.txt", "git restore"),
    ("git restore --staged --worktree tracked.txt", "git restore"),
    # The bare-path form, which reads far more innocently and discards just as
    # thoroughly. It got past the hook's first version and took a file's
    # uncommitted work with it on 2026-08-19.
    ("git checkout tracked.txt", "git checkout <path>"),
    # The shape that got past the WRITTEN rule on 2026-08-19: a compound line
    # with redirection and a fallback, which no prefix-matching deny pattern
    # reaches.
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
    """Documented, deliberate, and the reason the hook is trusted: it is the
    COMBINATION that is dangerous. A guard that fired on harmless invocations
    is one you learn to route around."""
    repo = _repo(tmp_path / "clean")
    assert _decision("guard-destructive-git.py", command, repo) is None, command


def test_destructive_guard_names_what_would_be_lost(tmp_path):
    """CLAUDE.md: "names what would be lost". A refusal that does not is a
    refusal Helen cannot act on, and she is the one being asked."""
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
    # `--staged` WITHOUT `--worktree` only unstages. The working tree is
    # untouched, so there is nothing to lose and nothing to block.
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
    # Writing ABOUT the commands. The CLAUDE.md entry this hook enforces names
    # three of them, so a commit message discussing it must not be refused.
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
    """The 2026-09-10 hole, from the other side: `git -C <nested> reset --hard`
    was judged by whether the OUTER tree was dirty. Outer clean, so allowed, and
    uncommitted work in the drafts repo destroyed.

    The flag pattern is the part that was wrong -- it allowed a flag but not the
    VALUE after it, so `-C ` matched and `_food_drafts` did not, and the command
    was never recognised as a reset at all. Not judged and allowed: never looked
    at.
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
    """A SECOND KIND OF LOSS, and it needs its own gate. Everything else here is
    about the working tree, so it is correctly allowed when the tree is clean.
    `git stash drop` destroys the stash LIST, which is just as gone either way --
    running the clean-tree check against it would have waved it through, and
    until 2026-08-20 it did, in a hook whose own refusal message recommends
    `git stash -u`.

    A throwaway repo, so this is our stash and not the shared stack.
    """
    repo = _repo(tmp_path / "stash")
    _dirty(repo)
    stashed = _git(repo, *IDENTITY, "stash", "push", "-u", "-m", "probe-stash")
    if stashed.returncode != 0:
        pytest.skip(f"could not stash in a probe repo: {stashed.stderr.strip()}")

    entries = _git(repo, "stash", "list").stdout.strip()
    assert "probe-stash" in entries, entries
    # The tree is now CLEAN, which is exactly the condition that used to let
    # these through.
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


# =============================================================================
# Wiring. A hook that exists but is not wired guards nothing, and the suite
# would not notice -- every test above runs the file directly.
# =============================================================================

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
