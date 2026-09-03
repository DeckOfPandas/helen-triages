"""The inbox parser: what an `ingest` issue must look like before it is written.

`scripts/ingest_inbox.py` turns a GitHub Issue raised from Helen's phone into a
file in `_food_drafts/` or `_cocktail_drafts/`. INGEST_INBOX_DESIGN.md §6 is the
envelope's specification and §8 is the threat model; this module is the proof
that the script implements the first and honours the second.

NOTHING HERE TOUCHES THE NETWORK OR HER REAL DRAFTS, and both halves of that are
deliberate. The script has exactly one function that reaches GitHub
(`fetch_issues`) and one that writes to it (`post_comment`), so a test replaces
the first and forbids the second, and a suite that would fail on a train stays
green on one. The drafts roots are never read: every case that needs existing
files builds them under this repo's own `tmp/` and removes them again, which is
also what lets the collision and duplicate cases exist at all -- the private
repos are absent in a worktree and in CI.

THE TWO VALID FIXTURES ARE THE DOCUMENTS' OWN WORKED EXAMPLES, copied
character for character out of `INGEST_ONE_RECIPE.md` §9 and
`INGEST_ONE_COCKTAIL.md` §9, and each is re-checked here against the schema
constants in `test_front_matter.py` and `test_cocktails.py`. A fixture that
drifts from the document teaches this parser a shape no browser will ever send
it, which is a green test guarding nothing -- the failure mode
`tests/test_suite_hygiene.py` exists for.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pytest
import yaml

# Suite marker, so `pytest -m shared` runs this. test_suite_hygiene.py asserts
# every module declares one -- an unmarked file is silently missed by every
# filtered run. `shared` because the inbox serves both sites.
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

    NOT `tmp_path`, and CLAUDE.md is why: nothing in this project writes under
    the system `/tmp`, for any reason. `tmp/` is gitignored here.
    """
    root = ROOT / "tmp" / "test_ingest_inbox_drafts"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    yield root
    shutil.rmtree(root)


# =============================================================================
# THE TWO VALID ENVELOPES
# =============================================================================

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

    That printed line is what a repo-less browser copies the SHAPE of, so it and
    the rebuild in `ingest_inbox.fingerprint` have to agree exactly -- a
    disagreement rejects every envelope the document teaches, and rejects it for
    the one reason (`fingerprint does not match`) that reads like the browser's
    fault.
    """
    env = inbox.parse_envelope(envelope_text(name), site)
    printed = (DOCS / doc).read_text(encoding="utf-8")
    assert f"`{env.fingerprint}`" in printed, (
        f"{doc} §0 does not print {env.fingerprint!r} as its worked example's "
        f"fingerprint. One of the two has moved; they are copies of each other."
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

    Reusing it rather than re-listing the rules is the point: a fixture judged by
    a second, private copy of the schema is a fixture that can be valid here and
    rejected by `pytest -m cocktails` the moment it lands in `_cocktail_drafts/`.
    """
    from test_cocktails import (INGREDIENT_KEYS_DRAFTS, META_KEYS_IN_ORDER,
                                REQUIRED_TOP_LEVEL, TOP_LEVEL_KEYS)
    from test_standalone_docs import _drink_problems

    env = inbox.parse_envelope(envelope_text("valid_cocktail"), "cocktail")
    fm = env.fm
    assert not _drink_problems(fm)
    assert set(fm) <= TOP_LEVEL_KEYS, f"undeclared key(s): {set(fm) - TOP_LEVEL_KEYS}"
    assert REQUIRED_TOP_LEVEL <= set(fm), f"missing: {REQUIRED_TOP_LEVEL - set(fm)}"
    assert list(fm["meta"]) == META_KEYS_IN_ORDER
    for item in fm["ingredients"]:
        assert set(item) <= INGREDIENT_KEYS_DRAFTS, (
            f"ingredient key(s) forbidden even on a draft: "
            f"{set(item) - INGREDIENT_KEYS_DRAFTS}"
        )


# =============================================================================
# EVERY REJECTION, ONE LINE EACH
# =============================================================================
# The design's whole claim about a bad body is that it can do nothing beyond
# earn a reason (§8). Each case below is one rule from §6, and the substring is
# the part of the message that names WHICH rule -- if a reason is reworded the
# test should still pass, and if a rule stops being enforced it must not.

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


