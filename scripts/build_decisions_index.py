"""Write model_instructions/DECISIONS_INDEX.md: one line per journal entry.

    python3 scripts/build_decisions_index.py --check    # diff, exit 1 if stale
    python3 scripts/build_decisions_index.py --write    # rewrite the index

WHY (#1202, 2026-09-29). DECISIONS.md is thousands of lines and no session can
read it whole, so "find its section in the journal before re-opening anything"
works only by grep -- and a ruling you do not know the keyword for is a ruling
you cannot find. The index is one line per top-level entry, in journal order:

    - 2026-09-20 · §10 · #1127 · "It's not useful to have a situation where …

so a session greps a few hundred lines of headlines, then greps the journal for
the headline's words to land on the entry itself.

NO LINE NUMBERS, ON PURPOSE (Helen, 2026-09-29). The issue proposed them, and a
generated, test-enforced file is the one place the "name files, never line
numbers" rule could bend. It was not bent because of merges: nearly every
branch adds a journal entry, one entry near the top renumbers every entry
below it, so two open branches would each rewrite most of the index and
conflict on every merge -- and an index merged wrong is a red test on `main`,
which is a deploy outage (MANUAL §10). Without them, a new entry is one new
index line, and two branches' additions merge exactly as the journal does.

NOTHING IN THE JOURNAL CHANGES. Every rule below reads the journal as it is
written, which is in several shapes; the least lossy reading of each:

  ENTRY    a line starting `- ` in column 0, running to the next one, a
           heading, or a `---` rule. Indented bullets are part of their entry.
  SECTION  the `§…` label of the nearest `##`/`###` heading above it.
  DATE     the first YYYY-MM-DD in the entry's first bold span, else in its
           first paragraph, else anywhere in the entry, else in its section's
           heading (§8.2's sub-entries are dated only there), else `undated`.
  ISSUES   every `#N` in the date span and the headline, in order, deduped.
  HEADLINE the first bold span in the first paragraph that says something
           once dates, issue numbers and joining words are stripped out --
           "**2026-09-20, #1127** — **"It's not useful…"**" indexes the second
           span. A leading date or issue is stripped, since both are fields
           already. A span under SHORT characters -- §12's stories are
           named "**The unpushed branch**" and nothing else -- takes the rest
           of its sentence with it, because a name alone gives grep nothing.
           No such span: the paragraph's first sentence, plain. Markdown
           emphasis and code ticks are removed so the words grep, and
           anything past HEADLINE_MAX characters ends in an ellipsis.

Measured on 2026-09-29: 547 entries, 21 undated -- §12's stories and a few
sub-entries that name no date anywhere, which is the truth about them.

tests/test_decisions_index.py runs `check()`, so the index cannot go stale:
edit the journal, run `--write`, commit both.
"""
from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "model_instructions" / "DECISIONS.md"
INDEX = ROOT / "model_instructions" / "DECISIONS_INDEX.md"

HEADLINE_MAX = 180
DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
ISSUE = re.compile(r"(?<![\w/])#(\d+)\b")
BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
SECTION = re.compile(r"^#{2,3} (§[\w.]+(?: / §[\w.]+)*)")
# What is left of a span once it is only a date and its issue: "2026-09-20,
# #1127", "#801, built 2026-09-07". Two letters or fewer is not a headline.
FILLER = re.compile(r"\b(?:built|and|on|the|from)\b|[\s,;:.()\-–—/+&]+")
# A headline's own leading date and issue, already in the line's fields.
LEAD = re.compile(r"^(?:20\d\d-\d\d-\d\d|#\d+|[\s,;:—–-])+")
SHORT = 40

HEADER = """\
# DECISIONS_INDEX

**GENERATED -- do not edit by hand.** `python3 scripts/build_decisions_index.py
--write` rewrites it from `DECISIONS.md`, and `tests/test_decisions_index.py`
fails whenever the two disagree. Edit the journal, re-run, commit both.

**One line per journal entry, in journal order**: date · section · issues ·
headline. Grep this file first, then grep `DECISIONS.md` for a few words of the
headline to land on the entry. A date of `undated` is an entry that names none.

**No line numbers, deliberately** (Helen, 2026-09-29): one new entry near the
top would renumber every line below it, so any two branches that each add an
entry would conflict here on every merge. The script's docstring has the
argument and the rules each field is read by.

"""


