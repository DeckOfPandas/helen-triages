#!/usr/bin/env python3
"""Check one ingest envelope, or a batch of them, with no repository at all.

    python3 envelope.py FILE [FILE ...]

Standard library and PyYAML only, so a claude.ai chat can fetch this one file
from `main` and run it on its own output before handing it to Helen:

    https://raw.githubusercontent.com/DeckOfPandas/helen-triages/main/scripts/envelope.py

For each envelope it prints the filename it earns and the fingerprint line,
or the one-line reason it would be rejected, and exits 1 if any is. A file
may be a whole batch, split at its `# ingest: <slug>` headings. The site is
read from each envelope's own marker.

This is the parser `ingest_inbox.py` imports, not a copy of it: what passes
here is exactly what Helen's repository accepts. INGEST_INBOX_DESIGN.md §6
describes the rules; `parse_envelope` is the authority.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass

import yaml

# The envelope versions this script implements. §0 of each INGEST_ONE_*.md
# tells a browser which one to write, and
# tests/test_ingest_inbox.py::test_both_documents_name_a_supported_version
# holds the two ends together: a document teaching a version this file does
# not implement is the one failure that would otherwise be silent.
SUPPORTED_VERSIONS = frozenset({1})

SITES = ("food", "cocktail")


MARKER = re.compile(r"^<!--\s*ingest\s+v(\d+)\s+([a-z]+)\s*-->$")
FENCE = re.compile(r"^```(.*)$")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)
BATCH_HEADING = re.compile(r"^#\s+ingest:\s*(\S+)\s*$")
SEPARATOR = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
HAND_BACK_HEADING = "## What I could not know"
FINGERPRINT_HEADING = "## Fingerprint"
SLUG_OK = re.compile(r"^[a-z0-9-]+$")


class Rejected(Exception):
    """A malformed envelope, with the one line that says which rule it broke."""


# --- The envelope ---

@dataclass
class Envelope:
    version: int
    site: str
    block: str          # the fenced block VERBATIM, which is what gets written
    fm: dict
    hand_back: list
    fingerprint: str


def _fenced_blocks(body: str):
    """Every fenced block as (info string, verbatim contents including its
    trailing newline). Counted rather than searched-for: `two fenced blocks` is
    a rejection, so the parser has to see the second one."""
    out, info, buf, inside = [], None, [], False
    for line in body.splitlines(keepends=True):
        match = FENCE.match(line.rstrip("\n"))
        if match and not inside:
            inside, info, buf = True, match.group(1).strip(), []
        elif match and inside:
            out.append((info, "".join(buf)))
            inside = False
        elif inside:
            buf.append(line)
    if inside:
        raise Rejected("a fenced code block is never closed")
    return out


def _strip_fences(body: str) -> str:
    """The prose half. Headings are looked for HERE so that a `##` line inside
    the file being carried can never be mistaken for the envelope's own."""
    out, inside = [], False
    for line in body.splitlines():
        if FENCE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def _section(prose: str, heading: str) -> list:
    """The non-blank lines under one `## ` heading, up to the next one."""
    lines = prose.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        raise Rejected(f"no `{heading}` section") from None
    out = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.strip():
            out.append(re.sub(r"^[-*]\s+", "", line.strip()))
    return out


QQ_LABEL = re.compile(r"^QQ( \S.*)?$")


def _reject_unlabelled_notes(fm: dict) -> None:
    """Every note an ingest adds is labelled `QQ` or `QQ <topic>`, with text
    beginning `QQ`.

    The page titles a note with no label "note", which looks finished, so an
    unread note would publish under a heading that says nothing is wrong
    (#1120). A topic after the `QQ` still reads unfinished, and leaves Helen
    the heading to keep (DECISIONS §4). Demanded of every entry but the empty
    pair, since an envelope carries no note of hers.
    """
    notes = fm.get("notes")
    if not isinstance(notes, list):
        return
    for number, note in enumerate(notes, start=1):
        if isinstance(note, str):
            problem = "is a bare string"
        elif not isinstance(note, dict):
            problem = f"is a {type(note).__name__}, not a `{{label, text}}` pair"
        elif note == {"label": "", "text": ""}:
            continue    # the empty pair: a slot for Helen, not a note (#1258)
        elif not (isinstance(note.get("label"), str)
                  and QQ_LABEL.match(note["label"])):
            problem = f"is labelled {note.get('label')!r}, not 'QQ' or 'QQ <topic>'"
        elif not (isinstance(note.get("text"), str)
                  and note["text"].lstrip().startswith("QQ")):
            problem = "has text that does not begin `QQ`"
        else:
            continue
        raise Rejected(
            f"note {number} {problem}; every note an ingest adds is "
            f'`label: "QQ"` or `"QQ <topic>"` with text beginning `QQ`, because a note with no '
            f'label is titled "note" on the page and looks finished (#1120)'
        )


def split_batch(body: str) -> list:
    """(heading slug or None, envelope text) for each envelope in one body.

    A batch is several envelopes, each under its own `# ingest: <slug>` line
    (CLAUDE_WEB_INGEST.md §2). Text before the first heading is the batch's
    index and is dropped; a horizontal rule ending a section is a separator.
    Headings inside a fence never split. A body with no heading is one
    envelope, so a single-envelope file or issue reads exactly as before.
    """
    sections, current, inside = [], None, False
    for line in body.replace("\r\n", "\n").splitlines(keepends=True):
        bare = line.rstrip("\n")
        if FENCE.match(bare):
            inside = not inside
        heading = None if inside else BATCH_HEADING.match(bare.strip())
        if heading:
            current = [heading.group(1), []]
            sections.append(current)
        elif current is not None:
            current[1].append(line)
    if not sections:
        return [(None, body)]
    out = []
    for slug, lines in sections:
        while lines and (not lines[-1].strip() or SEPARATOR.match(lines[-1].strip())):
            lines.pop()
        out.append((slug, "".join(lines) + "\n"))
    return out


