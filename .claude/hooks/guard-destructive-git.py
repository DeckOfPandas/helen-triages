#!/usr/bin/env python3
"""Block the destructive git commands, but only when there is something to lose.

Refused while `git status --porcelain` is not empty in the repository the
command is aimed at: `git checkout -- <paths>`, `git checkout .`,
`git checkout <path>` where the argument names something that exists,
`git reset --hard`, `git clean -f`, and `git restore` unless it is `--staged`
without `--worktree`. Refused whenever `git stash list` in that same
repository is not empty, clean tree or not: `git stash drop` and
`git stash clear`. DECISIONS §11.

The repository is found by reading a `cd <path>` and then a `git -C <path>`
out of the command, so a command aimed at a nested drafts repo is judged by
that repo's tree and stash list, not the outer one's.

Allowed on purpose:

  - Any of the first group on a clean tree, where there is nothing to lose. A
    guard that fires on harmless commands gets routed around.
  - `git stash` and `git stash pop`, and `git restore --staged` alone, which
    only unstages.
  - A command named inside a quoted string or a heredoc body, so a commit
    message may discuss them. `bash -c "git reset --hard"` passes for the same
    reason.

A hook rather than a `deny` entry because a deny pattern is a prefix match on
the command string and cannot ask git whether anything would be lost. Tested in
`tests/test_git_guards.py`.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

# Each entry: (compiled pattern, how to name the command in the refusal).
# `[^|;&]*?` keeps a match inside one command of a compound line.
#
# `_GIT` spells out which global flags take a value (`-C <path>`,
# `-c <key=value>`) and which do not. A pattern that allows a flag but not its
# value never matches `git -C _food_drafts reset --hard`; one that lets any
# token follow any flag can swallow the subcommand it is looking for.
_GIT = r"\bgit\s+(?:-[cC]\s+\S+\s+|--\S+\s+|-\S+\s+)*"

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # git checkout -- <paths>   and   git checkout <ref> -- <paths>
    (re.compile(_GIT + r"checkout\b[^|;&]*?\s--\s"), "git checkout -- <paths>"),
    # git checkout .   (same discard, no separator)
    (re.compile(_GIT + r"checkout\s+\.(?:\s|$|[|;&])"), "git checkout ."),
    # git reset --hard
    (re.compile(_GIT + r"reset\b[^|;&]*?\s--hard\b"), "git reset --hard"),
    # git clean -f / -fd / -xfd / --force
    (re.compile(_GIT + r"clean\b[^|;&]*?\s-(?:-force\b|[a-eg-zA-Z]*f)"), "git clean -f"),
]

# git restore is handled separately: `--staged` WITHOUT `--worktree` only
# unstages, which leaves the working tree alone and is recoverable.
RESTORE = re.compile(_GIT + r"restore\b([^|;&]*)")

# `git checkout <path>` with no `--` discards just as thoroughly. A regex cannot
# tell a path from a branch (`tests/foo.py` against `feat/some-branch`), so this
# asks the filesystem: an argument naming something that exists is a path. A
# branch that names a real file is ambiguous to git too, and blocking is right.
CHECKOUT_ARGS = re.compile(_GIT + r"checkout\b([^|;&]*)")


def _checkout_targets_a_real_file(command: str) -> bool:
    match = CHECKOUT_ARGS.search(command)
    if not match:
        return False
    for arg in match.group(1).split():
        if arg.startswith("-"):
            continue                     # a flag, not a path
        if arg in ("--",):
            continue
        try:
            if pathlib.Path(arg.strip("\"'")).exists():
                return True
        except OSError:
            continue
    return False

# Quoted spans are stripped before matching, so a commit message that names
# these commands is not refused. The cost is that `bash -c "git reset --hard"`
# passes; that is deliberate evasion, which no regex fixes.
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")

# Heredoc bodies are stripped too: a body is not quoted, it is data on stdin
# that looks like shell text. Matches `<<EOF`, `<<'EOF'`, `<<"EOF"` and `<<-`,
# up to a line holding only the delimiter.
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)


# Destroying a stash is a second kind of loss with its own gate: what goes is
# the stash list, which is just as gone on a clean tree, so the dirty-tree
# check does not apply. `git stash pop` is not here: it lands the content in
# the working tree, and on a conflict git keeps the stash.
STASH_DESTRUCTIVE = re.compile(_GIT + r"stash\s+(drop|clear)\b")


def _stash_entries(directory: pathlib.Path) -> list[str]:
    """`git stash list` lines in `directory`, or [] if there are none or it is
    not a repo."""
    try:
        result = subprocess.run(
            ["git", "stash", "list"],
            cwd=directory, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _matched_stash(command: str) -> str | None:
    command = HEREDOC.sub(" ", command)
    command = QUOTED.sub(" ", command)
    m = STASH_DESTRUCTIVE.search(command)
    return f"git stash {m.group(1)}" if m else None


def _matched(command: str) -> str | None:
    command = HEREDOC.sub(" ", command)
    command = QUOTED.sub(" ", command)
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
            return None    # unstages only; the working tree is untouched
        return "git restore"
    return None


# Which repository the command is aimed at. Without this a command aimed at a
# nested drafts repo is judged by whether the OUTER worktree is dirty.
# Duplicated from guard-main-branch.py on purpose: each hook is one file with
# no import path of its own. Fix one, fix the other.
CD_TARGET = re.compile(r"\bcd\s+([^\s;&|]+)")
GIT_C_TARGET = re.compile(r"\bgit\s+(?:-\S+\s+\S+\s+)*?-C\s+([^\s;&|]+)")


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

    A `cd` moves the shell; a later `-C` moves git again, RELATIVE TO WHERE THE
    `cd` LEFT IT, so the two compose rather than compete: `cd a && git -C b`
    runs in `a/b`.
    """
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


