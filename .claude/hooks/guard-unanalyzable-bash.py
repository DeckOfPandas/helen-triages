#!/usr/bin/env python3
"""Refuse a Bash command the permission checker cannot statically analyse.

WHY THIS EXISTS. Helen, 2026-09-10, after permitting two such calls by hand in
one session: *"can we either avoid needing to request permission, or block the
command if it can't be statically analysed?"* This is the second half of that
sentence. The first half is allow rules in `.claude/settings.json`.

IT ENFORCES A RULE THAT WAS ALREADY WRITTEN, AND STATES ITS OWN REASON.
`CLAUDE.md`'s working-practices section ends:

    All of these rules are one rule, and it is worth stating once. The
    permission checker proves, before anything runs, that a command touches
    only the working directory. It can do that only for a command whose text
    is its whole meaning. Every rule above names a way of hiding meaning from
    it -- on stdin, behind a glob, behind a substitution, behind a `cd`,
    behind an `&&`, behind a variable -- and the cost is never a refusal,
    always an interruption to Helen. When a command needs to be clever, put
    the cleverness in a file and run the file.

Six named shapes, one consequence each, and until now nothing but care stood
behind any of them. Care has a measured failure rate here: this is the sixth
guard in `.claude/hooks/`, and every one of the five before it exists because a
written rule was read and then broken. **A rule I read and break needs
enforcement, not rewording.**

THE COST FALLS ON THE RIGHT PERSON NOW. A prompt is not a refusal -- it is an
interruption, and it lands on Helen rather than on the session that earned it.
A denial lands on the session, which can simply write the script and carry on.
That asymmetry is the whole argument for blocking rather than asking.

WHAT IT REFUSES, each with the `CLAUDE.md` rule it belongs to:

  1. A HEREDOC (`<<'PY'`, `<<EOF`) -- the body arrives on stdin, opaque.
  2. COMMAND SUBSTITUTION (`$(...)`, backticks) -- the value does not exist
     until the command runs, so `git commit -m "$(cat <<'EOF' ...)"` and
     `gh pr create --body "$(...)"` can never be verified ahead of time.
  3. A GLOB in an argument (`cat some/*.txt`) -- expands at runtime, so the
     actual file list is unknown when the check would need to run. Point the
     command at the directory and let it recurse, or list the files.
  4. A LEADING `cd` -- allow rules match a command's PREFIX, so
     `cd /workspace; grep ...` starts with `cd` and matches nothing. The Bash
     tool already runs in the project root; there is nothing to cd into.
  5. CHAINING with `&&`, `||` or `;` -- checked as a whole, so it matches
     neither part's rule even when both parts are allowed on their own.
  6. A PIPE -- a pipeline's later stages are runtime-computed.

WHAT IT DELIBERATELY ALLOWS, because a guard that fires on harmless
invocations is one you learn to route around (the lesson `guard-destructive-git
.py` records):

  * REDIRECTION to a static path, including `2>&1` and `>/dev/null`. A
    redirection names its file in the command text, so it is analysable; it is
    only the PIPE that hides a later stage. `python3 tmp/x.py > tmp/out.txt
    2>&1` is fine.
  * Anything inside QUOTES. A quoted span is data, not shell syntax, so
    `grep -rn 'a && b' dir/` and a commit message discussing `$(...)` both
    pass. Single and double quotes alike are stripped before the scan -- unlike
    `guard-token-expansion.py`, which deliberately keeps double-quoted spans
    because `$VAR` expands inside them; that guard owns the secret-leak case
    and this one does not duplicate it.
  * `$VAR` on its own. Deliberately NOT refused, though `CLAUDE.md`'s sentence
    names it: a bare `$` appears too often in regexes and paths for a
    pattern-matcher to judge, and the one case that actually matters -- a
    secret -- already has `guard-token-expansion.py`. A guard that fires on
    `grep -n 'x$' file` would teach you to route around this one.

HOW IT READS THE COMMAND. Quote-stripping first, then substring and token
tests. NOT `shlex.split`: an unbalanced quote is exactly what a malformed
command has, and a guard that throws on its own bug reports is useless. If the
text cannot be scanned at all this ALLOWS it -- another guard, or the checker,
can have that one.

Invoked as `python3 .claude/hooks/guard-unanalyzable-bash.py` so it needs no
execute bit -- `CLAUDE.md` forbids changing file permissions without asking.
"""
from __future__ import annotations

import json
import re
import sys

# A redirection target, so `2>&1` and `>/dev/null` are not mistaken for
# chaining or a pipe. Matched and removed before the chaining/pipe scan.
_REDIRECT = re.compile(r"\d*>{1,2}\s*&?\s*\d*|\d*<\s*")

# `cd` as the first word, with or without a following path.
_LEADING_CD = re.compile(r"^\s*cd(\s|$)")

# A glob character in an unquoted token. `?` is deliberately excluded: it is
# far more often a regex or a URL query than a glob, and `*` is the form every
# CLAUDE.md example uses.
_GLOB = re.compile(r"\*")


