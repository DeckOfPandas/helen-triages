"""Structural rules: what a recipe file must contain, and what it must not.

One rule per test, so a failure names the rule and the file. The schema is
MANUAL §4. Run: `pytest -q tests/test_front_matter.py`.
"""
from __future__ import annotations

import re

import pytest
import yaml

from conftest import where, unquoted_scalars

pytestmark = pytest.mark.food

# `source_type` is required because nothing in a source string says whether it
# is a magazine or a book; tests/test_source_attribution.py reads the type
# rather than guessing (#406).
REQUIRED = ["title", "tagline", "source", "source_type", "main_ingredients",
            "tags", "ingredient_groups", "method_short", "meta"]

RETIRED = {
    "published": "removed from the schema",
    "date_added": "renamed to meta.date_last_edited",
    "difficulty": "removed from the schema",
    "nutrition": "removed from the schema",
    "filling_note": "folded into notes:",
    "headline_ingredient": "renamed to star_ingredient",
    "short_name": "removed from the schema, GitHub issue #169 -- confirmed "
                  "zero references in any template/JS/SCSS before removal, "
                  "2026-08-12; a leftover value is dead weight, not data",
    "cooked_before": "removed from the schema, GitHub issue #429 -- it lived "
                     "under meta: and was read by nothing",
    "date_last_edited": "removed from the schema, GitHub issue #429 -- a "
                        "hand-maintained date that git already knows exactly",
}

# Fields that belong under `meta:` and are silently ignored at the top level.
MISPLACED_META = ["rewritten", "proofread", "claude_rewritten"]


@pytest.mark.parametrize("field", REQUIRED)
def test_required_field_present(recipe, field):
    assert field in recipe.fm, (
        f"{where(recipe)} is missing the required field `{field}:`.\n"
        f"Every recipe needs all of: {', '.join(REQUIRED)}."
    )


def test_tagline_is_not_blank(recipe):
    """Present is not the same as written.

    `test_required_field_present` only checks the key exists, so
    `tagline: ""` passes it. A blank tagline is a gap on a published recipe
    and normal in `_food_drafts/`.
    """
    tagline = recipe.fm.get("tagline")
    assert isinstance(tagline, str) and tagline.strip(), (
        f"{where(recipe)} has a blank tagline ({tagline!r}).\n"
        f"Fine in _food_drafts/, not fine here — every published recipe "
        f"needs its one-line tagline written."
    )


def test_doneness_names_a_real_level(recipe, internal_temperatures):
    """`doneness` names a level the resolved node offers, and the node is one
    that offers levels at all (#189).

    Both failures are silent in Liquid: a typo'd level renders the label and
    its link with no figure between them, and `doneness` on a single-figure
    node does nothing while looking like it configures something.
    """
    ref, level = recipe.fm.get("internal_temp_ref"), recipe.fm.get("doneness")
    if not ref or not level:
        return

    node = internal_temperatures
    for key in ref.split("."):
        node = node.get(key) if isinstance(node, dict) else None
    if node is None:
        return                      # test_internal_temp_ref_resolves owns this

    assert "doneness" in node, (
        f"{where(recipe)} sets `doneness: {level}`, but {ref} has no doneness "
        f"levels — it is a single figure, so there is nothing to choose."
    )
    assert level in node["doneness"], (
        f"{where(recipe)} sets `doneness: {level}`, which {ref} doesn't offer. "
        f"It has: {sorted(node['doneness'])}"
    )


def test_internal_temp_ref_resolves(recipe, internal_temperatures):
    """`internal_temp_ref` (+ optional `doneness`) resolves to a real path in
    _data/food/internal_temperatures.yml.

    _layouts/recipe.html walks it the same way, dot-segment by dot-segment,
    and a typo'd path there renders no "Internal temp" line with no error.
    """
    ref = recipe.fm.get("internal_temp_ref")
    doneness = recipe.fm.get("doneness")

    if ref is None:
        assert doneness is None, (
            f"{where(recipe)} sets `doneness: {doneness!r}` with no "
            f"`internal_temp_ref:` to apply it to — it does nothing on its own."
        )
        return

    node = internal_temperatures
    walked = []
    for key in ref.split("."):
        walked.append(key)
        assert isinstance(node, dict) and key in node, (
            f"{where(recipe)} has `internal_temp_ref: {ref}`, but "
            f"{'.'.join(walked)} doesn't exist in "
            f"_data/food/internal_temperatures.yml."
        )
        node = node[key]

    if doneness is not None:
        assert isinstance(node, dict) and "doneness" in node, (
            f"{where(recipe)} sets `doneness: {doneness!r}`, but "
            f"internal_temp_ref: {ref} has no `doneness` map in "
            f"_data/food/internal_temperatures.yml -- that entry uses a "
            f"different shape (endpoint/target/tender_at), which doesn't "
            f"take a doneness level."
        )
        assert doneness in node["doneness"], (
            f"{where(recipe)} has `doneness: {doneness!r}`, which isn't one "
            f"of {sorted(node['doneness'].keys())} under "
            f"internal_temp_ref: {ref} in "
            f"_data/food/internal_temperatures.yml."
        )


