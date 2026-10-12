#!/usr/bin/env python3
"""Refuse any Bash command that mentions `sed`, anywhere in it, full stop.

Helen's rule covers the whole tool, not only `sed -i`: a subtly wrong regex
corrupts a file silently, with none of the visible diff an Edit call gives
her, and Python covers everything sed does. DECISIONS §11.

A hook rather than a `deny` rule because a permission pattern matches a
command's prefix and cannot express "anywhere in a pipeline". For the same
reason it has no `"if"` filter in its wiring: it runs on every Bash call and
does its own check.

It does not tell a safe sed from an unsafe one; that detection is where the
next gap grows.

Allowed on purpose: the word inside a quoted string or a heredoc body, so a
commit message can discuss it, and tokens that merely contain it
(`guard-sed.py`, `processed.txt`). Tested in `tests/test_text_tool_guards.py`.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import re
import sys

# Split on whitespace and the operators that start a new command. Whole tokens,
# not a word-boundary substring match: that also matches the `sed` in
# `guard-sed.py`, so any command naming this hook would trigger it.
TOKEN_SPLIT = re.compile(r"[\s|;&()]+")

# Same stripping as the other guards, and for the same reason: a guard that
# fires on WRITING ABOUT a command rather than running one is a guard people
# learn to route around.
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)


def _strip(command: str) -> str:
    return QUOTED.sub(" ", HEREDOC.sub(" ", command))


def _mentions_sed(command: str) -> bool:
    for token in TOKEN_SPLIT.split(command):
        # A bare "sed", or a path ending in "/sed" (e.g. /usr/bin/sed, or a
        # leading `command sed`/`env sed`) -- but not "guard-sed.py" or
        # "processed.txt", whose last path component isn't exactly "sed".
        if token and token.rsplit("/", 1)[-1] == "sed":
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    stripped = _strip(command)

    if not _mentions_sed(stripped):
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "BLOCKED: this command mentions `sed`.\n\n"
                "Helen's standing rule: no sed, ever, in any form -- not just "
                "`sed -i`. This is unconditional on purpose (see this file's "
                "own docstring for why), so it doesn't matter whether this "
                "particular invocation looks safe.\n\n"
                "WHAT TO DO INSTEAD: write the transformation in Python, in "
                "a tmp/*.py file run as a plain file argument, and run that "
                "instead -- never `python3 -c`, which guard-inline-script.py "
                "refuses however short (CLAUDE.md, 2026-09-10). It covers "
                "everything sed does, more precisely, and is easier to "
                "review.\n\n"
                "If you genuinely believe this specific case needs sed, say "
                "so and let Helen decide -- this hook is not the thing to "
                "route around."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
