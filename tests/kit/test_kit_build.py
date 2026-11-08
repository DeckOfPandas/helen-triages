"""tools/kit/build.py: the generated files, and the rules it merges by."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from .conftest import load_tool

ROOT = Path(__file__).resolve().parents[2]
build = load_tool("build")

KIT_SETTINGS = json.loads((ROOT / ".claude" / "kit" / "settings.kit.json").read_text(encoding="utf-8"))


def test_the_committed_generated_files_are_what_the_builder_writes():
    done = subprocess.run(["python3", "tools/kit/build.py", "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_project_lists_join_the_kits_without_repeats():
    merged = json.loads(build.build_settings(
        {"permissions": {"allow": ["Bash(a)", "Bash(b)"]}},
        {"permissions": {"allow": ["Bash(b)", "Bash(c)"]}}))
    assert merged["permissions"]["allow"] == ["Bash(a)", "Bash(b)", "Bash(c)"]


def test_project_hooks_add_to_the_kits():
    kit_hook = {"hooks": [{"type": "command", "command": "kit"}]}
    project_hook = {"matcher": "Bash", "hooks": [{"type": "command", "command": "project"}]}
    merged = json.loads(build.build_settings({"hooks": {"PreToolUse": [kit_hook]}},
                                             {"hooks": {"PreToolUse": [project_hook],
                                                        "SessionStart": [kit_hook]}}))
    assert merged["hooks"]["PreToolUse"] == [kit_hook, project_hook]
    assert merged["hooks"]["SessionStart"] == [kit_hook]


@pytest.mark.parametrize("project", [
    {"permissions": {"blockReadsOutsideWorkingDirectories": False}},
    {"worktree": {"baseRef": "origin/main"}},
    {"permissions": {"allow": "Bash(x)"}},
])
def test_project_may_not_change_a_kit_value(project):
    with pytest.raises(build.BuildError, match="may not change"):
        build.build_settings(KIT_SETTINGS, project)


@pytest.mark.parametrize("allow", [
    "Bash(chmod *)",
    "Bash(chmod 644 index.html)",
    "Bash(sudo apt-get install x)",
    "Bash(gh pr merge 12)",
    "Bash(sh scripts/gh-agent.sh pr *)",
    "Bash(sh scripts/gh-agent.sh *)",
    "Bash(*)",
    "Bash",
    "Read(./.env)",
])
def test_a_project_allow_cannot_undo_a_kit_deny(allow):
    with pytest.raises(build.BuildError, match="covered by the deny rule"):
        build.build_settings(KIT_SETTINGS, {"permissions": {"allow": [allow]}})


@pytest.mark.parametrize("allow", [
    "Bash(sh scripts/browser/shot.sh *)",
    "Bash(chmodx)",
    "Bash(sh scripts/gh-agent.sh pr create *)",
    "Read(./README.md)",
])
def test_unrelated_project_allows_pass(allow):
    merged = json.loads(build.build_settings(KIT_SETTINGS, {"permissions": {"allow": [allow]}}))
    assert allow in merged["permissions"]["allow"]
    assert merged["permissions"]["deny"] == KIT_SETTINGS["permissions"]["deny"]


def test_project_denies_add_and_kit_denies_stay():
    merged = json.loads(build.build_settings(KIT_SETTINGS, {"permissions": {"deny": ["Bash(rm *)"]}}))
    assert merged["permissions"]["deny"] == KIT_SETTINGS["permissions"]["deny"] + ["Bash(rm *)"]


def test_notes_never_reach_settings_json():
    merged = json.loads(build.build_settings(KIT_SETTINGS, {"_about": "x", "_reviewedOpenRules": {}}))
    assert not [key for key in merged if key.startswith("_")]


def test_output_is_stable_whatever_the_input_order():
    project = {"permissions": {"allow": ["Bash(x)"]}, "env": {"B": "1", "A": "2"}}
    reordered = {"env": {"A": "2", "B": "1"}, "permissions": {"allow": ["Bash(x)"]}}
    first = build.build_settings(KIT_SETTINGS, project)
    assert first == build.build_settings(KIT_SETTINGS, reordered)
    assert first == build.build_settings(json.loads(json.dumps(KIT_SETTINGS)), project)
    assert list(json.loads(first)) == sorted(json.loads(first))


def test_devcontainer_takes_the_name_from_kit_env():
    template = (ROOT / ".devcontainer" / "devcontainer.template.json").read_text(encoding="utf-8")
    rendered = json.loads(build.build_devcontainer(template, "# c\nPROJECT_NAME='my-site'  # n\n"))
    assert rendered["name"] == "my-site (sandboxed)"
    assert rendered["image"] == "my-site-devcontainer"
    assert {m.split(",")[0] for m in rendered["mounts"]} == {
        "source=my-site-claude-config", "source=my-site-bundle-cache"}
    assert rendered["workspaceMount"].startswith("source=${localWorkspaceFolder},")


@pytest.mark.parametrize("kit_env", ["PROJECT_NAME=My Site\n", "WITH_RUBY=1\n", "PROJECT_NAME=\n"])
def test_devcontainer_refuses_a_bad_name(kit_env):
    template = (ROOT / ".devcontainer" / "devcontainer.template.json").read_text(encoding="utf-8")
    with pytest.raises(build.BuildError, match="PROJECT_NAME"):
        build.build_devcontainer(template, kit_env)


def test_check_names_a_hand_edited_file(tmp_path):
    for path in ("tools/kit/build.py", ".claude/kit/settings.kit.json", ".claude/settings.project.json",
                 ".devcontainer/kit.env", ".devcontainer/devcontainer.template.json"):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes((ROOT / path).read_bytes())
    assert subprocess.run(["python3", "tools/kit/build.py"], cwd=tmp_path).returncode == 0
    settings = tmp_path / ".claude" / "settings.json"
    settings.write_text(settings.read_text().replace('"Bash(git log *)",\n', ""))
    done = subprocess.run(["python3", "tools/kit/build.py", "--check"], cwd=tmp_path,
                          capture_output=True, text=True)
    assert done.returncode == 1 and ".claude/settings.json is not what the builder writes" in done.stderr