# --- duplicate YAML keys are silent data loss ------------------------------

class _StrictLoader(yaml.SafeLoader):
    """A SafeLoader that refuses to quietly discard a repeated key."""


def _no_duplicates(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates
)


def test_front_matter_has_no_duplicate_keys(recipe):
    """A repeated key in a YAML mapping is discarded silently; the last one wins.

    yaml.safe_load accepts duplicates, and every other test reads the PARSED
    front matter, where the lost line is already gone -- so this loads with a
    loader that refuses them.
    """
    match = re.match(r"\A---\n(.*?\n)---", recipe.raw, re.S)
    try:
        yaml.load(match.group(1), Loader=_StrictLoader)
    except yaml.constructor.ConstructorError as exc:
        raise AssertionError(
            f"{where(recipe)} has a duplicate key in its front matter: {exc}.\n"
            f"YAML keeps only the last one, so whatever the earlier line said "
            f"has already been thrown away -- check what is missing from the "
            f"rendered page, not just what looks wrong in the file."
        ) from None


def test_no_retired_fields(recipe):
    found = {f: why for f, why in RETIRED.items() if f in recipe.fm}
    assert not found, (
        f"{where(recipe)} still has retired field(s): "
        + "; ".join(f"`{f}` ({why})" for f, why in found.items())
    )


def test_meta_fields_are_nested_not_top_level(recipe):
    stray = [f for f in MISPLACED_META if f in recipe.fm]
    assert not stray, (
        f"{where(recipe)} has {stray} at the top level. "
        f"These belong inside the `meta:` block — nothing in the templates "
        f"reads them from the top level, so they are silently ignored."
    )


def test_meta_block_complete(recipe):
    meta = recipe.fm.get("meta")
    assert isinstance(meta, dict), (
        f"{where(recipe)} has no `meta:` block, or it is not a mapping."
    )
    missing = [f for f in ("rewritten", "awaiting_fix", "proofread") if f not in meta]
    assert not missing, (
        f"{where(recipe)} `meta:` is missing {missing}. "
        f"All three are booleans and all three must be present. The publish "
        f"gate fails closed, so a missing `awaiting_fix` or `proofread` holds "
        f"the recipe back as surely as the wrong value; a missing `rewritten` "
        f"records no answer at all."
    )


# The three flags are read together, in the order a recipe moves through them
# (#429). Reordering a meta block changes no value, so
# `_only_invisible_keys_changed` exempts it and a fix here costs no proofread.
META_ORDER = ["rewritten", "awaiting_fix", "proofread"]


def test_meta_block_is_exactly_the_three_flags_in_order(recipe):
    meta = recipe.fm.get("meta")
    assert isinstance(meta, dict), f"{where(recipe)} has no `meta:` mapping."
    assert list(meta) == META_ORDER, (
        f"{where(recipe)} `meta:` is {list(meta)}, expected exactly "
        f"{META_ORDER}.\nThe three flags are read together and in the order a "
        f"recipe moves through them. cooked_before and date_last_edited were "
        f"retired by #429 — if one is back, it is dead weight, not data."
    )


def test_claude_rewritten_is_a_real_boolean(recipe):
    """`meta.claude_rewritten` is optional (#418), and where it appears it is
    a real boolean: a quoted "true" is a truthy string.
    """
    meta = recipe.fm.get("meta")
    if not isinstance(meta, dict) or "claude_rewritten" not in meta:
        return
    assert isinstance(meta["claude_rewritten"], bool), (
        f"{where(recipe)} has `meta.claude_rewritten: {meta['claude_rewritten']!r}`, "
        f"not a real boolean. Never quote it."
    )


def test_serves_xor_makes(recipe):
    has_serves = "serves" in recipe.fm
    has_makes = "makes" in recipe.fm
    assert has_serves != has_makes, (
        f"{where(recipe)} has "
        + ("neither `serves:` nor `makes:`" if not (has_serves or has_makes)
           else "both `serves:` and `makes:`")
        + ".\nUse `makes:` for anything you produce a quantity of (bakes, "
          "confectionery, sauces, base recipes) and `serves:` for dishes you "
          "portion out to people. Exactly one, never both."
    )


def test_method_xor_method_groups(recipe):
    has_flat = "method" in recipe.fm
    has_groups = "method_groups" in recipe.fm
    assert has_flat != has_groups, (
        f"{where(recipe)} has "
        + ("neither `method:` nor `method_groups:`" if not (has_flat or has_groups)
           else "both `method:` and `method_groups:`")
        + ".\nThey are mutually exclusive; the recipe layout renders one or the "
          "other, and having both means the second is silently dropped."
    )


