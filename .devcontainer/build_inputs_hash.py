"""Print one sha256 of everything in .devcontainer/ the image is built from.

`run.sh` stamps each image it builds with this and rebuilds when the stamp no
longer matches -- see the long comment there for why the check compares content
and not timestamps.

IN ITS OWN FILE SINCE 2026-09-24 (#1191), for one reason: it is now worth
testing. It used to be a `find | sort | sha256sum` pipeline inline in run.sh,
which nothing could exercise without running the whole container launcher.
`tests/test_devcontainer_hash.py` drives this directly.

PYTHON RATHER THAN SHELL, and not by preference: the shell version wanted a
temporary file to filter, and `mktemp` writes to the system /tmp, which
CLAUDE.md forbids outright. Nothing here writes anywhere at all.

WHAT IT EXCLUDES, and how getting that wrong stays safe. Files named in
`.devcontainer/.dockerignore` are left out, so the hash covers what Docker
actually receives and editing the README or run.sh costs no rebuild. It
understands EXACT FILENAMES ONLY: if any line there carries a `*`, `/`, `!` or
`?`, the WHOLE directory is hashed instead, ignore file included, with a note on
stderr. A half-understood pattern would silently shrink what the stamp covers,
and an image NOT rebuilt when it should be is the bug the stamp exists to
prevent -- so the failure mode is a spurious cached rebuild, never a missed one.

The ignore file is itself always hashed when it is understood: changing what is
excluded changes what the image is built from, so the stamp must move with it.

Run from the repo root (run.sh cd's there first). Prints the hash on stdout and
nothing else, so it can be captured directly.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

CONTEXT = Path(".devcontainer")
# Anything that makes a line more than a plain filename. `?` is included here
# though the hash never globs, because Docker WOULD treat it as a pattern, and
# the point is that the two agree.
NOT_A_PLAIN_NAME = set("*/!?")


def exclusions(context: Path) -> set[str]:
    """Basenames to leave out, or an empty set meaning "hash everything"."""
    ignore = context / ".dockerignore"
    if not ignore.is_file():
        return set()
    names = set()
    for line in ignore.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if set(line) & NOT_A_PLAIN_NAME:
            print(
                f"build_inputs_hash.py: .dockerignore line {line!r} is not a "
                f"plain filename, so the whole of {context}/ is hashed instead.",
                file=sys.stderr,
            )
            return set()
        names.add(line)
    return names


def build_inputs_hash(context: Path = CONTEXT) -> str:
    skip = exclusions(context)
    digest = hashlib.sha256()
    # Sorted by path so the answer does not depend on directory order, and the
    # path goes into the hash as well as the bytes: moving a file to a new name
    # changes what Docker sees, so it must change the stamp.
    for path in sorted(p for p in context.rglob("*") if p.is_file()):
        if path.name in skip and path.parent == context:
            continue
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


if __name__ == "__main__":
    print(build_inputs_hash())
