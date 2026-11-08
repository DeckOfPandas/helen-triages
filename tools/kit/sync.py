"""Bring this project's kit-owned files up to a clone of the kit.

USAGE (from the project root; /kit-sync wraps it):
    python3 tools/kit/sync.py --status     print the kit commit this project runs
    python3 tools/kit/sync.py --dry-run    report what a sync would do; write nothing
    python3 tools/kit/sync.py              sync
    python3 tools/kit/sync.py --adopt [--dry-run]
                                           first sync of a project with no kit.lock
    [--kit <dir>]                          the kit clone; default tmp/kit

The kit's kit/manifest says who owns each path (see its header). A sync
1. refuses if any file .claude/kit/kit.lock records no longer matches its hash
   -- a local edit to a kit file goes to the kit first, it is never overwritten
   -- or if a file the kit newly ships already exists here with other content;
2. copies every `kit` path, deletes those the kit dropped, writes each missing
   `project` file from its template and never touches an existing one;
3. rebuilds the generated files with the new tools/kit/build.py, and rewrites
   kit.lock with the kit's commit and each kit file's sha256;
4. writes its report to tmp/kit-sync-report.md (the PR description) and prints it.

With --adopt there is no lock to check, so files that differ from the kit are
replaced and listed. Compare them first (--adopt --dry-run): a project's better
version goes to the kit before the sync, not after.

A project may take a kit or generated path as its own by listing it in
.claude/kit/watched, one `<path> [<kit source>]` per line (the source defaults
to the path itself). The sync then writes a watched path only when it is
missing, never deletes it, and build.py never generates it. kit.lock records
the source's sha256 under "watched", and the report names every watched path
whose kit source changed since the last sync, for a person to compare.

Standard library and git only. Reads the kit clone; writes only inside this
project, and nothing at all with --dry-run or --status.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

LOCK = Path(".claude/kit/kit.lock")
WATCHED = Path(".claude/kit/watched")
REPORT = Path("tmp/kit-sync-report.md")
DEFAULT_KIT = Path("tmp/kit")
MANIFEST = Path("kit/manifest")
KINDS = ("kit", "project", "generated", "kit-repo")


class SyncError(Exception):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if done.returncode != 0:
        raise SyncError(f"git {' '.join(args)} failed in {cwd}: {done.stderr.strip()}")
    return done.stdout


def read_manifest(text: str) -> list[tuple[str, str, str | None]]:
    """(kind, path, template) for each line; template only for `project`."""
    entries = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        words = line.split()
        kind = words[0]
        if kind not in KINDS or len(words) < 2 or len(words) > (3 if kind == "project" else 2):
            raise SyncError(f"kit/manifest line {number} is not `<kind> <path>`: {line!r}")
        for word in words[1:]:
            if word.startswith("/") or ".." in Path(word).parts:
                raise SyncError(f"kit/manifest line {number}: {word!r} must be a relative path inside the repo")
        entries.append((kind, words[1], words[2] if len(words) == 3 else None))
    return entries


def read_watched(root: Path) -> dict[str, str]:
    """The project's .claude/kit/watched: {path: kit source path}."""
    path = root / WATCHED
    if not path.is_file():
        return {}
    watched = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        words = line.split("#", 1)[0].split()
        if not words:
            continue
        if len(words) > 2:
            raise SyncError(f"{WATCHED} line {number} is not `<path> [<kit source>]`: {line!r}")
        for word in words:
            if word.startswith("/") or ".." in Path(word).parts:
                raise SyncError(f"{WATCHED} line {number}: {word!r} must be a relative path inside the repo")
        watched[words[0]] = words[-1]
    return watched


def tracked(kit: Path) -> list[str]:
    return [p for p in git(kit, "ls-files", "-z").split("\0") if p]


def expand(entries, files: list[str]) -> dict[str, dict[str, str | None]]:
    """Each kind -> {path: template}. A path ending in / takes every tracked file under it."""
    owned: dict[str, dict[str, str | None]] = {kind: {} for kind in KINDS}
    owner: dict[str, str] = {}
    for kind, path, template in entries:
        if path.endswith("/"):
            matched = [f for f in files if f.startswith(path)]
            if not matched:
                raise SyncError(f"kit/manifest names {path}, under which the kit tracks nothing")
        elif kind == "generated" or path in files:
            matched = [path]
        else:
            raise SyncError(f"kit/manifest names {path}, which the kit doesn't track")
        for f in matched:
            if f in owner:
                raise SyncError(f"kit/manifest claims {f} twice ({owner[f]} and {kind})")
            owner[f] = kind
            owned[kind][f] = template
    return owned


def load_lock(root: Path) -> dict | None:
    path = root / LOCK
    if not path.is_file():
        return None
    lock = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(lock.get("files"), dict) or not lock.get("kit_commit"):
        raise SyncError(f"{LOCK} has no kit_commit or files")
    return lock


