"""Print AGENT_GH_TOKEN from .claude/settings.local.json, or nothing.

run.sh captures the output for the one `docker run` it makes and never echoes
it. A missing file, bad JSON or a missing key all print nothing and exit 0: the
GitHub wrappers are optional, and their absence must not stop a container.

Run from the repo root.
"""
from __future__ import annotations

import json
from pathlib import Path

SETTINGS = Path(".claude/settings.local.json")


def local_token(path: Path = SETTINGS) -> str:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))["env"]["AGENT_GH_TOKEN"]
    except (OSError, ValueError, KeyError, TypeError):
        return ""
    return value if isinstance(value, str) else ""


if __name__ == "__main__":
    token = local_token()
    if token:
        print(token)