def test_method_groups_have_name_and_steps(recipe):
    """A method_groups entry needs both `name` and a non-empty `steps`.

    A key typo (`step:` for `steps:`) or a missing `name` raises nothing: the
    group has no content, `recipe.method_steps` returns [] and every
    prose-scanning test has nothing left to scan.
    """
    for i, group in enumerate(recipe.fm.get("method_groups") or []):
        assert group.get("name"), (
            f"{where(recipe)} method_groups entry {i} has no `name`."
        )
        assert group.get("steps"), (
            f"{where(recipe)} method_groups entry {i} "
            f"({group.get('name')!r}) has no `steps` -- check for a "
            f"`step:` (singular) typo."
        )


def test_method_produces_actual_steps(recipe):
    """A recipe that declares `method` or `method_groups` yields at least one
    step. Every prose-scanning test iterates `method_steps`, so an empty list
    is skipped by all of them rather than failed.
    """
    if "method" not in recipe.fm and "method_groups" not in recipe.fm:
        return
    assert recipe.method_steps, (
        f"{where(recipe)} declares method/method_groups but produces zero "
        f"actual steps."
    )


def test_notes_is_a_list(recipe):
    if "notes" not in recipe.fm:
        return
    assert isinstance(recipe.fm["notes"], list), (
        f"{where(recipe)} has `notes:` as a "
        f"{type(recipe.fm['notes']).__name__}, not a list. "
        f"Notes are always a list of separate entries, never one blob — the "
        f"renderer styles each note individually."
    )


def test_note_dicts_have_label_and_text(recipe):
    """Every note is `{label, text}`, both present (#141).

    A bare string, or a dict missing either key, renders blank or unlabelled
    with no error. Published recipes only: this test never reads
    `_food_drafts/`, which has its own rule in tests/test_drafts.py.
    """
    for i, note in enumerate(recipe.fm.get("notes") or [], 1):
        assert isinstance(note, dict) and note.get("label") and note.get("text"), (
            f"{where(recipe)} note {i} must be `{{label, text}}`, both "
            f"present, not {note!r}."
        )


def test_method_short_is_a_list(recipe):
    ms = recipe.fm.get("method_short")
    assert isinstance(ms, list), (
        f"{where(recipe)} has `method_short:` as a "
        f"{type(ms).__name__}, not a list. The `has_short` check in index.html "
        f"iterates it, and iterating a bare string yields nothing."
    )


def test_method_short_uses_current_placeholder(recipe):
    ms = recipe.fm.get("method_short") or []
    retired = [s for s in ms if s in ("QQ", "none")]
    assert not retired, (
        f"{where(recipe)} uses retired method_short placeholder(s) {retired}. "
        f'The current convention is a single empty string: method_short: [""]'
    )


def test_ingredient_groups_named_when_there_is_more_than_one(recipe):
    groups = recipe.fm.get("ingredient_groups") or []
    if len(groups) < 2:
        return
    unnamed = [i for i, g in enumerate(groups) if not (isinstance(g, dict) and g.get("name"))]
    assert not unnamed, (
        f"{where(recipe)} has {len(groups)} ingredient groups but group(s) "
        f"{unnamed} have no `name:`. With more than one group every group needs "
        f"a name, or the reader gets an unlabelled block followed by labelled ones."
    )


def test_group_names_omit_leading_article(recipe):
    """Group names are bare nouns: `buttercream`, not `for the buttercream`.

    The recipe template renders ingredient group headings as "For the {name}:",
    so a name that already carries the article comes out as "For the for the
    dressing:" or "For the the icing:". Method groups render the name bare, so
    a leading article reads oddly there too.
    """
    offenders = []
    for key in ("ingredient_groups", "method_groups"):
        for group in recipe.fm.get(key) or []:
            name = group.get("name") if isinstance(group, dict) else None
            if name and re.match(r"^(for the |for |the )", name, re.I):
                offenders.append(f"{key}: {name!r}")
    assert not offenders, (
        f"{where(recipe)} has group name(s) with a leading article: {offenders}.\n"
        f'The template supplies "For the " itself, so `for the dressing` renders '
        f'as "For the for the dressing:". Strip the article — `dressing`.'
    )


# --- scalar front-matter values are always double-quoted (#168) -------------
# Top-level string scalars only. A `meta:` boolean is never in this list:
# quoting `proofread: true` makes it the string "true", which the publish gate
# and every `is True` check read as not set.
SCALAR_STRING_FIELDS = ["title", "tagline", "source", "prep_time",
                         "cook_time", "star_ingredient", "makes", "serves"]


