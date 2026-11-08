"""tools/kit/sync.py, end to end: a throwaway kit repo made from this checkout's
tracked files, synced into a throwaway project."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(not (ROOT / "kit" / "manifest").is_file(),
                                reason="this is a project: the sync is tested in the kit, from its tracked files")
GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *GIT_ID, *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout


def commit_all(repo: Path, message: str = "x") -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD").strip()


def sync(project: Path, kit: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(["python3", "tools/kit/sync.py", "--kit", str(kit), *flags],
                          cwd=project, capture_output=True, text=True, timeout=60)


def snapshot(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and ".git" not in p.parts
            and "tmp" not in p.relative_to(root).parts}


@pytest.fixture
def kit(tmp_path: Path) -> Path:
    kit = tmp_path / "helen-contains-claude-webdev"
    files = [f for f in git(ROOT, "ls-files", "-z").split("\0") if f]
    assert "kit/manifest" in files, "kit/manifest is not tracked -- git add it"
    for f in files:
        (kit / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / f, kit / f)
    git(kit, "init", "-q", "-b", "main")
    commit_all(kit, "kit")
    git(kit, "remote", "add", "origin", "https://github.com/your-org/helen-contains-claude-webdev.git")
    return kit


@pytest.fixture
def bare_project(tmp_path: Path, kit: Path) -> Path:
    """A project with only the sync tool, never synced. A real one would have
    it from its first copy of the kit."""
    project = tmp_path / "project"
    (project / "tools" / "kit").mkdir(parents=True)
    shutil.copyfile(kit / "tools" / "kit" / "sync.py", project / "tools" / "kit" / "sync.py")
    git(project, "init", "-q", "-b", "main")
    return project


@pytest.fixture
def project(bare_project: Path, kit: Path) -> Path:
    done = sync(bare_project, kit, "--adopt")
    assert done.returncode == 0, done.stderr
    return bare_project


def test_first_sync_needs_adopt(bare_project, kit):
    done = sync(bare_project, kit)
    assert done.returncode == 1 and "never been synced" in done.stderr
    assert not (bare_project / ".claude").exists()


def test_adopt_writes_the_kit_the_templates_and_the_generated_files(project, kit):
    lock = json.loads((project / ".claude" / "kit" / "kit.lock").read_text())
    assert lock["kit_commit"] == git(kit, "rev-parse", "HEAD").strip()
    assert lock["kit_repo"] == "helen-contains-claude-webdev"
    assert ".claude/hooks/guard-sed.py" in lock["files"] and "scripts/gh-read.sh" in lock["files"]
    assert "CLAUDE.md" not in lock["files"] and "README.md" not in lock["files"]
    for path, digest in lock["files"].items():
        assert hashlib.sha256((project / path).read_bytes()).hexdigest() == digest, path
    claude_md = (project / "CLAUDE.md").read_text()
    assert claude_md == (kit / "kit" / "templates" / "CLAUDE.md").read_text()
    assert "@.claude/kit/RULES.md" in claude_md
    assert not (project / "README.md").exists() and not (project / "kit").exists()
    assert (project / ".claude" / "settings.json").read_bytes() == (kit / ".claude" / "settings.json").read_bytes()
    assert (project / ".devcontainer" / "devcontainer.json").is_file()
    report = (project / "tmp" / "kit-sync-report.md").read_text()
    assert "Project files created" in report and "`CLAUDE.md`" in report


def test_a_second_sync_with_no_kit_change_does_nothing(project, kit):
    before = snapshot(project)
    for flags in ((), ("--dry-run",)):
        done = sync(project, kit, *flags)
        assert done.returncode == 0, done.stderr
        assert "Nothing to sync" in done.stdout
    assert snapshot(project) == before


def test_a_kit_change_arrives_and_project_files_stay(project, kit):
    (project / "CLAUDE.md").write_text("# mine\n@.claude/kit/RULES.md\n")
    (project / "scripts" / "mine.sh").write_text("echo mine\n")
    rules = kit / ".claude" / "kit" / "RULES.md"
    rules.write_text(rules.read_text() + "- A new kit rule.\n")
    (kit / "kit" / "templates" / "CLAUDE.md").write_text("# new template\n")
    (kit / "tools" / "dev" / "crop.js").unlink()
    new = commit_all(kit)

    dry = sync(project, kit, "--dry-run")
    assert dry.returncode == 0 and "(dry run)" in dry.stdout
    assert "A new kit rule" not in (project / ".claude" / "kit" / "RULES.md").read_text()

    done = sync(project, kit)
    assert done.returncode == 0, done.stderr
    assert "`.claude/kit/RULES.md`" in done.stdout and "`tools/dev/crop.js`" in done.stdout
    assert "A new kit rule" in (project / ".claude" / "kit" / "RULES.md").read_text()
    assert not (project / "tools" / "dev" / "crop.js").exists()
    assert (project / "CLAUDE.md").read_text() == "# mine\n@.claude/kit/RULES.md\n"
    assert (project / "scripts" / "mine.sh").read_text() == "echo mine\n"
    lock = json.loads((project / ".claude" / "kit" / "kit.lock").read_text())
    assert lock["kit_commit"] == new and "tools/dev/crop.js" not in lock["files"]
    assert "no container rebuild needed" in done.stdout
    assert "Nothing to sync" in sync(project, kit).stdout


def test_an_edited_kit_file_stops_the_sync(project, kit):
    guard = project / ".claude" / "hooks" / "guard-sed.py"
    guard.write_text(guard.read_text() + "# local tweak\n")
    (kit / "tools" / "dev" / "crop.js").unlink()
    commit_all(kit)
    before = snapshot(project)
    done = sync(project, kit)
    assert done.returncode == 1
    assert ".claude/hooks/guard-sed.py" in done.stderr and "helen-contains-claude-webdev" in done.stderr
    assert snapshot(project) == before


def test_a_new_kit_file_never_overwrites_the_projects_own(project, kit):
    (project / "scripts" / "extra.sh").write_text("echo project\n")
    (kit / "scripts" / "extra.sh").write_text("echo kit\n")
    commit_all(kit)
    done = sync(project, kit)
    assert done.returncode == 1 and "scripts/extra.sh" in done.stderr
    assert (project / "scripts" / "extra.sh").read_text() == "echo project\n"


def test_a_devcontainer_change_says_to_rebuild(project, kit):
    dockerfile = kit / ".devcontainer" / "Dockerfile"
    dockerfile.write_text(dockerfile.read_text() + "# change\n")
    commit_all(kit)
    done = sync(project, kit)
    assert done.returncode == 0, done.stderr
    assert "run `.devcontainer/run.sh` once" in done.stdout


def test_a_new_kit_env_key_is_reported(project, kit):
    env = kit / ".devcontainer" / "kit.env"
    env.write_text(env.read_text() + "NEW_TOGGLE=0\n")
    commit_all(kit)
    done = sync(project, kit)
    assert done.returncode == 0, done.stderr
    assert "`NEW_TOGGLE`" in done.stdout
    assert "NEW_TOGGLE" not in (project / ".devcontainer" / "kit.env").read_text()


def test_a_project_allow_that_a_new_kit_deny_covers_fails_loudly(project, kit):
    settings = project / ".claude" / "settings.project.json"
    data = json.loads(settings.read_text())
    data["permissions"]["allow"].append("Bash(rm -rf build)")
    settings.write_text(json.dumps(data))
    assert subprocess.run(["python3", "tools/kit/build.py"], cwd=project).returncode == 0
    kit_settings = kit / ".claude" / "kit" / "settings.kit.json"
    data = json.loads(kit_settings.read_text())
    data["permissions"]["deny"].append("Bash(rm -rf *)")
    kit_settings.write_text(json.dumps(data))
    commit_all(kit)
    done = sync(project, kit)
    assert done.returncode == 1 and "covered by the deny rule" in done.stderr


# --- watched: a kit or generated path the project has taken as its own ----------------

OURS = '{"name": "ours", "forwardPorts": [4001]}\n'
WATCH_DEVCONTAINER = ".devcontainer/devcontainer.json .devcontainer/devcontainer.template.json\n"


@pytest.fixture
def watching(bare_project: Path, kit: Path) -> Path:
    (bare_project / ".claude" / "kit").mkdir(parents=True)
    (bare_project / ".claude" / "kit" / "watched").write_text(
        "# ours, reported when the kit's template changes\n" + WATCH_DEVCONTAINER)
    (bare_project / ".devcontainer").mkdir()
    (bare_project / ".devcontainer" / "devcontainer.json").write_text(OURS)
    done = sync(bare_project, kit, "--adopt")
    assert done.returncode == 0, done.stderr
    assert "Watched files" in done.stdout and "`.devcontainer/devcontainer.json`" in done.stdout
    return bare_project


def test_adopt_keeps_a_watched_file_and_records_its_source(watching, kit):
    assert (watching / ".devcontainer" / "devcontainer.json").read_text() == OURS
    lock = json.loads((watching / ".claude" / "kit" / "kit.lock").read_text())
    template = (kit / ".devcontainer" / "devcontainer.template.json").read_bytes()
    assert lock["watched"] == {".devcontainer/devcontainer.json": hashlib.sha256(template).hexdigest()}
    assert ".devcontainer/devcontainer.json" not in lock["files"]
    assert subprocess.run(["python3", "tools/kit/build.py", "--check"], cwd=watching).returncode == 0
    assert "Nothing to sync" in sync(watching, kit).stdout


def test_a_change_to_a_watched_files_source_is_reported_and_never_applied(watching, kit):
    template = kit / ".devcontainer" / "devcontainer.template.json"
    template.write_text(template.read_text().replace("{", '{"newKey": 1, ', 1))
    commit_all(kit)
    done = sync(watching, kit)
    assert done.returncode == 0, done.stderr
    assert "Watched files" in done.stdout
    assert ("- `.devcontainer/devcontainer.json` from `.devcontainer/devcontainer.template.json`"
            in done.stdout)
    assert (watching / ".devcontainer" / "devcontainer.json").read_text() == OURS
    assert "Nothing to sync" in sync(watching, kit).stdout


def test_a_watched_file_is_never_deleted_and_is_written_once_if_missing(watching, kit):
    (watching / ".devcontainer" / "devcontainer.json").unlink()
    done = sync(watching, kit)
    assert done.returncode == 0, done.stderr
    assert ((watching / ".devcontainer" / "devcontainer.json").read_bytes()
            == (kit / ".devcontainer" / "devcontainer.template.json").read_bytes())


def test_taking_over_a_kit_file_later_does_not_count_as_editing_it(project, kit):
    guard = project / ".claude" / "hooks" / "guard-awk.py"
    guard.write_text(guard.read_text() + "# ours now\n")
    (project / ".claude" / "kit" / "watched").write_text(".claude/hooks/guard-awk.py\n")
    done = sync(project, kit)
    assert done.returncode == 0, done.stderr
    assert guard.read_text().endswith("# ours now\n")
    lock = json.loads((project / ".claude" / "kit" / "kit.lock").read_text())
    assert ".claude/hooks/guard-awk.py" in lock["watched"] and ".claude/hooks/guard-awk.py" not in lock["files"]


@pytest.mark.parametrize("line", [".devcontainer/devcontainer.json no/such/source\n",
                                  "/etc/passwd\n", "a b c\n", "../x\n"])
def test_a_bad_watched_line_is_refused(project, kit, line):
    (project / ".claude" / "kit" / "watched").write_text(line)
    before = snapshot(project)
    done = sync(project, kit)
    assert done.returncode == 1 and "watched" in done.stderr
    assert snapshot(project) == before


def test_status_prints_the_kit_commit(project, kit):
    done = subprocess.run(["python3", "tools/kit/sync.py", "--status"], cwd=project,
                          capture_output=True, text=True)
    assert done.stdout.strip() == f"kit: helen-contains-claude-webdev@{git(kit, 'rev-parse', 'HEAD').strip()}"


def test_refuses_to_sync_the_kit_itself(kit, tmp_path):
    other = tmp_path / "other-kit"
    shutil.copytree(kit, other)
    done = sync(other, kit)
    assert done.returncode == 1 and "this is the kit itself" in done.stderr


def test_refuses_a_dirty_kit_clone(project, kit):
    (kit / "stray.txt").write_text("x")
    done = sync(project, kit)
    assert done.returncode == 1 and "uncommitted changes" in done.stderr


def test_a_jekyll_project_must_exclude_the_kit(project):
    """The site check that ships to projects, run inside one."""
    def site_check() -> subprocess.CompletedProcess:
        return subprocess.run(["python3", "-m", "pytest", "-q", "tests/kit/test_site_excludes_kit.py"],
                              cwd=project, capture_output=True, text=True, timeout=120)

    (project / "_config.yml").write_text("title: x\nexclude:\n  - Gemfile\n")
    done = site_check()
    assert done.returncode == 1 and "scripts/gh-read.sh" in done.stdout, done.stdout
    (project / "_config.yml").write_text("title: x\nexclude: [Gemfile, scripts, tests, tools, pytest.ini]\n")
    (project / "_site" / "tools" / "dev").mkdir(parents=True)
    (project / "_site" / "tools" / "dev" / "shoot.js").write_text("x")
    done = site_check()
    assert done.returncode == 1 and "tools/dev/shoot.js" in done.stdout, done.stdout
    shutil.rmtree(project / "_site" / "tools")
    done = site_check()
    assert done.returncode == 0, done.stdout


def test_the_kits_tests_leave_a_projects_own_conftest_and_names_alone(project):
    """A project's tests/conftest.py and a project test sharing a kit test's
    name, run in one session with the kit's tests collected first."""
    tests = project / "tests"
    (tests / "conftest.py").write_text('ROOT = "the project\'s"\n')
    (tests / "test_ours.py").write_text(
        "from conftest import ROOT\n\ndef test_it():\n    assert ROOT == \"the project's\"\n")
    (tests / "test_hooks.py").write_text("def test_a_project_test_of_the_same_name():\n    pass\n")
    done = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                           "tests/kit/test_kit_lock.py", "tests/kit/test_hooks.py",
                           "tests/test_ours.py", "tests/test_hooks.py"],
                          cwd=project, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stdout


def test_the_projects_suite_goes_red_on_an_edited_kit_file(project):
    """The lock test that ships to projects, run inside one."""
    guard = project / ".claude" / "hooks" / "guard-awk.py"
    guard.write_text(guard.read_text() + "# local tweak\n")
    done = subprocess.run(["python3", "-m", "pytest", "-q", "tests/kit/test_kit_lock.py"],
                          cwd=project, capture_output=True, text=True, timeout=120)
    assert done.returncode == 1, done.stdout
    assert ".claude/hooks/guard-awk.py" in done.stdout
    assert "Make this change in helen-contains-claude-webdev" in done.stdout
    guard.write_text(guard.read_text().replace("# local tweak\n", ""))
    done = subprocess.run(["python3", "-m", "pytest", "-q", "tests/kit/test_kit_lock.py"],
                          cwd=project, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stdout
