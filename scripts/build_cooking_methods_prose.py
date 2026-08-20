"""Add per-group prose and column sets to _data/food/cooking_methods.yml.

Run AFTER scripts/build_cooking_methods.py, which writes the methods; this adds the
surrounding page furniture so cooking-methods.html can render from the data
instead of duplicating it.

WHY ORDERED PROSE BLOCKS RATHER THAN NAMED FIELDS. The obvious design is
`weight_note`, `safety_note`, `caveat`, `sources` -- one key per kind. It was
rejected after actually reading the page: there are at least seven kinds
(weight-range, weight-calculus, FOOD SAFETY, group intro, Caveat, a fish timing
rule of thumb, a dated correction), they don't appear in a consistent order,
beef/pork/lamb/ham have TWO of several, and any kind I failed to anticipate
would be silently dropped on the floor.

So each group keeps two ORDERED LISTS -- prose before its table and prose after
it -- with each item carrying its original class and its inner HTML verbatim.
Nothing has to be recognised to survive. The classifier only labels things for
the template's benefit; an unrecognised paragraph still renders, in the right
place, with its markup intact.

INNER HTML IS PRESERVED, not stripped. These paragraphs carry <strong> weight
figures, <em>, and the page's only four outbound links (Waitrose x2, Jamie
Oliver, Good To Know) -- and those links live INSIDE recipe-source notes, which
is exactly what a flatten-to-text would lose without anyone noticing.

Steak, fish and shellfish are deliberately not touched: they carry no timings,
so there is no page/data divergence to close, and the fish table uses 11
rowspans and empty cells that a generic rows-loop would silently reshape.
"""
import pathlib
import re
import subprocess

import yaml

SRC = pathlib.Path("food/reference/cooking-methods.html")
OUT = pathlib.Path("_data/food/cooking_methods.yml")
# ---------------------------------------------------------------------------
# THE SOURCE IS PINNED TO GIT, NOT READ FROM THE WORKING TREE, and it has to be.
#
# This script parses food/reference/cooking-methods.html's tables. That page now
# RENDERS FROM THIS SCRIPT'S OUTPUT -- so reading the working copy makes the
# generator its own consumer: it finds no tables, emits an empty data file, and
# the page it feeds goes blank. That happened once, and the completeness test
# caught it within a minute; without the pin it would happen every time anyone
# ran this again.
#
# So this is a MIGRATION TOOL, run against the last version of the page that
# still held the tables. Re-running it reproduces that migration exactly rather
# than reflecting whatever the page says today. The data file is the source of
# truth from here on; edit it directly, or edit this script and re-run.
PRE_MIGRATION = "8bdbd27"
html = subprocess.run(
    ["git", "show", f"{PRE_MIGRATION}:food/reference/cooking-methods.html"],
    capture_output=True, text=True, check=True).stdout
assert html.count("<table>") == 15, (
    f"expected the pre-migration page with 15 tables, got {html.count('<table>')} "
    f"-- has PRE_MIGRATION drifted off the right commit?")

data = yaml.safe_load(OUT.read_text(encoding="utf-8"))

TIMING_SECTIONS = set(data)   # the eight that have methods


def inner(fragment):
    """Collapse whitespace but keep tags — see the module docstring."""
    return re.sub(r"\s+", " ", fragment).strip()


def plain(fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment)).strip()


# Removing a method from the table isn't enough: the prose around it can vouch
# for it too. Beef's sources note carried "Closed-oven-off wasn't re-checked; it
# was already appropriately hedged" -- a citation for a row that no longer
# exists, which reads as a missing row rather than a deleted one.
#
# Kept as a list of DISPLAY NAMES rather than ids, because prose refers to
# methods the way a person would. Sentence-level removal, using the same
# capital-after-whitespace boundary the notes cleaner uses, so a decimal point
# can't truncate a paragraph.
EXCLUDED_NAMES = ["Closed-oven-off"]
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\u201c])")


def drop_excluded(html):
    if not any(n in html for n in EXCLUDED_NAMES):
        return html
    kept = [s for s in SENTENCE_SPLIT.split(html)
            if not any(n in s for n in EXCLUDED_NAMES)]
    return " ".join(kept).strip()


