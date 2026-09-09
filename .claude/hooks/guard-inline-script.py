#!/usr/bin/env python3
"""Refuse a LONG or MULTI-LINE inline program passed to an interpreter's -c/-e.

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

WHAT IT BLOCKS. An inline program given to `-c` (python) or `-e`
(ruby/node/perl) that is MULTI-LINE, or CONTAINS A SINGLE QUOTE, or is longer
than MAX_INLINE characters. All three are the shape the permission checker
cannot verify, so none can be allow-listed and every one costs Helen an
interruption.

THE SINGLE-QUOTE RULE IS THE ONE THAT BITES MOST OFTEN and it is not about
length at all. The allow rule is `Bash(python3 -c ' *)` -- single-quoted. A
program containing a `'` cannot be single-quoted in shell, so it must be
double-quoted, so it matches nothing and prompts however short it is.
CLAUDE.md has always said "short snippets WITH NO EMBEDDED SINGLE QUOTES";
only the length half was enforced at first, and an 89-character command
prompted Helen anyway, which is how this was found.

WHAT IT DELIBERATELY ALLOWS, because a guard that fires on harmless
invocations is one you learn to route around:

  * SHORT one-liners. `python3 -c 'import yaml, sys; print(yaml.safe_load(
    open("x.yml")).keys())'` is a legitimate quick look, CLAUDE.md explicitly
    permits "short snippets", and the existing `Bash(python3 -c ' *)` allow
    rule already covers them. The line this draws is length, not cleverness --
    length is the thing a human can judge at a glance, and judging it at a
    glance is the entire point (see guard-token-expansion.py, widened on the
    same day for the same reason).
  * `python3 tmp/thing.py` and any other FILE argument, which is the thing this
    hook is pushing you towards.
  * `-c` on a command that is not an interpreter -- `git -c
    credential.helper=...`, `docker run -c`, `bundle exec -c`. The interpreter
    has to be the word immediately governing the flag.

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

# Longer than this, or containing a newline, and it belongs in a file.
#
# 100, AND IT TOOK TWO CORRECTIONS TO GET HERE, both worth recording because
# each was found by measurement rather than argument:
#   160 -- the first draft. The probe caught a 155-character one-liner carrying
#          a dict comprehension: exactly the "cleverness" this is about, just
#          without a newline in it.
#   120 -- Helen then hit a prompt on an 89-character command and said "it
#          looks like you need to drop your character threshold".
# A real quick look still clears it: the canonical example in the docstring is
# 68 characters. The two commands that earned this hook were 210 and 268.
MAX_INLINE = 100


def _offending_program(command: str) -> tuple[str, str, str] | None:
    """Return (interpreter, flag, reason) for a program that belongs in a file."""
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
                    break
                program = tokens[j + 1]
                if "\n" in program:
                    return name, flag, "it spans multiple lines"
                # THE RULE THAT ACTUALLY BITES MOST OFTEN, and the one the
                # length check missed. The allow rule is `Bash(python3 -c ' *)`
                # -- SINGLE-quoted. A program containing a `'` cannot be
                # single-quoted in shell, so it has to be double-quoted, so it
                # matches no allow rule and always prompts, however short it
                # is. CLAUDE.md has always said "short snippets WITH NO
                # EMBEDDED SINGLE QUOTES"; this is that half, enforced. Found
                # when an 89-character command prompted Helen anyway.
                if "'" in program:
                    return (name, flag,
                            "it contains a single quote, so it cannot be "
                            "single-quoted and matches no allow rule")
                if len(program) > MAX_INLINE:
                    return (name, flag,
                            f"it is {len(program)} characters long "
                            f"(the limit is {MAX_INLINE})")
                break
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
    name, flag, reason = found

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED: this `{name} {flag}` program belongs in a file -- "
                f"{reason}.\n\n"
                "Helen, 2026-09-09, for the second time in one session: "
                "\"please please please write those long lines to files rather "
                "than running them all together.\" And CLAUDE.md: \"when a "
                "command needs to be clever, put the cleverness in a file and "
                "run the file.\"\n\n"
                "THE REASON IS NOT STYLE. The permission checker proves, "
                "before anything runs, that a command touches only the working "
                "directory -- and it can only do that for a command whose text "
                "is its whole meaning. A long inline program is where loops, "
                "pipes and substitutions hide, so it can never be "
                "allow-listed, and the cost is never a refusal: it is an "
                "interruption, and it lands on Helen.\n\n"
                "WHAT TO DO INSTEAD -- write it with the Write tool and run "
                "the file:\n\n"
                "    Write  tmp/thing.py\n"
                "    Bash   python3 tmp/thing.py\n\n"
                "That is a single static path, it matches the existing "
                "`Bash(python3 *)` allow rule, and it leaves a record of "
                "exactly what was measured, which a one-off inline program "
                "never does.\n\n"
                f"Short one-liners are still fine: under {MAX_INLINE} "
                "characters and on one line, this hook does not fire."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