def file_hash(path: Path) -> str | None:
    return sha256(path.read_bytes()) if path.is_file() else None


def edited_kit_files(root: Path, lock: dict) -> list[str]:
    """Kit-owned files that no longer match kit.lock, missing ones included."""
    return sorted(p for p, h in lock["files"].items() if file_hash(root / p) != h)


EDITED_ADVICE = ("Make each change in helen-contains-claude-webdev as a PR there (or move it "
                 "into a project-owned file), put the kit's copy back here, and sync with /kit-sync.")


def env_keys(text: str) -> list[str]:
    keys = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            keys.append(line.split("=", 1)[0])
    return keys


@dataclass
class Plan:
    kit_repo: str
    old_commit: str | None
    new_commit: str
    files: dict[str, bytes] = field(default_factory=dict)       # every kit path -> content
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    replaced: list[str] = field(default_factory=list)             # --adopt only
    removed: list[str] = field(default_factory=list)
    created: dict[str, bytes] = field(default_factory=dict)      # project files to write
    new_env_keys: list[str] = field(default_factory=list)
    watched: dict[str, str] = field(default_factory=dict)        # path -> its kit source's sha256
    watched_changed: list[str] = field(default_factory=list)     # source differs from the lock's
    watched_source: dict[str, str] = field(default_factory=dict) # path -> its kit source path

    def empty(self) -> bool:
        return (self.old_commit == self.new_commit and not self.added and not self.changed
                and not self.replaced and not self.removed and not self.created
                and not self.watched_changed)

    def devcontainer_changed(self) -> bool:
        touched = self.added + self.changed + self.replaced + self.removed + list(self.created)
        return any(p.startswith(".devcontainer/") for p in touched)


def kit_repo_name(kit: Path) -> str:
    url = git(kit, "remote", "get-url", "origin").strip()
    name = url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    return name[:-4] if name.endswith(".git") else name


def plan(root: Path, kit: Path, adopt: bool) -> Plan:
    if (root / MANIFEST).is_file():
        raise SyncError("this is the kit itself (it has kit/manifest); sync a project made from it")
    if not (kit / MANIFEST).is_file():
        raise SyncError(f"{kit} is not a clone of the kit: no {MANIFEST} -- "
                        "clone it with sh scripts/git-clone-agent.sh helen-contains-claude-webdev tmp/kit")
    if git(kit, "status", "--porcelain").strip():
        raise SyncError(f"{kit} has uncommitted changes; sync only from a clean clone")
    kit_files = tracked(kit)
    owned = expand(read_manifest((kit / MANIFEST).read_text(encoding="utf-8")), kit_files)
    watched = read_watched(root)
    for path, source in watched.items():
        if source not in kit_files:
            raise SyncError(f"{WATCHED} watches {path} against {source}, which the kit doesn't track")
        for kind in ("kit", "project", "generated"):
            owned[kind].pop(path, None)
    lock = load_lock(root)
    if lock is None and not adopt:
        raise SyncError(f"no {LOCK}: this project has never been synced. Compare it with the kit "
                        "first (--adopt --dry-run), then sync with --adopt")
    if lock is not None and adopt:
        raise SyncError(f"--adopt is only for a project with no {LOCK}")

    result = Plan(kit_repo=kit_repo_name(kit), old_commit=lock["kit_commit"] if lock else None,
                  new_commit=git(kit, "rev-parse", "HEAD").strip())
    locked = lock["files"] if lock else {}

    edited = [p for p in edited_kit_files(root, lock) if p not in watched] if lock else []
    if edited:
        raise SyncError(
            "these kit-owned files were changed in this project, so a sync would lose the change:\n"
            + "".join(f"  {p}\n" for p in edited) + EDITED_ADVICE)

    collisions = []
    for path in sorted(owned["kit"]):
        content = (kit / path).read_bytes()
        result.files[path] = content
        current = file_hash(root / path)
        if current is None:
            result.added.append(path)
        elif current == sha256(content):
            continue
        elif path in locked:
            result.changed.append(path)
        elif adopt:
            result.replaced.append(path)
        else:
            collisions.append(path)
    if collisions:
        raise SyncError(
            "the kit now ships these paths, and this project already has its own file there:\n"
            + "".join(f"  {p}\n" for p in collisions)
            + "Rename the project's file, or make it identical to the kit's, then sync.")

    result.removed = sorted(p for p in locked if p not in result.files and p not in watched
                            and (root / p).is_file())
    for path, template in sorted(owned["project"].items()):
        if not (root / path).exists():
            result.created[path] = (kit / (template or path)).read_bytes()

    recorded = lock.get("watched", {}) if lock else {}
    for path, source in sorted(watched.items()):
        content = (kit / source).read_bytes()
        result.watched[path] = sha256(content)
        result.watched_source[path] = source
        if recorded.get(path) != result.watched[path]:
            result.watched_changed.append(path)
        if not (root / path).exists():
            result.created[path] = content

    template_env = kit / ".devcontainer" / "kit.env"
    project_env = root / ".devcontainer" / "kit.env"
    if template_env.is_file() and project_env.is_file():
        have = set(env_keys(project_env.read_text(encoding="utf-8")))
        result.new_env_keys = [k for k in env_keys(template_env.read_text(encoding="utf-8")) if k not in have]
    return result


