"""The handshake between this repo's RULES and the private drafts' DATA. #624.

WHAT GOES WRONG WITHOUT IT. A rule lives here, in public; the data that has to
satisfy the rule lives in `_food_drafts/` or `_cocktail_drafts/`, which are
separate private repositories with their own `main`. Tightening a rule is
therefore TWO merges, and nothing made them arrive together:

  - Between them, `main` here is RED for anyone whose drafts clone is current,
    and the failures name real drinks and read exactly like a regression in
    whatever you were last working on.
  - CI is GREEN throughout, and cannot be otherwise: the runner has no drafts,
    so the corpus those tests read is empty and they pass vacuously.
  - Nothing anywhere records WHICH private branch makes it green again.

Twice now, at least. 2026-08-31, the garnish vocabulary: three tests failed
here while the `none` -> `no garnish` rename sat unmerged on a drafts branch.
2026-09-05, `made_before`: this repo's new guards required a field that only
existed on a private branch for the length of an afternoon.

WHAT THIS DOES, AND WHAT IT DELIBERATELY DOES NOT DO. It does not stop the two
merges being two merges -- two repositories mean two merges, and sometimes the
gap is unavoidable. It makes the gap SAY SO. Each drafts repo records the
schema it has been migrated to in a `SCHEMA_VERSION` file at its root; this
module declares the version the rules here need. Out of step, you get one
failure that names the mismatch, says which side is behind, and tells you the
other failures in the run are its fault -- instead of N cryptic ones.

WHY A HAND-MAINTAINED INTEGER rather than a fingerprint computed from the
schema constants. A fingerprint would bump itself, which sounds better and is
worse: NOT every schema change needs a data migration. Adding an optional key
requires nothing of the existing drinks, and a derived version would demand a
drafts commit anyway. The bump is a judgement -- "this change requires the data
to move" -- and judgements are declared, not computed. The changelog below is
the record of each one.

WHY IT IS NOT `pytest.exit()`. Stopping the run would be the tidiest way to
replace the N failures, and it is wrong: during a migration you are deliberately
out of step and you want to watch the suite go green drink by drink. A loud,
single, self-explaining FAILURE alongside the others is the honest shape.

IT CANNOT FIRE IN CI, by construction: no drafts directory, no check. That is
not a hole in it -- CI's blindness to private data is the condition this exists
to make survivable, not something a test in this repo can fix.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The version each drafts repo must have been migrated to for the rules in THIS
# checkout to be satisfiable. Bump one of these in the same commit as the rule
# that requires it, and say why in the changelog below.
REQUIRED = {
    "_cocktail_drafts": 1,
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

    ASKED HERE RATHER THAN IN THE TEST, and not to dodge anything.
    `test_every_drink_reading_test_goes_through_the_loader` forbids a test in
    test_cocktails.py from naming `DRAFTS`, because a test that globs a
    collection itself scans nothing in CI and reports green -- #540's hole.
    The handshake reads no drinks at all, so it is not that shape; routing the
    existence question through this module keeps the one-door rule intact
    without widening LOADER_GUARDS, which would be the change that actually
    weakened something.
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
            f"of this trap (HANDOVER 9.1)."
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
