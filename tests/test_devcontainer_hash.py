"""The devcontainer image's build-input hash — `.devcontainer/build_inputs_hash.py`.

`run.sh` stamps every image it builds with this hash and rebuilds when the stamp
no longer matches, so this function decides when Helen gets a fresh container.
Two directions matter and they are NOT symmetric:

  * A hash that changes when it should not costs one fully-cached rebuild:
    a second, no network. Noise.
  * A hash that does NOT change when it should means the image silently no
    longer matches the Dockerfile — which is the exact bug the stamp was built
    for (#1180, Helen: "I'd rebuilt the image... but my containers were being
    created from an older one").

So every test here that pins an exclusion is paired with one proving a real
build input still counts, and the `.dockerignore` parser's failure mode is
"hash everything" rather than "hash less than you thought".
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE = ROOT / ".devcontainer" / "build_inputs_hash.py"


def _load():
    """Import it by path: `.devcontainer` is not a package and never will be."""
    spec = importlib.util.spec_from_file_location("build_inputs_hash", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def hasher():
    assert MODULE.is_file(), (
        f"{MODULE} is missing. run.sh calls it on every launch, so its absence "
        f"stops the container starting, not just this test."
    )
    return _load()


def _context(tmp_path: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    context = tmp_path / ".devcontainer"
    context.mkdir()
    for name, body in files.items():
        (context / name).write_text(body, encoding="utf-8")
    return context


def test_the_real_devcontainer_hashes_to_something_stable(hasher):
    first = hasher.build_inputs_hash(ROOT / ".devcontainer")
    second = hasher.build_inputs_hash(ROOT / ".devcontainer")
    assert first == second
    assert len(first) == 64, first


def test_editing_the_dockerfile_changes_the_hash(tmp_path, hasher):
    """The direction that must never fail: a real build input counts."""
    context = _context(tmp_path, {"Dockerfile": "FROM ruby:3.3\n",
                                  ".dockerignore": "README.md\n",
                                  "README.md": "docs\n"})
    before = hasher.build_inputs_hash(context)
    (context / "Dockerfile").write_text("FROM ruby:3.3\nRUN apt-get update\n",
                                        encoding="utf-8")
    assert hasher.build_inputs_hash(context) != before


def test_editing_an_ignored_file_does_not_change_the_hash(tmp_path, hasher):
    """#1191: editing the README or run.sh used to cost a rebuild each time."""
    context = _context(tmp_path, {"Dockerfile": "FROM ruby:3.3\n",
                                  ".dockerignore": "README.md\nrun.sh\n",
                                  "README.md": "docs\n",
                                  "run.sh": "echo hi\n"})
    before = hasher.build_inputs_hash(context)
    (context / "README.md").write_text("docs, rewritten at length\n",
                                       encoding="utf-8")
    (context / "run.sh").write_text("echo hi\necho there\n", encoding="utf-8")
    assert hasher.build_inputs_hash(context) == before


def test_changing_what_is_excluded_changes_the_hash(tmp_path, hasher):
    """The ignore file is itself a build input: it decides what Docker receives,
    so the stamp has to move when it changes, or an image built from a narrower
    context keeps a stamp that says otherwise."""
    context = _context(tmp_path, {"Dockerfile": "FROM ruby:3.3\n",
                                  ".dockerignore": "README.md\n",
                                  "README.md": "docs\n"})
    before = hasher.build_inputs_hash(context)
    (context / ".dockerignore").write_text("", encoding="utf-8")
    assert hasher.build_inputs_hash(context) != before


