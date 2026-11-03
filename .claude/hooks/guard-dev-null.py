#!/usr/bin/env python3
"""Refuse `/dev/null` given to a command as an argument rather than a redirection.

With `blockReadsOutsideWorkingDirectories` on, the permission checker reads an
argument of `/dev/null` as a path outside the working directories and asks
Helen, and no allow rule lets it through: `Read(//dev/null)` covers the Read
tool, not `curl -o /dev/null` or `diff a /dev/null`. A redirection is not
checked, so `> /dev/null` and `2>/dev/null` pass. A denial lands on the
session, which can rewrite the command; a prompt lands on Helen. DECISIONS §11.

Refused: a word that is `/dev/null` unless the word before it is a redirection
operator, and an option glued to it (`-o/dev/null`, `--output=/dev/null`).
Commands `shlex` cannot split are allowed; `guard-unanalyzable-bash.py` judges
those. Tested in `tests/test_git_guards.py`.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import shlex
import sys

NULL = "/dev/null"


def _words(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def _is_redirection(word: str) -> bool:
    # punctuation_chars splits `2>/dev/null` into `2`, `>`, `/dev/null`, so the
    # operator arrives as a run of `<`, `>` and `&` on its own.
    return bool(word) and set(word) <= set("<>&") and any(c in word for c in "<>")


def _offence(command: str) -> str | None:
    try:
        words = _words(command)
    except ValueError:
        return None
    for i, word in enumerate(words):
        if word == NULL:
            if i == 0 or not _is_redirection(words[i - 1]):
                return f"`{NULL}` as an argument"
        elif word.endswith(NULL) and word.startswith("-"):
            return f"`{word}`, an option that names {NULL}"
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
                "The permission checker reads an argument of /dev/null as a "
                "path outside the working directories and asks Helen; no "
                "allow rule reaches past blockReadsOutsideWorkingDirectories. "
                "A redirection is not checked.\n\n"
                "WHAT TO DO INSTEAD: redirect -- `cmd > /dev/null 2>&1`. For "
                "an output file, name one under tmp/ (`-o tmp/x`). To check a "
                "link, use `sh scripts/check-link.sh <url>`. For an empty "
                "file to compare against, write one under tmp/ with the "
                "Write tool."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
