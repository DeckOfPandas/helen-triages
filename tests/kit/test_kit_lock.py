"""A project's kit-owned files are exactly the kit's: .claude/kit/kit.lock
records each one's sha256 at the last /kit-sync."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from .conftest import load_tool

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / ".claude" / "kit" / "kit.lock"
IS_THE_KIT = (ROOT / "kit" / "manifest").is_file()
sync = load_tool("sync")


def test_the_kit_has_no_lock():
    if not IS_THE_KIT:
        pytest.skip("this is a project; the kit checks it has no lock of its own")
    assert not LOCK.exists(), "the kit has a kit.lock: a sync was run into the kit itself"


def test_kit_owned_files_are_unchanged():
    if IS_THE_KIT:
        pytest.skip("this repo is the kit, where kit files are edited; projects lock them")
    assert LOCK.is_file(), "no .claude/kit/kit.lock: this project has never been synced -- /kit-sync"
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["files"], "kit.lock lists no files -- is it damaged?"
    edited = sync.edited_kit_files(ROOT, lock)
    assert not edited, (
        "these kit-owned files differ from what /kit-sync wrote (.claude/kit/kit.lock):\n"
        + "".join(f"  {path}\n" for path in edited)
        + "Make this change in helen-contains-claude-webdev and sync, or move it into a "
          "project-owned file (CLAUDE.md, .claude/settings.project.json, .devcontainer/kit.env).")
