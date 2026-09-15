"""guard-sed.py and guard-awk.py refuse the tools, and only the tools.

Neither hook had a test until 2026-09-15, when guard-awk.py was written:
Helen's README listed "Never `awk` (same)" beside "Never `sed`", and nothing
enforced the first. A guard nobody has broken on purpose is a claim, not a
guard (CLAUDE.md's hooks, passim) -- so both are exercised here, through the
same JSON the harness hands them.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

pytestmark = pytest.mark.shared

HOOKS = pathlib.Path(__file__).resolve().parents[1] / ".claude" / "hooks"


def _denied(hook: str, command: str) -> bool:
    result = subprocess.run(
        ["python3", str(HOOKS / hook)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return '"deny"' in result.stdout


@pytest.mark.parametrize("command", [
    "awk '{print $1}' data.csv",
    "awk -F, -f tmp/prog.awk data.csv",
    "gawk -i inplace '{gsub(/a/,\"b\")}1' file.txt",
    "mawk 'BEGIN{system(\"id\")}'",
    "nawk 'END{print NR}' file",
    "/usr/bin/awk '{print}' file",
    "env awk '{print}' file",
    "busybox awk '{print}' file",
    "grep -rn x dir/ | awk '{print $2}'",
    "true && awk 'BEGIN{print > \"out\"}'",
    "(awk '{print}' file)",
])
def test_guard_awk_refuses_every_way_of_running_awk(command):
    assert _denied("guard-awk.py", command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    "python3 .claude/hooks/guard-awk.py",
    "grep -rn 'awk' .claude/hooks/",
    "git commit -F tmp/msg-about-awk.txt",
    "cat hawkish.txt",
    "ls gawking/",
    'echo "no awk here, only prose"',
    "grep -c awkward notes.md",
])
def test_guard_awk_leaves_mentions_and_lookalikes_alone(command):
    assert not _denied("guard-awk.py", command), f"refused {command!r}"


@pytest.mark.parametrize("command", [
    "sed -n '1,5p' file",
    "sed -i 's/a/b/' file",
    "grep x file | sed 's/x/y/'",
    "/bin/sed 's/a/b/' file",
])
def test_guard_sed_refuses_sed(command):
    assert _denied("guard-sed.py", command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    "python3 .claude/hooks/guard-sed.py",
    "grep -rn 'sed' model_instructions/",
    "cat processed.txt",
])
def test_guard_sed_leaves_mentions_and_lookalikes_alone(command):
    assert not _denied("guard-sed.py", command), f"refused {command!r}"


def test_guard_sed_no_longer_recommends_python_dash_c():
    """Its refusal used to suggest `python3 -c '...'`, which
    guard-inline-script.py has refused since 2026-09-10 -- advice that walked
    straight into the next guard."""
    text = (HOOKS / "guard-sed.py").read_text(encoding="utf-8")
    assert "single-quoted `python3 -c" not in text


def test_both_guards_are_wired_into_settings():
    settings = json.loads((HOOKS.parent / "settings.json").read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for entry in settings["hooks"]["PreToolUse"]
        for hook in entry["hooks"]
    ]
    for name in ("guard-sed.py", "guard-awk.py"):
        wired = [c for c in commands if c.endswith(f'/.claude/hooks/{name}"')]
        assert wired, f"{name} exists but no PreToolUse hook runs it"
