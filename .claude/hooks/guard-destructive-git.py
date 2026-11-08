#!/usr/bin/env python3
"""Block the destructive git commands, but only when there is something to lose.

Refused while `git status --porcelain` is not empty in the repository the
command is aimed at: `git checkout -- <paths>`, `git checkout .`,
`git checkout <path>` where the argument names something that exists,
`git reset --hard`, `git clean -f`, and `git restore` unless it is `--staged`
without `--worktree`. Refused whenever the stash list of that same repository
is not empty, clean tree or not: `git stash drop` and `git stash clear`.

Allowed on purpose: the first group on a clean tree, where nothing can be lost;
`git stash`, `git stash pop` and `git restore --staged`; and any of these
inside a quoted string or heredoc, so a commit message may discuss them.

A hook rather than a `deny` rule because a deny pattern is a prefix match and
cannot ask git whether anything would be lost.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

# Global flags that take a value (`-C <path>`, `-c <key=value>`) are spelled
# out: a pattern letting any token follow any flag can swallow the subcommand.
_GIT = r"\bgit\s+(?:-[cC]\s+\S+\s+|--\S+\s+|-\S+\s+)*"

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(_GIT + r"checkout\b[^|;&]*?\s--\s"), "git checkout -- <paths>"),
    (re.compile(_GIT + r"checkout\s+\.(?:\s|$|[|;&])"), "git checkout ."),
    (re.compile(_GIT + r"reset\b[^|;&]*?\s--hard\b"), "git reset --hard"),
    (re.compile(_GIT + r"clean\b[^|;&]*?\s-(?:-force\b|[a-eg-zA-Z]*f)"), "git clean -f"),
]
RESTORE = re.compile(_GIT + r"restore\b([^|;&]*)")
CHECKOUT_ARGS = re.compile(_GIT + r"checkout\b([^|;&]*)")
STASH_DESTRUCTIVE = re.compile(_GIT + r"stash\s+(drop|clear)\b")

QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)
CD_TARGET = re.compile(r"\bcd\s+([^\s;&|]+)")
GIT_C_TARGET = re.compile(r"\bgit\s+(?:-\S+\s+\S+\s+)*?-C\s+([^\s;&|]+)")


def _strip(command: str) -> str:
    return QUOTED.sub(" ", HEREDOC.sub(" ", command))


def _checkout_targets_a_real_file(command: str) -> bool:
    """A regex cannot tell a path from a branch, so ask the filesystem: an
    argument naming something that exists is a path."""
    match = CHECKOUT_ARGS.search(command)
    if not match:
        return False
    for arg in match.group(1).split():
        if arg.startswith("-"):
            continue
        try:
            if pathlib.Path(arg.strip("\"'")).exists():
                return True
        except OSError:
            continue
    return False


def _matched(command: str) -> str | None:
    command = _strip(command)
    for pattern, label in PATTERNS:
        if pattern.search(command):
            return label
    if _checkout_targets_a_real_file(command):
        return "git checkout <path>"
    m = RESTORE.search(command)
    if m:
        args = m.group(1)
        staged = "--staged" in args or re.search(r"\s-S\b", args)
        worktree = "--worktree" in args or re.search(r"\s-W\b", args)
        if staged and not worktree:
            return None             # unstages only; the working tree is untouched
        return "git restore"
    return None


def _git_lines(directory: pathlib.Path, *args: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args], cwd=directory, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _resolve(raw: str, base: pathlib.Path) -> pathlib.Path | None:
    try:
        target = pathlib.Path(raw.strip("\"'")).expanduser()
        if not target.is_absolute():
            target = base / target
        target = target.resolve()
        return target if target.is_dir() else None
    except (OSError, ValueError):
        return None


def _repo_dir(command: str) -> pathlib.Path:
    """Where git will run; same model as guard-main-branch.py. Fix one, fix both."""
    base = pathlib.Path.cwd()
    cd_match = CD_TARGET.search(command)
    if cd_match:
        moved = _resolve(cd_match.group(1), base)
        if moved is not None:
            base = moved
    c_match = GIT_C_TARGET.search(command)
    if c_match:
        moved = _resolve(c_match.group(1), base)
        if moved is not None:
            return moved
    return base


def _shown(lines: list[str], limit: int) -> str:
    shown = "\n  ".join(lines[:limit])
    if len(lines) > limit:
        shown += f"\n  ... and {len(lines) - limit} more"
    return shown


def _deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""

    stash = STASH_DESTRUCTIVE.search(_strip(command))
    if stash:
        entries = _git_lines(_repo_dir(_strip(command)), "stash", "list")
        if not entries:
            return 0
        return _deny(
            f"BLOCKED: git stash {stash.group(1)} with {len(entries)} stash(es) "
            f"that would go.\n\n  {_shown(entries, 10)}\n\n"
            "A stash is where work goes to be safe, so destroying one is the "
            "same loss as destroying the tree, clean tree or not. Record each "
            "SHA (`git rev-parse 'stash@{N}'`), check it against what is "
            "already committed, then ask the human, naming what would be lost."
        )

    label = _matched(command)
    if not label:
        return 0
    target = _repo_dir(_strip(command))
    dirty = _git_lines(target, "status", "--porcelain")
    if not dirty:
        return 0

    return _deny(
        f"BLOCKED: {label} with {len(dirty)} uncommitted change(s) in "
        f"{target}.\n\n  {_shown(dirty, 20)}\n\n"
        "This discards uncommitted work with no undo, and cannot tell your "
        "edits from the human's. CLAUDE.md: ask first, every time, and name "
        "what would be lost.\n\n"
        "Undoing an edit you just made? Re-edit the file instead. Something "
        "has to be put aside? `git stash push -u -m <tag>` does it reversibly.\n\n"
        "(The same command on a clean tree is allowed: it is the combination "
        "that is dangerous.)"
    )


if __name__ == "__main__":
    sys.exit(main())
