#!/usr/bin/env python3
"""Refuse any Bash command that mentions `sed`, anywhere in it, full stop.

WHY THIS EXISTS. Helen's standing rule is "never sed, ever" -- not "never
sed -i", not "never sed with an e command", the whole tool, unconditionally.
Her reasoning, confirmed 2026-09-08: sed -i can silently corrupt a file with
a subtly-wrong regex, with none of the visible-diff review an Edit tool call
gives her, in a project full of hand-curated content where that's expensive
to notice later. Python already covers everything sed does, more precisely
and more reviewably, so banning sed outright costs her nothing real.

The two `permissions.deny` rules that already tried to express this --
`Bash(sed -i*)` and `Bash(sed*e*)` in settings.local.json -- are BOTH prefix
patterns: they only match a command that literally STARTS with `sed`. A
command like `grep -rn "x" dir/ | sed 's|dir/||' | sort` starts with `grep`,
so neither deny rule ever sees it, and it falls through to a confirmation
prompt instead of an automatic block -- exactly the kind of pattern-matching
gap this repository keeps finding and keeps closing with a hook instead of a
cleverer pattern, because the pattern-matching engine here is prefix-only and
cannot express "contains, anywhere in a pipeline." See guard-main-branch.py
and guard-destructive-git.py for the same shape of fix for a different verb.

DELIBERATELY NOT CLEVER. This does not try to distinguish a safe sed (no -i,
no e/w/r command, pure stream filter) from an unsafe one. That distinction is
exactly the kind of detection logic that could itself grow a gap later --
the whole reason this hook exists is that clever pattern-matching keeps
missing cases. A flat, unconditional block is easy to verify correct and
matches the policy Helen actually wants: no sed, full stop.

WHAT IT DELIBERATELY ALLOWS: mentioning "sed" inside a quoted string or a
heredoc body, so a commit message or comment can still discuss it (e.g. this
file's own introducing commit, or CLAUDE.md's prose about the rule).

No `"if"` filter in its hooks wiring, unlike the two existing git guards --
an `"if": "Bash(sed *)"` filter would have the exact same prefix-only blind
spot this hook exists to close, since it uses the same permission-pattern
matching engine. Instead this runs on every Bash call and does its own cheap
regex check, so there is no gate to bypass by putting something else first.

Invoked as `python3 .claude/hooks/guard-sed.py` so it needs no execute bit:
CLAUDE.md forbids changing file permissions without asking, and a hook that
required a chmod to install would be self-defeating.
"""
from __future__ import annotations

import json
import re
import sys

# Split on shell word-separators (whitespace and the operators that start a
# new command: pipes, semicolons, ampersands, parens). Deliberately NOT a
# `\bsed\b` substring regex -- that also matches "sed" inside an unrelated
# filename like this very file, guard-sed.py (word boundaries exist on both
# sides of "sed" there too, right before the hyphen and the dot), which
# would self-trigger on any command that so much as mentions this hook by
# name. Checking whole tokens instead of substrings avoids that.
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
                "WHAT TO DO INSTEAD: write the transformation in Python "
                "(a tmp/*.py file run as a plain file argument, or a "
                "single-quoted `python3 -c '...'` for something short) and "
                "run that instead. It covers everything sed does, more "
                "precisely, and is easier to review.\n\n"
                "If you genuinely believe this specific case needs sed, say "
                "so and let Helen decide -- this hook is not the thing to "
                "route around."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
