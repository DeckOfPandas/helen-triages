#!/usr/bin/env python3
"""Refuse a Bash command that would expand a secret into its own output.

WHY THIS EXISTS, AND WHY IT IS A HOOK RATHER THAN A FIRMER SENTENCE.
`CLAUDE.md` has said since 2026-09-06: "Never test whether it is set with a
shell form that expands it -- `echo ${GH_TOKEN:-unset}` prints the whole token
when it IS set, and did." The rule was then broken twice more, both times in
the same session, both times by an agent that had read it:

  * 2026-09-08, start of session: `${GH_TOKEN:-unset-marker-check}`. The
    permission checker happened to refuse the call for an unrelated reason, so
    nothing leaked, and the agent wrote "the denial was correct, I won't probe
    it that way again."
  * 2026-09-08, later, on the NEW token: `${AGENT_GH_TOKEN:-MISSING}`. Helen
    rejected the call by hand. Nothing leaked, because she was watching.

Twice out of three the only thing between the token and the transcript was
luck or a human. That is the exact situation this repository already has a
verdict on, from guard-main-branch.py's own history: **a rule that is read and
broken needs enforcement, not rewording.**

WIDENED 2026-09-10 AFTER A FOURTH, DIFFERENT LEAK -- NOT AN ECHO AT ALL.
CLAUDE.md's own documented pattern for the private repos --
`git clone "https://DeckOfPandas-agentic:${AGENT_GH_TOKEN}@github.com/..."` --
was followed exactly as written. Git then stored that URL, token included, as
the clone's `origin` remote. A routine `git remote -v`, run for an unrelated
and legitimate reason (MANUAL §2.1 says to check which remote a clone points
at), printed the token in full. No echo, no printf, no default-expansion --
the value sat in `.git/config` and any later command that shows a remote URL
would have surfaced it the same way. Two things follow, and this file now does
both:

  1. `_secret_in_url` refuses embedding a secret in a URL's userinfo at all,
     regardless of quoting -- see its own comment for why quoting doesn't
     save this one the way it saves an echo. The fix is
     `scripts/git-credential-agent-token.sh`: a per-repo git credential
     helper that hands the token to git at the moment of use and never
     writes it to a remote URL or to `.git/config` in the first place. Use a
     PLAIN url (`https://github.com/OWNER/REPO.git`) everywhere from now on.
  2. `_literal_token` refuses a real GitHub-token-shaped string anywhere in a
     command, leak vector aside -- the token above is now sitting in this
     session's transcript, so a future command that pastes it back in (from
     the transcript, from a stray note) is exactly as dangerous as one that
     expands it fresh.

AND WIDENED THE SAME DAY FOR WHERE IT LOOKS. Every other guard in this
directory tells you, when it refuses a command, to move the cleverness into a
script in `tmp/` and run the file -- and that is exactly how the leak above
was written: the risky line went into `tmp/clone_food_drafts.sh` to get past
`guard-unanalyzable-bash.py`'s complaint about the URL's complexity, and
nothing scanned the file it ran. `_scan` now also opens the argument of any
`sh`/`bash`/`python3`/`ruby`/`node`/`perl` invocation that names a real file
inside the working directory, and runs every check in this module against
its contents too. A command is judged by what it will actually run, not by
how many characters of it are visible on the command line.

WHAT IT BLOCKS, AND WHY EACH FORM HAS NO DEFENSIBLE USE.

  1. THE DEFAULT-VALUE EXPANSIONS: `${TOK:-x}`, `${TOK:=x}`, `${TOK-x}`,
     `${TOK=x}`. Every one of these evaluates to THE VARIABLE'S OWN VALUE when
     it is set, and to `x` only when it is not. The only reason anyone writes
     one against a secret is to probe whether it is set -- and that probe
     prints the secret in the case where the answer is yes, which is the case
     you were asking about.

  2. ECHOING ONE AT ALL, IN ANY FORM: `echo $TOK`, `printf "%s" "${TOK}"`,
     and -- WIDENED 2026-09-09 -- the placeholder probes too, `echo
     "${TOK:+set}"` and `echo ${#TOK}`, neither of which can render the value.

     HELEN'S REASON IS THE WHOLE POINT, and it is not about what leaks. The
     `+` form is genuinely safe; she still had to REJECT THE CALL BY HAND to
     establish that, because `echo "${GH_TOKEN:+GH_TOKEN set}"` looks exactly
     like a leak until you have run this file's regex in your head. *"I
     shouldn't have to reject the call!! I'm only human!"* A guard that leaves
     the human doing the parsing has not removed the work, it has moved it. So
     the rule is now one a human can check at a glance, with no exceptions to
     hold in mind: **an `echo` or `printf` never mentions a secret.**

     AND NOTHING IS GIVEN UP, which is what made this easy to widen. Every
     probe was only ever asking "is the credential there?", and the honest
     answer to that is to USE it and read the status code -- a 401 or a 403
     settles it without the name ever reaching an `echo`. Helen: *"I can't
     imagine why we wouldn't do that having thought of it."*

WHAT IT DELIBERATELY ALLOWS, because these are how the token is legitimately
used and a guard that blocked them would be routed around within a day:

  * `${TOK}` or `$TOK` anywhere that is not an echo, a URL, or a literal --
    passing it to `GH_TOKEN="$AGENT_GH_TOKEN" gh ...`, or reading it inside
    `scripts/git-credential-agent-token.sh` to answer git's credential
    protocol, are both CONSUMING the value rather than printing it.
  * The whole thing inside SINGLE quotes, for the echo/default-expansion
    checks only -- so prose and commit messages may discuss those forms. See
    the stripping note below, which is where this hook differs from its
    siblings. The URL and literal-token checks are NOT quoting-sensitive;
    see their own comments for why.
  * A script's own `printf`/`echo` of the token is not flagged by opening the
    file -- only the URL-embedding and literal-token shapes are checked
    inside a referenced script. `scripts/git-credential-agent-token.sh`
    genuinely must write the token to its stdout; that is git's own
    credential protocol reading a pipe, not a transcript, and is exactly the
    sanctioned exception the module docstring names.

STRIPPING IS NOT THE SAME HERE AS IN guard-sed.py, AND THE DIFFERENCE IS THE
WHOLE CORRECTNESS ARGUMENT. That hook strips single AND double quoted spans,
which is right for detecting a command NAME: `"sed"` inside double quotes is
just a word. It is wrong for detecting a variable EXPANSION, because the shell
expands `$VAR` inside double quotes and not inside single ones. `echo
"$GH_TOKEN"` is a real leak wearing double quotes. So this strips only the
spans where expansion genuinely cannot happen: single-quoted spans, and
heredocs whose delimiter is quoted.

Invoked as `python3 .claude/hooks/guard-token-expansion.py` so it needs no
execute bit -- CLAUDE.md forbids changing file permissions without asking, and
a hook that required a chmod to install would be self-defeating.
"""
from __future__ import annotations