def test_scalar_fields_are_quoted(recipe):
    """The named top-level scalars are double-quoted in the raw front matter.

    The scan is `conftest.unquoted_scalars`, shared with the drinks (#670);
    only the field list differs.
    """
    match = re.match(r"\A---\n(.*?\n)---", recipe.raw, re.S)
    bad = unquoted_scalars(match.group(1), SCALAR_STRING_FIELDS)
    assert not bad, (
        f"{where(recipe)} has unquoted scalar front-matter value(s): {bad!r}. "
        f'Wrap each in double quotes, e.g. title: "Beef Wellington".'
    )


def test_group_names_are_quoted(recipe):
    """Every ingredient and method group's `- name:` is double-quoted (#1416).

    Quoted and bare parse the same, so no page shows the fault and only this
    keeps the files alike. The line shape is
    `tidy_drafts.fix_group_name_quoting`'s, which fixes what this reports.
    """
    match = re.match(r"\A---\n(.*?\n)---", recipe.raw, re.S)
    bad = [m.group(1).strip() for m in
           re.finditer(r"^[ \t]*- name:[ \t]*(.+)$", match.group(1), re.M)
           if not m.group(1).strip().startswith('"')]
    assert not bad, (
        f"{where(recipe)} has unquoted group name(s): {bad!r}. Write "
        f'`- name: "dressing"`; `python3 scripts/tidy_drafts.py --only quoting '
        f"--apply` does it on a draft."
    )


# --- provenance: an agent-edited recipe is not proofread (#367) --------------
# Helen's proofread covers the words she read. An agent edit after it must set
# `meta.proofread` back to false in the same commit. The flag is a leg of the
# publish gate, so this is a test and not only a written rule.
# Ancestry, not dates, decides what the baseline exempts: a rebase rewrites
# dates but not the shape of history.
import pathlib
import subprocess

from conftest import FRONT_MATTER, DRAFTS_PRESENT, ALL_DRAFTS

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The newest commit whose agent edits Helen has read herself. A recipe whose
# newest commit is this one, or an ancestor of it, is exempt from the proofread
# flip. Moving it is Helen's grant, never a way to turn a red test green
# (DECISIONS §4.0):
#   1. run the test with the old value; it must name only the granted files;
#   2. move it in a commit of its own, quoting her grant in the message;
#   3. move it before the next agent edit, or it covers that too.
# Grants made on parallel branches need the merge commit with both behind it.
BASELINE_COMMIT = "d1e95eca"   # `fiddly and fun` on the duck confit, Helen's grant
AGENT_TRAILER = "co-authored-by: claude"



def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          cwd=ROOT).stdout


# --- keys that change nothing Helen reads -------------------------------------
# Her proofread is of the words on the page. A commit whose every difference
# is confined to INVISIBLE_KEYS, with the body byte-identical, needs no flip
# (DECISIONS §4.0). "Nothing reads this key" is a fact about the repository:
# `test_invisible_keys_are_really_invisible` scans RENDER_SURFACE for each key,
# so an entry cannot be added unless it is true, and must go the day it is not.
RENDER_SURFACE = ("_layouts", "_includes", "_plugins", "assets/js", "scripts")

INVISIBLE_KEYS = {
    "source_type": (
        "Classifies a citation (publication / book / website / person / place / "
        "unknown) so the source-shape tests can tell a dateless magazine from a "
        "finished book citation -- `Adapted from Good Food` and `Adapted from "
        "Gordon Ramsay's Ultimate Cookery Course` are the same string shape and "
        "no regex separates them. Read by tests only. Issue #406."
    ),
    "meta.cooked_before": (
        "Retired 2026-08-21, issue #429. Recorded whether Helen had cooked the "
        "recipe before; read by no layout, include, plugin or script, and "
        "listed here so REMOVING it from all 86 recipes does not invalidate 86 "
        "proofreads. Kept on the list after removal rather than deleted with "
        "it: the entry is what makes the removal commit exempt, and a future "
        "commit re-adding the key would be exempt for the same honest reason."
    ),
    "meta.date_last_edited": (
        "Retired 2026-08-21, issue #429. A hand-maintained date that git "
        "already knows exactly and nothing rendered -- see meta.cooked_before "
        "above for why the entry outlives the key."
    ),
}

