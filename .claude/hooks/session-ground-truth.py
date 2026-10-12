#!/usr/bin/env python3
"""Tell a starting session where it actually is, before it assumes.

`/workspace` is a bind mount of Helen's checkout, so another session, or
Helen, switching branch moves the ground under a running Claude with no
signal. A SessionStart hook puts the facts in the first thing a session reads.

It reports the checkout's path, then: the branch, and whether it is `main` or
detached; how many uncommitted changes are already there; the position against
`origin/main` as last fetched; and whether the two private drafts clones are
present, with the command that clones each absent one, since without them most
of the suite is never collected and a green run says nothing about them.

It makes no network call and runs no fetch: a hook that waits on GitHub delays
every session start. `origin/main` is read as it stands on disk.

It never blocks and never fails loudly: every git call is wrapped, and anything
that goes wrong degrades to a line saying so.

`additionalContext` gives the report to the model; `systemMessage` shows Helen
the same text.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# The checkout this FILE was loaded from, which is not the session's: Claude
# Code invokes the hook from $CLAUDE_PROJECT_DIR, and in a worktree session
# that is the primary clone. So it is only resolve_root's last resort.
_FALLBACK_ROOT = Path(__file__).resolve().parent.parent.parent

# The two private drafts repos, as (folder, repository).
DRAFTS = [
    ("_cocktail_drafts", "helen-triages-cocktails-private"),
    ("_food_drafts", "helen-triages-food-private"),
]


def _git_in(cwd: Path, *args: str) -> str | None:
    """A git command's stdout, or None if it failed for any reason at all."""
    try:
        done = subprocess.run(
            ["git", *args], cwd=cwd,
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def resolve_root(payload: dict) -> Path:
    """The checkout this session is actually working in.

    In order of trust: the `cwd` the hook was handed, the process's own cwd,
    then this file's location, which in a worktree session is the primary
    clone. Each candidate is confirmed by asking git for `--show-toplevel`
    from it, so the returned path is the one git itself would act on.
    """
    candidates = []
    for value in (payload.get("cwd"), os.getcwd()):
        if value:
            candidates.append(Path(str(value)))
    candidates.append(_FALLBACK_ROOT)
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        top = _git_in(candidate, "rev-parse", "--show-toplevel")
        if top:
            return Path(top)
    return _FALLBACK_ROOT


def _branch_line(root: Path) -> str:
    branch = _git_in(root, "branch", "--show-current")
    if branch is None:
        return "branch: could not be read"
    if not branch:
        return "branch: DETACHED HEAD -- commit nowhere until this is resolved"
    if branch == "main":
        return ("branch: main -- DO NOT COMMIT OR MERGE HERE. Branch first; "
                "guard-main-branch.py will refuse you otherwise")
    return f"branch: {branch}"


def _dirty_line(root: Path) -> str:
    status = _git_in(root, "status", "--porcelain")
    if status is None:
        return "tree: could not be read"
    if not status:
        return "tree: clean"
    n = len(status.splitlines())
    return f"tree: {n} uncommitted change{'s' if n != 1 else ''} already here"


def _position_line(root: Path) -> str:
    """How this branch sits against origin/main AS LAST FETCHED."""
    counts = _git_in(root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
    if counts is None:
        return "vs origin/main: no origin/main ref -- run sh scripts/git-fetch-main.sh"
    try:
        behind, ahead = (int(x) for x in counts.split())
    except ValueError:
        return "vs origin/main: could not be read"
    if not behind and not ahead:
        return "vs origin/main: level (as last fetched)"
    parts = []
    if ahead:
        parts.append(f"{ahead} ahead")
    if behind:
        parts.append(f"{behind} behind")
    tail = ("" if not behind else
            " -- sh scripts/git-fetch-main.sh, then git merge origin/main")
    return f"vs origin/main: {', '.join(parts)} (as last fetched){tail}"


def _drafts_lines(root: Path) -> list[str]:
    missing = [(d, repo) for d, repo in DRAFTS if not (root / d).is_dir()]
    if not missing:
        return ["drafts: both private clones present -- the suite is complete"]
    out = [
        "drafts: " + ", ".join(d for d, _ in missing) + " ABSENT. A pytest run "
        "here is NOT evidence about them: it collects far fewer tests and the "
        "skip count FALLS, because the missing checks are never created rather "
        "than skipped. Cloning is reading, and needs no ask:"
    ]
    out += [f"    sh scripts/git-clone-agent.sh {repo} {d}" for d, repo in missing]
    return out


def main() -> int:
    try:
        payload = {}
        raw = sys.stdin.read()
        if raw.strip():
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                payload = {}
        root = resolve_root(payload if isinstance(payload, dict) else {})
        lines = [_branch_line(root), _dirty_line(root), _position_line(root)]
        lines += _drafts_lines(root)
        # The path comes first: a branch reported with no subject cannot be
        # told from a report about a different checkout.
        report = f"Where this session actually is -- {root}:\n" + "\n".join(
            f"  {line}" for line in lines
        )
    except Exception as exc:                 # never stop a session starting
        report = f"Ground-truth hook failed harmlessly: {exc!r}"

    print(json.dumps({
        "systemMessage": report,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": report,
        },
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
