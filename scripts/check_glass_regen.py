"""Would regenerating the glass icons reproduce what is shipped, byte for byte?

    python3 scripts/check_glass_regen.py

`scripts/normalise_glass_icons.py` rebuilds the whole icon set from
`_design_sources/cocktails/glasses/`, deleting the published directory first.
Which source becomes which icon is decided by three hand-maintained registries
in that file: SKIP, SOLID and RENAME. A missing entry does not fail there: it
silently reverts a drawing, or writes an orphan beside the right one. Run this
after touching them (DECISIONS §9.11).

It deletes and writes nothing: it resolves names and classes as the
generator's main() does, normalises in memory, and diffs against
`_includes/icons/glasses/`. Exit 1 on any unexpected line.

  COLLISION  two archived sources resolve to one published name, and
             `sorted()` decides the winner. Add the loser to SKIP.
  ORPHAN     a source resolves to a name nothing ships. Usually a missing
             RENAME entry.
  UNREACHED  a shipped icon that no archived source produces: regenerating
             would delete it.
  DIFFERS    regenerating would change the file: the shipped copy was
             hand-edited, or the source changed and was never republished.
  REFUSED    the generator's own guards rejected the source; the message says
             which guard.

Nothing is expected to differ. `KNOWN` is where a deliberate divergence is
recorded, and it is meant to stay empty.
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import normalise_glass_icons as N  # noqa: E402

ARCHIVE = ROOT / "_design_sources" / "cocktails" / "glasses"
SHIPPED = ROOT / "_includes" / "icons" / "glasses"

# Named so the report can say "expected" rather than leaving the reader to
# remember. Keep this empty if you can; every entry is a known lie.
KNOWN = {}


def main():
    if not ARCHIVE.is_dir():
        raise SystemExit("%s does not exist." % ARCHIVE.relative_to(ROOT))

    sources = sorted(ARCHIVE.glob("*.svg"))
    usable = [s for s in sources if s.name not in N.SKIP]

    produced, problems, expected = {}, [], []
    for p in usable:
        stem = p.stem.replace("glass-", "")
        name = N.RENAME.get(stem, stem)
        cls = "glass-icon-solid" if p.name in N.SOLID else "glass-icon-line"

        if name in produced:
            problems.append("COLLISION  %-22s written by both %s and %s"
                            % (name, produced[name], p.name))
            continue
        produced[name] = p.name

        try:
            got = N.normalise(p.read_text(encoding="utf-8"), name, cls)
        except SystemExit as exc:
            problems.append("REFUSED    %-22s %s" % (name, exc))
            continue

        target = SHIPPED / ("%s.svg" % name)
        if not target.exists():
            problems.append("ORPHAN     %-22s would be written; nothing ships it" % name)
        elif got != target.read_text(encoding="utf-8"):
            line = "DIFFERS    %-22s regenerating would change the shipped file" % name
            (expected if name in KNOWN else problems).append(
                line + (" [expected: %s]" % KNOWN[name] if name in KNOWN else ""))

    for shipped in sorted(SHIPPED.glob("*.svg")):
        if shipped.stem not in produced:
            problems.append("UNREACHED  %-22s is shipped; no archived source makes it"
                            % shipped.stem)

    print("\n%d archived sources, %d after SKIP, %d icons produced, %d shipped"
          % (len(sources), len(usable), len(produced), len(list(SHIPPED.glob("*.svg")))))
    for line in expected:
        print("  " + line)
    for line in problems:
        print("  " + line)

    if problems:
        print("\n%d unexpected problem(s). A regeneration would not be safe." % len(problems))
        return 1
    print("\nOK -- a wholesale regeneration reproduces the shipped set%s."
          % (", bar the expected divergence above" if expected else " exactly"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