def _strip_quoted(command: str, quotes: str) -> str:
    """Blank out spans in the given quote characters, keeping the length.

    `quotes` IS THE WHOLE SUBTLETY, and getting it wrong is a correctness bug
    rather than a friction one. Found by breaking this guard on purpose,
    2026-09-10: `git commit -m "$(cat tmp/msg.txt)"` walked straight through a
    version that blanked both quote kinds before looking for `$(`.

      * `&&`, `||`, `;`, `|` and `*` inside EITHER kind of quote are inert
        data, so both kinds are stripped before those tests.
      * `$(...)` and backticks inside DOUBLE quotes are LIVE -- the shell
        expands them there -- so only single quotes are stripped before that
        test. This is the same distinction `guard-token-expansion.py` draws for
        `$VAR`, and for the same reason.

    So prose about substitution belongs in SINGLE quotes. Replacing with spaces
    rather than deleting keeps offsets stable.

    BACKSLASH ESCAPES ARE HONOURED, and that is not a nicety -- it was a real
    false positive on 2026-09-10, hours after this guard shipped. A perfectly
    ordinary command was refused:

        grep -n "PATTERNS\\|re.compile(r\\"\\\\bgit\\|_matched" some-file.py

    The `\\"` in the middle is an ESCAPED quote, still inside the double-quoted
    span. Without escape handling the scanner treated it as the closing quote,
    left the rest of the pattern exposed, found a `|`, and called it a pipe. A
    guard that refuses a legitimate command is one you learn to route around,
    which is the failure mode this repository names in three other hooks.

    Inside SINGLE quotes there is no escaping -- a backslash is a literal
    backslash to the shell -- so escapes are honoured everywhere else and not
    there.
    """
    out = []
    quote = None
    escaped = False
    for ch in command:
        if escaped:
            # The escaped character is whatever it is, never a delimiter.
            out.append(" " if quote is not None else ch)
            escaped = False
        elif ch == "\\" and quote != "'":
            out.append(" " if quote is not None else ch)
            escaped = True
        elif quote is None and ch in quotes:
            quote = ch
            out.append(" ")
        elif quote is not None and ch == quote:
            quote = None
            out.append(" ")
        elif quote is not None:
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def _offence(command: str) -> tuple[str, str] | None:
    """Return (shape, what to do instead) for an unanalysable command."""
    # Both quote kinds stripped: these operators are inert inside either.
    bare = _strip_quoted(command, "'\"")
    # Only single quotes stripped: the shell expands `$(...)` and backticks
    # inside double quotes, so those spans are live and must still be scanned.
    live = _strip_quoted(command, "'")

    if "<<" in bare:
        return ("a heredoc, whose body arrives on stdin",
                "write the script to a file in `tmp/` with the Write tool and "
                "run it as a plain file argument: `python3 tmp/thing.py`")

    if "$(" in live or "`" in live:
        return ("command substitution, whose value does not exist until it runs",
                "for a commit message or a PR body, write it to a file and "
                "pass the file: `git commit -F tmp/commit-msg.txt`, "
                "`gh pr create --body-file tmp/pr-body.md`. Otherwise put the "
                "whole thing in a script in `tmp/` and run the script")

    if _LEADING_CD.match(bare):
        return ("a leading `cd`, which breaks every prefix-based allow rule",
                "drop it -- the Bash tool already runs in the project root, so "
                "`grep ...` works where `cd /workspace; grep ...` matches no "
                "allow rule and always prompts")

    # Redirections out of the way first, so `2>&1` is not read as chaining.
    scannable = _REDIRECT.sub(" ", bare)

    if "|" in scannable:
        return ("a pipe, whose later stages are computed at runtime",
                "write the pipeline into a script in `tmp/` and run the file "
                "(`sh tmp/thing.sh`, `python3 tmp/thing.py`) -- which also "
                "leaves a record of exactly what was measured")

    if "&&" in scannable or "||" in scannable or ";" in scannable:
        return ("two or more commands chained together",
                "one command per Bash call. A chained command is checked as a "
                "whole, so it matches neither part's allow rule even when both "
                "parts are allowed on their own. Two calls cost a round trip; "
                "one chained call costs Helen an interruption")

    if _GLOB.search(scannable):
        return ("a glob, which expands at runtime so the file list cannot be "
                "verified",
                "point the command at the directory and let it recurse "
                "(`grep -r 'x' dir/`, no `*.md` needed), or list the files "
                "explicitly")

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the call

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        return 0

    try:
        found = _offence(command)
    except Exception:
        return 0                    # a guard must not block its own bug reports
    if not found:
        return 0
    shape, remedy = found

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED: this command contains {shape}, so the permission "
                "checker cannot statically analyse it.\n\n"
                "Helen, 2026-09-10, having permitted two such calls by hand in "
                "one session: \"can we either avoid needing to request "
                "permission, or block the command if it can't be statically "
                "analysed?\" This is the second half of that sentence.\n\n"
                "WHY THIS IS A DENIAL AND NOT A PROMPT. The checker proves, "
                "before anything runs, that a command touches only the working "
                "directory -- and it can only do that for a command whose text "
                "is its whole meaning. When it cannot, the cost is not a "
                "refusal: it is an interruption, and it lands on Helen rather "
                "than on the session that earned it. A denial lands on the "
                "session, which can write the script and carry on.\n\n"
                f"WHAT TO DO INSTEAD -- {remedy}.\n\n"
                "CLAUDE.md: \"When a command needs to be clever, put the "
                "cleverness in a file and run the file.\"\n\n"
                "Quoted text is exempt for `&&`, `||`, `;`, `|` and globs, "
                "which are inert inside either kind of quote. NOT for "
                "`$(...)` and backticks: the shell expands those inside "
                "DOUBLE quotes, so prose about substitution belongs in single "
                "quotes. Redirection to a static path is fine, `2>&1` "
                "included -- it is only the pipe that hides a later stage."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
