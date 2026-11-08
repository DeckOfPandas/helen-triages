#!/usr/bin/env python3
"""Refuse the git diff options that write a file, read outside, or run a program.

`Bash(git diff *)`, `git log *` and `git show *` are allowed unasked because
they only read the repository, but they all take diff options, and four of
those break that:

  --output=<file>, --output <file>   writes the diff to any path, overwriting it
  --no-index                         diffs two paths, inside the repo or not
  --ext-diff                         runs the diff.external program
  --textconv                         runs the textconv filters

A permission rule matches a command's prefix, so `git diff HEAD --output=x`
cannot be denied by one; this hook reads every word after the subcommand. Git
2.39 rejects abbreviations of these, but a later git may accept them, so any
prefix that could only mean one of them is refused too (`--outp=`, `--no-ind`,
`--ext-`, `--textc`). `--text` and `--output-indicator-*` are other options
and pass.

Refuses only after `git` and one of DIFF_COMMANDS, global options skipped.
Unbalanced quotes fall back to splitting on whitespace rather than passing,
since this guards a write. Tested in `tests/kit/test_git_output_guard.py`.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import shlex
import sys

DIFF_COMMANDS = {"diff", "log", "show", "whatchanged", "diff-tree", "diff-index", "diff-files"}

# Option, and the shortest prefix of it that is refused.
REFUSED = {
    "--output": "--ou",
    "--no-index": "--no-ind",
    "--ext-diff": "--ext",
    "--textconv": "--textc",
}

# Global options that take the next word as their value: `git -c k=v diff`.
GLOBAL_WITH_VALUE = {"-c", "-C", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


def _refused_option(word: str) -> str | None:
    name = word.split("=", 1)[0]
    for option, shortest in REFUSED.items():
        if name.startswith(shortest) and option.startswith(name):
            return option
    return None


def _offence(command: str) -> str | None:
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    i = 0
    while i < len(words):
        if words[i].rsplit("/", 1)[-1] != "git":
            i += 1
            continue
        # Skip global options to reach the subcommand.
        j = i + 1
        while j < len(words) and words[j].startswith("-"):
            j += 2 if words[j] in GLOBAL_WITH_VALUE else 1
        if j < len(words) and words[j] in DIFF_COMMANDS:
            for word in words[j + 1:]:
                if word.rsplit("/", 1)[-1] == "git":
                    break
                found = _refused_option(word)
                if found:
                    return f"`git {words[j]} {word}`, which is {found}"
        i = j + 1
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    found = _offence(command)
    if not found:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED: {found}.\n\n"
                "`git diff`, `git log` and `git show` are allowed unasked "
                "because they only read the repository. --output writes a "
                "file anywhere, overwriting it; --no-index reads paths outside "
                "the repository; --ext-diff and --textconv run programs from "
                "git config. None of that is a read, and an allow rule cannot "
                "exclude an option that comes later in the command.\n\n"
                "WHAT TO DO INSTEAD: to save a diff, redirect it to a named "
                "file under tmp/ -- `git diff main > tmp/changes.patch` -- "
                "which the permission checker can see. To compare two files, "
                "commit or stage them and diff the revisions, or use the "
                "Read tool on each. If you genuinely need one of these "
                "options, say so and let the human decide."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
