#!/usr/bin/env python3
"""Warn a session that started where the project's rules and hooks don't load.

Claude Code reads a project's .claude/settings.json (every guard hook) from the
git repository the session starts in, and follows CLAUDE.md's @-imports only
inside it. A session started in a nested clone under /workspace therefore gets
none of the guards and only part of the rules. This hook is wired in the
image's managed settings, so it runs in every session in the container,
wherever it starts, and the project cannot switch it off.

Quiet when the session's repository is the project root or one of its
worktrees under .claude/worktrees/. Never blocks; a failure prints nothing.

USAGE:  python3 session-place.py <project root>     (SessionStart payload on stdin)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def toplevel(cwd: Path) -> Path | None:
    try:
        done = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd,
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(done.stdout.strip()) if done.returncode == 0 else None


def warning(cwd: Path, root: Path) -> str | None:
    cwd, root = cwd.resolve(), root.resolve()
    if cwd != root and root not in cwd.parents:
        return (f"WARNING: this session started in {cwd}, outside the project at {root}. "
                "The project's rules and guard hooks do not apply here. Tell the user "
                f"before doing anything else, and suggest restarting claude in {root}.")
    top = toplevel(cwd)
    if top is None:
        return None
    top = top.resolve()
    if top == root or top.parent == root / ".claude" / "worktrees":
        return None
    return (f"WARNING: this session started in {top}, a separate git repository inside "
            f"the project (a nested clone). The project's .claude/settings.json hooks -- "
            f"every guard -- do not run here, and CLAUDE.md's imported kit rules do not "
            f"load. Tell the user before doing anything else, and suggest restarting "
            f"claude in {root} or one of its worktrees.")


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 2:
            return 0
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        cwd = Path(str(payload.get("cwd") or os.getcwd())) if isinstance(payload, dict) else Path.cwd()
        message = warning(cwd, Path(argv[1]))
    except Exception:                        # never stop a session starting
        return 0
    if message:
        print(json.dumps({
            "systemMessage": message,
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": message},
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
