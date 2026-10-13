#!/usr/bin/env python3
"""Refuse any Bash command that runs `awk` (or gawk, mawk, nawk), anywhere in it.

awk is a programming language whose program arrives inline, in a quoted
argument the permission checker cannot see into: `print > "path"` writes any
file, `system("...")` and `"cmd" | getline` run any command, and
`gawk -i inplace` edits in place. Python covers it, in a file the checker can
name. DECISIONS §11.

It does not tell a harmless awk from one that writes or runs something: that
means parsing awk, and detection logic is where the next gap grows.

Allowed on purpose: the word inside a quoted string or a heredoc body, and
tokens that merely contain it (`guard-awk.py`, `hawkish.txt`), because it
matches whole command words. `sh -c 'awk ...'` therefore passes this hook, as
it passes guard-sed.py. Tested in `tests/test_text_tool_guards.py`.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import re
import sys

AWKS = {"awk", "gawk", "mawk", "nawk"}

# Whole shell words, split on whitespace and the operators that start a new
# command -- the same tokenising as guard-sed.py, for the same reason.
TOKEN_SPLIT = re.compile(r"[\s|;&()]+")
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)


def _strip(command: str) -> str:
    return QUOTED.sub(" ", HEREDOC.sub(" ", command))


def _mentions_awk(command: str) -> bool:
    for token in TOKEN_SPLIT.split(command):
        # A bare name, or a path ending in one (/usr/bin/awk, `env awk`,
        # `busybox awk` -- the last is two tokens and the second matches).
        if token and token.rsplit("/", 1)[-1] in AWKS:
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not _mentions_awk(_strip(command)):
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "BLOCKED: this command runs `awk`.\n\n"
                "Helen's rule, 2026-09-15: no awk, in any form. awk is a "
                "programming language whose program arrives inline, where the "
                "permission checker cannot see it write a file (`print > "
                "\"path\"`) or run a command (`system()`). See this file's "
                "docstring.\n\n"
                "WHAT TO DO INSTEAD: write it in Python, in a file under tmp/, "
                "and run the file (`python3 tmp/thing.py`). For a column or a "
                "count, a committed allow-listed wrapper or a plain `grep` may "
                "already answer it.\n\n"
                "If you believe this case genuinely needs awk, say so and let "
                "Helen decide -- this hook is not the thing to route around."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
