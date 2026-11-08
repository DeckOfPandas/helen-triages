#!/usr/bin/env python3
"""Refuse a burst of GitHub issue or PR creations.

GitHub flags an account that creates many issues or PRs in a short time as
spam, and then hides everything it ever wrote from everyone else. This logs
creations and refuses one within MIN_GAP of the last, or one that would make
more than MAX_ISSUES_PER_DAY issues or MAX_PRS_PER_DAY PRs in 24 hours. The
gap counts issues and PRs together. A command that creates two is refused.

A creation is any of: `scripts/gh-write.sh pr-create` or `issue-create`;
`issue create` or `pr create` through `scripts/gh-agent.sh` or bare `gh`; and
`gh api` with a POST to a repository's `issues` or `pulls` collection.
Comments, labels and PR body edits are not counted.

A creation inside a script the command runs (`sh tmp/x.sh`), other than the
two wrappers above, is refused outright: a script can loop, so the count it
would add is unknowable. A creation is always one direct call, and the
wrappers run without asking.

The log is CREATION_LOG under the Claude Code config directory, so every
session and worktree in the container shares one count, it survives a restart
of the container, and it lies outside the working directory. A creation is
counted when this allows it, before it runs: one that then fails still
counts, which errs towards fewer.

Invoked as `python3 <path>` so it needs no execute bit.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import sys
import time

MIN_GAP = 5 * 60
MAX_ISSUES_PER_DAY = 20
MAX_PRS_PER_DAY = 5
DAY = 24 * 60 * 60
CREATION_LOG = os.path.join("claude-kit", "github-creations.log")

_GH = r"(?:^|[\s/;&|(`])"
CREATIONS = [
    re.compile(r"gh-write\.sh\s+(pr-create|issue-create)\b"),
    re.compile(_GH + r"(?:gh|gh-agent\.sh)\s+(?:-\S+\s+)*(issue|pr)\s+create\b"),
]
GH_API = re.compile(_GH + r"(?:gh|gh-agent\.sh)\s+api\b[^\n;&|]*")
POST = re.compile(r"(?:-X|--method)(?:\s+|=)['\"]?POST\b", re.IGNORECASE)
COLLECTION = re.compile(r"/(issues|pulls)(?![\w/-])")
_SCRIPT_INTERPRETERS = {"sh", "bash", "dash", "python3", "python", "ruby", "node", "perl"}
# The wrappers make one call each, which the command itself names and this
# counts; their source holds the calls they build, which are not creations.
WRAPPERS = {"scripts/gh-write.sh", "scripts/gh-agent.sh"}


def creations_in(text: str) -> list[str]:
    """Each creation call in `text`, named by what it creates."""
    found: list[str] = []
    for pattern in CREATIONS:
        for match in pattern.finditer(text):
            found.append("PR" if match.group(1).startswith("pr") else "issue")
    for call in GH_API.finditer(text):
        segment = call.group(0)
        collection = COLLECTION.search(segment)
        if collection and POST.search(segment):
            found.append("PR" if collection.group(1) == "pulls" else "issue")
    return found


def _referenced_script(command: str) -> str | None:
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


def log_path() -> str:
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    if not config:
        config = os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(config, CREATION_LOG)


def _recent(lines: list[str], now: float) -> list[tuple[float, str]]:
    """The log's entries from the last DAY; an unreadable line is dropped."""
    kept = []
    for line in lines:
        parts = line.split()
        try:
            stamp = float(parts[0])
        except (IndexError, ValueError):
            continue
        if now - DAY < stamp <= now:
            kept.append((stamp, parts[1] if len(parts) > 1 else "?"))
    return kept


def _when(seconds: float) -> str:
    minutes = max(1, int(seconds // 60) + 1)
    if minutes < 90:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return f"{minutes // 60} h {minutes % 60:02d} min"


def _deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


BATCH_ADVICE = (
    "CLAUDE.md: never create issues or PRs in a burst. A batch is ONE issue "
    "with a checklist, and a piece of work is ONE PR."
)
SPAM = (
    "GitHub flags a burst as spam and then hides everything the account ever "
    "wrote."
)


def judge(kinds: list[str], now: float) -> str | None:
    """Count `kinds` against the log; a refusal, or None once recorded."""
    if len(kinds) > 1:
        return (
            f"BLOCKED: this one command creates {len(kinds)} GitHub issues or "
            f"PRs; the limit is one every {MIN_GAP // 60} minutes. {SPAM}\n\n"
            f"{BATCH_ADVICE}\n\nWHAT TO DO NOW: make one creation per call."
        )
    path = log_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        entries = _recent(handle.read().splitlines(), now)
        latest = max((stamp for stamp, _ in entries), default=None)
        if latest is not None and now - latest < MIN_GAP:
            return (
                f"BLOCKED: a GitHub issue or PR was created less than "
                f"{MIN_GAP // 60} minutes ago, and the limit is one every "
                f"{MIN_GAP // 60} minutes. {SPAM}\n\n{BATCH_ADVICE}\n\n"
                "WHAT TO DO NOW: fold this into an issue or PR that already "
                "exists, or wait. The next slot opens in about "
                f"{_when(latest + MIN_GAP - now)}."
            )
        kind = kinds[0]
        limit = MAX_PRS_PER_DAY if kind == "PR" else MAX_ISSUES_PER_DAY
        same = [stamp for stamp, logged in entries if logged == kind]
        if len(same) >= limit:
            return (
                f"BLOCKED: {len(same)} {kind}s have been created on GitHub in "
                f"the last 24 hours, and the limit is {limit}. {SPAM}\n\n"
                f"{BATCH_ADVICE}\n\nWHAT TO DO NOW: tell the human. The next "
                f"{kind} slot opens in about {_when(min(same) + DAY - now)}."
            )
        entries.append((now, kind))
        handle.seek(0)
        handle.truncate()
        handle.write("".join(f"{int(stamp)} {kind}\n" for stamp, kind in entries))
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        return 0

    script = _referenced_script(command)
    if script and os.path.normpath(script) not in WRAPPERS:
        content = _read_within_project(script)
        if content is not None and creations_in(content):
            return _deny(
                f"BLOCKED: `{script}` creates a GitHub issue or PR. A script "
                "can loop, so how many it would create cannot be counted, and "
                "GitHub flags a burst as spam.\n\n"
                f"{BATCH_ADVICE}\n\nWHAT TO DO NOW: make the one creation as a "
                "direct call, such as\n"
                '    sh scripts/gh-write.sh issue-create <repo> "<title>" tmp/<body>.md'
            )

    kinds = creations_in(command)
    if not kinds:
        return 0
    try:
        reason = judge(kinds, time.time())
    except OSError as error:
        return _deny(
            f"BLOCKED: the GitHub creation count in {log_path()} could not be "
            f"read or written ({error}), so this creation cannot be checked "
            "against the burst limit. Tell the human."
        )
    return _deny(reason) if reason else 0


if __name__ == "__main__":
    sys.exit(main())
