#!/usr/bin/env python3
"""Refuse a Bash command the permission checker cannot statically analyse.

The checker proves, before anything runs, that a command touches only the
working directory, and it can do that only when the command's text is its whole
meaning. Otherwise it prompts Helen; a denial here lands on the session
instead, which can put the cleverness in a file and run the file. DECISIONS §11.

Refused:

  1. A heredoc: the body arrives on stdin.
  2. Command substitution, `$(...)` or backticks: the value does not exist
     until the command runs.
  3. A glob `*` in an argument: it expands at run time. `?` is not matched,
     being far more often a regex or a URL query.
  4. A leading `cd`: allow rules match a command's prefix, so it matches none.
  5. Chaining with `&&`, `||` or `;`: checked as a whole, so it matches
     neither part's allow rule.
  6. A pipe: its later stages are computed at run time.
  7. A quoted `[`, `]` or `|` in an argument to `sh scripts/...`: the checker
     reads a script's arguments as possible paths, and these make one look
     computed, quotes or not. Only `sh scripts/` is covered.
  8. A leading `NAME=value` before the command word: the checker cannot tell
     what the assignment routes the rest of the command through. `FOO=bar`
     alone runs nothing and passes.
  9. An unquoted `(` or `)`: a subshell, or a parse error. A backslash-escaped
     one passes.
 10. `git -C <path>` as a command word, anywhere: every git allow rule names a
     subcommand, and a `-C` before it defeats the prefix match. `--git-dir=`
     and `--work-tree=` are not refused.
 11. `$[` outside single quotes: legacy arithmetic, which the checker's parser
     gives up on. It arrives as a regex with a class after a dollar. A
     backslash-escaped dollar is inert and passes; a dollar after an escaped
     backslash is live and refused. `${...}` is not refused.

Allowed on purpose, because a guard that fires on harmless commands gets
routed around:

  * Redirection to a static path, `2>&1` and `>/dev/null` included: the file
    is named in the command text.
  * Anything inside quotes, with two exceptions: shapes 2 and 11 are live
    inside DOUBLE quotes, where the shell still expands them, and shape 7 is
    about quoted text.
  * A bare `$VAR`: too common in regexes and paths to judge, and the secret
    case belongs to `guard-token-expansion.py`.
  * An `=` that is not a leading assignment: `--flag=value`, and lowercase
    `git -c key=value`, which is how the `scripts/git-*-agent.sh` wrappers
    pass the credential helper. Shape 10 is case-sensitive for that reason.

Quote-stripping first, then substring and token tests; not `shlex.split`,
which throws on the unbalanced quote a malformed command has. Text that cannot
be scanned is allowed.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import re
import sys

# A redirection target, so `2>&1` and `>/dev/null` are not mistaken for
# chaining or a pipe. Matched and removed before the chaining/pipe scan.
_REDIRECT = re.compile(r"\d*>{1,2}\s*&?\s*\d*|\d*<\s*")

_LEADING_CD = re.compile(r"^\s*cd(\s|$)")

# Shape 10. Case-sensitive on purpose: lowercase `git -c key=value` is a
# different flag, and is how every scripts/git-*-agent.sh passes the credential
# helper. Not anchored to the start of the command.
_GIT_DASH_C = re.compile(r"(?:^|\s)git\s+-C(?=\s|$)")

# `$[` with a LIVE dollar -- shape 11. Applied to the text with only single
# quotes stripped, since double quotes do not stop the shell reading it. The
# lookbehind and the pairs of backslashes are what tell `\$[` (an escaped
# dollar, inert) from `\\$[` (an escaped backslash, then a live dollar).
_LEGACY_ARITHMETIC = re.compile(r"(?<!\\)(?:\\\\)*\$\[")

# A glob character in an unquoted token. `?` is deliberately excluded: it is
# far more often a regex or a URL query than a glob, and `*` is the form every
# CLAUDE.md example uses.
_GLOB = re.compile(r"\*")

# The only command shape 7 applies to: a committed wrapper run as `sh scripts/`.
_SCRIPT_CALL = re.compile(r"^\s*sh\s+scripts/")

# A single token shaped like a shell environment assignment: `NAME=`, with
# whatever follows. Applied only to the LEADING run of tokens (shape 8) --
# `git -c credential.helper=x` never reaches this, because its first token is
# `git`, which does not match.
_ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _has_leading_env_assignment(bare: str) -> bool:
    """True if one or more `NAME=value` tokens precede an actual command word.

    Splits the QUOTE-STRIPPED command on whitespace. Stripping first matters
    here as much as it does for the pipe/chaining checks: it blanks a quoted
    value's spaces to plain spaces (`NAME='a b' cmd` -> `NAME=      cmd`),
    which `.split()` then collapses back into the right token boundaries
    without needing to understand quoting itself. A token is required both
    before AND after the run of assignments -- `FOO=bar` alone sets a
    variable and runs nothing, so it is not this shape.
    """
    tokens = bare.split()
    count = 0
    for token in tokens:
        if _ENV_ASSIGNMENT.match(token):
            count += 1
        else:
            break
    return 0 < count < len(tokens)


def _strip_quoted(command: str, quotes: str) -> str:
    """Blank out spans in the given quote characters, keeping the length.

    `quotes` is the subtlety. `&&`, `||`, `;`, `|` and `*` are inert inside
    either kind of quote, so both kinds are stripped before those tests.
    `$(...)`, backticks and `$[` are live inside DOUBLE quotes, so only single
    quotes are stripped before those: blanking both lets a substitution inside
    a double-quoted commit message through.

    A backslash escape is honoured outside single quotes, so an escaped quote
    inside a double-quoted span does not close it and expose the rest of a
    pattern. Inside single quotes a backslash is literal. Spaces replace the
    characters so offsets stay stable.
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

    if _LEGACY_ARITHMETIC.search(live):
        return ("`$[` outside single quotes, which the shell reads as legacy "
                "arithmetic and the checker's parser cannot analyse",
                "put the pattern in SINGLE quotes, where `$[` is two ordinary "
                "characters: `grep -n -E '^\\$[a-z-]*width:' _sass/`. If the "
                "pattern also needs a single quote, put the command in a "
                "script in `tmp/` and run the file")

    if _LEADING_CD.match(bare):
        return ("a leading `cd`, which breaks every prefix-based allow rule",
                "drop it -- the Bash tool already runs in the project root, so "
                "`grep ...` works where `cd /workspace; grep ...` matches no "
                "allow rule and always prompts")

    if _GIT_DASH_C.search(bare):
        return ("`git -C <path>`, which breaks every prefix-based git allow rule",
                "drop it -- the Bash tool already runs in the worktree root, so "
                "`git status --short` works where "
                "`git -C /workspace/.claude/worktrees/foo status --short` "
                "matches no allow rule and prompts Helen. Every git allow rule "
                "names the SUBCOMMAND (`git status *`, `git add -- *`, "
                "`git commit -F *`, the exact `git branch --show-current`), and "
                "a `-C` between `git` and its subcommand makes the prefix match "
                "fail. Lowercase `git -c key=value` is a different flag and is "
                "not refused")

    if _has_leading_env_assignment(bare):
        return ("a leading shell environment assignment (`NAME=value` before "
                "the command word), which the checker cannot see through to "
                "know what the rest of the command will do",
                "use a committed wrapper instead -- `scripts/browser/`'s "
                "scripts already source `scripts/browser/env.sh` themselves, "
                "so a Playwright command never needs "
                "`PLAYWRIGHT_BROWSERS_PATH=...`/`NODE_PATH=...` typed by hand "
                "-- or put the whole command in a script in `tmp/` and run "
                "the file, where the assignment sits on its own line with no "
                "prefix at all")

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

    # Shape 9. An unquoted parenthesis is a subshell or, as in an unquoted
    # `git log --format=%(trailers)`, a parse error. A backslash-escaped paren
    # is an ordinary character and is cleared first; a quoted one was stripped
    # above.
    if re.search(r"[()]", re.sub(r"\\[()]", "  ", scannable)):
        return ("an unquoted `(` or `)`, which the shell reads as a subshell or "
                "cannot parse at all",
                "quote the argument that carries it -- single quotes, e.g. "
                "`git log --format='%h %s %(trailers:key=Fixes)'` -- or, for a "
                "real subshell, put the commands in a script in `tmp/` and run "
                "the file")

    if _GLOB.search(scannable):
        return ("a glob, which expands at runtime so the file list cannot be "
                "verified",
                "point the command at the directory and let it recurse "
                "(`grep -r 'x' dir/`, no `*.md` needed), or list the files "
                "explicitly")

    # Shape 7. `bare` has the same length as `command`, with every quoted
    # character blanked -- so a character blanked in `bare` and a bracket or
    # pipe in `command` is one that sat inside quotes.
    if _SCRIPT_CALL.match(command) and any(
        bare[i] == " " and ch in "[]|" for i, ch in enumerate(command)
    ):
        return ("a quoted `[`, `]` or `|` in an argument to a scripts/ wrapper, "
                "which Claude Code reads as a path computed at run time and "
                "asks Helen about even though the wrapper is allow-listed "
                "(measured 2026-09-15)",
                "for a GitHub read, name the fields instead of writing jq: "
                "`sh scripts/gh-read.sh <endpoint> --fields state,merged_at` "
                "for one object, `--each number,title` for a list. Otherwise "
                "rephrase the argument without brackets or a pipe")

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
                "which are inert inside either kind of quote -- EXCEPT a "
                "quoted `[`, `]` or `|` given to `sh scripts/...`. NOT for "
                "`$(...)`, backticks and `$[`: the shell reads those inside "
                "DOUBLE quotes, so prose about substitution, and a regex with "
                "a class after a dollar, belong in single quotes. Redirection to a static path is fine, `2>&1` "
                "included -- it is only the pipe that hides a later stage."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