# --- stripping comments before matching (#428) -------------------------------
# A word-grep cannot tell code from prose: a key named like an English word
# reads as rendered the moment a comment uses the word.
# Strings are deliberately kept. A string literal is how a key gets read
# (`page["source_type"]`), so stripping them would turn a real read into a
# silent miss. They are tracked, or the `//` in "https://..." would read as a
# comment and eat the rest of the line.
# Not a parser: a `<!--` inside a Liquid string would confuse it.
LINE_COMMENT = {".js": "//", ".py": "#", ".rb": "#"}
BLOCK_COMMENT = {".js": ("/*", "*/")}
QUOTES = {".js": "\"'`", ".py": "\"'", ".rb": "\"'"}
LIQUID_COMMENT = re.compile(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}",
                            re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _strip_comments(text, suffix):
    """`text` with its comments blanked out, keeping string literals intact."""
    if suffix in (".html", ".svg", ".md", ".xml"):
        return HTML_COMMENT.sub(" ", LIQUID_COMMENT.sub(" ", text))
    if suffix not in LINE_COMMENT:
        return text

    line, block, quotes = LINE_COMMENT[suffix], BLOCK_COMMENT.get(suffix), QUOTES[suffix]
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in quotes:                     # a string: copy it out verbatim
            out.append(ch)
            i += 1
            while i < n and text[i] != ch:
                if text[i] == "\\":
                    out.append(text[i])
                    i += 1
                    if i >= n:
                        break
                out.append(text[i])
                i += 1
            if i < n:
                out.append(text[i])
                i += 1
        elif text.startswith(line, i):
            i = text.find("\n", i)
            if i == -1:
                break
        elif block and text.startswith(block[0], i):
            end = text.find(block[1], i + len(block[0]))
            i = n if end == -1 else end + len(block[1])
            out.append(" ")
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _render_surface_reads(key):
    """Files on the render surface whose CODE (not comments) names `key`.

    A dotted key is checked by its last segment: `meta.rewritten` is written
    `page.meta.rewritten` in Liquid but reached as `["meta"]["rewritten"]`
    elsewhere, and the leading `meta` is shared by every key under it.
    """
    word = re.compile(r"\b" + re.escape(key.rsplit(".", 1)[-1]) + r"\b")
    hits = []
    for root in RENDER_SURFACE:
        for path in sorted((ROOT / root).rglob("*")):
            if not path.is_file() or path.suffix == ".pyc":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if word.search(_strip_comments(text, path.suffix)):
                hits.append(path.relative_to(ROOT).as_posix())
    return hits


def test_invisible_keys_are_really_invisible():
    """Every key in INVISIBLE_KEYS is read by nothing that builds a page.

    This is the check that makes the exemption safe rather than merely stated.
    If a key on this list is ever rendered, the recipes carrying it stopped
    being unchanged-as-far-as-Helen-is-concerned, and the entry must go.
    """
    rendered = {}
    for key in sorted(INVISIBLE_KEYS):
        hits = _render_surface_reads(key)
        if hits:
            rendered[key] = hits

    assert not rendered, (
        "INVISIBLE_KEYS names front matter key(s) that something actually "
        "reads:\n  "
        + "\n  ".join(f"{k}: {', '.join(v)}" for k, v in rendered.items())
        + "\n\nThe whole basis for exempting these from the proofread rule is "
          "that they render nothing, so a recipe carrying one shows Helen "
          "exactly what she proofread. Once a key is rendered that is false. "
          "Remove it from the list -- do not narrow this test."
    )


# The scanner is tested on both sides: prose must not register as a read, and
# a real read must not be lost. The second matters more: a false negative lets
# a rendered key sit on INVISIBLE_KEYS unnoticed (#428).
SCANNER_CASES = [
    (".js", "// main_ingredients text is rewritten in the include", False),
    (".js", "/* rewritten\n   across lines */", False),
    (".js", "const x = 1; // rewritten", False),
    (".js", 'fetch("https://example.com/a"); const y = r.rewritten;', True),
    (".js", 'if (item["rewritten"]) render();', True),
    (".js", 'const s = "not a // comment: rewritten";', True),
    (".py", "# rewritten, but only in a comment", False),
    (".py", 'KEYS = ["rewritten"]', True),
    (".py", '"""A docstring mentioning rewritten."""', True),
    (".rb", "# rewritten in prose", False),
    (".rb", 'data.fetch("rewritten")', True),
    (".html", "{% comment %} rewritten {% endcomment %}", False),
    (".html", "{%- comment -%} rewritten {%- endcomment -%}", False),
    (".html", "<!-- rewritten -->", False),
    (".html", "{% if page.meta.rewritten %}yes{% endif %}", True),
    (".svg", "<!-- rewritten --><title>x</title>", False),
]


@pytest.mark.parametrize("suffix,source,is_read", SCANNER_CASES,
                         ids=[f"{s[1:]}:{t[:38]}" for s, t, _ in SCANNER_CASES])
def test_the_invisible_keys_scanner_tells_code_from_prose(suffix, source, is_read):
    found = re.search(r"\brewritten\b", _strip_comments(source, suffix)) is not None
    assert found is is_read, (
        f"_strip_comments({suffix}) got this backwards:\n    {source!r}\n"
        + ("The key is genuinely read here and the scanner lost it -- a false "
           "negative lets a rendered key sit on INVISIBLE_KEYS unnoticed, which "
           "is the failure this whole mechanism exists to prevent."
           if is_read else
           "That is prose, not a read. Over-reporting is why meta.rewritten "
           "could not be listed before #428.")
    )


