"""`scripts/resolve_pours.py` -- what the dictionaries settle, and what they do not.

WHY THIS MODULE EXISTS RATHER THAN A CHECK OVER THE DRAFTS. Run against the
collection today the script resolves NOTHING: all six untyped pours are Tier 3,
because not one of them names a bottle `bottles.yml` declares. That is the
script working, and it exercises none of it -- the same hole
`test_qq_followed_by_the_sources_words_is_still_a_qq` was written to fill, and
for the same reason (CI has no drafts clone at all).

So the tiers are pinned directly, against the REAL dictionaries and with the
words a source would actually print. A synthetic vocabulary would prove the
algorithm and nothing about whether the algorithm fits this repo's data.
"""
import importlib.util
import pathlib

import pytest

pytestmark = pytest.mark.cocktails

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "resolve_pours.py"

spec = importlib.util.spec_from_file_location("resolve_pours", SCRIPT)
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)


@pytest.fixture(scope="module")
def tables():
    return rp.bottle_index(), rp.declared_generics()


# =============================================================================
# TIER 1 -- the source names a bottle the repo declares
# =============================================================================

def test_a_declared_bottle_resolves_to_its_generic(tables):
    """Helen, 2026-09-21: "If the source says 'Gosling's' then the correct
    thing for Claude to do is give 'moderately aged rum, character: blackstrap'."

    The generic and the suggestion are a dictionary read. The CHARACTER is not
    -- see the next test.
    """
    got = rp.resolve("Gosling's", *tables)
    assert got, "`Gosling's` is a declared alias and must resolve"
    assert got["tier"] == 1
    assert got["generic"] == "moderately aged rum"
    assert got["suggestion"] == ["Gosling's Black Seal"], (
        "a Tier 1 resolution writes the bottle's CANONICAL name, not the "
        "alias the source happened to use"
    )


def test_a_bottles_character_is_a_proposal_and_never_an_answer(tables):
    """`bottles.yml` has no character column, and says so.

    Its note against Gosling's Black Seal: the bottle is "reached for FOR its
    blackstrap, which is a `character` on the recipe and never a generic --
    #314, and the reason this file has no character column". And Helen,
    2026-09-14: "We don't name characters on bottles. We name characters on
    recipe lines ... having a character is only in a context."

    So the script may offer `blackstrap` and may never assert it.
    """
    got = rp.resolve("Gosling's Black Seal", *tables)
    assert got["character_claude"] == ["blackstrap"]
    assert "character" not in got, (
        "a resolved bottle must not write `character` outright -- a character "
        "is what THIS recipe wants from the pour, which no dictionary knows"
    )


def test_a_bottle_helen_does_not_buy_never_resolves(tables):
    """`not_reached_for` is excluded from the index on purpose.

    `away-colour` names Ron del Barrilito, which Helen ruled she does not buy
    on 2026-09-05. Resolving onto it would propose a drink she cannot make.
    """
    assert rp.resolve("Ron del Barrilito Three Stars", *tables) is None


# =============================================================================
# TIER 2 -- the source's words ARE a declared generic
# =============================================================================

@pytest.mark.parametrize("words,expected", [
    ("lime juice", "lime juice"),
    ("Campari", "Campari"),
    ("LIME JUICE", "lime juice"),          # folded
    ("  lime   juice  ", "lime juice"),    # whitespace collapsed
    ("creme de cacao", "crème de cacao"),  # accents flattened on the way in
])
def test_an_exact_vocabulary_match_resolves(words, expected, tables):
    got = rp.resolve(words, *tables)
    assert got, f"{words!r} is a declared generic and must resolve"
    assert got["tier"] == 2
    assert got["generic"] == expected, (
        "a Tier 2 resolution writes the vocabulary's own spelling, so a "
        "source's casing or missing accent does not reach the file"
    )
    assert got["suggestion"] == []


def test_a_generic_helen_reserved_never_resolves(tables):
    """`hers_to_apply` is excluded, which is the rule it exists for.

    MANUAL 9.3.1: those styles are "Helen's to apply and never to be typed into
    from a source's own words". A resolver that typed one would be doing the
    precise thing the list forbids.
    """
    assert rp.resolve("caramel-forward Jamaican rum", *tables) is None


# =============================================================================
# TIER 3 -- everything else, and this is the half Helen asked for
# =============================================================================

