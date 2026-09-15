#!/usr/bin/env python3
"""Refuse any Bash command that runs `awk` (or gawk, mawk, nawk), anywhere in it.

WHY THIS EXISTS (2026-09-15). Helen, drafting the README's list of guards,
had written "Never `awk` (same)" beside "Never `sed`" and found no hook behind
it: "Should I have a guard against awk? I feel like I should."

The case is stronger than sed's. awk is not a stream filter with one dangerous
flag; it is a whole programming language whose program arrives INLINE, in a
quoted argument the permission checker cannot see into -- the same opacity
guard-inline-script.py refuses for `python -c`, `ruby -e`, `node -e` and
`perl -e`, which never listed awk only because nobody thought of it as an
interpreter. Inside that quoted program:
  * `print > "path"` and `printf ... >> "path"` write any file,
  * `system("...")` and `"cmd" | getline` run any command,
  * `gawk -i inplace` edits files in place, sed -i's exact failure mode.
None of that is visible to the checker, which sees `awk` and a string.

Python covers everything awk does, more readably, in a file the checker can
name (CLAUDE.md: every program goes in a file, however short).

A pipe into awk (`grep ... | awk '{print $2}'`) is ALREADY refused, by
guard-unanalyzable-bash.py, for being a pipe. What got through before this
hook was awk standing alone: `awk -F, '{...}' some.csv`, one command, no pipe,
no substitution -- analysable in shape, opaque in content.

DELIBERATELY NOT CLEVER, for guard-sed.py's reason: telling a harmless
`awk '{print $1}'` from one that writes or runs something means parsing awk,
and detection logic is exactly what grows the next gap. No awk, full stop.

WHAT IT DELIBERATELY ALLOWS: the word inside a quoted string or a heredoc body,
so a commit message or grep pattern can discuss it; and tokens that merely
contain it (`guard-awk.py`, `hawkish.txt`), because it matches whole command
words, not substrings. `sh -c 'awk ...'` hides it in quotes and passes this
hook -- as it passes guard-sed.py -- but `sh -c` with a program is itself the
unanalysable shape, and a script FILE containing awk still asks Helen, as every
tmp/ script does.

Invoked as `python3 .claude/hooks/guard-awk.py`, so it needs no execute bit.
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