def test_a_rejection_never_reaches_the_writing_half(drafts):
    """A refusal is a refusal, not a slower write."""
    plan = inbox.plan_for(envelope_text("no_marker"), "food", [], drafts, number=7)
    assert plan.reason and not plan.ok
    assert plan.path is None
    with pytest.raises(ValueError):
        inbox.write(plan)
    assert not list(drafts.rglob("*.md"))


# =============================================================================
# WHAT IS ALREADY IN THE DRAFTS
# =============================================================================

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
    """§6: the duplicate check compares FORMULAS, never titles."""
    first = _plan("valid_food", "food", drafts)
    inbox.write(first)
    again = _plan("valid_food", "food", drafts)
    assert not again.ok
    assert again.duplicate_of == "crispy-sage-butter-gnocchi"
    assert "PROBABLE DUPLICATE" in again.one_line()
    assert len(list(drafts.rglob("*.md"))) == 1


def test_the_same_title_with_a_different_formula_is_the_sazerac_case(drafts):
    """Two recipes, one name -- written separately and reported, never merged.

    HANDOVER §9.2.1: Helen's Sazerac and Death & Co's share a name, four of her
    own bottle suggestions, and nothing else. `sazerac` and
    `sazerac-death-and-co` live side by side because she named the second one.
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
    """`rglob`, not `glob`. `_food_drafts/` has `to-cook/` and friends under it,
    and food's own loader silently stopped seeing seven files -- the seven
    closest to promotion -- the day that pipeline appeared (HANDOVER §4).
    """
    (drafts / "to-cook").mkdir()
    inbox.write(_plan("valid_food", "food", drafts))
    (drafts / "to-cook" / "crispy-sage-butter-gnocchi.md").write_text(
        (drafts / "crispy-sage-butter-gnocchi.md").read_text(encoding="utf-8"),
        encoding="utf-8")
    (drafts / "crispy-sage-butter-gnocchi.md").unlink()
    plan = _plan("valid_food", "food", drafts)
    assert plan.duplicate_of == "crispy-sage-butter-gnocchi"


# =============================================================================
# THE CLI, WITH THE ONE NETWORK DOOR STUBBED
# =============================================================================

def test_the_run_writes_what_the_dry_run_promised(drafts, monkeypatch, capsys):
    """End to end over the ONE function the design says tests replace.

    Stubbing `fetch_issues` and forbidding `post_comment` is the whole
    isolation story: if a second door to GitHub is ever added, this test keeps
    passing while the suite quietly starts needing a network, which is why the
    door count is part of the design rather than an implementation detail.
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
    """`--comment` posts the outcome AND the browser's hand-back bullets.

    Helen, 2026-09-03: "Bullets too please." The issue is where she reads on
    her phone, so the list of what the browser could not know goes there,
    not only into a terminal she is not looking at.
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
    """Helen, 2026-09-03: "Slug the whole title." Not the head clause.

    Two "with" dishes sharing a head clause would otherwise collide and the
    second would land as `-2` for no reason a reader could see in the name.
    """
    assert inbox.slug_for("Roast Chicken with Lemon and Thyme") == "roast-chicken-with-lemon-and-thyme"
    assert inbox.slug_for("Crème Brûlée") == "creme-brulee"
    assert inbox.slug_for("Anita's Attitude Adjuster") == "anitas-attitude-adjuster"


def test_an_absent_drafts_repo_is_a_loud_refusal(capsys):
    """The absent-repo case, in the shape `tidy_drafts.py` set (#537).

    A worktree and CI both lack the private repos, so "found nothing" is the
    NORMAL state here and must never be reported as a clean run.
    """
    with pytest.raises(SystemExit) as caught:
        inbox.main(["--site", "cocktail", "--drafts-dir",
                    str(ROOT / "tmp" / "no-such-drafts-root"),
                    "--from-file", str(FIXTURES / "valid_cocktail.md")])
    message = str(caught.value)
    assert "is not here" in message and "private repo" in message
    assert caught.value.code != 0


# =============================================================================
# THE VERSION HANDSHAKE
# =============================================================================

def test_both_documents_name_a_supported_version():
    """§8's one silent failure: a document teaching v2 to a browser that reaches
    a consumer implementing v1.

    The marker carries the version so the mismatch is loud AT PARSE TIME, and
    this is the other end of the same wire -- it makes the mismatch loud at
    COMMIT time instead, which is where it can still be free to fix.
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
