"""The build stamp: what moves it and what does not."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def stamp(kit_root: Path):
    spec = importlib.util.spec_from_file_location(
        "build_inputs_hash", kit_root / ".devcontainer" / "build_inputs_hash.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def context(tmp_path: Path) -> Path:
    (tmp_path / "Dockerfile").write_text("FROM x\n")
    (tmp_path / "run.sh").write_text("echo hi\n")
    (tmp_path / ".dockerignore").write_text("# comment\nrun.sh\n")
    return tmp_path


def test_ignored_file_does_not_move_it(stamp, context):
    before = stamp.build_inputs_hash(context)
    (context / "run.sh").write_text("echo changed\n")
    assert stamp.build_inputs_hash(context) == before


def test_built_file_moves_it(stamp, context):
    before = stamp.build_inputs_hash(context)
    (context / "Dockerfile").write_text("FROM y\n")
    assert stamp.build_inputs_hash(context) != before


def test_rename_moves_it(stamp, context):
    before = stamp.build_inputs_hash(context)
    (context / "Dockerfile").rename(context / "Containerfile")
    assert stamp.build_inputs_hash(context) != before


def test_build_args_move_it(stamp, context):
    assert stamp.build_inputs_hash(context, "WITH_RUBY=0") != stamp.build_inputs_hash(context, "WITH_RUBY=1")


def test_a_pattern_falls_back_to_hashing_everything(stamp, context):
    (context / ".dockerignore").write_text("run.sh\n*.md\n")
    before = stamp.build_inputs_hash(context)
    (context / "run.sh").write_text("echo changed\n")
    assert stamp.build_inputs_hash(context) != before


def test_command_line_takes_a_context(kit_root, context):
    import subprocess
    script = kit_root / ".devcontainer" / "build_inputs_hash.py"
    from_arg = subprocess.run(["python3", str(script), "A=1", str(context)],
                              capture_output=True, text=True, check=True).stdout.strip()
    (context / ".devcontainer").mkdir()
    for name in ("Dockerfile", "run.sh", ".dockerignore"):
        (context / ".devcontainer" / name).write_bytes((context / name).read_bytes())
    default = subprocess.run(["python3", str(script), "A=1"], cwd=context,
                             capture_output=True, text=True, check=True).stdout.strip()
    assert from_arg == default


def test_shipped_dockerignore_is_understood(stamp, kit_root):
    names = stamp.exclusions(kit_root / ".devcontainer")
    assert names, "the shipped .dockerignore fell back to hashing everything"
    # kit.local.env is gitignored and README.md is a project's own notes, so
    # neither is in a fresh clone of the kit.
    for name in names - {"kit.local.env", "README.md"}:
        assert (kit_root / ".devcontainer" / name).is_file(), f".dockerignore names a missing {name}"
    for built in ("Dockerfile", "init-firewall.sh", "requirements.txt"):
        assert built not in names, f"{built} is COPY'd by the Dockerfile and must stay in the stamp"
