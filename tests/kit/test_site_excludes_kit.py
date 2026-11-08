"""No kit-owned, generated or watched file is ever part of a project's Jekyll
site, so a sync can break tooling but never the live site. Excluded in
_config.yml, and absent from the built site when there is one."""
from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "_config.yml"
GENERATED = [".claude/settings.json", ".devcontainer/devcontainer.json"]


def _scalar(value: str) -> str:
    return value.strip().strip("\"'")


def read_config(text: str) -> dict:
    """source, destination, exclude and include from _config.yml. PyYAML when
    the image has it; otherwise the plain forms Jekyll configs use."""
    try:
        import yaml
        data = yaml.safe_load(text) or {}
        return {k: data.get(k) for k in ("source", "destination", "exclude", "include")}
    except ImportError:
        pass
    data: dict = {}
    key = None
    for line in text.splitlines():
        line = re.sub(r"\s+#.*$", "", line).rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        top = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if top:
            key, rest = top.group(1), top.group(2)
            if rest.startswith("["):
                data[key] = [_scalar(v) for v in rest.strip("[]").split(",") if v.strip()]
            elif rest:
                data[key] = _scalar(rest)
            else:
                data[key] = []
            continue
        item = re.match(r"^\s+-\s*(.+)$", line)
        if item and key and isinstance(data.get(key), list):
            data[key].append(_scalar(item.group(1)))
    return {k: data.get(k) for k in ("source", "destination", "exclude", "include")}


def _matches(path: str, patterns: list[str]) -> bool:
    parts = path.split("/")
    prefixes = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
    for pattern in patterns:
        pattern = pattern.strip("/")
        if any(fnmatch.fnmatch(prefix, pattern) for prefix in prefixes):
            return True
    return False


def excluded(path: str, config: dict) -> bool:
    """Whether Jekyll leaves `path` (relative to the source) out of the site."""
    include = config.get("include") or []
    hidden = any(part[:1] in "._#~" for part in path.split("/"))
    if hidden and not _matches(path, include):
        return True
    return _matches(path, config.get("exclude") or [])


def kit_paths() -> list[str]:
    lock = ROOT / ".claude" / "kit" / "kit.lock"
    if not lock.is_file():
        return []
    data = json.loads(lock.read_text(encoding="utf-8"))
    return sorted(set(data["files"]) | set(data.get("watched", {})) | set(GENERATED))


def _site_relative(config: dict) -> tuple[Path, list[str]]:
    """The source folder, and the kit paths inside it relative to it."""
    source = (ROOT / (config.get("source") or ".")).resolve()
    inside = []
    for path in kit_paths():
        full = (ROOT / path).resolve()
        if source == full or source in full.parents:
            inside.append(str(full.relative_to(source)))
    return source, inside


@pytest.fixture
def config() -> dict:
    if not CONFIG.is_file():
        pytest.skip("no _config.yml: this project has no Jekyll site")
    assert kit_paths(), "no .claude/kit/kit.lock: sync the kit before checking the site against it"
    return read_config(CONFIG.read_text(encoding="utf-8"))


def test_config_excludes_every_kit_path(config):
    _, inside = _site_relative(config)
    built = [path for path in inside if not excluded(path, config)]
    assert not built, (f"_config.yml lets Jekyll publish kit files: {built}. Add their top-level "
                       "folders (or the files) to `exclude:` in _config.yml.")


def test_the_built_site_has_no_kit_path(config):
    source, inside = _site_relative(config)
    site = source / (config.get("destination") or "_site")
    if not site.is_dir():
        pytest.skip(f"no built site at {site}; test_config_excludes_every_kit_path still ran")
    published = [path for path in inside if (site / path).exists()]
    assert not published, f"the built site at {site} contains kit files: {published}"


# --- the reading itself, which runs in the kit too -------------------------------------------

def test_read_config_handles_block_and_flow_lists():
    text = ("source: .\nexclude:\n  - scripts/\n  - 'tests'  # ours\n"
            "include: [.well-known]\ndestination: _site\n")
    assert read_config(text) == {"source": ".", "destination": "_site",
                                 "exclude": ["scripts/", "tests"], "include": [".well-known"]}


@pytest.mark.parametrize("path,expected", [
    (".claude/hooks/guard-sed.py", True),
    (".well-known/security.txt", False),
    ("scripts/gh-read.sh", True),
    ("tools/dev/shoot.js", True),
    ("tools/kit/sync.py", True),
    ("tests/kit/test_hooks.py", False),
    ("index.md", False),
])
def test_excluded_follows_jekylls_rules(path, expected):
    config = {"exclude": ["scripts", "tools/*"], "include": [".well-known"]}
    assert excluded(path, config) is expected
