#!/usr/bin/env python3
"""Tell a starting session where it actually is, before it assumes.

WHY THIS EXISTS. Helen, 2026-09-21, of a list of devops suggestions:
*"Yes please let's do this."* Every other hook in this directory REFUSES
something. Not one of them ever told a session a fact. That asymmetry is the
gap this fills, and `CLAUDE.md` had been compensating for it with prose:

    So the question the check answers is not only "am I on `main`" but "am I
    still where I left off" -- and the answer can be no even when nothing you
    did changed it.

That paragraph exists because `/workspace` is a bind mount of Helen's checkout,
so another session -- or Helen -- switching branch moves the ground under a
running Claude with no signal at all. Prose can only ask a session to remember
to look. A SessionStart hook makes looking unnecessary: the facts are simply
there, in the first thing the session reads.

WHAT IT REPORTS, and every line is something a session has got wrong before:

  * THE BRANCH, and whether it is `main`. Commits landed on `main` three times
    (2026-08-18 twice, 2026-08-20) before `guard-main-branch.py` existed.
  * WHETHER THE TREE IS DIRTY, and how many files. An uncommitted edit rode
    into somebody else's branch on 2026-09-08 because nobody looked.
  * POSITION AGAINST `origin/main`, as last fetched. Not a network call --
    see below.
  * WHETHER THE TWO PRIVATE DRAFTS CLONES ARE PRESENT, with the exact commands
    when they are not. A bare worktree collects 10,660 tests where a complete
    one collects 30,901, and the skip count FALLS, because most of the missing
    checks are parametrised per file and are never created at all. That green
    is true of what it scanned and silent about what it never opened -- the
    failure mode `conftest.py`'s DRAFTS_PRESENT already fights on one front.

IT MAKES NO NETWORK CALL AND RUNS NO FETCH, deliberately. A hook that waits on
GitHub delays every session start by however long the network takes today, and
a hook that is slow is one Helen turns off. `origin/main` is read as it stands
on disk, and the line says "as last fetched" rather than pretending to be
current. `sh scripts/git-fetch-main.sh` is the session's job, not this hook's.

IT NEVER BLOCKS AND NEVER FAILS LOUDLY. Every git call is wrapped; anything
that goes wrong degrades to a line saying so, because a broken status report
must not stop a session starting. `SessionStart` has no permission decision to
make, so there is nothing here that can refuse anything.

BOTH AUDIENCES GET IT. `additionalContext` puts the facts into the model's
context, which is the point -- the session KNOWS where it is rather than having
to ask. `systemMessage` shows Helen the same thing, so she can see at a glance
that a session started somewhere she did not expect.

Invoked as `python3 .claude/hooks/session-ground-truth.py` so it needs no
execute bit -- `CLAUDE.md` forbids changing file permissions without asking.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# WHICH REPOSITORY IS THIS ABOUT? -- fixed 2026-09-24, and it reported the WRONG
# ONE on its first real outing, which is worse than reporting nothing.
#
# It used to be `Path(__file__).resolve().parent.parent.parent`, i.e. "the
# checkout this script was loaded from". Claude Code invokes the hook as
# `$CLAUDE_PROJECT_DIR/.claude/hooks/session-ground-truth.py`, and in a worktree
# session $CLAUDE_PROJECT_DIR is the PRIMARY clone -- so the hook opened a
# session in `.claude/worktrees/opus-improve-devops` by announcing
# `branch: main`, `1 uncommitted change`, `13 behind`. Every word was true of
# `/workspace` and none of it was true of the session. The session then read its
# own hook and nearly acted on it.
#
# This is the `--show-toplevel` bug of DECISIONS §1 arriving from the other
# side: `run.sh` needed the primary clone and was getting the worktree; this
# needed the worktree and was getting the primary.
#
# TWO CHANGES, and the second is the one that makes a future mistake survivable.
# It now prefers the hook payload's own `cwd`, then the process's, and only then
# falls back to its own location -- and it asks git for `--show-toplevel` from
# there, so the answer is whatever git itself would use. And it PRINTS THE PATH
# in the first line. A fact with no subject attached is what made this
# misleading rather than merely wrong.
_FALLBACK_ROOT = Path(__file__).resolve().parent.parent.parent

# The two private drafts repos, and the wrapper that clones each. Helen's
# standing grant, 2026-09-21: clone them into a fresh worktree whenever you
# want them, no ask, because cloning is reading.
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
    then this file's location. The first two are where the SESSION is; the third
    is only where this SCRIPT is, which in a worktree is the primary clone and
    is what made the first version report someone else's branch.

    Each candidate is confirmed by asking git for `--show-toplevel` from it, so
    the returned path is the one git itself would act on rather than a guess.
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
        # THE PATH IS THE FIRST THING PRINTED, and that is the fix for the
        # 2026-09-24 bug rather than a nicety: the old report stated a
        # branch with no subject, so a reader had no way to notice it
        # described a different checkout.
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
