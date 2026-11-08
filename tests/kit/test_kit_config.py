"""The config files agree with each other and with run.sh."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def kit_env(kit_root: Path) -> dict[str, str]:
    values = {}
    for line in (kit_root / ".devcontainer" / "kit.env").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            key, _, value = line.partition("=")
            values[key] = value.strip("\"'")
    return values


def test_devcontainer_json_uses_the_project_name(kit_root):
    name = kit_env(kit_root)["PROJECT_NAME"]
    config = json.loads((kit_root / ".devcontainer" / "devcontainer.json").read_text())
    assert config["image"] == f"{name}-devcontainer"
    assert config["name"] == f"{name} (sandboxed)"
    sources = {m.split(",")[0].removeprefix("source=") for m in config["mounts"]}
    assert sources == {f"{name}-claude-config", f"{name}-bundle-cache"}


def test_mount_targets_match_the_dockerfile(kit_root):
    dockerfile = (kit_root / ".devcontainer" / "Dockerfile").read_text()
    run_sh = (kit_root / ".devcontainer" / "run.sh").read_text()
    for target in ("/state/claude-config", "/state/bundle"):
        assert target in dockerfile and target in run_sh


def test_every_kit_env_key_is_known_to_run_sh(kit_root):
    run_sh = (kit_root / ".devcontainer" / "run.sh").read_text()
    accepted = re.search(r"case \"\$key\" in\n(.*?)\)", run_sh, re.DOTALL).group(1)
    for key in kit_env(kit_root):
        assert key in accepted, f"kit.env key {key} would be refused by run.sh"


def test_build_args_exist_in_the_dockerfile_with_kit_env_defaults(kit_root):
    dockerfile = (kit_root / ".devcontainer" / "Dockerfile").read_text()
    args = dict(re.findall(r"^ARG (\w+)=?(.*)$", dockerfile, re.MULTILINE))
    run_sh = (kit_root / ".devcontainer" / "run.sh").read_text()
    block = re.search(r"BUILD_ARGS=\(\n(.*?)\n\)", run_sh, re.DOTALL).group(1)
    for name in re.findall(r'"(\w+)=', block) + ["CLAUDE_CODE_VERSION"]:
        assert name in args, f"run.sh passes {name}, which the Dockerfile never declares"
    # A project sets its own versions and toggles in kit.env, so the Dockerfile's
    # defaults agree with run.sh's; a bare `docker build` gets every toggle off.
    defaults = run_sh_defaults(run_sh)
    for name in ("NODE_MAJOR", "PLAYWRIGHT_VERSION"):
        assert args[name].strip('"') == defaults[name], f"Dockerfile default for {name} differs from run.sh's"
    for name in KIT_DEFAULTS:
        if name.startswith("WITH_"):
            assert args[name].strip('"') == "0", f"Dockerfile default for {name} is not off"


def run_sh_defaults(run_sh: str) -> dict[str, str]:
    block = re.search(r"^PROJECT_NAME=\"\"\n(.*?)\n\n", run_sh, re.DOTALL | re.MULTILINE).group(1)
    return {k: v.strip("\"'") for k, v in re.findall(r"^(\w+)=(.*)$", block, re.MULTILINE)}


def test_the_kits_kit_env_ships_run_sh_defaults(kit_root):
    if not (kit_root / "kit" / "manifest").is_file():
        pytest.skip("a project's kit.env holds its own values; the kit checks its template")
    defaults = run_sh_defaults((kit_root / ".devcontainer" / "run.sh").read_text())
    env = kit_env(kit_root)
    assert defaults, "read no defaults from run.sh -- has its layout changed?"
    for name, value in defaults.items():
        assert env[name] == value, f"the kit's kit.env ships {name}={env[name]}, run.sh defaults to {value}"


def test_python_packages_are_pinned(kit_root):
    dockerfile = (kit_root / ".devcontainer" / "Dockerfile").read_text()
    assert re.search(r'"pytest==\d+\.\d+\.\d+"', dockerfile), "pytest is not pinned in the Dockerfile"
    for line in (kit_root / ".devcontainer" / "requirements.txt").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            assert re.fullmatch(r"[A-Za-z0-9_.-]+==[0-9][A-Za-z0-9.]*", line), f"unpinned: {line}"


def test_settings_json_hooks_exist(kit_root):
    settings = json.loads((kit_root / ".claude" / "settings.json").read_text())
    commands = [h["command"] for event in settings["hooks"].values()
                for group in event for h in group["hooks"]]
    for command in commands:
        path = re.search(r"\$CLAUDE_PROJECT_DIR/([^\"]+)", command).group(1)
        assert (kit_root / path).is_file(), path
    assert "Bash(sh scripts/gh-agent.sh pr merge *)" in settings["permissions"]["deny"]


def test_playwright_lives_in_an_allowed_directory(kit_root):
    settings = json.loads((kit_root / ".claude" / "settings.json").read_text())
    dockerfile = (kit_root / ".devcontainer" / "Dockerfile").read_text()
    assert "/opt/playwright" in dockerfile
    assert "/opt" in settings["permissions"]["additionalDirectories"]


def test_settings_local_example_is_what_run_sh_reads(tmp_path, kit_root):
    (tmp_path / ".claude").mkdir()
    example = kit_root / ".claude" / "settings.local.example.json"
    settings = json.loads(example.read_text())
    assert settings["env"]["AGENT_GH_TOKEN"] == ""
    shutil.copy(example, tmp_path / ".claude" / "settings.local.json")
    done = subprocess.run(["python3", str(kit_root / ".devcontainer" / "read_local_token.py")],
                          cwd=tmp_path, capture_output=True, text=True)
    assert done.returncode == 0 and done.stdout == ""


@pytest.mark.parametrize("local,committed", [
    (".claude/settings.local.json", ".claude/settings.local.example.json"),
    ("scripts/github.local.conf", "scripts/github.conf"),
    (".devcontainer/kit.local.env", ".devcontainer/kit.local.example.env"),
])
def test_only_the_template_is_committed(tmp_path, kit_root, local, committed):
    shutil.copy(kit_root / ".gitignore", tmp_path / ".gitignore")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    ignored = subprocess.run(["git", "check-ignore", "-q", local], cwd=tmp_path)
    template = subprocess.run(["git", "check-ignore", "-q", committed], cwd=tmp_path)
    assert ignored.returncode == 0, f"{local} would be committed"
    assert template.returncode == 1, f"{committed} would not be committed"
    assert (kit_root / committed).is_file()


def test_host_dotfiles_that_reload_bashrc_do_not_loop(tmp_path, kit_root):
    snippet = (kit_root / ".devcontainer" / "container.bashrc").read_text()
    (tmp_path / ".bashrc").write_text("echo pass >> \"$HOME/passes\"\n" + snippet)
    (tmp_path / ".host-bashrc").write_text('. "$HOME/.bashrc"\nalias from-host=true\n')
    (tmp_path / ".host-bash_aliases").write_text('. "$HOME/.bashrc"\n')
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run(["bash", "-i", "-c", "type from-host; bash -i -c 'type from-host'"],
                          env=env, capture_output=True, text=True, timeout=10)
    assert done.returncode == 0, done.stderr
    # Three passes per shell: its own, then one reload from each host file.
    assert (tmp_path / "passes").read_text().count("pass") == 6


def copy_build_inputs(kit_root: Path, dest: Path) -> None:
    """What set-project-name.py and tools/kit/build.py need to run in `dest`."""
    shutil.copytree(kit_root / ".devcontainer", dest / ".devcontainer")
    shutil.copytree(kit_root / "tools" / "kit", dest / "tools" / "kit")
    (dest / ".claude" / "kit").mkdir(parents=True)
    shutil.copy(kit_root / ".claude" / "kit" / "settings.kit.json", dest / ".claude" / "kit")
    shutil.copy(kit_root / ".claude" / "settings.project.json", dest / ".claude")


def test_set_project_name(tmp_path, kit_root):
    copy_build_inputs(kit_root, tmp_path)
    done = subprocess.run(["python3", ".devcontainer/set-project-name.py", "my-site"],
                          cwd=tmp_path, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert kit_env(tmp_path)["PROJECT_NAME"] == "my-site"
    test_devcontainer_json_uses_the_project_name(tmp_path)
    bad = subprocess.run(["python3", ".devcontainer/set-project-name.py", "My Site"],
                         cwd=tmp_path, capture_output=True, text=True)
    assert bad.returncode == 2


# --- run.sh, against a stub docker ----------------------------------------------------
# The stub is an exported bash function, so no file needs an execute bit.

STUB = '() { printf "%s\\n" "docker $*" >> "$STUB_LOG"; [ "$1" != image ]; }'

# The kit's own toggle values. The run.sh tests edit from these, whatever a
# project has set in its kit.env.
KIT_DEFAULTS = {
    "WITH_RUBY": "0",
    "WITH_PLAYWRIGHT": "0",
    "WITH_PY_REQS": "0",
    "PORTS": '""',
    "EXTRA_ALLOWED_DOMAINS": '""',
    "MOUNT_DOTFILES": "1",
}


@pytest.fixture
def project(tmp_path: Path, kit_root: Path) -> Path:
    copy_build_inputs(kit_root, tmp_path)
    (tmp_path / ".devcontainer" / "kit.local.env").unlink(missing_ok=True)
    kit = tmp_path / ".devcontainer" / "kit.env"
    text = kit.read_text()
    for key, value in KIT_DEFAULTS.items():
        text = re.sub(rf"^{key}=.*$", f"{key}={value}", text, flags=re.MULTILINE)
    kit.write_text(text)
    subprocess.run(["python3", ".devcontainer/set-project-name.py", "demo"], cwd=tmp_path, check=True,
                   capture_output=True)
    # Its own repo, or run.sh would resolve the repo root of whatever encloses it.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def run_sh(project: Path, *args: str, kit_env_text: str | None = None, token: bool = False):
    if kit_env_text is not None:
        (project / ".devcontainer" / "kit.env").write_text(kit_env_text)
    log = project / "docker.log"
    log.write_text("")
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(project / "home"),
           "STUB_LOG": str(log), "PIN_CLAUDE_CODE": "9.9.9", "BASH_FUNC_docker%%": STUB}
    if token:
        (project / ".claude").mkdir(exist_ok=True)
        (project / ".claude" / "settings.local.json").write_text('{"env": {"AGENT_GH_TOKEN": "x"}}')
    done = subprocess.run(["bash", ".devcontainer/run.sh", *args], cwd=project,
                          capture_output=True, text=True, env=env, timeout=60)
    return done, log.read_text().splitlines()


def test_run_sh_builds_then_runs(project):
    done, calls = run_sh(project)
    assert done.returncode == 0, done.stderr
    build = next(c for c in calls if c.startswith("docker build"))
    assert "BASE_IMAGE=debian:bookworm-slim" in build
    assert "CLAUDE_CODE_VERSION=9.9.9" in build and "-t demo-devcontainer" in build
    run = next(c for c in calls if c.startswith("docker run"))
    assert "--name demo-primary" in run and "demo-claude-config:/state/claude-config" in run
    assert "AGENT_GH_TOKEN" not in run and "NET_ADMIN" not in run and "bundle" not in run


def test_run_sh_toggles_and_flags(project):
    text = (project / ".devcontainer" / "kit.env").read_text()
    text = text.replace("WITH_RUBY=0", "WITH_RUBY=1").replace('PORTS=""', 'PORTS="5998:4000"')
    done, calls = run_sh(project, "--firewall", kit_env_text=text, token=True)
    assert done.returncode == 0, done.stderr
    build = next(c for c in calls if c.startswith("docker build"))
    assert "BASE_IMAGE=ruby:3.3-slim-bookworm" in build and "WITH_RUBY=1" in build
    run = next(c for c in calls if c.startswith("docker run"))
    assert "-e AGENT_GH_TOKEN" in run and "--cap-add=NET_ADMIN" in run
    assert "-p 5998:4000" in run and "demo-bundle-cache:/state/bundle" in run
    assert "init-firewall.sh" in run


def test_run_sh_build_only_does_not_run(project):
    done, calls = run_sh(project, "--build-only")
    assert done.returncode == 0, done.stderr
    assert not any(c.startswith("docker run") for c in calls)


def test_run_sh_in_a_worktree_builds_its_kit_and_mounts_the_primary(project, kit_root):
    # A worktree made in the container: its .git names a path the host lacks.
    worktree = project / ".claude" / "worktrees" / "wt"
    shutil.copytree(project / ".devcontainer", worktree / ".devcontainer")
    (worktree / ".git").write_text("gitdir: /no/such/.git/worktrees/wt\n")
    kit = worktree / ".devcontainer" / "kit.env"
    kit.write_text(kit.read_text().replace("WITH_RUBY=0", "WITH_RUBY=1"))
    log = project / "docker.log"
    log.write_text("")
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(project / "home"),
           "STUB_LOG": str(log), "PIN_CLAUDE_CODE": "9.9.9", "BASH_FUNC_docker%%": STUB}
    done = subprocess.run(["bash", str(worktree / ".devcontainer" / "run.sh")], cwd=worktree,
                          capture_output=True, text=True, env=env, timeout=60)
    assert done.returncode == 0, done.stderr
    calls = log.read_text().splitlines()
    build = next(c for c in calls if c.startswith("docker build"))
    assert "WITH_RUBY=1" in build and f"-f {worktree}/.devcontainer/Dockerfile" in build
    run = next(c for c in calls if c.startswith("docker run"))
    assert f"-v {project}:/workspace" in run and "--name demo-primary" in run


def test_kit_local_env_overrides_the_name(project):
    text = (project / ".devcontainer" / "kit.env").read_text().replace("PROJECT_NAME=demo", "PROJECT_NAME=changeme")
    (project / ".devcontainer" / "kit.local.env").write_text("# mine\nPROJECT_NAME=mine\n")
    done, calls = run_sh(project, kit_env_text=text)
    assert done.returncode == 0, done.stderr
    assert "--name mine-primary" in next(c for c in calls if c.startswith("docker run"))


def test_kit_local_env_takes_only_the_name(project):
    (project / ".devcontainer" / "kit.local.env").write_text("WITH_RUBY=1\n")
    done, calls = run_sh(project)
    assert done.returncode == 1 and "only PROJECT_NAME" in done.stderr
    assert calls == []


@pytest.mark.parametrize("edit,message", [
    (("WITH_RUBY=0", "WITH_RUBBY=1"), "unknown key"),
    (("WITH_RUBY=0", "WITH_RUBY=yes"), "must be 0 or 1"),
    (('PORTS=""', 'PORTS="80"'), "host:container"),
    (('EXTRA_ALLOWED_DOMAINS=""', 'EXTRA_ALLOWED_DOMAINS="a.com;b"'), "not a hostname"),
    (("PROJECT_NAME=demo", "PROJECT_NAME=changeme"), "set-project-name"),
])
def test_run_sh_refuses_bad_kit_env(project, edit, message):
    text = (project / ".devcontainer" / "kit.env").read_text().replace(*edit)
    done, calls = run_sh(project, kit_env_text=text)
    assert done.returncode == 1 and message in done.stderr
    assert calls == []