import json
import os
import re
import sys

# WHICH NAMES COUNT AS A SECRET. Deliberately a short, high-signal list rather
# than anything containing "key": `$SSH_KEY_PATH` and `$API_KEY_FILE` are
# paths, not secrets, and a guard that fired on those would be noise. Covers
# AGENT_GH_TOKEN, the only credential this repo still carries since GH_TOKEN
# was retired on 2026-09-09, plus the obvious siblings -- and GH_TOKEN itself
# still matches, which is wanted: the name survives as the variable `gh` reads
# (`GH_TOKEN="$AGENT_GH_TOKEN" gh ...`) and a guard should not stop covering a
# name just because the secret behind it was rotated away.
SECRET_NAME = re.compile(r"^(.*_)?(TOKEN|SECRET|PASSWORD|PASSWD)$")

# `${NAME:-`, `${NAME:=`, `${NAME-`, `${NAME=` -- the four expansions that
# evaluate to the variable's own value when it is set. `:+`, `+` and `:?` are
# deliberately absent: none of them can emit the value.
DEFAULT_EXPANSION = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\s*:?[-=]")

# ANY reference to a secret's name, for the echo check. Three shapes:
#
#   $NAME                      bare
#   ${NAME<anything>}          including `:+`, `+`, `:?` and `?`
#   ${#NAME}                   the length
#
# UNTIL 2026-09-09 THIS CARRIED AN EXCLUSION -- `(?! :?[+?] )` -- so that the
# `+` forms, which evaluate to the replacement word and cannot render a value,
# stayed legal. It is gone deliberately; see the docstring. The test is no
# longer "can this leak" but "does an echo mention a secret", because the first
# question is one only a regex can answer and Helen was the one answering it.
#
# `${#NAME}` is matched now for the same reason, though it emits a length
# rather than a value: once the `+` probe is refused it is the obvious next
# thing to reach for, and it is a probe with the same non-existent use case.
SECRET_REFERENCE = re.compile(
    r"""\$(?:
          \{ \#? \s* ([A-Za-z_][A-Za-z0-9_]*) [^}]* \}
        | ([A-Za-z_][A-Za-z0-9_]*)
        )""",
    re.VERBOSE,
)