@pytest.mark.parametrize("words", [
    "blackstrap rum",     # a CHARACTER wearing a category's clothes
    "black rum",          # retired: "there's no such thing as black rum"
    "navy rum",           # retired: three real categories wear the word
    "dark rum",           # retired: colour, not production
    "aged Jamaican rum",  # near-miss: two declared Jamaicans, neither is this
    "simple syrup",       # which sugar? what ratio? unanswerable
    "tequila",            # blanco, reposado or añejo -- the source did not say
    "agave nectar",       # near-miss for `agave syrup`, and a near-miss is a guess
    "Planteray Three Star",   # a real bottle this repo has not declared
    "Cruzan Single Barrel",   # the same
])
def test_words_nobody_can_resolve_are_left_alone(words, tables):
    """Helen, 2026-09-21: "if a recipe gives 'blackstrap' Claude shouldn't
    suggest anything."

    THE MATCHING IS EXACT SO THAT THIS LIST IS POSSIBLE. Every entry here is a
    phrase a source really prints, and every one is a phrase a model could
    produce a confident wrong answer for -- `blackstrap rum` most of all,
    because the repo DOES know a blackstrap bottle and the inference from one to
    the other is a single plausible step. An exact read cannot take that step.
    """
    assert rp.resolve(words, *tables) is None, (
        f"{words!r} must fall to Tier 3 and keep its `QQ`"
    )


def test_the_tier_three_list_is_still_about_this_repo(tables):
    """The cases above must be unresolvable for the REASON given, not because
    the loader broke and everything is unresolvable.
    """
    bottles, generics = tables
    assert len(bottles) > 100, f"only {len(bottles)} bottle names loaded"
    assert len(generics) > 150, f"only {len(generics)} generics loaded"
    assert rp.resolve("Campari", *tables), (
        "a value that MUST resolve does not, so the Tier 3 cases above prove "
        "nothing -- the tables are empty or the fold has changed"
    )


# =============================================================================
# THE REWRITE
# =============================================================================

POUR = '''---
title: "Test"
ingredients:
  - amount: "45 ml"
    generic: "QQ Gosling's"
    suggestion: []
  - amount: "15 ml"
    generic: "lime juice"
    suggestion: []
---
'''


def test_apply_writes_the_resolution(tmp_path, tables, monkeypatch):
    """One drink, one Tier 1 pour, written end to end."""
    drafts = tmp_path / "_cocktail_drafts"
    drafts.mkdir()
    path = drafts / "test-drink.md"
    path.write_text(POUR, encoding="utf-8")
    monkeypatch.setattr(rp, "DRAFTS", drafts)

    assert rp.main(["--apply"]) == 0
    got = path.read_text(encoding="utf-8")

    assert 'generic: "moderately aged rum"' in got
    assert 'suggestion: ["Gosling\'s Black Seal"]' in got
    assert 'character_claude: ["blackstrap"]' in got
    assert 'note: "QQ -' in got, (
        "a character proposal must arrive with the open question it answers, "
        "or `test_a_claude_proposal_only_sits_beside_an_open_question` refuses "
        "the pour it just wrote"
    )
    assert 'generic: "QQ' not in got, (
        "the generic was settled by the dictionary, so its QQ is answered "
        "and goes"
    )
    assert 'generic: "lime juice"' in got, (
        "the pour that was already typed must be untouched"
    )
    assert got.startswith("---\n"), "the front matter fence survived"


def test_what_apply_writes_passes_the_suite_that_judges_it(tmp_path, tables,
                                                           monkeypatch):
    """The output is checked by the real schema, not by this module's opinion.

    A writer whose output its own suite refuses is the shape this repo keeps
    finding: a rule written down in one place and enforced in another. So the
    file this script produces is run through the two guards that judge a
    proposal, with the real vocabulary behind them.
    """
    import yaml
    from test_cocktails import (CLAUDE_PROPOSALS, INGREDIENT_KEYS, _is_qq,
                                _unanswered)

    drafts = tmp_path / "_cocktail_drafts"
    drafts.mkdir()
    path = drafts / "test-drink.md"
    path.write_text(POUR, encoding="utf-8")
    monkeypatch.setattr(rp, "DRAFTS", drafts)
    rp.main(["--apply"])

    body = path.read_text(encoding="utf-8").split("---")[1]
    fm = yaml.safe_load(body)
    for entry in fm["ingredients"]:
        assert set(entry) <= INGREDIENT_KEYS, (
            f"undeclared key(s): {set(entry) - INGREDIENT_KEYS}")
        if set(entry) & set(CLAUDE_PROPOSALS):
            assert (_unanswered([entry.get("generic")])
                    or _is_qq(entry.get("note"))), (
                f"the script wrote a proposal onto a pour with nothing open: "
                f"{entry!r}")


def test_a_report_writes_nothing(tmp_path, tables, monkeypatch):
    """The default is a report, like scripts/tidy_drafts.py."""
    drafts = tmp_path / "_cocktail_drafts"
    drafts.mkdir()
    path = drafts / "test-drink.md"
    path.write_text(POUR, encoding="utf-8")
    monkeypatch.setattr(rp, "DRAFTS", drafts)

    assert rp.main([]) == 0
    assert path.read_text(encoding="utf-8") == POUR
