""".devcontainer/seed_memory.py gives a new project's memory the kit's notes, once."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def seed_dir(kit_root: Path) -> Path:
    return kit_root / ".claude" / "memory-seed"


def run(kit_root: Path, seed: Path, memory: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["python3", str(kit_root / ".devcontainer" / "seed_memory.py"), str(seed), str(memory)],
                          capture_output=True, text=True, timeout=30)


def notes(seed: Path) -> list[str]:
    return sorted(p.name for p in seed.glob("*.md") if p.name != "MEMORY.md")


def test_every_seed_note_is_well_formed_and_indexed(seed_dir):
    names = notes(seed_dir)
    assert names, "the seed holds no notes"
    index = (seed_dir / "MEMORY.md").read_text()
    for name in names:
        text = (seed_dir / name).read_text()
        front = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        assert front, f"{name} has no frontmatter"
        assert f"name: {name[:-3]}\n" in front.group(1), f"{name}'s name: is not its filename"
        assert "description:" in front.group(1) and "type: " in front.group(1)
        assert index.count(f"({name})") == 1, f"MEMORY.md does not index {name} exactly once"


def test_a_new_memory_gets_every_note_and_the_index(kit_root, seed_dir, tmp_path):
    memory = tmp_path / "memory"
    done = run(kit_root, seed_dir, memory)
    assert done.returncode == 0, done.stderr
    for name in notes(seed_dir):
        assert (memory / name).read_text() == (seed_dir / name).read_text()
        assert name in done.stdout
    assert (memory / "MEMORY.md").read_text() == (seed_dir / "MEMORY.md").read_text()
    assert (memory / ".kit-seeded").is_file()


def test_existing_notes_and_index_lines_are_kept(kit_root, seed_dir, tmp_path):
    memory = tmp_path / "memory"
    memory.mkdir()
    first = notes(seed_dir)[0]
    (memory / first).write_text("the user's own version\n")
    (memory / "MEMORY.md").write_text(f"- [Mine](mine.md) — mine\n- [Theirs]({first}) — edited")
    assert run(kit_root, seed_dir, memory).returncode == 0
    assert (memory / first).read_text() == "the user's own version\n"
    index = (memory / "MEMORY.md").read_text()
    assert index.startswith(f"- [Mine](mine.md) — mine\n- [Theirs]({first}) — edited\n")
    for name in notes(seed_dir):
        assert index.count(f"({name})") == 1


def test_once_marked_a_deleted_note_stays_deleted(kit_root, seed_dir, tmp_path):
    memory = tmp_path / "memory"
    assert run(kit_root, seed_dir, memory).returncode == 0
    gone = notes(seed_dir)[0]
    (memory / gone).unlink()
    done = run(kit_root, seed_dir, memory)
    assert done.returncode == 0 and done.stdout == ""
    assert not (memory / gone).exists()


def test_a_missing_seed_does_nothing(kit_root, tmp_path):
    memory = tmp_path / "memory"
    done = run(kit_root, tmp_path / "no-seed", memory)
    assert done.returncode == 0 and not memory.exists()


def test_an_unwritable_memory_never_fails_the_shell(kit_root, seed_dir, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("")
    done = run(kit_root, seed_dir, blocker / "memory")
    assert done.returncode == 0
    assert "not seeded" in done.stderr


def test_container_bashrc_runs_it_only_without_the_marker(kit_root):
    snippet = (kit_root / ".devcontainer" / "container.bashrc").read_text()
    assert "projects/-workspace/memory/.kit-seeded" in snippet
    assert "python3 /workspace/.devcontainer/seed_memory.py" in snippet
