#!/usr/bin/env python3
"""Serve tmp/serve (the symlinked local build) on the first free port from 4010.

A port search, not a fixed port, because several sessions run in one
container, each in its own worktree: on one fixed port the second server dies
and its shoot.sh measures the first session's build. Each worktree's server
takes its own port and writes it to that worktree's tmp/browser/port, which
its own shoot.sh and crop.sh read. The file is removed when the server exits,
so a stale one cannot point a later shoot at a dead or foreign port.

Run through `sh scripts/browser/serve.sh`, in the background; the allow rule is
on that exact command.
"""

import functools
import http.server
import os
import sys

FIRST = 4010
LAST = 4059
ROOT = os.path.join(os.getcwd(), "tmp", "serve")
PORT_FILE = os.path.join(os.getcwd(), "tmp", "browser", "port")


def main():
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=ROOT
    )
    server = None
    for port in range(FIRST, LAST + 1):
        try:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
            break
        except OSError:
            continue
    if server is None:
        sys.exit(f"no free port between {FIRST} and {LAST}")

    os.makedirs(os.path.dirname(PORT_FILE), exist_ok=True)
    with open(PORT_FILE, "w", encoding="utf-8") as fh:
        fh.write(f"{port}\n")
    print(f"SERVING http://127.0.0.1:{port}/helen-triages/  (port in {PORT_FILE})",
          flush=True)
    try:
        server.serve_forever()
    finally:
        try:
            os.remove(PORT_FILE)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
