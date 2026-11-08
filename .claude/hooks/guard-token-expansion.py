#!/usr/bin/env python3
"""Refuse a Bash command that would put a secret where it can be read.

To learn whether a credential is there, use it and read the 401 or 403;
nothing ever needs to print one.

Refused:
  1. `${TOK:-x}`, `${TOK:=x}`, `${TOK-x}`, `${TOK=x}` on a secret: each
     evaluates to the value itself when it is set.
  2. Any reference to a secret in an `echo` or `printf`, in any segment of a
     pipeline or list, `${TOK:+set}` and `${#TOK}` included.
  3. `gh` (bare or through scripts/gh-*.sh) with `env` or `$ENV` anywhere:
     gh's jq reads the process environment, where gh-agent.sh puts the token.
  4. A secret in a URL's userinfo (`https://u:$TOK@host`): git stores the
     URL in .git/config and `git remote -v` prints it.
  5. A literal GitHub token, whatever the quoting.
  6. Dumping the environment: `printenv`, a bare `env`, `/proc/*/environ`.

Checks 4 and 5 also read a script the command runs (`sh x`, `python3 x`, ...),
since every guard here says to move a refused command into a file. Single
quotes and quoted-delimiter heredocs are exempt from 1 and 2, so prose may
discuss those forms.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import os
import re
import sys

# A short, high-signal list rather than anything containing "key":
# `$SSH_KEY_PATH` is a path, not a secret.
SECRET_NAME = re.compile(r"^(.*_)?(TOKEN|SECRET|PASSWORD|PASSWD)$")
DEFAULT_EXPANSION = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\s*:?[-=]")
SECRET_REFERENCE = re.compile(
    r"""\$(?:
          \{ \#? \s* ([A-Za-z_][A-Za-z0-9_]*) [^}]* \}
        | ([A-Za-z_][A-Za-z0-9_]*)
        )""",
    re.VERBOSE,
)
PRINTERS = ("echo", "printf")

# SINGLE quotes only: the shell expands `$VAR` inside double quotes.
SINGLE_QUOTED = re.compile(r"'[^']*'")
QUOTED_HEREDOC = re.compile(
    r"<<-?\s*(['\"])([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)
SECRET_IN_URL = re.compile(
    r"://[^\s/@'\"]*:\s*\$?\{?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}?\s*@"
)
# The 20-character floor clears an example in prose ("a ghp_ token").
LITERAL_TOKEN = re.compile(
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}\b"
)
GH_CALL = re.compile(r"(?:^|\s)(?:\S*/)?(?:gh|gh-agent\.sh|gh-read\.sh)(?:\s|$)")
JQ_ENV = re.compile(r"\$ENV\b|(?<![\w.$-])env\b")
PROC_ENVIRON = re.compile(r"/proc/[^\s/]+/environ")
SEGMENT_SPLIT = re.compile(r"[|;&]+|\$\(|\)|`")
_SCRIPT_INTERPRETERS = {"sh", "bash", "python3", "python", "ruby", "node", "perl"}


def _strip(command: str) -> str:
    return SINGLE_QUOTED.sub(" ", QUOTED_HEREDOC.sub(" ", command))


def _is_secret(name: str) -> bool:
    return bool(SECRET_NAME.match(name))


def _default_expansion_of_a_secret(text: str) -> str | None:
    for match in DEFAULT_EXPANSION.finditer(text):
        if _is_secret(match.group(1)):
            return match.group(1)
    return None


def _echoed_secret(text: str) -> str | None:
    for segment in SEGMENT_SPLIT.split(text):
        words = segment.split()
        if not words or words[0].rsplit("/", 1)[-1] not in PRINTERS:
            continue
        for match in SECRET_REFERENCE.finditer(segment):
            name = match.group(1) or match.group(2)
            if name and _is_secret(name):
                return name
    return None


def _dumps_environment(text: str) -> bool:
    if PROC_ENVIRON.search(text):
        return True
    for segment in SEGMENT_SPLIT.split(text):
        words = segment.split()
        if not words:
            continue
        first = words[0].rsplit("/", 1)[-1]
        if first == "printenv":
            return True
        # `env` with nothing after it but flags prints everything; `env X=1 cmd`
        # runs a command and is left alone.
        if first == "env" and all(w.startswith("-") for w in words[1:]):
            return True
    return False


def _referenced_script_path(command: str) -> str | None:
    parts = command.split()
    if not parts or parts[0].rsplit("/", 1)[-1] not in _SCRIPT_INTERPRETERS:
        return None
    for token in parts[1:]:
        if not token.startswith("-"):
            return token
    return None


def _read_within_project(path: str) -> str | None:
    project_dir = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    full = os.path.abspath(os.path.join(project_dir, path))
    if os.path.commonpath([project_dir, full]) != project_dir:
        return None
    try:
        with open(full, "r", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def _deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


USE_IT_INSTEAD = (
    "Don't ask whether the credential is there: use it and read the result. "
    "A 401 or 403 answers exactly, and the value is never rendered. "
    "`${NAME}` is fine where it is CONSUMED rather than printed, as in "
    "scripts/gh-agent.sh."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        return 0
    stripped = _strip(command)

    name = _default_expansion_of_a_secret(stripped)
    if name:
        return _deny(
            f"BLOCKED: `${{{name}:-...}}` and its siblings evaluate to the "
            "variable's own value whenever it is set, so the case being tested "
            f"for is exactly the case that leaks.\n\n{USE_IT_INSTEAD}"
        )

    name = _echoed_secret(stripped)
    if name:
        return _deny(
            f"BLOCKED: an echo or printf mentions `{name}`. No form of printing "
            "a secret is wanted, and double quotes do not help: the shell "
            f"expands `$VAR` inside them.\n\n{USE_IT_INSTEAD}"
        )

    if GH_CALL.search(command) and JQ_ENV.search(command):
        return _deny(
            "BLOCKED: this runs gh with `env` or `$ENV` in it. gh's jq can read "
            "the process environment, where scripts/gh-agent.sh puts the token. "
            "Select the fields you need from the API's JSON instead."
        )

    if _dumps_environment(stripped):
        return _deny(
            "BLOCKED: this prints the process environment, which holds "
            "AGENT_GH_TOKEN. Ask for the one variable you need by name, and "
            "never a secret's."
        )

    found_via = [("this command", command)]
    try:
        script_path = _referenced_script_path(command)
        if script_path:
            content = _read_within_project(script_path)
            if content is not None:
                found_via.append((f"`{script_path}`", content))
    except Exception:
        pass                                  # a guard must not break itself

    for where, text in found_via:
        for match in SECRET_IN_URL.finditer(text):
            if _is_secret(match.group(1)):
                return _deny(
                    f"BLOCKED: {where} embeds `{match.group(1)}` in a URL. Git "
                    "stores that URL, token included, in .git/config, and "
                    "`git remote -v` then prints it. Use the wrappers, which "
                    "pass a credential helper per invocation:\n\n"
                    "    sh scripts/git-clone-agent.sh <repo> [dir]\n"
                    "    sh scripts/git-fetch-agent.sh <dir> <repo> [ref]\n"
                    "    sh scripts/git-push-agent.sh <refspec> [repo] [dir]"
                )
        token = LITERAL_TOKEN.search(text)
        if token:
            return _deny(
                f"BLOCKED: {where} contains what looks like a real GitHub token "
                f"(`{token.group(0)[:8]}…`). A token's value never belongs in a "
                "command or a file; if it came from anywhere but the "
                "environment, it is exposed and the human should rotate it."
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