def test_a_pattern_it_cannot_parse_falls_back_to_hashing_everything(tmp_path, hasher, capsys):
    """A half-understood pattern must widen the hash, never narrow it.

    With `*.md` in the ignore file this could plausibly have decided nothing was
    excluded by NAME and quietly matched neither README.md nor anything else --
    which is fine here, but the same shortcut on `Dockerfile*` would stop the
    Dockerfile counting. So it refuses to guess and hashes the lot.
    """
    context = _context(tmp_path, {"Dockerfile": "FROM ruby:3.3\n",
                                  ".dockerignore": "*.md\n",
                                  "README.md": "docs\n"})
    before = hasher.build_inputs_hash(context)
    assert "not a plain filename" in capsys.readouterr().err
    (context / "README.md").write_text("changed\n", encoding="utf-8")
    assert hasher.build_inputs_hash(context) != before, (
        "an unparsable .dockerignore must fall back to hashing everything, so a "
        "README edit still moves the hash"
    )


def test_an_ignored_name_in_a_subdirectory_still_counts(tmp_path, hasher):
    """`.dockerignore` here is read as top-level names only, so a file of the
    same name nested deeper is a different file and must still be hashed."""
    context = _context(tmp_path, {"Dockerfile": "FROM ruby:3.3\n",
                                  ".dockerignore": "README.md\n",
                                  "README.md": "docs\n"})
    nested = context / "extras"
    nested.mkdir()
    (nested / "README.md").write_text("one\n", encoding="utf-8")
    before = hasher.build_inputs_hash(context)
    (nested / "README.md").write_text("two\n", encoding="utf-8")
    assert hasher.build_inputs_hash(context) != before


def test_renaming_a_file_changes_the_hash(tmp_path, hasher):
    """The path is hashed as well as the bytes: a COPY names a path, so moving a
    file changes what the image is built from even with identical content."""
    context = _context(tmp_path, {"Dockerfile": "FROM ruby:3.3\n",
                                  "init-firewall.sh": "echo firewall\n"})
    before = hasher.build_inputs_hash(context)
    (context / "init-firewall.sh").rename(context / "firewall.sh")
    assert hasher.build_inputs_hash(context) != before


def _copied_paths(dockerfile: str) -> list[str]:
    """Every path a COPY or ADD pulls out of the build context.

    ONLY those instructions, and this precision is the point rather than
    pedantry: the first version of this test substring-matched the whole
    Dockerfile and failed on the word "README.md" inside a prose comment
    (`see .devcontainer/README.md on why that's deliberate`). A guard that fires
    on a harmless mention is one you learn to route around, which this
    repository has recorded about four other hooks.

    Continuation lines are joined first, so a multi-line COPY is read whole.
    The last argument of a COPY is the DESTINATION inside the image, not a
    context path, so it is dropped.
    """
    joined = dockerfile.replace("\\\n", " ")
    paths: list[str] = []
    for line in joined.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        head, _, rest = line.partition(" ")
        if head.upper() not in ("COPY", "ADD"):
            continue
        args = [a for a in rest.split() if not a.startswith("--")]
        paths += args[:-1]          # everything but the destination
    return paths


def test_the_real_dockerignore_only_names_files_the_image_does_not_copy(hasher):
    """A live guard on the committed ignore file, not on a fixture.

    Excluding a file the Dockerfile actually COPYs would stop the stamp seeing
    changes to it — the missed-rebuild direction, which is the one that matters.
    """
    ignore = ROOT / ".devcontainer" / ".dockerignore"
    if not ignore.is_file():
        pytest.skip(".devcontainer/.dockerignore does not exist")
    excluded = {line.strip() for line in ignore.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")}
    assert excluded, (
        ".dockerignore exists but excludes nothing -- this check would pass "
        "while checking nothing, which is the failure this suite is built around."
    )
    copied = _copied_paths((ROOT / ".devcontainer" / "Dockerfile").read_text(encoding="utf-8"))
    assert copied, (
        "no COPY or ADD found in the Dockerfile -- the parser has stopped "
        "matching, so this check is vacuous."
    )
    for name in excluded:
        assert name not in copied, (
            f".dockerignore excludes {name!r}, but the Dockerfile COPYs it. "
            f"Excluding a real build input from the hash means a change to it "
            f"will not rebuild the image, which is the bug the stamp exists for."
        )