def _dirty(directory: pathlib.Path) -> list[str]:
    """Lines of `git status --porcelain` in `directory`, or [] if not a repo."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0            # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""

    # The stash family first, because its gate is different: what is at risk is
    # the stash list, not the working tree, so tree cleanliness says nothing.
    stash_label = _matched_stash(command)
    if stash_label:
        entries = _stash_entries(_repo_dir(command))
        if not entries:
            return 0        # nothing stashed, so nothing to lose
        shown = "\n  ".join(entries[:10])
        if len(entries) > 10:
            shown += f"\n  ... and {len(entries) - 10} more"
        return _deny(
            f"BLOCKED: {stash_label} with {len(entries)} stash(es) that would go.\n\n"
            f"  {shown}\n\n"
            "A stash is where work goes to be SAFE -- this hook's own refusal "
            "message recommends `git stash -u` for exactly that -- so destroying "
            "one is the same loss as destroying the tree, and it does not matter "
            "whether the tree is clean.\n\n"
            "A dropped stash is not in `git stash list`, not in the tree, and not "
            "anywhere obvious. It survives briefly as an unreachable commit and "
            "can sometimes be found with `git fsck --unreachable`, which is a "
            "rescue operation rather than a plan.\n\n"
            "BEFORE DROPPING ANYTHING: record the SHAs (`git rev-parse "
            "'stash@{N}'` for each), and check each stash against what is already "
            "committed -- an old stash is usually redundant, and occasionally it "
            "is the only copy of something. On 2026-08-20 nine stashes were "
            "reviewed this way: seven were redundant, and two held work that had "
            "never been applied, including a live config fix.\n\n"
            "Ask Helen, name what would be lost, and wait."
        )

    label = _matched(command)
    if not label:
        return 0

    target = _repo_dir(command)
    dirty = _dirty(target)
    if not dirty:
        return 0            # nothing to lose, so nothing to stop

    shown = "\n  ".join(dirty[:20])
    if len(dirty) > 20:
        shown += f"\n  ... and {len(dirty) - 20} more"

    reason = (
        f"BLOCKED: {label} with {len(dirty)} uncommitted change(s) in "
        f"{target}.\n\n"
        f"  {shown}\n\n"
        "This discards uncommitted work with no undo and no reflog entry to "
        "recover it from, and it does not distinguish your edits from Helen's -- "
        "she edits this tree while you work. CLAUDE.md: ask first, every single "
        "time, and name what would be lost.\n\n"
        "If you are undoing an edit YOU just made, re-edit the file instead; "
        "reaching for git to revert your own change is what caused this rule to "
        "be written. If something genuinely has to be put aside, `git stash -u` "
        "does it reversibly. If it genuinely has to be destroyed, ask Helen and "
        "let her run it.\n\n"
        "(This hook allows the same command on a clean tree -- it is the "
        "combination that is dangerous, not the command.)"
    )

    return _deny(reason)


def _deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
