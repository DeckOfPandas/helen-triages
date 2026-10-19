"""The handshake between this repo's rules and the private drafts' data (#624).

A rule lives here; the data that must satisfy it lives in `_food_drafts/` or
`_cocktail_drafts/`, separate private repositories. Tightening a rule is two
merges, and between them `main` here is red for anyone with a current clone
while CI, which has no drafts, stays green. Each drafts repo records the
schema it has been migrated to in `SCHEMA_VERSION` at its root; this module
declares the version the rules here need, so a gap is one failure that names
the mismatch and which side is behind.

The version is a hand-maintained integer, not a fingerprint: not every schema
change needs a data migration, so the bump is a judgement. The check fails
rather than calling `pytest.exit()`, because during a migration the suite is
watched going green file by file. It cannot fire in CI: no drafts, no check.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The version each drafts repo must have been migrated to for the rules in THIS
# checkout to be satisfiable. Bump one of these in the same commit as the rule
# that requires it, and say why in the changelog below.
REQUIRED = {
    "_cocktail_drafts": 3,
    "_food_drafts": 1,
}

# What each version required of the data. One line per bump; never rewrite a
# line, because the whole value of this file is being able to read what a
# mismatch means.
CHANGELOG = {
    "_cocktail_drafts": {
        1: "2026-09-05, #722/#712 -- every drink carries `meta.made_before` as "
           "a real boolean, `meta.ship` is a rung or \"who knows\" (`QQ` is no "
           "longer a ship value), and `meta.date_last_edited` is gone.",
        2: "2026-10-04, #1213 -- every draft's top-level keys are in the order the page "
           "prints them (`TOP_LEVEL_KEYS_IN_ORDER` in tests/test_cocktails.py), "
           "written by `python3 scripts/tidy_drafts.py --site cocktails --only "
           "order --apply`.",
        3: "2026-10-18, #1413 -- `meta.ship` may also be \"IOU\" (made, liked, "
           "never rated), and `ship: \"who knows\"` exactly when `made_before: "
           "false` (`test_ship_agrees_with_made_before`).",
    },
    "_food_drafts": {
        1: "2026-09-05, #624 -- the state on the day the handshake was added. "
           "No migration; this is the baseline every later bump is measured "
           "from.",
    },
}

VERSION_FILE = "SCHEMA_VERSION"


def _read(repo: str) -> int | None:
    """The version a drafts clone claims, or None if it claims none."""
    path = ROOT / repo / VERSION_FILE
    if not path.is_file():
        return None
    try:
        return int(path.read_text(encoding="utf-8").split("#")[0].strip())
    except ValueError:
        return None


def present(repo: str) -> bool:
    """Is this drafts repo on the machine at all?

    Asked here rather than in the test:
    `test_every_drink_reading_test_goes_through_the_loader` forbids a test in
    test_cocktails.py from naming `DRAFTS`. The handshake reads no drinks, so
    the existence question goes through this module instead of widening
    LOADER_GUARDS.
    """
    return (ROOT / repo).is_dir()


def mismatch(repo: str) -> str | None:
    """A message describing how `repo` is out of step, or None if it is fine.

    Returns None when the repo is ABSENT -- that is CI, and the ordinary state
    of a fresh worktree, not a fault.
    """
    if not (ROOT / repo).is_dir():
        return None

    want = REQUIRED[repo]
    have = _read(repo)
    log = CHANGELOG[repo]

    if have == want:
        return None

    if have is None:
        return (
            f"`{repo}/{VERSION_FILE}` is missing or unreadable, and this "
            f"checkout needs schema {want}.\n"
            f"  Either the clone predates the handshake (#624) or the file was "
            f"lost. Write the version it has actually been migrated to.\n"
            f"  Schema {want} means: {log.get(want, '(undocumented)')}"
        )

    if have < want:
        needed = "\n".join(f"    {v}: {log.get(v, '(undocumented)')}"
                           for v in range(have + 1, want + 1))
        return (
            f"YOUR DRAFTS CLONE IS BEHIND. `{repo}` is at schema {have}; the "
            f"rules in this checkout need {want}.\n"
            f"  OTHER FAILURES IN THIS RUN ARE PROBABLY THIS, not a regression "
            f"in your work: tests here will report real drinks as breaking "
            f"rules whose migration simply has not arrived yet.\n"
            f"  Fetch and merge the drafts branch that carries:\n{needed}\n"
            f"  `git -C {repo} fetch` first -- a stale clone is the other half "
            f"of this trap (MANUAL 9.1)."
        )

    ahead = "\n".join(f"    {v}: {log.get(v, '(undocumented)')}"
                      for v in range(want + 1, have + 1))
    return (
        f"THIS CHECKOUT IS BEHIND THE DRAFTS. `{repo}` is at schema {have}; "
        f"the rules here only require {want}.\n"
        f"  The data has been migrated for a rule change that has not merged "
        f"in this repo yet, so a guard that should be enforcing something is "
        f"silently not. Pull the public branch that carries:\n{ahead}"
    )
