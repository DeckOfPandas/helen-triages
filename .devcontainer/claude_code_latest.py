"""Print the version npm's `latest` tag names for Claude Code, e.g. `2.1.0`.

run.sh passes it to `docker build` as CLAUDE_CODE_VERSION and labels the image
with it. A concrete number changes the Dockerfile's RUN text exactly when there
is something new; a literal `latest` would be a cache hit forever.

It fails quiet: offline, slow, malformed or not `N.N.N`, it prints a note on
stderr, nothing on stdout, and exits 1, and run.sh keeps the image it has. Only
`N.N.N` is let through, because the value lands in a RUN line and a label.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request

URL = "https://registry.npmjs.org/@anthropic-ai/claude-code/latest"
TIMEOUT_SECONDS = 5
PLAIN_VERSION = re.compile(r"\d+\.\d+\.\d+")


def parse_version(body: bytes) -> str | None:
    """The `version` field of a registry answer, or None if it is not N.N.N."""
    try:
        version = json.loads(body)["version"]
    except (ValueError, KeyError, TypeError):
        return None
    if isinstance(version, str) and PLAIN_VERSION.fullmatch(version):
        return version
    return None


def latest_version(url: str = URL, timeout: float = TIMEOUT_SECONDS) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return parse_version(response.read())
    except (OSError, ValueError):       # URLError and timeouts are both OSError
        return None


if __name__ == "__main__":
    found = latest_version()
    if found is None:
        print("claude_code_latest.py: could not read the latest Claude Code "
              "version from npm, so the image keeps the one it has.",
              file=sys.stderr)
        sys.exit(1)
    print(found)
