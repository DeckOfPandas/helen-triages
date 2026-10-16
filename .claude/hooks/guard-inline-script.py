#!/usr/bin/env python3
"""Refuse ANY inline program passed to an interpreter's -c/-e. Put it in a file.

Matched: `-c` after `python`, `python2` or `python3`, and `-e` after `ruby`,
`node` or `perl`, with a program following it. There is no length or quoting
carve-out: an inline program is opaque to the permission checker, which must
prove before anything runs that a command reads only inside the working
directory, so under `blockReadsOutsideWorkingDirectories` it asks Helen at any
length, whatever the allow list says. DECISIONS §11.

Allowed on purpose:

  * A file argument (`python3 tmp/thing.py`), which is what this pushes
    towards.
  * `-c` on a command that is not one of those interpreters, such as
    `git -c credential.helper=...`. The interpreter has to be the word
    governing the flag, with only other options between them.
  * `sh -c` and `bash -c`, which are not in INTERPRETERS.

`shlex.split`, not a regex: the program is a quoted argument, and quoting is
what a regex gets wrong. A command that will not tokenise is allowed rather
than guessed at. Tested in `tests/test_text_tool_guards.py`.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import shlex
import sys

# Interpreters whose -c/-e takes a program. `sh` and `bash` are deliberately
# absent.
INTERPRETERS = {
    "python": "-c", "python3": "-c", "python2": "-c",
    "ruby": "-e", "node": "-e", "perl": "-e",
}


def _offending_program(command: str) -> tuple[str, str] | None:
    """Return (interpreter, flag) for an inline program that belongs in a file.

    Every inline program qualifies; there is no length or quoting test.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None                 # unbalanced quotes; not ours to judge

    for i, token in enumerate(tokens):
        name = token.rsplit("/", 1)[-1]
        flag = INTERPRETERS.get(name)
        if flag is None:
            continue
        # Look ahead for the flag and its program, allowing other options
        # between them (`python3 -B -c '...'`).
        for j in range(i + 1, len(tokens)):
            if tokens[j] == flag:
                if j + 1 >= len(tokens):
                    break           # the flag with no program; not ours
                return name, flag
            # A new interpreter or a bare file argument ends the search.
            if not tokens[j].startswith("-"):
                break
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    found = _offending_program(command)
    if not found:
        return 0
    name, flag = found

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED: this `{name} {flag}` program belongs in a file. "
                "Every inline program does, however short.\n\n"
                "Helen, 2026-09-09, for the second time in one session: "
                "\"please please please write those long lines to files rather "
                "than running them all together.\" And CLAUDE.md: \"when a "
                "command needs to be clever, put the cleverness in a file and "
                "run the file.\"\n\n"
                "THE REASON IS NOT STYLE, AND IT IS NOT LENGTH. "
                "`.claude/settings.json` sets "
                "`blockReadsOutsideWorkingDirectories`. Under that block, a "
                "command the shell parser cannot analyze asks Helen -- "
                "whatever the allow list says -- because the checker's job is "
                "to prove, before anything runs, that the command reads only "
                "inside the working directory, and it cannot prove that about "
                "code it cannot see. An inline program is opaque by "
                "construction, so it always asks. A file argument is one "
                "static path the checker can see. A `tmp/` script still asks "
                "Helen, on purpose, so reach first for a committed "
                "allow-listed wrapper; a `tmp/` script is for the genuine "
                "one-off.\n\n"
                "WHAT TO DO INSTEAD -- write it with the Write tool and run "
                "the file:\n\n"
                "    Write  tmp/thing.py\n"
                "    Bash   python3 tmp/thing.py\n\n"
                "That leaves a record of exactly what was measured, which a "
                "one-off inline program never does.\n\n"
                "This hook had a carve-out for short single-quoted one-liners "
                "until 2026-09-10. It was removed because it rested on a "
                "`Bash(python3 -c ' *)` allow rule that does not exist, and "
                "because the read block would have asked anyway. Do not "
                "reinstate it by shortening your program."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
