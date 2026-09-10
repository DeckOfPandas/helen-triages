#!/usr/bin/env python3
"""Refuse ANY inline program passed to an interpreter's -c/-e. Put it in a file.

WHY THIS EXISTS, AND WHY IT IS A HOOK RATHER THAN A FIRMER SENTENCE. CLAUDE.md
has said since 2026-09-08, in Helen's own words: "if they take or emit
variables, please write a script in tmp/ so you don't need to request
permissions from me", and "when a command needs to be clever, put the
cleverness in a file and run the file." The rule was read and broken twice in
one session on 2026-09-09, both times with a multi-line `python3 -c`:

  * once mid-triage, to inspect a YAML file's shape. Helen rejected the call.
  * once an hour later, to strip markup out of a rendered page. She allowed it
    and then asked, for the second time: "please please please write those long
    lines to files rather than running them all together."

That is the situation this repository already has a verdict on, from
guard-main-branch.py, guard-sed.py and guard-token-expansion.py alike:
**a rule I read and break needs enforcement, not rewording.**

WHAT IT BLOCKS, SINCE 2026-09-10: every inline program given to `-c` (python)
or `-e` (ruby/node/perl). No length carve-out, no quoting carve-out, no
exceptions to hold in your head.

THE CARVE-OUT THIS USED TO HAVE WAS BUILT ON AN ALLOW RULE THAT DOES NOT
EXIST. Until 2026-09-10 this hook allowed a single-quoted one-liner under 100
characters, and both this docstring and CLAUDE.md justified that by "the
existing `Bash(python3 -c ' *)` allow rule already covers them". It does not:
there is no such rule in `.claude/settings.json`, and there never was. Helen
hit a prompt on a 78-character single-quoted one-liner -- comfortably inside
every limit the carve-out set -- and asked, reasonably, to either do it more
safely or not be asked at all.

AND THE ALLOW RULE WOULD NOT HAVE SAVED IT ANYWAY, which is the part that
settles this. `.claude/settings.json` sets
`"blockReadsOutsideWorkingDirectories": true`. Under that block a command the
shell parser CANNOT ANALYZE asks the person, whatever the allow list says --
the checker's job is to prove, before anything runs, that the command reads
only inside the working directory, and it cannot prove that about code it
cannot see. An inline program is opaque by construction. So:

    python3 -c '<anything at all>'     -> unanalyzable -> ALWAYS asks Helen
    python3 tmp/thing.py              -> one static path -> silent

There is no short-enough, no quote-free-enough. The length threshold was
measuring the wrong thing all along: the three calibrations it went through
(160 -> 120 -> 100, each from a real measurement) were all trying to find a
length at which an opaque command stops being opaque, and no such length
exists. Keeping a threshold meant Helen stayed the backstop for judging it.

WHAT IT DELIBERATELY STILL ALLOWS, because a guard that fires on harmless
invocations is one you learn to route around:

  * `python3 tmp/thing.py` and any other FILE argument, which is the thing this
    hook is pushing you towards, and which is silent under the read block.
  * `-c` on a command that is not an interpreter -- `git -c
    credential.helper=...`, `docker run -c`, `bundle exec -c`. The interpreter
    has to be the word immediately governing the flag.
  * `sh -c` and `bash -c`, which is how a git credential helper is spelled
    (CLAUDE.md's documented push shape); blocking it would break the
    documented workflow.

HOW IT READS THE COMMAND. `shlex.split`, not a regex: the program is a quoted
argument and quoting is exactly what a regex gets wrong. If the command will
not tokenise (unbalanced quotes), this ALLOWS it rather than guessing --
another guard, or the permission checker, can have that one. A guard that
blocks on parse failure blocks its own bug reports.

Invoked as `python3 .claude/hooks/guard-inline-script.py` so it needs no
execute bit -- CLAUDE.md forbids changing file permissions without asking, and
a hook that required a chmod to install would be self-defeating.
"""
from __future__ import annotations

import json
import shlex
import sys

# Interpreters whose -c/-e takes a PROGRAM. `sh`/`bash` are deliberately
# absent: `sh -c` is how a git credential helper is spelled (CLAUDE.md's
# documented push shape) and blocking it would break the documented workflow.
INTERPRETERS = {
    "python": "-c", "python3": "-c", "python2": "-c",
    "ruby": "-e", "node": "-e", "perl": "-e",
}


def _offending_program(command: str) -> tuple[str, str] | None:
    """Return (interpreter, flag) for an inline program that belongs in a file.

    Every inline program qualifies. There is no length or quoting test left:
    see the module docstring -- under `blockReadsOutsideWorkingDirectories` an
    inline program is unanalyzable, so it asks Helen at any length.
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
                "static path, so it is silent.\n\n"
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
