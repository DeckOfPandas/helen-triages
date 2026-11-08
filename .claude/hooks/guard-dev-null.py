#!/usr/bin/env python3
"""Refuse `/dev/null` as a command argument; leave it alone as a redirection.

With `blockReadsOutsideWorkingDirectories` on, the permission checker reads
`/dev/null` as an argument (`ls /dev/null`, `curl -o /dev/null`,
`diff a /dev/null`) as a read outside the working directories and stops to
ask the human. No allow rule lifts that block, `Read(//dev/null)` included.
A redirection target (`> /dev/null`, `2>/dev/null`, `< /dev/null`) is never
checked. So a refusal here lands on the session, which can rewrite the
command, instead of a prompt landing on the human.

Refused: the token `/dev/null` anywhere but straight after a redirection
operator, and an option that carries it (`-o/dev/null`, `--output=/dev/null`).
Allowed: redirections, and `/dev/null` inside a longer quoted string such as
a commit message. A command shlex cannot split is allowed: another guard or
the checker has it. Tested in `tests/kit/test_text_tool_guards.py`.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

DEV_NULL = "/dev/null"
# shlex with punctuation_chars returns each run of these as one token, so
# `2>/dev/null` comes out as `2`, `>`, `/dev/null`.
REDIRECT = re.compile(r"^(?:&?>>?\|?|<|<>|>&|&>>?)$")
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)


def _argument_uses(command: str) -> list[str]:
    lexer = shlex.shlex(HEREDOC.sub(" ", command), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    found = []
    for i, token in enumerate(tokens):
        after_redirect = i > 0 and REDIRECT.match(tokens[i - 1]) is not None
        if token == DEV_NULL and not after_redirect:
            found.append(token)
        elif token.startswith("-") and token.endswith(DEV_NULL):
            found.append(token)
    return found


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    uses = _argument_uses(command)
    if not uses:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED: `{uses[0]}` uses /dev/null as a command argument.\n\n"
                "WHY: with blockReadsOutsideWorkingDirectories on, the "
                "permission checker treats /dev/null as an argument as a read "
                "outside the working directories and stops to ask the human. "
                "No allow rule lifts that. As a redirection target it is never "
                "checked.\n\n"
                "WHAT TO DO INSTEAD:\n"
                "- Discard output with `> /dev/null` or `2>/dev/null`, and "
                "feed nothing with `< /dev/null`.\n"
                "- Where a command wants an output file, name one under tmp/ "
                "(`curl -o tmp/body.html`). To check a link, "
                "`sh scripts/check-link.sh <https-url>`.\n"
                "- Where a command needs an empty file, write one in tmp/ with "
                "the Write tool and name that instead.\n"
                "- Inside a committed script in scripts/, /dev/null as an "
                "argument is fine: the checker sees only `sh scripts/<name>.sh`."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
