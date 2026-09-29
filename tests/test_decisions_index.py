"""model_instructions/DECISIONS_INDEX.md matches the journal it indexes (#1202).

The index exists so a session can grep a few hundred headlines instead of
thousands of lines of journal. An index that has drifted is worse than none:
it answers "is there a ruling about this?" with a confident no. So it is
generated (scripts/build_decisions_index.py) and this test holds the committed
copy to the generator's output, both directions.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_decisions_index as bdi  # noqa: E402


def test_the_rulings_index_matches_the_journal():
    diff = bdi.check()
    assert not diff, (
        "model_instructions/DECISIONS_INDEX.md is stale against DECISIONS.md:\n"
        + diff[:3000]
        + "\nRun: python3 scripts/build_decisions_index.py --write\n"
          "and commit the index with the journal edit. Never hand-edit it."
    )


def test_the_rulings_index_is_not_vacuous():
    """A parser that stopped matching would generate a header and no lines,
    and a committed empty index would then match itself perfectly."""
    rows = list(bdi.entries())
    journal = bdi.JOURNAL.read_text(encoding="utf-8")
    top_level = len(re.findall(r"^- ", journal, re.M))
    assert len(rows) == top_level, (
        f"{top_level} top-level entries in the journal, {len(rows)} indexed")
    assert len(rows) > 400, f"only {len(rows)} entries indexed -- is the parser matching?"

    undated = [r for r in rows if r[0] == "undated"]
    assert len(undated) < len(rows) // 10, (
        f"{len(undated)} of {len(rows)} entries read as undated -- the date "
        f"rule has probably stopped matching")
    unsectioned = [r for r in rows if r[1] == "§?"]
    assert not unsectioned, f"{len(unsectioned)} entries sit above any § heading"
    empty = [r for r in rows if len(r[3]) < 5]
    assert not empty, f"entries with no usable headline: {empty[:5]}"
