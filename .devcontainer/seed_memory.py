"""Give a project's Claude Code memory the kit's starting notes, once.

The memory lives in the per-project config volume, so a new project starts
with none. This copies each note in .claude/memory-seed/ into the memory
folder unless a file of that name is already there, adds its line from the
seed's MEMORY.md to the index unless the index already names the file, and
leaves a `.kit-seeded` marker. With the marker present it does nothing, so a
note the user deletes stays deleted.

container.bashrc runs it at shell start when the marker is missing. It never
fails the shell: any error is one line on stderr.

USAGE:  python3 seed_memory.py [<seed dir> <memory dir>]

The memory folder's name is the project path with `/` as `-`. Both run.sh and
devcontainer.json open the project at /workspace, hence projects/-workspace.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

SEED = Path("/workspace/.claude/memory-seed")
MARKER = ".kit-seeded"
INDEX = "MEMORY.md"


def default_memory_dir() -> Path:
    config = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(config) / "projects" / "-workspace" / "memory"


def seed(seed_dir: Path, memory_dir: Path) -> list[str]:
    """Copies what is missing; returns the names of the notes copied."""
    if (memory_dir / MARKER).exists() or not seed_dir.is_dir():
        return []
    memory_dir.mkdir(parents=True, exist_ok=True)
    seed_index = seed_dir / INDEX
    lines = seed_index.read_text(encoding="utf-8").splitlines() if seed_index.is_file() else []
    index = memory_dir / INDEX
    existing = index.read_text(encoding="utf-8") if index.is_file() else ""
    copied, new_lines = [], []
    for note in sorted(seed_dir.glob("*.md")):
        if note.name == INDEX:
            continue
        if not (memory_dir / note.name).exists():
            shutil.copyfile(note, memory_dir / note.name)
            copied.append(note.name)
        if f"({note.name})" not in existing:
            new_lines += [line for line in lines if f"({note.name})" in line]
    if new_lines:
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        with index.open("a", encoding="utf-8") as out:
            out.write(prefix + "\n".join(new_lines) + "\n")
    (memory_dir / MARKER).write_text("The kit's memory seed was copied here once.\n", encoding="utf-8")
    return copied


def main() -> int:
    if len(sys.argv) == 3:
        seed_dir, memory_dir = Path(sys.argv[1]), Path(sys.argv[2])
    elif len(sys.argv) == 1:
        seed_dir, memory_dir = SEED, default_memory_dir()
    else:
        print("usage: python3 seed_memory.py [<seed dir> <memory dir>]", file=sys.stderr)
        return 2
    try:
        copied = seed(seed_dir, memory_dir)
    except OSError as e:
        print(f"seed_memory.py: memory not seeded: {e}", file=sys.stderr)
        return 0
    if copied:
        print(f"Claude memory seeded from .claude/memory-seed/: {', '.join(copied)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
