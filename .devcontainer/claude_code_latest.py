"""Print the version npm's `latest` tag names for Claude Code, e.g. `2.1.0`.

`run.sh` calls this on every launch, passes the answer to `docker build` as
`CLAUDE_CODE_VERSION`, and labels the image with it -- so a new release rebuilds
the image the next time a container starts, and nobody edits a pin by hand.

WHY THE HOST ASKS, RATHER THAN THE DOCKERFILE SAYING `latest`. Docker caches a
`RUN` by its TEXT. `npm install -g ...@latest` reads the same on every build, so
after the first one it is a cache hit forever and "latest" means "whatever was
newest the day this layer was first built". A concrete version number in a build
argument changes the text exactly when there is something new to fetch.

IT FAILS QUIET, ON PURPOSE. Offline, a slow registry, a body that is not JSON, a
version that is not three plain numbers: each prints a line on stderr, nothing
on stdout, and exits 1. `run.sh` reads empty as "could not find out" and keeps
the image it has. Not knowing the newest version must never stop a container
starting.

THE SHAPE CHECK IS A GUARD, NOT TIDINESS. The value lands in a `RUN` line and an
image label, so only `N.N.N` is let through -- a registry answer cannot put
anything else into the build.

Named in `.dockerignore`: the image does not use it, so editing it costs no
rebuild.
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