# The source page's prose links to /food/reference/internal-temperatures/, which
# was retired on 2026-08-14 in favour of the charts. Its anchors changed too --
# the charts split beef three ways where the old tables had one #beef -- and it
# still called the figures "pull temps", the word this reference layer stopped
# using. Rewritten on the way through, so regenerating keeps it.
#
# THE PAGE IS CALLED internal-temperatures AGAIN, which makes this table read
# oddly until you know the history. There have been two pages of that name: the
# original tables page, retired 2026-08-14 when it was split into temperatures +
# timings, and the CURRENT charts page, which issue #384 renamed from
# `temperatures` back to `internal-temperatures` on 2026-08-19. So several
# mappings below now have the same path on both sides and only change the
# ANCHOR -- which is the part that still genuinely differs, because the charts
# split beef three ways and salmon out of fish.
#
# The right-hand sides pointed at `../temperatures/` until 2026-08-20, i.e. at a
# page deleted the day before, and regenerating would have re-broken ten links
# in cooking_methods.yml. Nothing caught that: the links live inside a JSON blob
# as escaped HTML, so neither the template scanner nor the built-html scanner in
# tests/test_page_links.py can see them. test_links_built_outside_templates_
# still_resolve now can.
LINK_FIXES = [
    ('../internal-temperatures/#beef"', '../internal-temperatures/#beef-tender-roasting-cuts"'),
    ('../internal-temperatures/#pork"', '../internal-temperatures/#pork"'),
    ('../internal-temperatures/#lamb"', '../internal-temperatures/#lamb"'),
    ('../internal-temperatures/#ham"', '../internal-temperatures/#ham"'),
    ('../internal-temperatures/#fish"', '../internal-temperatures/#fish-salmon"'),
    ('../internal-temperatures/"', '../internal-temperatures/"'),
    (">internal temperatures</a>", ">temperature charts</a>"),
    ("Doneness pull temps:", "Doneness temperatures:"),
    ("the internal-temperatures page", "the temperature charts"),
    # Prose mentions of the page by name, not as a link -- "(90–95°C on the
    # internal-temperatures page)". Same retired page, no anchor to fix.
    ("internal-temperatures page", "temperature charts page"),
    ("on the <a", "on the <a"),
]


def relink(html):
    for a, b in LINK_FIXES:
        html = html.replace(a, b)
    return html


def kind_of(cls, text):
    if cls == "recipe-source":
        return "sources"
    low = text.lower()
    if low.startswith("weight"):
        return "weight"
    if low.startswith("food safety"):
        return "safety"
    if low.startswith("caveat"):
        return "caveat"
    if low.startswith("see also"):
        return "see_also"
    if low.startswith("correction,"):
        return "correction"
    return "prose"


sections = re.split(r'<h2 class="recipe-section-heading" id="([^"]+)"', html)
counted = 0

for i in range(1, len(sections), 2):
    sid, body = sections[i], sections[i + 1]
    if sid not in TIMING_SECTIONS:
        continue

    # Walk the section in DOCUMENT ORDER. Position is the whole point: beef runs
    # subtitle -> table -> weight -> source -> subtitle -> intro -> table ->
    # weight -> source, and a template that assumed one shape would reorder it.
    tokens = []
    for m in re.finditer(
            r'<p class="recipe-section-subtitle">(.*?)</p>'
            r'|<div class="table-scroll">.*?<thead>\s*<tr>(.*?)</tr>'
            r'|<p(?:\s+class="([^"]*)")?>(.*?)</p>',
            body, re.S):
        if m.group(1) is not None:
            tokens.append(("subtitle", inner(m.group(1))))
        elif m.group(2) is not None:
            tokens.append(("table", [plain(c) for c in
                                     re.findall(r"<th>(.*?)</th>", m.group(2), re.S)]))
        else:
            cls, text = m.group(3) or "", m.group(4)
            if cls == "recipe-section-subtitle":
                continue
            tokens.append(("p", (cls, inner(text))))

    groups, current, seen_table = [], None, False
    section_see_also = None

    def open_group(name):
        return {"name": name, "columns": None, "before": [], "after": []}

    for kind, payload in tokens:
        if kind == "subtitle":
            if current:
                groups.append(current)
            current = open_group(payload)
            seen_table = False
        elif kind == "table":
            if current is None:
                current = open_group(None)
            current["columns"] = payload
            seen_table = True
        else:
            cls, text = payload
            k = kind_of(cls, plain(text))
            if current is None:
                current = open_group(None)
            if k == "see_also":
                section_see_also = text
                continue
            entry = {"kind": k, "html": relink(drop_excluded(text))}
            (current["after"] if seen_table else current["before"]).append(entry)
            counted += 1
    if current:
        groups.append(current)

    data[sid]["groups"] = groups
    if section_see_also:
        data[sid]["see_also"] = section_see_also

header = OUT.read_text(encoding="utf-8").split("\n\n", 1)[0]
extra = """#
# `groups` carries the page furniture around each table: its subtitle, its
# column names, and TWO ORDERED LISTS of prose -- `before` the table and
# `after` it -- each item keeping its original class and inner HTML verbatim.
#
# Ordered lists rather than named fields (weight_note, safety_note, ...) so that
# a kind of paragraph nobody anticipated still survives, in the right place,
# with its markup. The `kind` label is a hint for styling, not a filter: an
# unrecognised paragraph renders as `prose` rather than disappearing.
#
# Steak, fish and shellfish are absent by design -- no timings, so nothing to
# reconcile, and the fish table's 11 rowspans don't survive a generic loop."""

OUT.write_text(header + "\n" + extra + "\n\n"
               + yaml.dump(data, sort_keys=False, allow_unicode=True,
                           width=1000, default_flow_style=False),
               encoding="utf-8")
print(f"captured {counted} prose paragraphs across "
      f"{sum(len(v.get('groups', [])) for v in data.values())} groups")
for sid in data:
    g = data[sid].get("groups", [])
    print(f"  {sid:8} {len(g)} group(s): "
          + "; ".join(f"{(x['name'] or '(unnamed)')[:28]} "
                      f"[{len(x['before'])}before/{len(x['after'])}after]" for x in g))