def parse_envelope(body: str, site: str) -> Envelope:
    """INGEST_INBOX_DESIGN.md §6, rule for rule. Raises `Rejected` with one line."""
    lines = [line.rstrip() for line in body.replace("\r\n", "\n").split("\n")]
    first = next((line for line in lines if line.strip()), "")
    match = MARKER.match(first.strip())
    if not match:
        raise Rejected(
            f"first non-blank line is not an `<!-- ingest v<N> <site> -->` "
            f"marker: {first.strip()[:60]!r}"
        )
    version, named_site = int(match.group(1)), match.group(2)
    if named_site not in SITES:
        raise Rejected(
            f"marker names site {named_site!r}, which is not one of "
            f"{', '.join(SITES)}"
        )
    if version not in SUPPORTED_VERSIONS:
        raise Rejected(
            f"envelope is v{version} and this script implements "
            f"v{'/v'.join(str(v) for v in sorted(SUPPORTED_VERSIONS))}"
        )
    if named_site != site:
        raise Rejected(f"marker says site {named_site!r} but --site is {site!r}")

    blocks = _fenced_blocks(body)
    if len(blocks) != 1:
        raise Rejected(
            f"{len(blocks)} fenced code blocks; the envelope carries exactly "
            f"one, holding the whole file"
        )
    info, block = blocks[0]
    if info not in ("", "yaml"):
        raise Rejected(
            f"the fenced block's info string is {info!r}; it must be `yaml` or "
            f"empty"
        )
    if not block.startswith("---\n"):
        raise Rejected(
            "the fenced block does not begin with `---`; it must be the whole "
            "file, front matter and all"
        )
    fm_match = FRONT_MATTER.match(block)
    if not fm_match:
        raise Rejected("the fenced block's front matter is never closed with `---`")
    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as exc:
        raise Rejected(
            f"the fenced block is not valid YAML: "
            f"{str(exc).splitlines()[0][:80]}"
        ) from None
    if not isinstance(fm, dict):
        raise Rejected(
            f"the fenced block's YAML is a {type(fm).__name__}, not a mapping"
        )
    title = fm.get("title")
    if not isinstance(title, str) or not title.strip():
        raise Rejected("the fenced block has no `title:`")
    _reject_unlabelled_notes(fm)

    prose = _strip_fences(body)
    hand_back = _section(prose, HAND_BACK_HEADING)
    printed = _section(prose, FINGERPRINT_HEADING)
    if len(printed) != 1:
        raise Rejected(
            f"the `{FINGERPRINT_HEADING}` section has {len(printed)} non-blank "
            f"lines; it carries exactly one"
        )

    envelope = Envelope(version, named_site, block, fm, hand_back, printed[0])
    rebuilt = fingerprint(fm, named_site)
    if rebuilt != envelope.fingerprint:
        raise Rejected(
            f"fingerprint does not match the file it sits under: envelope says "
            f"{envelope.fingerprint!r}, the file gives {rebuilt!r}"
        )
    return envelope


def fingerprint(fm: dict, site: str) -> str:
    """The title lowercased, then every amount in the file's own order.

    It compares formulas, never titles: two different drinks can share a name
    (the Sazerac case). An entry with no amount contributes nothing.
    """
    amounts = []
    if site == "food":
        for group in (fm.get("ingredient_groups") or []):
            if not isinstance(group, dict):
                continue
            for item in (group.get("items") or []):
                if isinstance(item, dict) and item.get("amount") not in (None, ""):
                    amounts.append(str(item["amount"]).strip())
    else:
        for item in (fm.get("ingredients") or []):
            if isinstance(item, dict) and item.get("amount") not in (None, ""):
                amounts.append(str(item["amount"]).strip())
    title = str(fm.get("title") or "").strip().lower()
    return " | ".join([title] + amounts)


def slug_for(title: str) -> str:
    """The whole title, folded and hyphenated, not its head clause.

    Two "with" dishes that share a head clause get distinct slugs
    (DECISIONS §4).
    """
    text = _fold(title.replace("’", "").replace("'", ""))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text)).strip("-")


def _fold(text: str) -> str:
    """Strip diacritics and case. The same fold as `test_taxonomy._fold`,
    restated because this file imports nothing from the repository;
    tests/test_ingest_inbox.py holds the two together."""
    stripped = "".join(
        c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c)
    )
    return stripped.lower()


def _check(path: str) -> int:
    """Print one line per envelope in `path`; the number rejected."""
    with open(path, encoding="utf-8") as handle:
        body = handle.read()
    bad = 0
    for heading, text in split_batch(body):
        where = f"{path} {heading}" if heading else path
        marker = MARKER.match(next((l.strip() for l in text.splitlines() if l.strip()), ""))
        site = marker.group(2) if marker else SITES[0]
        try:
            env = parse_envelope(text, site)
        except Rejected as why:
            print(f"{where}: REJECTED: {why}")
            bad += 1
            continue
        slug = slug_for(env.fm["title"])
        note = "" if heading in (None, slug) else f" (the heading says {heading!r})"
        print(f"{where}: OK, {slug}.md{note}")
        print(f"    fingerprint: {env.fingerprint}")
    return bad


def main(argv=None) -> int:
    paths = sys.argv[1:] if argv is None else argv
    if not paths:
        print(__doc__.split("\n\n")[1])
        return 2
    return 1 if sum(_check(p) for p in paths) else 0


if __name__ == "__main__":
    sys.exit(main())