# A command whose first word prints its arguments. Checked after stripping, on
# each command in a pipeline or list, so `foo | echo $TOK` is caught too.
PRINTERS = ("echo", "printf")

# SINGLE quotes only -- see the docstring. A double-quoted span still expands.
SINGLE_QUOTED = re.compile(r"'[^']*'")
# A heredoc whose delimiter is quoted (<<'EOF') suppresses expansion; one whose
# delimiter is bare (<<EOF) does not, so only the quoted form is stripped.
QUOTED_HEREDOC = re.compile(
    r"<<-?\s*(['\"])([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)

# A secret referenced inside a URL's userinfo segment: `scheme://user:PASS@`.
# Deliberately NOT run against the quote-stripped text -- see the module
# docstring's 2026-09-10 addition. A single-quoted `'https://u:$TOK@host'`
# would not actually expand in a real shell, but it is still refused, because
# the pattern itself -- not just whether it happens to fire this time -- is
# what gets stored in `.git/config` and printed by some unrelated later
# command. There is no longer a reason to write this shape at all; see
# `scripts/git-credential-agent-token.sh`.
SECRET_IN_URL = re.compile(
    r"://[^\s/@'\"]*:\s*\$?\{?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}?\s*@"
)

# A real GitHub token, by its own prefix: classic PAT (ghp_), OAuth (gho_), a
# GitHub App's installation/user token (ghu_/ghs_), a refresh token (ghr_), or
# a fine-grained PAT (github_pat_). The length floor (20) is chosen to clear a
# short illustrative example in prose ("a ghp_-prefixed token") while catching
# a real one, which runs much longer. Checked regardless of where the text
# came from or how it is quoted: a leaked token pasted back in from a
# transcript is exactly as dangerous printed a second time.
LITERAL_TOKEN = re.compile(
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}\b"
)

# Interpreters whose first non-flag argument is a script FILE to run, per the
# pattern every guard in this directory recommends as the fix for its own
# refusal ("write it to a file in tmp/ and run the file"). A command shaped
# like this is judged by what the file actually contains, not by how little
# of it is visible on the command line -- see the module docstring.
_SCRIPT_INTERPRETERS = {"sh", "bash", "python3", "python", "ruby", "node", "perl"}


def _strip(command: str) -> str:
    """Remove only the spans where the shell performs no expansion."""
    return SINGLE_QUOTED.sub(" ", QUOTED_HEREDOC.sub(" ", command))