# The `.py` docstring case passes because strings are kept, though a docstring
# is prose. Telling one from `KEYS = ["rewritten"]` needs `ast.parse`, not a
# regex.


def _file_at(commit, relpath):
    """(front matter mapping, body) for `relpath` at `commit`, or None."""
    result = subprocess.run(["git", "show", f"{commit}:{relpath}"],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    match = FRONT_MATTER.match(result.stdout)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None
    return data, result.stdout[match.end():]


def _only_invisible_keys_changed(commit, relpath):
    """True if this commit touched `relpath` ONLY in keys that render nothing.

    Compares the whole file against its state in the parent commit: every key
    whose value differs must be in INVISIBLE_KEYS, and the body must be
    identical. Anything it cannot read confidently -- a new file, a merge,
    unparseable YAML -- returns False, so the proofread rule still applies.
    """
    after = _file_at(commit, relpath)
    before = _file_at(f"{commit}^", relpath)
    if after is None or before is None:
        return False                      # new file, or nothing to compare with

    (new_data, new_body), (old_data, old_body) = after, before
    if new_body != old_body:
        return False                      # the prose moved; nothing else matters

    changed = {k for k in set(new_data) | set(old_data)
               if new_data.get(k, object()) != old_data.get(k, object())}

    # meta is a nested mapping, so it is compared key by key: a bare "meta" in
    # `changed` matches no entry in INVISIBLE_KEYS.
    if "meta" in changed:
        new_meta = new_data.get("meta") if isinstance(new_data.get("meta"), dict) else {}
        old_meta = old_data.get("meta") if isinstance(old_data.get("meta"), dict) else {}
        changed.discard("meta")
        changed |= {f"meta.{k}" for k in set(new_meta) | set(old_meta)
                    if new_meta.get(k, object()) != old_meta.get(k, object())}

    # Keys are compared by full dotted name, so a top-level key is not exempted
    # by its namesake under meta.
    #
    # An empty `changed` means exempt, not unknown (#429): a pure reorder of
    # the meta block changes no value. It cannot swallow a real edit, because
    # the body is compared above and every differing value lands in `changed`;
    # anything unreadable has already returned False.
    return changed <= set(INVISIBLE_KEYS)


def _rewritten_at(repo, rev, relpath):
    """`meta.rewritten` for a file at a revision, or None if unreadable."""
    result = subprocess.run(["git", "show", f"{rev}:{relpath}"],
                            cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    match = FRONT_MATTER.match(result.stdout)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None
    return (data.get("meta") or {}).get("rewritten")


def _agent_claimed_rewrites(repo, pathspec, adjudicated=frozenset()):
    """Commits where an agent flipped `meta.rewritten` from false to true.

    `adjudicated` holds short SHAs Helen has personally ruled on -- see
    ADJUDICATED_REWRITES. They are skipped HERE rather than filtered by the
    caller, so that the meta-test can ask this same function with an empty
    set and get the unfiltered truth.

    Narrowed with `-G` before doing any real work: only commits whose DIFF
    touches a `rewritten:` line are candidates, so this stays a handful of
    `git show` calls rather than a walk of the whole history.
    """
    shas = subprocess.run(
        ["git", "log", "--format=%H", f"--grep={AGENT_TRAILER}", "-i",
         "-G", r"rewritten:", "--", pathspec],
        cwd=repo, capture_output=True, text=True,
    ).stdout.split()

    offenders = []
    for sha in shas:
        files = subprocess.run(
            ["git", "show", "--name-only", "--format=", sha, "--", pathspec],
            cwd=repo, capture_output=True, text=True,
        ).stdout.split()
        for relpath in files:
            if not relpath.endswith(".md"):
                continue
            before = _rewritten_at(repo, f"{sha}^", relpath)
            after = _rewritten_at(repo, sha, relpath)
            if before is False and after is True:
                if sha[:8] in adjudicated:
                    continue
                offenders.append(f"{sha[:8]}  {relpath}")
    return offenders


# --- commits Helen has personally ruled on ------------------------------------
# The scan walks the whole history, so one violation fails the test for ever:
# setting the flag back does not remove the commit that flipped it. An entry
# records "ruled on, closed". It is Helen's to grant, never an agent's, and
# never to turn a red test green. Write what she decided and why;
# `test_every_adjudicated_rewrite_still_offends` refuses a dead entry.
ADJUDICATED_REWRITES = {
    "_food_drafts": {
        "1fbd2f81": (
            "sticky-squidge-ginger-loaf.md, 2026-09-05. Helen revised the "
            "spice blend herself in f16035c and never flipped the flag; an "
            "agent flipped it while fixing two typos in the same file. She "
            "confirmed the prose IS hers, so the VALUE was already true and "
            "stays true -- but it was still the wrong hand on the switch, "
            "which is the whole of what this test is for."
        ),
    },
}


def _adjudicated(repo_key):
    return frozenset(ADJUDICATED_REWRITES.get(repo_key, {}))


def test_every_adjudicated_rewrite_still_offends():
    """No dead entries in ADJUDICATED_REWRITES.

    A SHA that no longer flips `meta.rewritten` false -> true under an agent
    trailer is dead weight, and an exception list with dead weight stops being
    read. Skips where `_food_drafts/` is absent, which includes CI.
    """
    drafts = ROOT / "_food_drafts"
    if not (DRAFTS_PRESENT and (drafts / ".git").exists()):
        pytest.skip(
            "`_food_drafts/` is not on this machine, so its adjudicated SHAs "
            "cannot be looked up. Clone it to check this."
        )

    live = {line.split()[0] for line in _agent_claimed_rewrites(drafts, ".")}
    stale = sorted(_adjudicated("_food_drafts") - live)
    assert not stale, (
        f"ADJUDICATED_REWRITES names commit(s) that no longer offend: {stale}\n\n"
        "Either the history was rewritten or the SHA is wrong. Delete the "
        "entry -- an exception nobody can account for is how an exception list "
        "stops being read."
    )


def test_no_agent_commit_claims_helens_rewrite():
    """`meta.rewritten` is Helen's claim; an agent commit never sets it true.

    An assisted pass records itself with `meta.claude_rewritten` (#418).
    Helen's rulings on past violations are in ADJUDICATED_REWRITES.

    Not caught: a file created by an agent already saying `rewritten: true`.
    Only a false-to-true transition is flagged, because `before` is also None
    for a rename or a promotion, and failing those would fail Helen's own
    workflow.

    In CI `_food_drafts/` is absent (#378), so a green run there covers the
    published recipes and none of the drafts, which is where tidy-up passes
    happen. It does not skip, because the published half is the half that
    ships; it is registered in tests/test_suite_hygiene.py's PARTIAL_IN_CI.
    """
    assert (ROOT / ".git").exists(), "Not a git checkout -- this test cannot run."

    offenders = _agent_claimed_rewrites(ROOT, "_food_recipes/",
                                        _adjudicated("_food_recipes"))

    drafts = ROOT / "_food_drafts"
    # Names ALL_DRAFTS so the registry in tests/test_suite_hygiene.py, which
    # finds draft-reading tests by that token, sees this one.
    if DRAFTS_PRESENT and ALL_DRAFTS and (drafts / ".git").exists():
        offenders += [f"_food_drafts/  {line}"
                      for line in _agent_claimed_rewrites(
                          drafts, ".", _adjudicated("_food_drafts"))]

    assert not offenders, (
        "An agent commit set `meta.rewritten: true`, which is Helen's claim "
        "and hers alone:\n  "
        + "\n  ".join(offenders)
        + "\n\n`meta.rewritten` means the prose is genuinely in her voice. An "
          "assisted pass records itself with `meta.claude_rewritten: true` and "
          "leaves `rewritten` alone -- tidying structure and wording is not the "
          "same thing as her rewriting a step (issue #418). If she asked for "
          "this herself, the commit is hers to make, not an agent's."
    )



def test_agent_edited_recipes_are_not_marked_proofread():
    """A recipe whose newest commit is an agent's must have proofread: false."""
    assert (ROOT / ".git").exists(), "Not a git checkout -- this test cannot run."
    assert "true" not in _git("rev-parse", "--is-shallow-repository").lower(), (
        "This is a SHALLOW clone, so `git log` cannot see who last touched each "
        "recipe and this test would silently check almost nothing. Fetch full "
        "history (actions/checkout needs `fetch-depth: 0`)."
    )

    # Newest commit per recipe, in one pass.
    last: dict[str, str] = {}
    sha = None
    for line in _git("log", "--format=%H", "--name-only", "--", "_food_recipes/").splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
            sha = line
        elif line.endswith(".md"):
            last.setdefault(line, sha)

    assert last, (
        "No recipe history found at all. This test would pass while checking "
        "nothing, which is the failure mode tests/test_suite_hygiene.py exists "
        "to prevent."
    )

    base = BASELINE_COMMIT
    agent_commit: dict[str, bool] = {}
    offenders, checked = [], 0

    for relpath, commit in sorted(last.items()):
        path = ROOT / relpath
        if not path.exists():
            continue                                  # renamed or deleted since
        # Grandfathered: at or before the baseline.
        if subprocess.run(["git", "merge-base", "--is-ancestor", commit, base],
                          cwd=ROOT, capture_output=True).returncode == 0:
            continue
        if _only_invisible_keys_changed(commit, relpath):
            continue                                  # renders nothing; see above
        if commit not in agent_commit:
            body = _git("show", "-s", "--format=%B", commit).lower()
            agent_commit[commit] = AGENT_TRAILER in body
        if not agent_commit[commit]:
            continue                                  # Helen's own commit
        checked += 1
        raw = path.read_text(encoding="utf-8")
        match = FRONT_MATTER.match(raw)
        meta = (yaml.safe_load(match.group(1)) or {}).get("meta", {}) or {}
        if meta.get("proofread") is not False:
            offenders.append(f"{relpath} (last touched by {commit[:8]})")

    assert not offenders, (
        "Recipe(s) last edited by an agent but still marked proofread:\n  "
        + "\n  ".join(offenders)
        + "\n\nAn agent editing a recipe invalidates Helen's proofread of it, so "
          "the SAME commit must set `meta.proofread: false` (issue #367).\n\n"
          "There are three ways out, in order of how often they are the right "
          "one:\n"
          "  1. Set proofread: false. Almost always correct.\n"
          "  2. If the commit changed ONLY keys that render nothing, add them to "
          "INVISIBLE_KEYS -- but only if test_invisible_keys_are_really_"
          "invisible still passes, which is the check that keeps this honest.\n"
          "  3. If Helen reviewed the change herself, move BASELINE_COMMIT "
          "forward, in a commit of its own, quoting her. It is hers to grant.\n\n"
          "There is no per-recipe exemption list: one keyed on a filename never "
          "expires, so it would excuse every future edit to that file too. "
          "DECISIONS §4.0."
    )


# --- the publish gate's data side (#331) -------------------------------------
# _plugins/publish_gate.rb publishes a recipe only on `awaiting_fix: false` and
# `proofread: true`, and drops the document on anything else.
# tests/test_site_config.py guards the mechanism; these guard the data it reads.

def test_every_recipe_declares_awaiting_fix():
    """The flag is present on every recipe, so its absence is never the answer.

    The gate fails closed: a recipe with no `awaiting_fix` key is held back
    from the live site. This names the file, so a page going dark is a red
    test and not a surprise.
    """
    missing = []
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta = (yaml.safe_load(FRONT_MATTER.match(raw).group(1)) or {}).get("meta", {}) or {}
        if "awaiting_fix" not in meta:
            missing.append(path.name)
    assert not missing, (
        "Recipe(s) with no `meta.awaiting_fix` key:\n  " + "\n  ".join(missing)
        + "\n\nThe publish gate fails closed, so these pages are held back "
          "from the live site. Add `awaiting_fix: false` if nothing is open on "
          "the recipe."
    )


def test_awaiting_fix_is_a_real_boolean():
    """`awaiting_fix: "false"` is a STRING, and the gate holds the page back.

    The plugin publishes only when `meta["awaiting_fix"] == false` -- Ruby's
    `false`, not a falsy value. A quoted "false" is not equal to it, so a page
    meant to be live goes dark. A quoted "true" is held back too, but for the
    wrong reason, and stops meaning anything to code that tests for `true`.
    """
    bad = []
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta = (yaml.safe_load(FRONT_MATTER.match(raw).group(1)) or {}).get("meta", {}) or {}
        if "awaiting_fix" in meta and not isinstance(meta["awaiting_fix"], bool):
            bad.append(f"{path.name}: {meta['awaiting_fix']!r} ({type(meta['awaiting_fix']).__name__})")
    assert not bad, (
        "`meta.awaiting_fix` must be an unquoted true/false:\n  " + "\n  ".join(bad)
        + "\n\nThe publish gate needs exactly `false`, so a quoted value "
          "holds the page back from the live site. Never quote this value."
    )


def test_no_recipe_uses_the_old_hyphenated_awaiting_fix_key():
    """No recipe carries the old hyphenated `awaiting-fix` key.

    Liquid parses `page.meta.awaiting-fix` as subtraction, so a template
    reading the flag through that name gets arithmetic, not the flag. A recipe
    with only the old key also has no `awaiting_fix`, so the gate holds it
    back without saying why; this names the file.
    """
    offenders = []
    for path in sorted((ROOT / "_food_recipes").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        if "awaiting-fix" in raw:
            offenders.append(path.name)
    assert not offenders, (
        "Recipe(s) still using the old hyphenated `awaiting-fix` key:\n  "
        + "\n  ".join(offenders)
        + "\n\nRename to `awaiting_fix`. Liquid reads the hyphenated form as a "
          "subtraction, so a template asking whether the page is flagged gets "
          "arithmetic instead of the flag."
    )
