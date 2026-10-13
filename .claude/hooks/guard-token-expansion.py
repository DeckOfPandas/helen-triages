#!/usr/bin/env python3
"""Refuse a Bash command that would put a secret where it can be read.

An `echo` or `printf` never mentions a secret, with no exceptions for a human
to verify; to learn whether a credential is there, use it and read the 401 or
403. DECISIONS §11.

Refused:

  1. The default-value expansions of a secret, `${TOK:-x}`, `${TOK:=x}`,
     `${TOK-x}`, `${TOK=x}`: each evaluates to the variable's own value when
     it is set, which is the case a probe is asking about.
  2. Any reference to a secret in an `echo` or `printf`, in any segment of a
     pipeline or list: `$TOK`, `${TOK}`, and also `${TOK:+set}` and `${#TOK}`,
     which cannot render the value but look like a leak to a reader.
  3. A command that runs `gh` (bare, by path, or through `gh-agent.sh` or
     `gh-read.sh`) and mentions `env` or `$ENV`: gh's built-in jq reads the
     process environment, and `scripts/gh-agent.sh` hands gh the token there
     as `GH_TOKEN`. Matched on the raw text, since a jq expression is
     single-quoted.
  4. A secret in a URL's userinfo (`scheme://user:$TOK@host`), whatever the
     quoting: git stores a clone's URL in `.git/config`, and `git remote -v`
     then prints it. The git wrappers pass
     `scripts/git-credential-agent-token.sh` per invocation instead.
  5. A literal GitHub token (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`,
     `github_pat_`), whatever the quoting.

Checks 4 and 5 also run on the content of a script the command runs (`sh`,
`bash`, `python`, `python3`, `ruby`, `node` or `perl`, and a file inside the
project), because every guard here says to move a refused command into a file.
Checks 1 to 3 read the command text only: a script's own `printf` of the token
is not flagged, since the credential helper must write it to git's pipe.

Allowed on purpose: `$TOK` or `${TOK}` where the value is consumed rather than
printed, and, for checks 1 and 2, anything inside SINGLE quotes or a heredoc
with a quoted delimiter, so prose may discuss those forms.

The stripping differs from `guard-sed.py`, which also strips double-quoted
spans: that is right for a command name and wrong for an expansion, because
the shell expands `$VAR` inside double quotes.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import os
import re
import sys

# Which names count as a secret. A short, high-signal list rather than anything
# containing "key": `$SSH_KEY_PATH` is a path, not a secret. `GH_TOKEN` matches
# as well as `AGENT_GH_TOKEN`: it is the variable `gh` reads, which
# scripts/gh-agent.sh sets.
SECRET_NAME = re.compile(r"^(.*_)?(TOKEN|SECRET|PASSWORD|PASSWD)$")

# `${NAME:-`, `${NAME:=`, `${NAME-`, `${NAME=` -- the four expansions that
# evaluate to the variable's own value when it is set. `:+`, `+` and `:?` are
# deliberately absent: none of them can emit the value.
DEFAULT_EXPANSION = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\s*:?[-=]")

# Any reference to a secret's name, for the echo check: `$NAME`,
# `${NAME<anything>}` (the `:+`, `+`, `:?` and `?` forms included) and
# `${#NAME}`. The test is "does an echo mention a secret", not "can this leak".
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

# A secret in a URL's userinfo, `scheme://user:PASS@`. Run on the raw text, not
# the quote-stripped text: a single-quoted URL would not expand, but the shape
# is what ends up stored in `.git/config`, and nothing needs to write it.
SECRET_IN_URL = re.compile(
    r"://[^\s/@'\"]*:\s*\$?\{?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}?\s*@"
)

# A real GitHub token, by its prefix: classic PAT (ghp_), OAuth (gho_), an app's
# installation or user token (ghu_/ghs_), a refresh token (ghr_), a fine-grained
# PAT (github_pat_). The floor of 20 characters clears an example in prose
# ("a ghp_-prefixed token"). Checked whatever the quoting.
LITERAL_TOKEN = re.compile(
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}\b"
)

# Interpreters whose first non-flag argument is a script file to run. Such a
# command is judged by what the file contains.
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


# A command that runs gh: bare, by path, or through either wrapper in scripts/.
GH_CALL = re.compile(r"(?:^|\s)(?:\S*/)?(?:gh|gh-agent\.sh|gh-read\.sh)(?:\s|$)")

# jq's two doors into the environment, `env` and `$ENV`. Deliberately a word
# match on the RAW command: the expression is always single-quoted, so the
# stripping the echo check uses would blank it out.
JQ_ENV = re.compile(r"\$ENV\b|(?<![\w.$-])env\b")


def _gh_reads_environment(command: str) -> bool:
    return bool(GH_CALL.search(command) and JQ_ENV.search(command))


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

    # The default-expansion and echo checks read the command text only; a
    # referenced script's own printf is the credential helper's business.
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

    if _gh_reads_environment(command):
        return _deny(
            "BLOCKED: this runs gh with a --jq expression that mentions `env` "
            "or `$ENV`.\n\n"
            "gh's built-in jq can read the process environment (measured "
            "2026-09-11: `env | length` printed 38), and scripts/gh-agent.sh "
            "hands gh the token through that environment as GH_TOKEN. So a jq "
            "expression that reads the environment can print the token, "
            "through an allow-listed call, with no echo and no expansion for "
            "any other check to see.\n\n"
            "Select the fields you need from the API's JSON instead; nothing "
            "this repository reads from GitHub lives in the environment."
        )

    # The URL and literal-token checks read the command text and, if the
    # command runs one, the referenced script's content.
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
