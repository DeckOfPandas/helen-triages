"""Add per-group prose and column sets to _data/food/cooking_methods.yml.

DO NOT RUN THIS. It is a spent migration tool, kept as the record of how the
page's prose reached the data. It has no flags and no `__main__` guard:
running or importing it rewrites `_data/food/cooking_methods.yml` through a
YAML dumper. That file has been edited by hand since and no longer carries
`groups` (DECISIONS §14).

It ran after scripts/build_cooking_methods.py. It reads the page as it stood
at the commit PRE_MIGRATION, through `git show`, and the data file, with the
repository root as the working directory, and adds `groups` and `see_also` to
each section that has methods.

Each group keeps two ordered lists, prose before its table and prose after
it, each item carrying a `kind` label and its inner HTML verbatim. Ordered
lists and not named fields, so that a paragraph of a kind nobody anticipated
survives in place; inner HTML and not text, because the paragraphs carry the
page's outbound links. Sections with no timings are not touched.
"""
import pathlib
import re
import subprocess

import yaml

SRC = pathlib.Path("food/reference/cooking-methods.html")
OUT = pathlib.Path("_data/food/cooking_methods.yml")
# The source is pinned to git, not read from the working tree: the page now
# renders from the data, so the working copy holds no tables. A re-run
# reproduces the migration and overwrites every hand edit made since.
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


# Removing a method from the table is not enough: the prose around it can
# vouch for it too, and a citation for a row that is gone reads as a missing
# row. Display names, not ids, because prose refers to a method as a person
# would. Removal is by sentence, on the capital-after-whitespace boundary, so
# a decimal point cannot truncate a paragraph.
EXCLUDED_NAMES = ["Closed-oven-off"]
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\u201c])")


def drop_excluded(html):
    if not any(n in html for n in EXCLUDED_NAMES):
        return html
    kept = [s for s in SENTENCE_SPLIT.split(html)
            if not any(n in s for n in EXCLUDED_NAMES)]
    return " ".join(kept).strip()


# The source page's links and wording predate the temperature charts: the
# charts split beef three ways and salmon out of fish, so the anchors differ
# where the path does not. These links end up as escaped HTML inside data,
# where only test_links_built_outside_templates_still_resolve
# (tests/test_page_links.py) can see them.
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
    # Prose mentions of the page by name, not as a link.
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

    # Walk the section in document order. Position is the point: beef runs
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
