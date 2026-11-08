"""Build the generated files from their kit part and their project part.

USAGE (from the project root):
    python3 tools/kit/build.py            write both files
    python3 tools/kit/build.py --check    write nothing; exit 1 naming each stale file

.claude/settings.json      = .claude/kit/settings.kit.json + .claude/settings.project.json
.devcontainer/devcontainer.json = .devcontainer/devcontainer.template.json
                             with PROJECT_NAME from .devcontainer/kit.env

Merge rules, so the project can add to the kit but never take away from it:
- an object merges key by key; a list is the kit's items, then the project's
  items the kit lacks;
- a value the kit sets cannot be changed by the project: refused;
- an allow rule that a deny rule covers is refused, so a project allow can
  never undo a kit deny;
- a project key starting with `_` is a note for people and tests, and never
  reaches settings.json;
- every object's keys are sorted, so the same inputs write the same bytes.

A path listed in .claude/kit/watched is the project's own: it is neither
written nor checked here.

Standard library only. Writes only the two generated files.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KIT_SETTINGS = Path(".claude/kit/settings.kit.json")
PROJECT_SETTINGS = Path(".claude/settings.project.json")
SETTINGS = Path(".claude/settings.json")
KIT_ENV = Path(".devcontainer/kit.env")
DEVCONTAINER_TEMPLATE = Path(".devcontainer/devcontainer.template.json")
DEVCONTAINER = Path(".devcontainer/devcontainer.json")
WATCHED = Path(".claude/kit/watched")
VALID_NAME = re.compile(r"[a-z0-9][a-z0-9_.-]*")
RULE = re.compile(r"^(?P<tool>[A-Za-z_]+)(?:\((?P<spec>.*)\))?$")


class BuildError(Exception):
    pass


def merge(kit, project, where: str = ""):
    if isinstance(kit, dict) and isinstance(project, dict):
        merged = dict(kit)
        for key, value in project.items():
            merged[key] = merge(kit[key], value, f"{where}.{key}") if key in kit else value
        return merged
    if isinstance(kit, list) and isinstance(project, list):
        return kit + [item for item in project if item not in kit]
    if kit == project and type(kit) is type(project):
        return kit
    raise BuildError(f"the project may not change the kit's setting {where.lstrip('.')} "
                     f"({json.dumps(kit)} -> {json.dumps(project)})")


def _parse_rule(rule: str) -> tuple[str, str | None, bool]:
    """(tool, fixed part, open-ended?) -- `Bash(git log *)` is ("Bash", "git log", True)."""
    match = RULE.match(rule)
    if not match:
        raise BuildError(f"cannot read the permission rule {rule!r}")
    spec = match.group("spec")
    if spec is None:
        return match.group("tool"), None, True
    for suffix in (" *", ":*"):
        if spec.endswith(suffix):
            return match.group("tool"), spec[: -len(suffix)], True
    if spec == "*":
        return match.group("tool"), "", True
    return match.group("tool"), spec, False


def covers(deny: str, allow: str) -> bool:
    """True when some command both rules match: the deny would win, so the
    allow is a mistake. Overlap counts, not only containment."""
    d_tool, d_fixed, d_open = _parse_rule(deny)
    a_tool, a_fixed, a_open = _parse_rule(allow)
    if d_tool != a_tool:
        return False
    if d_fixed is None or a_fixed is None:
        return True

    def reaches(open_fixed: str, other: str) -> bool:
        return open_fixed == "" or other == open_fixed or other.startswith(open_fixed + " ")

    if d_open and reaches(d_fixed, a_fixed):
        return True
    if a_open and reaches(a_fixed, d_fixed):
        return True
    return d_fixed == a_fixed


def strip_notes(project: dict) -> dict:
    return {key: value for key, value in project.items() if not key.startswith("_")}


def sort_keys(value):
    if isinstance(value, dict):
        return {key: sort_keys(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [sort_keys(item) for item in value]
    return value


def build_settings(kit: dict, project: dict) -> str:
    merged = merge(kit, strip_notes(project))
    permissions = merged.get("permissions", {})
    for allow in permissions.get("allow", []):
        for deny in permissions.get("deny", []):
            if covers(deny, allow):
                raise BuildError(f"the allow rule {allow!r} is covered by the deny rule {deny!r}: "
                                 "a deny always wins, so remove the allow")
    return json.dumps(sort_keys(merged), indent=2, ensure_ascii=False) + "\n"


def read_kit_env(text: str) -> dict[str, str]:
    """The same reading run.sh does: `#` starts a comment, one pair of
    surrounding quotes is dropped."""
    values = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        key, sep, value = line.partition("=")
        if not sep:
            raise BuildError(f"kit.env: {line!r} is not KEY=value")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def build_devcontainer(template: str, kit_env: str) -> str:
    name = read_kit_env(kit_env).get("PROJECT_NAME", "")
    if not VALID_NAME.fullmatch(name):
        raise BuildError(f"kit.env: PROJECT_NAME {name!r} must be lowercase letters, digits, . _ -")
    rendered = template.replace("{{PROJECT_NAME}}", name)
    if "{{" in rendered:
        raise BuildError("devcontainer.template.json has a placeholder other than {{PROJECT_NAME}}")
    json.loads(rendered)
    return rendered


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BuildError(f"{path} is missing") from None
    except json.JSONDecodeError as e:
        raise BuildError(f"{path} is not valid JSON: {e}") from None


def watched(root: Path) -> set[Path]:
    """The first word of each line of .claude/kit/watched; sync.py checks the rest."""
    path = root / WATCHED
    if not path.is_file():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {Path(words[0]) for line in lines if (words := line.split("#", 1)[0].split())}


def outputs(root: Path) -> dict[Path, str]:
    skip = watched(root)
    built = {}
    if SETTINGS not in skip:
        project_settings = root / PROJECT_SETTINGS
        project = _load_json(project_settings) if project_settings.is_file() else {}
        built[SETTINGS] = build_settings(_load_json(root / KIT_SETTINGS), project)
    if DEVCONTAINER not in skip:
        built[DEVCONTAINER] = build_devcontainer(
            (root / DEVCONTAINER_TEMPLATE).read_text(encoding="utf-8"),
            (root / KIT_ENV).read_text(encoding="utf-8"))
    return built


def main(argv: list[str]) -> int:
    if argv[1:] not in ([], ["--check"]):
        print(__doc__, file=sys.stderr)
        return 2
    root = Path.cwd()
    try:
        built = outputs(root)
    except (BuildError, OSError) as e:
        print(f"build.py: {e}", file=sys.stderr)
        return 1
    stale = [path for path, text in built.items()
             if not (root / path).is_file() or (root / path).read_text(encoding="utf-8") != text]
    if argv[1:] == ["--check"]:
        for path in stale:
            print(f"build.py: {path} is not what the builder writes -- edit its sources, "
                  "then run python3 tools/kit/build.py", file=sys.stderr)
        return 1 if stale else 0
    for path in stale:
        (root / path).write_text(built[path], encoding="utf-8")
        print(f"wrote {path}")
    if not stale:
        print("generated files already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
