"""scripts/kit-ports.sh: the pairs in force, each container port's state, and
what it refuses."""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = KIT_ROOT / "scripts" / "kit-ports.sh"


def ports(*args: str, env_ports: str | None = None, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "KIT_PORTS"}
    if env_ports is not None:
        env["KIT_PORTS"] = env_ports
    return subprocess.run(["sh", str(script), *args], capture_output=True, text=True, env=env, timeout=30)


def test_lists_each_pair_with_a_state():
    out = ports(env_ports="18301:8301 18302:8302")
    assert out.returncode == 0, out.stderr
    lines = out.stdout.splitlines()
    assert [line.split(" ", 1)[0] for line in lines] == ["18301:8301", "18302:8302"]
    assert all(line.split(" ", 1)[1] in ("free", "in use", "unknown (no ss)") for line in lines)


@pytest.mark.skipif(shutil.which("ss") is None, reason="ss is not installed")
def test_a_listening_container_port_is_in_use_and_a_closed_one_free():
    with socket.socket() as server:
        server.bind(("0.0.0.0", 0))
        server.listen()
        port = server.getsockname()[1]
        busy = ports(env_ports=f"1:{port}")
    free = ports(env_ports=f"1:{port}")
    assert busy.stdout.strip() == f"1:{port} in use"
    assert free.stdout.strip() == f"1:{port} free"


def test_no_pairs_exits_1_and_says_where_to_add_them():
    out = ports(env_ports="")
    assert out.returncode == 1
    assert out.stdout == ""
    assert "PORTS in .devcontainer/kit.env" in out.stderr


def test_unset_reads_kit_env(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".devcontainer").mkdir()
    shutil.copy(SCRIPT, tmp_path / "scripts" / "kit-ports.sh")
    (tmp_path / ".devcontainer" / "kit.env").write_text(
        '# a comment naming PORTS="1:1"\nPROJECT_NAME=x\nPORTS="18311:8311 18312:8312"\n')
    out = ports(script=tmp_path / "scripts" / "kit-ports.sh")
    assert out.returncode == 0, out.stderr
    lines = out.stdout.splitlines()
    assert "kit.env's PORTS" in lines[0]
    assert [line.split(" ", 1)[0] for line in lines[1:]] == ["18311:8311", "18312:8312"]


@pytest.mark.parametrize("args", [["7000"], ["--all"], ["-h"]])
def test_refuses_any_argument(args):
    out = ports(*args, env_ports="7000:7000")
    assert out.returncode == 2
    assert "refused" in out.stderr and out.stdout == ""


@pytest.mark.parametrize("bad", ["7000", "7000:", ":7000", "7000:7000:1", "70a0:7000", "7000:$(id)"])
def test_refuses_a_malformed_pair(bad):
    out = ports(env_ports=bad)
    assert out.returncode == 2
    assert "is not host:container" in out.stderr