def _referenced_script_path(command: str) -> str | None:
    """The file argument of a plain `<interpreter> <path> [args...]` command.

    Deliberately simple: the first non-flag token after a known interpreter.
    Good enough to catch `sh tmp/thing.sh` -- anything cleverer ($(...), a
    pipe, chaining) is already refused by guard-unanalyzable-bash.py before
    this hook would need to reason about it.
    """
    parts = command.split()
    if not parts:
        return None
    interpreter = parts[0].rsplit("/", 1)[-1]
    if interpreter not in _SCRIPT_INTERPRETERS:
        return None
    for token in parts[1:]:
        if not token.startswith("-"):
            return token
    return None


def _read_within_project(path: str) -> str | None:
    """The content of `path` if it names a real file inside the project."""
    project_dir = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    full = os.path.abspath(os.path.join(project_dir, path))
    if os.path.commonpath([project_dir, full]) != project_dir:
        return None                 # outside the project; not this hook's job
    try:
        with open(full, "r", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def _is_secret(name: str) -> bool:
    return bool(SECRET_NAME.match(name))


def _default_expansion_of_a_secret(text: str) -> str | None:
    for match in DEFAULT_EXPANSION.finditer(text):
        if _is_secret(match.group(1)):
            return match.group(1)
    return None


def _echoed_secret(text: str) -> str | None:
    """A secret referenced by an echo/printf, anywhere in a pipeline or list."""
    for segment in re.split(r"[|;&]+|\$\(|\)|`", text):
        words = segment.split()
        if not words:
            continue
        first = words[0].rsplit("/", 1)[-1]
        if first not in PRINTERS:
            continue
        for match in SECRET_REFERENCE.finditer(segment):
            name = match.group(1) or match.group(2)
            if name and _is_secret(name):
                return name
    return None


def _url_embedded_secret(text: str) -> str | None:
    for match in SECRET_IN_URL.finditer(text):
        if _is_secret(match.group(1)):
            return match.group(1)
    return None


def _literal_token(text: str) -> str | None:
    match = LITERAL_TOKEN.search(text)
    return match.group(0) if match else None


def _reason(name: str, form: str) -> str:
    return (
        f"BLOCKED: this command would print the value of `{name}`.\n\n"
        f"{form}\n\n"
        "CLAUDE.md: never print, echo, log or commit the token, and never "
        "test whether it is set with a shell form that expands it. This hook "
        "exists because that written rule was read and then broken three "
        "times across three sessions -- twice the only thing between the "
        "token and the transcript was luck or Helen watching.\n\n"
        "THERE IS NO SAFE PROBE ANY MORE, AND YOU DO NOT NEED ONE. The `+` "
        f"form (`${{{name}:+set}}`) was allowed until 2026-09-09 because it "
        "cannot render the value -- but establishing that took Helen reading "
        "a regex to decide whether a command was safe, which is work a guard "
        "is supposed to remove. An `echo` or `printf` now never mentions a "
        "secret, with no exceptions to remember.\n\n"
        "DON'T ASK WHETHER THE CREDENTIAL IS THERE -- USE IT AND READ THE "
        "RESULT. A 401 or a 403 answers the question exactly, and the value "
        "is never rendered. In Python, `os.environ[\"AGENT_GH_TOKEN\"]` "
        "raises a clear KeyError when it is missing.\n\n"
        f"Using `${{{name}}}` is fine where it is CONSUMED rather than "
        "printed: a credential helper, or `GH_TOKEN=\"$AGENT_GH_TOKEN\" gh "
        "...`, which is CLAUDE.md's documented shape."
    )


def _reason_url(name: str, where: str) -> str:
    return (
        f"BLOCKED: {where} embeds `{name}` in a URL.\n\n"
        "This is the shape that leaked the token on 2026-09-10: "
        f'`https://user:${{{name}}}@host/...` works, but git then stores '
        "that URL -- token included -- as the repo's `origin` remote in "
        "`.git/config`. Every later command that surfaces a remote URL "
        "(`git remote -v`, `git remote show`, `git config -l`, `cat "
        ".git/config`, some git error messages) then prints the token in "
        "plain text. That is exactly what happened: a routine `git remote "
        "-v`, run for the unrelated and legitimate reason MANUAL §2.1 gives, "
        "printed it in full.\n\n"
        "USE THE WRAPPERS INSTEAD. Each one takes a PLAIN url and passes "
        "`scripts/git-credential-agent-token.sh` to git for that one "
        "invocation, so the token is never in a URL and never on disk:\n\n"
        "    sh scripts/git-clone-agent.sh <repo> [dir]\n"
        "    sh scripts/git-fetch-agent.sh <dir> <repo> [ref]\n"
        "    sh scripts/git-push-agent.sh <refspec> [repo] [dir]\n\n"
        "Do NOT `git config credential.helper` it anywhere, and especially "
        "not in this project's own config: that file is shared by every "
        "worktree, git runs a configured helper from each worktree's top "
        "level, and a path that exists on one branch fails on every other "
        "(measured 2026-09-10). Per invocation, from the wrapper, is the "
        "whole interface. Git calls the helper at the moment it needs to "
        "authenticate; the token is read from the environment right there "
        "and handed to git over a pipe, so there is nothing for a later "
        "command to print."
    )


def _reason_literal(token: str, where: str) -> str:
    redacted = token[:8] + "…"
    return (
        f"BLOCKED: {where} contains what looks like a real GitHub token "
        f"(`{redacted}`).\n\n"
        "This is refused regardless of quoting or context -- there is no "
        "legitimate reason for a real token's literal value to appear "
        "anywhere in a command or a script file rather than being read from "
        "`$AGENT_GH_TOKEN` at the point of use. If this value came from a "
        "transcript, a note, or anywhere other than the environment, that is "
        "itself the problem: the token has been exposed and belongs to "
        "Helen to rotate, not to reuse.\n\n"
        "Read it from the environment instead: `${AGENT_GH_TOKEN}` where it "
        "is CONSUMED (a credential helper, `GH_TOKEN=\"$AGENT_GH_TOKEN\" gh "
        "...`), never typed out."
    )


def _deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        return 0
    stripped = _strip(command)

    # The default-expansion and echo/printf probes stay scoped to the literal
    # Bash command text -- see the module docstring's 2026-09-10 addition for
    # why a referenced script's own printf is a different question.
    name = _default_expansion_of_a_secret(stripped)
    if name:
        form = (
            f"`${{{name}:-...}}` and its siblings (`:=`, `-`, `=`) evaluate to "
            f"the VARIABLE'S OWN VALUE whenever it is set. The fallback only "
            f"appears when it is unset -- so the case you were testing for is "
            f"exactly the case that leaks."
        )
        return _deny(_reason(name, form))

    name = _echoed_secret(stripped)
    if name:
        form = (
            "There is no version of printing a secret that is wanted. Note "
            "that DOUBLE quotes do not help: the shell expands `$VAR` inside "
            "them."
        )
        return _deny(_reason(name, form))

    # The URL-embedding and literal-token checks run against the command text
    # AND, if this command runs one, the referenced script's own content --
    # closing the gap where the risky text was moved into a file specifically
    # to get past a different guard's complaint about the command line.
    try:
        found_via = [("this command", command)]
        script_path = _referenced_script_path(command)
        if script_path:
            content = _read_within_project(script_path)
            if content is not None:
                found_via.append((f"`{script_path}`", content))
    except Exception:
        found_via = [("this command", command)]  # a guard must not break itself

    for where, text in found_via:
        name = _url_embedded_secret(text)
        if name:
            return _deny(_reason_url(name, where))
        token = _literal_token(text)
        if token:
            return _deny(_reason_literal(token, where))

    return 0


if __name__ == "__main__":
    sys.exit(main())
