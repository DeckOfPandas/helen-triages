#!/usr/bin/env python3
"""Block the destructive git commands, but only when there is something to lose.

WHY THIS EXISTS, AND WHY IT IS CODE RATHER THAN A SENTENCE IN CLAUDE.md.
CLAUDE.md has said "NEVER run `git reset --hard` (or `git checkout --` /
`git restore` over a dirty tree, or `git clean -fd`) without asking me first,
every single time" since 2026-08-18, when one of those commands destroyed a
half-finished handover edit. On 2026-08-19 an agent that had read that rule ran
`git checkout -- <two files> 2>/dev/null || true` anyway, to undo an edit it had
just made itself, and discarded work in the process.

So the rule is not the problem. A rule an agent reads and then breaks needs
enforcement, not rewording -- which is the same conclusion this repository
already reached about `meta.awaiting_fix` and `meta.proofread`, both of which
were documented long before anything checked them.

WHAT IT DOES NOT DO, deliberately:

  - It does not block on a CLEAN tree. `git checkout -- x` with nothing
    uncommitted is a no-op, and a guard that fires on harmless invocations
    teaches whoever meets it to route around the guard rather than to think.
    The dangerous thing is the combination, so the combination is what is
    checked.
  - It does not block `git stash`, which is the reversible answer, or
    `git restore --staged` on its own, which only unstages and leaves the
    working tree untouched.
  - It cannot see a `cd` earlier in the command line: it asks git about the
    directory the hook itself runs in. A command that changes directory first
    may be judged against the wrong repository. Accepted -- the common case is
    the one that bit, and a wrong-but-loud block is recoverable in a way that a
    silent discard is not.

The reason to prefer this over a `deny` entry in permissions is that a deny
pattern is a prefix match on the command string, and the command that got past
the written rule was `git checkout -- a b 2>/dev/null || true`: a compound line
with redirection and a fallback. This reads the whole command, and asks git
whether anything would actually be lost.

Invoked as `python3 .claude/hooks/guard-destructive-git.py` so it needs no
execute bit -- CLAUDE.md forbids changing file permissions without asking, and a
hook that requires a chmod to install would be self-defeating.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

# Each entry: (compiled pattern, how to name the command in the refusal).
#
# `[^|;&]*?` keeps a match inside ONE command of a compound line, so
# `git log && git checkout -- x` is caught on its second clause and
# `echo "git reset --hard"` is not caught at all.
_GIT = r"\bgit\s+(?:-\S+\s+)*"

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # git checkout -- <paths>   and   git checkout <ref> -- <paths>
    (re.compile(_GIT + r"checkout\b[^|;&]*?\s--\s"), "git checkout -- <paths>"),
    # git checkout .   (same discard, no separator)
    (re.compile(_GIT + r"checkout\s+\.(?:\s|$|[|;&])"), "git checkout ."),
    # git reset --hard
    (re.compile(_GIT + r"reset\b[^|;&]*?\s--hard\b"), "git reset --hard"),
    # git clean -f / -fd / -xfd / --force
    (re.compile(_GIT + r"clean\b[^|;&]*?\s-(?:-force\b|[a-eg-zA-Z]*f)"), "git clean -f"),
]

# git restore is handled separately: `--staged` WITHOUT `--worktree` only
# unstages, which leaves the working tree alone and is recoverable.
RESTORE = re.compile(_GIT + r"restore\b([^|;&]*)")

# Quoted spans are stripped before matching, and this is not a nicety. Commit
# messages and handover notes in this repository quote these commands by name
# constantly -- the entry in CLAUDE.md that this hook enforces contains three of
# them -- so without this, `git commit -m "...git checkout -- ..."` is refused.
# A guard that fires on writing ABOUT a command, rather than running one, is a
# guard people learn to work around, which is worse than no guard.
#
# The cost is that `bash -c "git reset --hard"` slips through. That is deliberate
# evasion rather than the accident this exists to catch, and no amount of regex
# fixes it -- the answer to an agent determined to route around a safety rail is
# not a better rail.
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")

# Heredoc BODIES are stripped too, for the same reason and then some. Found the
# hard way: this hook blocked the very commit that introduced it, because the
# commit message -- written as `git commit -F` from a heredoc, which is the
# house style here for anything longer than a line -- described the commands it
# refuses. Quoted-span stripping does not help, since a heredoc body is not
# quoted; it is data on stdin that merely looks like shell text.
#
# Matches `<<EOF`, `<<'EOF'`, `<<"EOF"` and the `<<-` indented form, and drops
# everything up to a line holding just the delimiter.
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)


def _matched(command: str) -> str | None:
    command = HEREDOC.sub(" ", command)
    command = QUOTED.sub(" ", command)
    for pattern, label in PATTERNS:
        if pattern.search(command):
            return label
    m = RESTORE.search(command)
    if m:
        args = m.group(1)
        staged = "--staged" in args or re.search(r"\s-S\b", args)
        worktree = "--worktree" in args or re.search(r"\s-W\b", args)
        if staged and not worktree:
            return None    # unstages only; the working tree is untouched
        return "git restore"
    return None


def _dirty() -> list[str]:
    """Lines of `git status --porcelain`, or [] if this is not a repo."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0            # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    label = _matched(command)
    if not label:
        return 0

    dirty = _dirty()
    if not dirty:
        return 0            # nothing to lose, so nothing to stop

    shown = "\n  ".join(dirty[:20])
    if len(dirty) > 20:
        shown += f"\n  ... and {len(dirty) - 20} more"

    reason = (
        f"BLOCKED: {label} with {len(dirty)} uncommitted change(s) in the tree.\n\n"
        f"  {shown}\n\n"
        "This discards uncommitted work with no undo and no reflog entry to "
        "recover it from, and it does not distinguish your edits from Helen's -- "
        "she edits this tree while you work. CLAUDE.md: ask first, every single "
        "time, and name what would be lost.\n\n"
        "If you are undoing an edit YOU just made, re-edit the file instead; "
        "reaching for git to revert your own change is what caused this rule to "
        "be written. If something genuinely has to be put aside, `git stash -u` "
        "does it reversibly. If it genuinely has to be destroyed, ask Helen and "
        "let her run it.\n\n"
        "(This hook allows the same command on a clean tree -- it is the "
        "combination that is dangerous, not the command.)"
    )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
