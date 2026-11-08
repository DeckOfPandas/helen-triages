"""Print one sha256 of everything the image is built from.

That is every file in the build context except those `.dockerignore` names,
plus the build arguments run.sh passes as this script's one optional argument.
run.sh labels each image with the result and rebuilds when it stops matching:
content, not timestamps, so `touch` costs nothing and reverting an edit returns
to the image that already matches.

`.dockerignore` is read as EXACT FILENAMES ONLY. Any line carrying `*`, `/`,
`!` or `?` makes this hash the whole directory instead, with a note on stderr:
a spurious cached rebuild is harmless, and a missed rebuild is the bug.

USAGE:  python3 build_inputs_hash.py [<build args> [<context dir>]]

The context defaults to .devcontainer, relative to the current directory.
Prints the hash and nothing else on stdout.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

CONTEXT = Path(".devcontainer")
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


def build_inputs_hash(context: Path = CONTEXT, build_args: str = "") -> str:
    skip = exclusions(context)
    digest = hashlib.sha256()
    # Sorted, and the path hashed with the bytes: a rename changes what Docker
    # receives, so it must change the stamp.
    for path in sorted(p for p in context.rglob("*") if p.is_file()):
        if path.name in skip and path.parent == context:
            continue
        digest.update(path.relative_to(context).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    digest.update(b"build-args\0")
    digest.update(build_args.encode("utf-8"))
    return digest.hexdigest()


if __name__ == "__main__":
    print(build_inputs_hash(
        context=Path(sys.argv[2]) if len(sys.argv) > 2 else CONTEXT,
        build_args=sys.argv[1] if len(sys.argv) > 1 else "",
    ))
