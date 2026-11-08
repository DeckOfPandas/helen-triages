#!/usr/bin/env python3
"""Tell a starting session where it actually is, before it assumes.

A bind-mounted checkout can change branch under a running session with no
signal, so the facts go in the first thing a session reads: the checkout's
path, whether this is the container or the bare host, the branch, uncommitted
changes, the position against `origin/main` as last fetched, how far the
project's kit commit (.claude/kit/kit.lock) is behind the kit clone in tmp/kit,
and which `folder:repo` nested clones in the GitHub config are absent: a test
suite that reads one collects nothing from it, and reports green.

It never waits on the network: a hook that waits on GitHub delays every start.
The one network call, a fetch of tmp/kit, runs detached and serves the next
session. It never blocks; anything that fails degrades to a line saying so.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_FALLBACK_ROOT = Path(__file__).resolve().parent.parent.parent


def _git_in(cwd: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def resolve_root(payload: dict) -> Path:
    """The checkout git itself would act on: the hook's `cwd`, then the
    process cwd, then this file's own checkout."""
    candidates = [Path(str(v)) for v in (payload.get("cwd"), os.getcwd()) if v]
    candidates.append(_FALLBACK_ROOT)
    for candidate in candidates:
        if candidate.is_dir():
            top = _git_in(candidate, "rev-parse", "--show-toplevel")
            if top:
                return Path(top)
    return _FALLBACK_ROOT


def _sandbox_line() -> str:
    if Path("/.dockerenv").exists() or Path("/run/.containerenv").exists():
        return "sandbox: inside the container"
    return ("sandbox: NOT in a container -- this session can see the whole "
            "host. Start it with .devcontainer/run.sh")


def _branch_line(root: Path) -> str:
    branch = _git_in(root, "branch", "--show-current")
    if branch is None:
        return "branch: could not be read"
    if not branch:
        return "branch: DETACHED HEAD -- commit nowhere until this is resolved"
    if branch in ("main", "master"):
        return (f"branch: {branch} -- DO NOT COMMIT OR MERGE HERE. Branch first; "
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
    counts = _git_in(root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
    if counts is None:
        return "vs origin/main: no origin/main ref -- run sh scripts/git-fetch-main.sh"
    try:
        behind, ahead = (int(x) for x in counts.split())
    except ValueError:
        return "vs origin/main: could not be read"
    if not behind and not ahead:
        return "vs origin/main: level (as last fetched)"
    parts = [f"{ahead} ahead"] if ahead else []
    if behind:
        parts.append(f"{behind} behind")
    tail = " -- sh scripts/git-fetch-main.sh, then git merge origin/main" if behind else ""
    return f"vs origin/main: {', '.join(parts)} (as last fetched){tail}"


def _kit_clone(root: Path) -> Path | None:
    """tmp/kit in this checkout, else in the main checkout: a worktree rarely
    has its own."""
    common = _git_in(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    for checkout in (root, Path(common).parent if common else None):
        if checkout and (checkout / "tmp" / "kit" / ".git").exists():
            return checkout
    return None


def _refresh_in_background(checkout: Path, repo: str) -> None:
    """Fetches the kit clone's main without waiting, so the next session's
    count is current. Offline it fails silently; it never moves HEAD."""
    try:
        subprocess.Popen(
            ["sh", "scripts/git-fetch-agent.sh", "tmp/kit", repo, "main", "--keep-head"],
            cwd=checkout, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
        )
    except OSError:
        pass


def _kit_line(root: Path) -> str:
    if (root / "kit" / "manifest").is_file():
        return "kit: this repo is the kit"
    try:
        lock = json.loads((root / ".claude" / "kit" / "kit.lock").read_text(encoding="utf-8"))
        commit, repo = str(lock["kit_commit"]), str(lock.get("kit_repo", ""))
    except (OSError, ValueError, KeyError, TypeError):
        return "kit: no readable .claude/kit/kit.lock -- never synced? /kit-sync"
    checkout = _kit_clone(root)
    if checkout is None:
        return f"kit: synced at {commit[:12]}; no tmp/kit clone to compare with -- /kit-sync clones one"
    if repo:
        _refresh_in_background(checkout, repo)
    behind = _git_in(checkout / "tmp" / "kit", "rev-list", "--count", f"{commit}..origin/main")
    if behind is None:
        return f"kit: synced at {commit[:12]}, which tmp/kit's origin/main does not contain"
    if behind == "0":
        return f"kit: up to date (synced at {commit[:12]}; as last fetched)"
    return f"kit: {behind} commits behind (synced at {commit[:12]}; as last fetched) -- /kit-sync"


def _github_conf(root: Path) -> dict[str, str]:
    """KEY=value from the GitHub config, found as scripts/_github_conf.sh finds
    it: this checkout's github.local.conf, the main checkout's, then the
    committed github.conf. Values are not validated; the wrappers do that."""
    common = _git_in(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    candidates = [root / "scripts" / "github.local.conf"]
    if common:
        candidates.append(Path(common).parent / "scripts" / "github.local.conf")
    candidates.append(root / "scripts" / "github.conf")
    for path in candidates:
        if path.is_file():
            values = {}
            for line in path.read_text(encoding="utf-8").splitlines():
                key, sep, value = line.split("#", 1)[0].partition("=")
                if sep:
                    values[key.strip()] = value.strip().strip("\"'")
            return values
    return {}


def _nested_lines(root: Path) -> list[str]:
    """One line per absent `folder:repo` clone; nothing when all are present."""
    missing = []
    for entry in _github_conf(root).get("NESTED_DIRS", "").split():
        folder, sep, repo = entry.partition(":")
        if sep and repo and not (root / folder / ".git").exists():
            missing.append((folder, repo))
    if not missing:
        return []
    return ["nested: " + ", ".join(f for f, _ in missing) + " ABSENT. A test run here is NOT "
            "evidence about them: their checks are never collected, so the count falls and "
            "nothing reports missing. Cloning is reading:"] + [
        f"    sh scripts/git-clone-agent.sh {repo} {folder}" for folder, repo in missing]


def main() -> int:
    try:
        raw = sys.stdin.read()
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, ValueError):
            payload = {}
        root = resolve_root(payload if isinstance(payload, dict) else {})
        lines = [_sandbox_line(), _branch_line(root), _dirty_line(root), _position_line(root),
                 _kit_line(root), *_nested_lines(root)]
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
