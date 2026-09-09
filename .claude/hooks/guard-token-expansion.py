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

  * `${TOK}` or `$TOK` anywhere that is not an echo -- passing it to a
    credential helper, or to `GH_TOKEN="$AGENT_GH_TOKEN" gh pr create`, is the
    documented way to use it (CLAUDE.md, git workflow step 1a).
  * The whole thing inside SINGLE quotes, so prose and commit messages may
    discuss these forms. See the stripping note below, which is where this
    hook differs from its siblings.

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


def _strip(command: str) -> str:
    """Remove only the spans where the shell performs no expansion."""
    return SINGLE_QUOTED.sub(" ", QUOTED_HEREDOC.sub(" ", command))


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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    stripped = _strip(command)

    name = _default_expansion_of_a_secret(stripped)
    if name:
        form = (
            f"`${{{name}:-...}}` and its siblings (`:=`, `-`, `=`) evaluate to "
            f"the VARIABLE'S OWN VALUE whenever it is set. The fallback only "
            f"appears when it is unset -- so the case you were testing for is "
            f"exactly the case that leaks."
        )
    else:
        name = _echoed_secret(stripped)
        if not name:
            return 0
        form = (
            "There is no version of printing a secret that is wanted. Note "
            "that DOUBLE quotes do not help: the shell expands `$VAR` inside "
            "them."
        )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": _reason(name, form),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
