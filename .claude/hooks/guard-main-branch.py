#!/usr/bin/env python3
"""Refuse `git commit` and `git merge` while the current branch is `main` or `master`.

A branch check in the same shell command as a commit prints after the commit
has happened; this is the check that can stop the call.

It asks the repository the command is aimed at, reading a `cd <path>` and then
a `git -C <path>` out of the command, so a nested clone with its own `main` is
judged by its own branch.

Allowed on purpose: every other git command on `main` (reading, fetching,
branching, checking out, pushing an existing commit); commit and merge on any
other branch, on a detached HEAD or outside a repo; and these words inside a
quoted string or heredoc, so a commit message may discuss them.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

_GIT = r"\bgit\s+(?:-\S+\s+\S*\s*)*"
WRITES_HISTORY = re.compile(_GIT + r"(commit|merge)\b")

# A guard that fires on WRITING ABOUT a command gets routed around, so quoted
# spans and heredoc bodies are blanked before matching.
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)
CD = re.compile(r"\bcd\s+([^\s;&|]+)")
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
    """Where git will run: a `cd` moves the shell, a later `-C` moves git
    again relative to it, so `cd a && git -C b commit` runs in `a/b`."""
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
        return 0

    verb = match.group(1)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED: `git {verb}` while on `{branch}` in {directory}.\n\n"
                "CLAUDE.md: never commit or merge directly onto main, in any "
                "repo in this tree. Work happens on a branch, Claude pushes it "
                "and opens a PR, and a human merges it.\n\n"
                "WHAT TO DO NOW:\n"
                f"  git checkout -b <branch>     # in {directory}\n"
                "then re-run the command. Nothing is staged or lost: this was "
                "refused before it ran.\n\n"
                "If you ALREADY committed to main in an earlier call, do not "
                "force-push anything to fix it. Say so and let the human choose."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
