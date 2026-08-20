#!/usr/bin/env python3
"""Refuse `git commit` and `git merge` while the current branch is `main`.

WHY THIS EXISTS. CLAUDE.md has said "NEVER commit or merge directly onto main,
for any reason, even a one-line fix" since 2026-08-18, when it happened twice in
one day. It then added a second sentence -- "Check `git branch --show-current`
IMMEDIATELY before every `git commit`. Not at the start of the task -- Helen
merges PRs and checks out main while I am working" -- and on 2026-08-20 an agent
that had read both did it anyway.

The instructive part is HOW it failed, because it was not carelessness. The
agent DID run the check. It ran it in the same shell command as the commit:

    git branch --show-current
    git add ...
    git commit -F ...

so the check printed "main" in the output of the very call that had already
committed. A check that reports a problem after the fact is not a check, it is
a narration. This hook is the same instruction expressed as something that can
actually stop the call, which is the conclusion this repository keeps reaching:
a rule read and broken needs enforcement, not rewording. See
guard-destructive-git.py, meta.awaiting_fix and meta.proofread.

WHICH REPOSITORY IT ASKS ABOUT. The rule covers every repo in the tree, not just
helen-triages -- the nested private drafts repos (_food_drafts/,
_cocktail_drafts/) have their own main and the same rule, and four commits went
onto _cocktail_drafts' main on 2026-08-17 because the rule read as if there were
only one repo. So this does not assume the hook's own directory: it reads any
leading `cd <path>` out of the command and asks git about THAT directory. The
sibling hook documents not doing this as an accepted limitation; here it is the
common case rather than an edge one.

WHAT IT DELIBERATELY ALLOWS:

  - Every other git command on main. Reading, fetching, pulling, branching,
    checking out, pushing an already-made commit. Only the two verbs that write
    history to the branch are refused.
  - `git commit` on any branch that is not main. That is the whole workflow.
  - Any mention of these commands inside a quoted string or a heredoc body, so
    a commit message may discuss them. Commit messages here do that constantly
    -- this file's own introducing commit will.

Invoked as `python3 .claude/hooks/guard-main-branch.py` so it needs no execute
bit: CLAUDE.md forbids changing file permissions without asking, and a hook that
required a chmod to install would be self-defeating.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

# `git commit` and `git merge`, allowing for global flags like `git -C x commit`.
_GIT = r"\bgit\s+(?:-\S+\s+\S*\s*)*"
WRITES_HISTORY = re.compile(_GIT + r"(commit|merge)\b")

# Same stripping as guard-destructive-git.py, and for the same reason: a guard
# that fires on WRITING ABOUT a command rather than running one is a guard
# people learn to route around.
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)

# A leading `cd <path>` -- the command may be operating on a nested repo.
CD = re.compile(r"\bcd\s+([^\s;&|]+)")

PROTECTED = {"main", "master"}


def _strip(command: str) -> str:
    return QUOTED.sub(" ", HEREDOC.sub(" ", command))


def _repo_dir(command: str) -> pathlib.Path:
    """The directory git will actually run in: any `cd` target, else cwd."""
    match = CD.search(command)
    if not match:
        return pathlib.Path.cwd()
    try:
        target = pathlib.Path(match.group(1).strip("\"'")).expanduser()
        if not target.is_absolute():
            target = pathlib.Path.cwd() / target
        return target if target.is_dir() else pathlib.Path.cwd()
    except (OSError, ValueError):
        return pathlib.Path.cwd()


def _current_branch(directory: pathlib.Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=directory, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0                    # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""
    stripped = _strip(command)

    match = WRITES_HISTORY.search(stripped)
    if not match:
        return 0

    directory = _repo_dir(stripped)
    branch = _current_branch(directory)
    if branch is None or branch not in PROTECTED:
        return 0                    # not a repo, detached, or a working branch

    verb = match.group(1)
    where = directory if directory != pathlib.Path.cwd() else pathlib.Path.cwd()

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED: `git {verb}` while on `{branch}` in {where}.\n\n"
                "CLAUDE.md: never commit or merge directly onto main, in ANY "
                "repo in this tree -- including the nested private drafts "
                "repos, which have their own main and the same rule.\n\n"
                "The workflow: work happens on a branch, Helen opens the PR, "
                "reviews and merges it, then pulls main. `main` only ever moves "
                "via a pulled merge.\n\n"
                "WHAT TO DO NOW:\n"
                f"  git checkout -b <branch>     # in {where}\n"
                "then re-run the commit. Nothing is staged or lost -- this "
                "refused the call before it ran, so your index is exactly as "
                "you left it.\n\n"
                "If you have ALREADY committed to main in an earlier call, do "
                "not try to fix it by force-pushing a shared branch. Say so and "
                "let Helen choose.\n\n"
                "(This exists because the written rule was read and broken on "
                "2026-08-20 by an agent that ran `git branch --show-current` in "
                "the same shell command as the commit -- so the check printed "
                "'main' in the output of the call that had already committed. A "
                "check that cannot gate is a narration.)"
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