def _plain(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", text)
    return text.strip(" —–-:;,")


def _says_something(span: str) -> bool:
    rest = FILLER.sub(" ", ISSUE.sub(" ", DATE.sub(" ", span)))
    return len(re.sub(r"\W", "", rest)) > 2


def _clip(text: str) -> str:
    if len(text) <= HEADLINE_MAX:
        return text
    return text[:HEADLINE_MAX].rsplit(" ", 1)[0].rstrip(" ,;:—–-") + " …"


def entries(journal: str = None):
    """Yield (date, section, issues, headline) per top-level entry."""
    lines = (journal if journal is not None
             else JOURNAL.read_text(encoding="utf-8")).splitlines()
    section, heading = "§?", ""
    current: list[str] = []

    def finish():
        if current:
            yield _entry(current, section, heading)

    for line in lines:
        m = SECTION.match(line)
        if m or re.match(r"#{1,6} ", line) or line.strip() == "---":
            yield from finish()
            current = []
            if m:
                section, heading = m.group(1), line
            continue
        if line.startswith("- "):
            yield from finish()
            current = [line[2:]]
        elif current:
            current.append(line)
    yield from finish()


def _entry(body_lines, section, heading):
    whole = "\n".join(body_lines)
    first_para = whole.split("\n\n", 1)[0]
    spans = BOLD.findall(first_para)

    date_src = spans[0] if spans else ""
    date = (DATE.search(date_src) or DATE.search(first_para)
            or DATE.search(whole) or DATE.search(heading))
    date = date.group(0) if date else "undated"

    headline_span = next((s for s in spans if _says_something(s)), None)
    if headline_span is not None:
        headline = _plain(LEAD.sub("", _plain(headline_span)))
        if len(headline) < SHORT:
            # "**The unpushed branch** — the story…": a name alone gives grep
            # nothing to find, so the sentence it opens comes with it.
            after = first_para.split("**" + headline_span + "**", 1)[-1]
            after = re.split(r"(?<=[.!?])\s", _plain(after), 1)[0]
            if after:
                headline = f"{headline.rstrip('.')} — {after}"
    else:
        text = first_para
        if spans:                        # drop the date span, keep what follows
            text = first_para.split("**" + spans[0] + "**", 1)[-1]
        text = _plain(text)
        headline = re.split(r"(?<=[.!?])\s", text, 1)[0]

    issues = []
    for src in (date_src, headline_span or headline):
        for n in ISSUE.findall(src):
            if f"#{n}" not in issues:
                issues.append(f"#{n}")
    return date, section, issues, _clip(headline)


def render(journal: str = None) -> str:
    out = [HEADER]
    for date, section, issues, headline in entries(journal):
        fields = [date, section] + ([" ".join(issues)] if issues else []) + [headline]
        out.append("- " + " · ".join(fields) + "\n")
    return "".join(out)


def check():
    """(a unified diff of what --write would do). Empty when the index is current."""
    want = render()
    have = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    return "".join(difflib.unified_diff(
        have.splitlines(keepends=True), want.splitlines(keepends=True),
        "DECISIONS_INDEX.md (committed)", "DECISIONS_INDEX.md (generated)", n=0))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="diff, exit 1 if stale")
    mode.add_argument("--write", action="store_true", help="rewrite the index")
    args = parser.parse_args(argv)
    if args.write:
        INDEX.write_text(render(), encoding="utf-8")
        print(f"wrote {INDEX.relative_to(ROOT)}")
        return 0
    diff = check()
    if diff:
        print(diff)
        print("\nStale. Run: python3 scripts/build_decisions_index.py --write")
        return 1
    print("DECISIONS_INDEX.md is current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
