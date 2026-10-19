"""The inbox parser: what an `ingest` issue must look like before it is written.

`scripts/ingest_inbox.py` turns a GitHub Issue raised from Helen's phone into a
file in `_food_drafts/` or `_cocktail_drafts/`. INGEST_INBOX_DESIGN.md §6 is the
envelope's specification and §8 is the threat model.

Nothing here touches the network or her real drafts. The script has one
function that reaches GitHub (`fetch_issues`) and one that writes to it
(`post_comment`); a test replaces the first and forbids the second. Every case
that needs existing files builds them under this repo's own `tmp/`, because
the private repos are absent in a worktree and in CI.

The two valid fixtures are the documents' own worked examples
(`INGEST_ONE_RECIPE.md` §9, `INGEST_ONE_COCKTAIL.md` §9), re-checked here
against the schema constants in `test_front_matter.py` and `test_cocktails.py`.
A fixture that drifts from its document teaches this parser a shape no browser
sends, so `test_the_valid_fixture_is_its_documents_worked_example` compares
them.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.shared

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ingest_inbox"
DOCS = ROOT / "model_instructions"

sys.path.insert(0, str(ROOT / "scripts"))

import ingest_inbox as inbox  # noqa: E402


def envelope_text(name: str) -> str:
    path = FIXTURES / f"{name}.md"
    assert path.is_file(), (
        f"fixture {path.relative_to(ROOT)} is missing. Every case below names "
        f"one; a missing file must fail loudly rather than let its case pass."
    )
    return path.read_text(encoding="utf-8")


@pytest.fixture
def drafts():
    """A drafts root under this repo's own `tmp/`, removed afterwards.

    Not `tmp_path`: nothing in this project writes under the system `/tmp`.
    """
    root = ROOT / "tmp" / "test_ingest_inbox_drafts"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    yield root
    shutil.rmtree(root)


# ---- The two valid envelopes ----

@pytest.mark.parametrize("name,site,slug", [
    ("valid_food", "food", "crispy-sage-butter-gnocchi"),
    ("valid_cocktail", "cocktail", "jungle-bird"),
])
def test_a_valid_envelope_parses_and_names_its_file(name, site, slug):
    env = inbox.parse_envelope(envelope_text(name), site)
    assert env.version in inbox.SUPPORTED_VERSIONS
    assert env.site == site
    assert env.hand_back, "the hand-back list is the half Helen actually reads"
    assert inbox.slug_for(env.fm["title"]) == slug
    assert inbox.SLUG_OK.match(inbox.slug_for(env.fm["title"]))


@pytest.mark.parametrize("name,site,doc", [
    ("valid_food", "food", "INGEST_ONE_RECIPE.md"),
    ("valid_cocktail", "cocktail", "INGEST_ONE_COCKTAIL.md"),
])
def test_the_fixture_fingerprint_is_the_one_its_document_prints(name, site, doc):
    """§0 of each document prints the fingerprint for its own worked example.

    A repo-less browser copies the shape of that line, so it and the rebuild
    in `ingest_inbox.fingerprint` must agree exactly. A disagreement rejects
    every envelope the document teaches, for the one reason (`fingerprint does
    not match`) that reads like the browser's fault.
    """
    env = inbox.parse_envelope(envelope_text(name), site)
    printed = (DOCS / doc).read_text(encoding="utf-8")
    assert f"`{env.fingerprint}`" in printed, (
        f"{doc} §0 does not print {env.fingerprint!r} as its worked example's "
        f"fingerprint. One of the two has moved; they are copies of each other."
    )


@pytest.mark.parametrize("name,doc", [
    ("valid_food", "INGEST_ONE_RECIPE.md"),
    ("valid_cocktail", "INGEST_ONE_COCKTAIL.md"),
])
def test_the_valid_fixture_is_its_documents_worked_example(name, doc):
    """The fixture is the §9 envelope, character for character.

    The document is uploaded to a web Project, so it is the source and the
    fixture follows it: copy the four-backtick block into the fixture.
    """
    fence = "`" * 4
    printed = (DOCS / doc).read_text(encoding="utf-8")
    blocks = re.findall(rf"^{fence}\n(.*?)^{fence}$", printed, re.S | re.M)
    assert len(blocks) == 1, (
        f"{doc} has {len(blocks)} four-backtick blocks; this expects its worked "
        f"example to be the only one."
    )
    assert envelope_text(name) == blocks[0], (
        f"tests/fixtures/ingest_inbox/{name}.md has drifted from {doc} §9. "
        f"Copy the document's four-backtick block into the fixture."
    )


def test_the_food_fixture_obeys_the_food_schema():
    """The same constants `test_front_matter.py` holds recipes to, imported."""
    from test_front_matter import META_ORDER, REQUIRED, SCALAR_STRING_FIELDS

    env = inbox.parse_envelope(envelope_text("valid_food"), "food")
    missing = [f for f in REQUIRED if f not in env.fm]
    assert not missing, f"the food fixture is missing required field(s): {missing}"
    assert list(env.fm["meta"]) == META_ORDER
    assert all(v is False for v in env.fm["meta"].values())

    unquoted = []
    for line in env.block.split("\n"):
        m = re.match(r"^([a-z_]+):\s*(.+?)\s*$", line)
        if m and m.group(1) in SCALAR_STRING_FIELDS and not m.group(2).startswith('"'):
            unquoted.append(line)
    assert not unquoted, f"unquoted scalar(s) in the food fixture: {unquoted}"


def test_the_cocktail_fixture_obeys_the_drink_schema():
    """`_drink_problems` is the check the cocktail document's own example gets.

    Reused, not re-listed: a fixture judged by a private copy of the schema
    can be valid here and rejected by `pytest -m cocktails` the moment it
    lands in `_cocktail_drafts/`.
    """
    from test_cocktails import (INGREDIENT_KEYS, META_KEYS_IN_ORDER,
                                REQUIRED_TOP_LEVEL, TOP_LEVEL_KEYS)
    from test_standalone_docs import _drink_problems

    env = inbox.parse_envelope(envelope_text("valid_cocktail"), "cocktail")
    fm = env.fm
    assert not _drink_problems(fm)
    assert set(fm) <= TOP_LEVEL_KEYS, f"undeclared key(s): {set(fm) - TOP_LEVEL_KEYS}"
    assert REQUIRED_TOP_LEVEL <= set(fm), f"missing: {REQUIRED_TOP_LEVEL - set(fm)}"
    assert list(fm["meta"]) == META_KEYS_IN_ORDER
    for item in fm["ingredients"]:
        assert set(item) <= INGREDIENT_KEYS, (
            f"undeclared ingredient key(s): {set(item) - INGREDIENT_KEYS}"
        )


# ---- Every rejection, one line each ----
# A bad body can do nothing beyond earn a reason (INGEST_INBOX_DESIGN.md §8).
# Each case is one rule from §6, and the substring is the part of the message
# that names which rule: a reworded reason still passes, an unenforced rule
# does not.

@pytest.mark.parametrize("name,site,expected", [
    ("no_marker", "food", "is not an `<!-- ingest v<N> <site> -->` marker"),
    ("unknown_site", "food", "which is not one of"),
    ("unsupported_version", "food", "this script implements"),
    ("two_blocks", "food", "fenced code blocks; the envelope carries exactly one"),
    ("yaml_is_a_list", "food", "is a list, not a mapping"),
    ("missing_hand_back", "food", "no `## What I could not know` section"),
    ("missing_fingerprint", "food", "no `## Fingerprint` section"),
    ("fingerprint_mismatch", "food", "fingerprint does not match the file"),
    ("valid_cocktail", "food", "but --site is 'food'"),
])
def test_a_malformed_envelope_is_rejected_with_its_reason(name, site, expected):
    with pytest.raises(inbox.Rejected) as caught:
        inbox.parse_envelope(envelope_text(name), site)
    reason = str(caught.value)
    assert expected in reason, f"reason was {reason!r}"
    assert "\n" not in reason, "a rejection is ONE line -- it is read in a list"


COCKTAIL_NOTE = (
    '  - label: "QQ"\n'
    '    text: "QQ - two pours carry the source\'s words behind a `QQ`. '
    '`blackstrap` is a character rather than a category, and `simple syrup` '
    'does not say which sugar or what ratio. No `suggestion` is filled in."\n'
)
FOOD_NOTE = (
    '  - label: "QQ"\n'
    '    text: "QQ - the source stops after the garlic. Nothing tells you when '
    'the parmesan goes in, or how the gnocchi and the butter meet."\n'
)


@pytest.mark.parametrize("name,site,old,new,expected", [
    # A bare string renders under the page's fallback title, "note" -- #1120.
    ("valid_cocktail", "cocktail", COCKTAIL_NOTE,
     '  - "QQ - generics not filled in."\n',
     "note 1 is a bare string"),
    ("valid_cocktail", "cocktail", COCKTAIL_NOTE,
     '  - label: "note"\n    text: "QQ - generics not filled in."\n',
     "note 1 is labelled 'note', not 'QQ'"),
    ("valid_cocktail", "cocktail", COCKTAIL_NOTE,
     '  - label: "QQ"\n    text: "Generics not filled in."\n',
     "note 1 has text that does not begin `QQ`"),
    ("valid_cocktail", "cocktail", COCKTAIL_NOTE,
     COCKTAIL_NOTE + '  - "QQ - a second note, bare."\n',
     "note 2 is a bare string"),
    # A topic must follow a space: `QQnutrition` and a trailing space are typos.
    ("valid_cocktail", "cocktail", COCKTAIL_NOTE,
     '  - label: "QQnutrition"\n    text: "QQ - generics not filled in."\n',
     "note 1 is labelled 'QQnutrition'"),
    ("valid_cocktail", "cocktail", COCKTAIL_NOTE,
     '  - label: "QQ "\n    text: "QQ - generics not filled in."\n',
     "note 1 is labelled 'QQ '"),
    # The food site has the same fallback title and the same rule.
    ("valid_food", "food", FOOD_NOTE,
     '  - "QQ - the source stops after the garlic."\n',
     "note 1 is a bare string"),
])
def test_a_note_that_is_not_labelled_qq_is_rejected(name, site, old, new, expected):
    """A note is `{label: "QQ", text: "QQ ..."}` or the envelope is refused (#1120).

    Built by replacing the valid fixture's note, so the `old in text` assert
    is what stops a reworded fixture turning the replacement into a no-op.
    """
    text = envelope_text(name)
    assert old in text, f"the {name} fixture's note has moved; update this test"
    with pytest.raises(inbox.Rejected) as caught:
        inbox.parse_envelope(text.replace(old, new), site)
    reason = str(caught.value)
    assert expected in reason, f"reason was {reason!r}"
    assert "#1120" in reason
    assert "\n" not in reason, "a rejection is ONE line -- it is read in a list"


@pytest.mark.parametrize("name,site", [
    ("valid_cocktail", "cocktail"),
    ("valid_food", "food"),
])
def test_a_qq_label_may_carry_a_topic(name, site):
    """`QQ nutrition` reads as unfinished on the page, and when Helen proofreads
    she deletes the `QQ ` and keeps the heading (DECISIONS §4)."""
    text = envelope_text(name)
    old = COCKTAIL_NOTE if site == "cocktail" else FOOD_NOTE
    assert old in text, f"the {name} fixture's note has moved; update this test"
    topical = text.replace(old, old.replace('label: "QQ"', 'label: "QQ nutrition"'))
    assert topical != text
    assert inbox.parse_envelope(topical, site).fm["notes"][0]["label"] == "QQ nutrition"


@pytest.mark.parametrize("name,site", [
    ("valid_cocktail", "cocktail"),
    ("valid_food", "food"),
])
def test_an_envelope_with_no_notes_is_not_a_rejection(name, site):
    """The rule is about the notes that are there. A source that answers
    everything has nothing to ask, and an empty `notes` must not be refused."""
    text = envelope_text(name)
    old = COCKTAIL_NOTE if site == "cocktail" else FOOD_NOTE
    assert old in text, f"the {name} fixture's note has moved; update this test"
    swapped = text.replace("notes:\n" + old, "notes: []\n")
    assert swapped != text
    assert inbox.parse_envelope(swapped, site).fm["notes"] == []
    # The empty pair is what both documents ask for in that case (#1258): a
    # slot, not a note, so the `QQ` rule does not apply.
    slot = text.replace(old, '  - label: ""\n    text: ""\n')
    assert inbox.parse_envelope(slot, site).fm["notes"] == \
        [{"label": "", "text": ""}]


@pytest.mark.parametrize("name,site", [
    ("valid_cocktail", "cocktail"),
    ("valid_food", "food"),
])
def test_an_envelope_with_no_notes_is_written_with_a_slot(name, site, drafts):
    """#1258: the draft gets the empty pair, and nothing else in it moves.

    The one place `write` is not byte for byte. Compared against the envelope's
    own block with that single line swapped, so a rule that leaked onto any
    other line fails here.
    """
    text = envelope_text(name)
    old = COCKTAIL_NOTE if site == "cocktail" else FOOD_NOTE
    swapped = text.replace("notes:\n" + old, "notes: []\n")
    plan = inbox.plan_for(swapped, site, [], drafts)
    inbox.write(plan)
    got = plan.path.read_text(encoding="utf-8")
    assert got == plan.envelope.block.replace(
        "notes: []\n", 'notes:\n  - label: ""\n    text: ""\n')
    assert yaml.safe_load(re.match(r"\A---\n(.*?)\n---", got, re.S).group(1)
                          )["notes"] == [{"label": "", "text": ""}]
    assert any("empty {label, text} pair" in n for n in plan.notes)


def test_a_rejection_never_reaches_the_writing_half(drafts):
    """A refusal is a refusal, not a slower write."""
    plan = inbox.plan_for(envelope_text("no_marker"), "food", [], drafts, number=7)
    assert plan.reason and not plan.ok
    assert plan.path is None
    with pytest.raises(ValueError):
        inbox.write(plan)
    assert not list(drafts.rglob("*.md"))


# ---- What is already in the drafts ----

def _plan(name, site, drafts, number=None):
    existing = inbox.scan_drafts(drafts, site)
    return inbox.plan_for(envelope_text(name), site, existing, drafts, number)


def test_a_write_is_byte_for_byte_and_is_never_repeated(drafts):
    """The fenced block verbatim -- no YAML round trip, no second write.

    A dumper would lose comment placement, key order and the exact `[""]` shape
    `method_short` depends on. What the browser wrote is what Helen proofreads,
    so the bytes are the contract.
    """
    plan = _plan("valid_food", "food", drafts)
    inbox.write(plan)
    written = (drafts / "crispy-sage-butter-gnocchi.md")
    assert written.read_text(encoding="utf-8") == plan.envelope.block
    assert yaml.safe_load(re.match(r"\A---\n(.*?)\n---", written.read_text(
        encoding="utf-8"), re.S).group(1))["title"] == "Crispy Sage Butter Gnocchi"
    with pytest.raises(FileExistsError):
        inbox.write(plan)


def test_a_slug_that_is_taken_gains_a_number_and_says_so(drafts):
    """Never an overwrite, and never a silent one either."""
    (drafts / "crispy-sage-butter-gnocchi.md").write_text(
        '---\ntitle: "Something Else Entirely"\n---\n', encoding="utf-8")
    plan = _plan("valid_food", "food", drafts)
    assert plan.ok
    assert plan.path.name == "crispy-sage-butter-gnocchi-2.md"
    assert any("slug collision" in n for n in plan.notes)


def test_the_same_formula_is_a_probable_duplicate_and_is_not_written(drafts):
    """§6: the duplicate check compares formulas, never titles."""
    first = _plan("valid_food", "food", drafts)
    inbox.write(first)
    again = _plan("valid_food", "food", drafts)
    assert not again.ok
    assert again.duplicate_of == "crispy-sage-butter-gnocchi"
    assert "PROBABLE DUPLICATE" in again.one_line()
    assert len(list(drafts.rglob("*.md"))) == 1


def test_the_same_title_with_a_different_formula_is_the_sazerac_case(drafts):
    """Two recipes, one name -- written separately and reported, never merged.

    `sazerac` and `sazerac-death-and-co` live side by side (MANUAL §9.2.1).
    The consumer's job is to notice and say so, not to choose.
    """
    inbox.write(_plan("valid_food", "food", drafts))
    plan = _plan("title_only_match", "food", drafts)
    assert plan.ok, "a different formula under the same title is a NEW recipe"
    assert plan.path.name == "crispy-sage-butter-gnocchi-2.md"
    assert any("SAZERAC" in n for n in plan.notes)
    inbox.write(plan)
    assert len(list(drafts.rglob("*.md"))) == 2


def test_a_draft_in_a_staging_subfolder_still_counts(drafts):
    """`rglob`, not `glob`: `_food_drafts/` has staging folders such as
    `2-make/` under it (PIPELINE.md §3), and a flat scan silently stops seeing
    the drafts closest to promotion.
    """
    (drafts / "2-make").mkdir()
    inbox.write(_plan("valid_food", "food", drafts))
    (drafts / "2-make" / "crispy-sage-butter-gnocchi.md").write_text(
        (drafts / "crispy-sage-butter-gnocchi.md").read_text(encoding="utf-8"),
        encoding="utf-8")
    (drafts / "crispy-sage-butter-gnocchi.md").unlink()
    plan = _plan("valid_food", "food", drafts)
    assert plan.duplicate_of == "crispy-sage-butter-gnocchi"


# ---- The CLI, with the one network door stubbed ----

def test_the_run_writes_what_the_dry_run_promised(drafts, monkeypatch, capsys):
    """End to end, with `fetch_issues` stubbed and `post_comment` forbidden.

    That is the whole isolation: a second door to GitHub would leave this
    test passing while the suite quietly starts needing a network.
    """
    issues = [{"number": 12, "body": envelope_text("valid_food")},
              {"number": 13, "body": envelope_text("no_marker")}]
    monkeypatch.setattr(inbox, "fetch_issues", lambda site, number=None: issues)
    monkeypatch.setattr(inbox, "post_comment", lambda *a, **k: pytest.fail(
        "post_comment must never fire without --comment"))

    args = ["--site", "food", "--drafts-dir", str(drafts)]
    assert inbox.main(args) == 0
    dry = capsys.readouterr().out
    assert "would write crispy-sage-butter-gnocchi.md" in dry
    assert "#13: REJECTED" in dry
    assert not list(drafts.rglob("*.md")), "a dry run writes nothing"

    assert inbox.main(args + ["--write"]) == 0
    wet = capsys.readouterr().out
    assert "wrote crispy-sage-butter-gnocchi.md" in wet
    assert [p.name for p in drafts.rglob("*.md")] == ["crispy-sage-butter-gnocchi.md"]
    assert "no issue was closed" in wet


def _batch(*parts) -> str:
    """A combined batch file in the shape CLAUDE_WEB_INGEST.md §2 asks for."""
    out = ["# Recipe ingest batch: test\n\n## Index\n\n1. Something\n\n---\n\n"]
    for heading, body in parts:
        out.append(f"# ingest: {heading}\n\n{body}\n\n---\n\n")
    return "".join(out)


def test_a_batch_splits_at_its_headings_and_drops_the_index():
    """Each `# ingest: <slug>` section is one envelope, and the trailing rule
    between sections is not read as a second fingerprint line."""
    body = _batch(("crispy-sage-butter-gnocchi", envelope_text("valid_food")),
                  ("whatever", envelope_text("no_marker")))
    parts = inbox.split_batch(body)
    assert [h for h, _ in parts] == ["crispy-sage-butter-gnocchi", "whatever"]
    assert inbox.parse_envelope(parts[0][1], "food").fm["title"] == \
        "Crispy Sage Butter Gnocchi"
    with pytest.raises(inbox.Rejected):
        inbox.parse_envelope(parts[1][1], "food")


def test_a_body_with_no_batch_heading_is_one_envelope():
    text = envelope_text("valid_food")
    assert inbox.split_batch(text) == [(None, text)]


def test_a_batch_from_file_reports_every_envelope(drafts, monkeypatch, capsys):
    """A folder of files, one of them a batch: every envelope gets its own
    line naming the file and the heading, and a heading that disagrees with
    the title is reported rather than obeyed."""
    monkeypatch.setattr(inbox, "fetch_issues", lambda *a, **k: pytest.fail(
        "--from-file must not reach GitHub"))
    inbox_dir = drafts.parent / "test_ingest_inbox_batch"
    if inbox_dir.exists():
        shutil.rmtree(inbox_dir)
    inbox_dir.mkdir()
    try:
        (inbox_dir / "batch.md").write_text(_batch(
            ("not-the-title", envelope_text("valid_food")),
            ("cut-off", "<!-- ingest v1 food -->\n")), encoding="utf-8")
        assert inbox.main(["--site", "food", "--drafts-dir", str(drafts),
                           "--from-file", str(inbox_dir)]) == 0
        out = capsys.readouterr().out
        assert "batch.md not-the-title: would write crispy-sage-butter-gnocchi.md" in out
        assert "the batch heading says 'not-the-title'" in out
        assert "batch.md cut-off: REJECTED: 0 fenced code blocks" in out
    finally:
        shutil.rmtree(inbox_dir)


def test_comment_is_a_no_op_with_from_file(drafts, monkeypatch, capsys):
    """There is no issue to comment on, so `--comment` must not invent one."""
    monkeypatch.setattr(inbox, "post_comment", lambda *a, **k: pytest.fail(
        "commented on an issue that does not exist"))
    monkeypatch.setattr(inbox, "fetch_issues", lambda *a, **k: pytest.fail(
        "--from-file must not reach GitHub"))
    assert inbox.main(["--site", "food", "--comment", "--drafts-dir", str(drafts),
                       "--from-file", str(FIXTURES / "valid_food.md")]) == 0
    assert "would write" in capsys.readouterr().out


def test_comment_carries_the_hand_back_list(drafts, monkeypatch, capsys):
    """`--comment` posts the outcome and the browser's hand-back bullets.

    The issue is where Helen reads on her phone, so the list of what the
    browser could not know goes there, not only into a terminal.
    """
    posted = []
    issues = [{"number": 21, "body": envelope_text("valid_food")}]
    monkeypatch.setattr(inbox, "fetch_issues", lambda site, number=None: issues)
    monkeypatch.setattr(inbox, "post_comment",
                        lambda site, number, text: posted.append((number, text)))
    assert inbox.main(["--site", "food", "--comment", "--drafts-dir", str(drafts)]) == 0
    capsys.readouterr()
    assert len(posted) == 1 and posted[0][0] == 21
    text = posted[0][1]
    assert text.startswith("would write ")
    env = inbox.parse_envelope(envelope_text("valid_food"), "food")
    for item in env.hand_back:
        assert f"- {item}" in text, f"hand-back bullet missing from the comment: {item!r}"


def test_slug_is_the_whole_title():
    """The slug is the whole title, not its head clause.

    Two "with" dishes sharing a head clause otherwise collide, and the second
    lands as `-2` for no reason a reader can see in the name.
    """
    assert inbox.slug_for("Roast Chicken with Lemon and Thyme") == "roast-chicken-with-lemon-and-thyme"
    assert inbox.slug_for("Crème Brûlée") == "creme-brulee"
    assert inbox.slug_for("Anita's Attitude Adjuster") == "anitas-attitude-adjuster"


def test_an_absent_drafts_repo_is_a_loud_refusal(capsys):
    """The absent-repo case, in the shape `tidy_drafts.py` set (#537).

    A worktree and CI both lack the private repos, so "found nothing" is the
    normal state here and must never be reported as a clean run.
    """
    with pytest.raises(SystemExit) as caught:
        inbox.main(["--site", "cocktail", "--drafts-dir",
                    str(ROOT / "tmp" / "no-such-drafts-root"),
                    "--from-file", str(FIXTURES / "valid_cocktail.md")])
    message = str(caught.value)
    assert "is not here" in message and "private repo" in message
    assert caught.value.code != 0


# ---- The version handshake ----

def test_both_documents_name_a_supported_version():
    """§8's one silent failure: a document teaching v2 to a browser that reaches
    a consumer implementing v1.

    The marker carries the version so the mismatch is loud at parse time;
    this makes it loud at commit time, where it is still free to fix.
    """
    pattern = re.compile(r"<!--\s*ingest\s+v(\d+)\s+([a-z]+)\s*-->")
    expected = {"INGEST_ONE_RECIPE.md": "food",
                "INGEST_ONE_COCKTAIL.md": "cocktail"}
    problems = []
    found = 0
    for name, site in expected.items():
        text = (DOCS / name).read_text(encoding="utf-8")
        markers = pattern.findall(text)
        if not markers:
            problems.append(f"{name}: §0 prints no `<!-- ingest v<N> <site> -->`")
            continue
        for version, named in markers:
            found += 1
            if int(version) not in inbox.SUPPORTED_VERSIONS:
                problems.append(
                    f"{name}: teaches v{version}, which "
                    f"scripts/ingest_inbox.py does not implement "
                    f"{sorted(inbox.SUPPORTED_VERSIONS)}")
            if named != site:
                problems.append(f"{name}: marker names site {named!r}, not {site!r}")
    assert found, (
        "no ingest markers found in either standalone document -- the scan has "
        "gone stale against their formatting, and an empty scan must never read "
        "as 'nothing wrong'."
    )
    assert not problems, "the envelope version handshake has broken:\n  " + \
        "\n  ".join(problems)


# ---- envelope.py, the parser a web Claude runs on its own ----

import ast  # noqa: E402
import subprocess  # noqa: E402

ENVELOPE = ROOT / "scripts" / "envelope.py"


def test_envelope_py_imports_nothing_from_the_repository():
    """A claude.ai chat fetches this one file and runs it. An import of a
    repo module would work here and fail there, which is the silent case."""
    tree = ast.parse(ENVELOPE.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    allowed = set(sys.stdlib_module_names) | {"yaml", "__future__"}
    assert names <= allowed, f"envelope.py imports {sorted(names - allowed)}"


def test_envelope_py_folds_as_the_search_layer_does():
    """Its `_fold` is restated, not imported (above); this holds the two together."""
    import envelope
    from test_taxonomy import _fold
    for text in ("Röstis", "Pâté", "Crème Fraîche", "jalapeño", "Rich Ragù"):
        assert envelope._fold(text) == _fold(text), text


def test_envelope_py_runs_alone_and_exits_on_a_rejection():
    good = subprocess.run([sys.executable, "-I", str(ENVELOPE),
                           str(FIXTURES / "valid_food.md")],
                          capture_output=True, text=True)
    assert good.returncode == 0, good.stdout + good.stderr
    assert "OK, crispy-sage-butter-gnocchi.md" in good.stdout
    assert "fingerprint: crispy sage butter gnocchi" in good.stdout
    bad = subprocess.run([sys.executable, "-I", str(ENVELOPE),
                          str(FIXTURES / "no_marker.md")],
                         capture_output=True, text=True)
    assert bad.returncode == 1 and "REJECTED" in bad.stdout, bad.stdout


# ---- folding the bullets a standing ruling settles ----

def test_a_settled_bullet_folds_and_a_question_never_does():
    fm = {"source": "Adapted from Somebody's Book"}
    settled = "**Times not printed.** Estimated, not from the source: prep 10 mins."
    asking = "**Butter is unspecified in the source.** Which do you want?"
    other = "**The apple is never added in the source.**"
    kept, folded = inbox.fold_hand_back([settled, asking, other], fm)
    assert kept == [asking, other]
    assert [b for _, b in folded] == [settled]


def test_a_page_check_folds_even_though_it_asks():
    """Helen takes page checks at rewrite, from the source; the exception is named."""
    bullet = "**The page was angled.** Please check \"400 ml stock\"."
    kept, folded = inbox.fold_hand_back([bullet], {})
    assert not kept and folded[0][0] == inbox.PHOTO_LABEL


def test_a_source_ruling_folds_only_for_its_own_source():
    oven = "**The oven is 190°C/Gas 5 with no fan figure.** I kept it as printed."
    riverford = {"source": "Adapted from Riverford Companions: Autumn and Winter Veg, Guy Watson"}
    elsewhere = {"source": "Adapted from Somebody's Book"}
    assert inbox.fold_hand_back([oven], riverford)[0] == []
    assert inbox.fold_hand_back([oven], elsewhere)[0] == [oven]


def test_the_report_counts_what_it_folds(drafts, monkeypatch, capsys):
    text = envelope_text("valid_food").replace(
        "## What I could not know\n",
        "## What I could not know\n\n- **Times not printed.** Estimated, prep 5 mins.\n", 1)
    monkeypatch.setattr(inbox, "fetch_issues", lambda site, number=None:
                        [{"number": 3, "body": text}])
    assert inbox.main(["--site", "food", "--drafts-dir", str(drafts)]) == 0
    out = capsys.readouterr().out
    assert "Times not printed" not in out
    assert "an unprinted time, written as `Estimated N mins`: 1" in out
    assert inbox.main(["--site", "food", "--drafts-dir", str(drafts),
                       "--every-bullet"]) == 0
    assert "Times not printed" in capsys.readouterr().out


def test_a_dry_run_counts_each_envelope_for_the_next(drafts, monkeypatch, capsys):
    """Two envelopes with one slug, and two with one formula, in a single run:
    the dry run reports the -2 and the duplicate a --write would make."""
    text = envelope_text("valid_food")
    other = text.replace("| 500 g |", "| 400 g |").replace('"500 g"', '"400 g"')
    assert other != text
    monkeypatch.setattr(inbox, "fetch_issues", lambda site, number=None: [
        {"number": 1, "body": text}, {"number": 2, "body": text},
        {"number": 3, "body": other}])
    assert inbox.main(["--site", "food", "--drafts-dir", str(drafts)]) == 0
    out = capsys.readouterr().out
    assert "#2: PROBABLE DUPLICATE of crispy-sage-butter-gnocchi (earlier in this run)" in out
    assert "#3: would write crispy-sage-butter-gnocchi-2.md" in out
    assert not list(drafts.rglob("*.md")), "still a dry run"


def test_a_published_recipe_counts_as_existing(drafts, monkeypatch, capsys):
    """A duplicate of a PUBLISHED recipe is a duplicate, reported as such."""
    published = drafts.parent / "test_ingest_inbox_published"
    if published.exists():
        shutil.rmtree(published)
    published.mkdir()
    try:
        env = inbox.parse_envelope(envelope_text("valid_food"), "food")
        (published / "crispy-sage-butter-gnocchi.md").write_text(env.block, encoding="utf-8")
        monkeypatch.setattr(inbox, "fetch_issues", lambda site, number=None:
                            [{"number": 4, "body": envelope_text("valid_food")}])
        assert inbox.main(["--site", "food", "--drafts-dir", str(drafts),
                           "--recipes-dir", str(published)]) == 0
        assert "PROBABLE DUPLICATE of published crispy-sage-butter-gnocchi" in \
            capsys.readouterr().out
    finally:
        shutil.rmtree(published)


# ---- ingest_review.py ----

def test_the_review_page_has_a_row_per_recipe_and_its_open_questions(drafts):
    import ingest_review
    body = envelope_text("valid_food")
    page = ingest_review.review([(None, "valid_food.md", None, body)], drafts)
    assert "| 1 | Crispy Sage Butter Gnocchi (not written) |" in page
    env = inbox.parse_envelope(body, "food")
    kept, _ = inbox.fold_hand_back(env.hand_back, env.fm)
    for bullet in kept:
        assert bullet in page, f"an open question is missing: {bullet!r}"
    assert f"## Questions still open: {len(kept)}" in page
