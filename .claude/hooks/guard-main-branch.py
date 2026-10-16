#!/usr/bin/env python3
"""Refuse `git commit` and `git merge` while the current branch is `main`.

A branch check run in the same shell command as the commit prints after the
commit has happened; this is the check that can stop the call. DECISIONS §11.

It asks the repository the command is aimed at, not the hook's own directory:
it reads a `cd <path>` and then a `git -C <path>` out of the command, because
the nested private drafts repos have their own `main` and the same rule.
`master` is protected too.

Allowed on purpose:

  - Every other git command on `main`: reading, fetching, branching, checking
    out, pushing an existing commit. Only the two verbs that write history to
    the branch are refused.
  - `git commit` and `git merge` on any other branch, on a detached HEAD, or
    outside a repository.
  - These commands named inside a quoted string or a heredoc body, so a commit
    message may discuss them.

Tested in `tests/test_git_guards.py`.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

# `git commit` and `git merge`, allowing for global flags like `git -C x commit`.
_GIT = r"\bgit\s+(?:-\S+\s+\S*\s*)*"
WRITES_HISTORY = re.compile(_GIT + r"(commit|merge)\b")

# Same stripping as guard-destructive-git.py, and for the same reason: a guard
# that fires on WRITING ABOUT a command rather than running one is a guard
# people learn to route around.
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)

# A leading `cd <path>` -- the command may be operating on a nested repo.
CD = re.compile(r"\bcd\s+([^\s;&|]+)")

# `git -C <path>`, the other way to aim at a nested repo. Read as well as `cd`,
# or a commit there is checked against the outer worktree's branch.
GIT_C = re.compile(r"\bgit\s+(?:-\S+\s+\S+\s+)*?-C\s+([^\s;&|]+)")

PROTECTED = {"main", "master"}


def _strip(command: str) -> str:
    return QUOTED.sub(" ", HEREDOC.sub(" ", command))


def _resolve(raw: str, base: pathlib.Path) -> pathlib.Path | None:
    """A path argument as a real directory, resolved against `base`, or None."""
    try:
        target = pathlib.Path(raw.strip("\"'")).expanduser()
        if not target.is_absolute():
            target = base / target
        target = target.resolve()
        return target if target.is_dir() else None
    except (OSError, ValueError):
        return None


def _repo_dir(command: str) -> pathlib.Path:
    """The directory git will actually run in, modelling the shell in order.

    A `cd` moves the shell; a later `-C` moves git again, relative to where the
    `cd` left it. `cd a && git -C b commit` runs in `a/b`, not `a` and not `b`.
    """
    base = pathlib.Path.cwd()

    cd_match = CD.search(command)
    if cd_match:
        moved = _resolve(cd_match.group(1), base)
        if moved is not None:
            base = moved

    c_match = GIT_C.search(command)
    if c_match:
        moved = _resolve(c_match.group(1), base)
        if moved is not None:
            return moved

    return base


def _current_branch(directory: pathlib.Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=directory, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    stripped = _strip(command)

    match = WRITES_HISTORY.search(stripped)
    if not match:
        return 0

    directory = _repo_dir(stripped)
    branch = _current_branch(directory)
    if branch is None or branch not in PROTECTED:
        return 0                    # not a repo, detached, or a working branch

    verb = match.group(1)
    where = directory

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED: `git {verb}` while on `{branch}` in {where}.\n\n"
                "CLAUDE.md: never commit or merge directly onto main, in ANY "
                "repo in this tree -- including the nested private drafts "
                "repos, which have their own main and the same rule.\n\n"
                "The workflow: work happens on a branch, Claude pushes it and "
                "opens the PR, Helen reviews and merges it. `main` only ever "
                "moves via a PR she merges.\n\n"
                "WHAT TO DO NOW:\n"
                f"  git checkout -b <branch>     # in {where}\n"
                "then re-run the commit. Nothing is staged or lost -- this "
                "refused the call before it ran, so your index is exactly as "
                "you left it.\n\n"
                "If you have ALREADY committed to main in an earlier call, do "
                "not try to fix it by force-pushing a shared branch. Say so and "
                "let Helen choose.\n\n"
                "(This exists because the written rule was read and broken on "
                "2026-08-20 by an agent that ran `git branch --show-current` in "
                "the same shell command as the commit -- so the check printed "
                "'main' in the output of the call that had already committed. A "
                "check that cannot gate is a narration.)"
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
