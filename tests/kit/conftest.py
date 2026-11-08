from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]


def load_tool(name: str):
    """tools/kit/<name>.py as a module. Registered in sys.modules before it
    runs, because dataclasses look their module up there."""
    if f"kit_{name}" in sys.modules:
        return sys.modules[f"kit_{name}"]
    spec = importlib.util.spec_from_file_location(f"kit_{name}", KIT_ROOT / "tools" / "kit" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def kit_root() -> Path:
    return KIT_ROOT


def run_hook(hook: Path, command: str, cwd: Path, env: dict[str, str] | None = None) -> dict | None:
    """Feed a Bash PreToolUse payload to a hook; its JSON verdict, or None.
    `env` adds to the minimal environment the hook otherwise gets."""
    done = subprocess.run(
        ["python3", str(hook)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        capture_output=True, text=True, cwd=cwd, timeout=30,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(cwd), **(env or {})},
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout) if done.stdout.strip() else None


def denied(verdict: dict | None) -> bool:
    return bool(verdict) and verdict["hookSpecificOutput"]["permissionDecision"] == "deny"