def apply(root: Path, p: Plan) -> list[str]:
    """Writes the plan; returns the generated files the rebuild changed."""
    for path in p.added + p.changed + p.replaced:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.files[path])
    for path in p.removed:
        (root / path).unlink()
    for path, content in p.created.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    lock = {"kit_repo": p.kit_repo, "kit_commit": p.new_commit,
            "files": {path: sha256(content) for path, content in sorted(p.files.items())}}
    if p.watched:
        lock["watched"] = dict(sorted(p.watched.items()))
    (root / LOCK).parent.mkdir(parents=True, exist_ok=True)
    (root / LOCK).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    done = subprocess.run([sys.executable, "tools/kit/build.py"], cwd=root, capture_output=True, text=True)
    if done.returncode != 0:
        raise SyncError("kit files are synced, but rebuilding the generated files failed:\n"
                        + done.stderr.strip()
                        + "\nFix .claude/settings.project.json or .devcontainer/kit.env, then run "
                          "python3 tools/kit/build.py")
    return [line.removeprefix("wrote ") for line in done.stdout.splitlines() if line.startswith("wrote ")]


def report(p: Plan, rebuilt: list[str] | None, dry_run: bool) -> str:
    short = p.new_commit[:12]
    if p.empty() and not rebuilt:
        return f"Kit sync: already at {p.kit_repo}@{short}. Nothing to sync.\n"
    old = p.old_commit[:12] if p.old_commit else "no kit.lock"
    lines = [f"Kit sync {'(dry run) ' if dry_run else ''}from {old} to {p.kit_repo}@{short}.", ""]

    def section(title: str, paths) -> None:
        if paths:
            lines.append(f"**{title}**")
            lines.extend(f"- `{path}`" for path in paths)
            lines.append("")

    section("Added", p.added)
    section("Changed", p.changed)
    section("Replaced (this project's copy differed from the kit's)", p.replaced)
    section("Removed (the kit no longer ships them)", p.removed)
    section("Project files created from the kit's templates: fill them in", list(p.created))
    section("Watched files whose kit source changed since the last sync: they are this "
            "project's, so compare each with its source by hand",
            [f"{path}` from `{p.watched_source[path]}" for path in p.watched_changed])
    if rebuilt is not None:
        section("Generated files rebuilt", rebuilt)
    if p.new_env_keys:
        lines.append("**`kit.env`:** the kit's template has keys this project's lacks, so run.sh uses "
                     "its defaults for them: " + ", ".join(f"`{k}`" for k in p.new_env_keys))
        lines.append("")
    if p.devcontainer_changed() or (rebuilt and ".devcontainer/devcontainer.json" in rebuilt):
        lines.append("**`.devcontainer/` changed:** after merging, run `.devcontainer/run.sh` once "
                     "from the host so the container picks it up.")
    else:
        lines.append("`.devcontainer/` is unchanged: no container rebuild needed.")
    return "\n".join(lines) + "\n"


def status(root: Path) -> str:
    if (root / MANIFEST).is_file():
        return "kit: this repo is the kit"
    lock = load_lock(root)
    if lock is None:
        return f"kit: never synced (no {LOCK})"
    return f"kit: {lock.get('kit_repo', '?')}@{lock['kit_commit']}"


def main(argv: list[str]) -> int:
    args = argv[1:]
    kit = DEFAULT_KIT
    if "--kit" in args:
        i = args.index("--kit")
        if i + 1 >= len(args):
            print(__doc__, file=sys.stderr)
            return 2
        kit = Path(args[i + 1])
        del args[i:i + 2]
    flags = set(args)
    if len(flags) != len(args) or not flags <= {"--status", "--dry-run", "--adopt"} \
            or ("--status" in flags and len(flags) > 1):
        print(__doc__, file=sys.stderr)
        return 2
    root = Path.cwd()
    try:
        if "--status" in flags:
            print(status(root))
            return 0
        dry_run = "--dry-run" in flags
        p = plan(root, kit, "--adopt" in flags)
        rebuilt = None if dry_run or p.empty() else apply(root, p)
    except (SyncError, OSError, json.JSONDecodeError) as e:
        print(f"sync.py: refused -- {e}", file=sys.stderr)
        return 1
    text = report(p, rebuilt, dry_run)
    (root / REPORT).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
