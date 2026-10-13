"""`scripts/resolve_pours.py` -- what the dictionaries settle, and what they do not.

The tiers are pinned directly rather than by a check over the drafts, which CI
does not have. They run against the real dictionaries with the words a source
prints: a synthetic vocabulary would prove the algorithm and nothing about
whether it fits this repo's data.
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
    """A source's name for a declared bottle resolves to that bottle's generic,
    with the bottle's canonical name as the suggestion. The character is not a
    dictionary read: see the next test.
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
    """The script may offer a bottle's character as `character_claude` and never
    write `character` itself (#314).

    A character belongs to a recipe line, not to a bottle, which is why
    `bottles.yml` has no character column.
    """
    got = rp.resolve("Gosling's Black Seal", *tables)
    assert got["character_claude"] == ["blackstrap"]
    assert "character" not in got, (
        "a resolved bottle must not write `character` outright -- a character "
        "is what THIS recipe wants from the pour, which no dictionary knows"
    )


def test_a_bottle_helen_does_not_buy_never_resolves(tables):
    """`not_reached_for` is excluded from the index on purpose: resolving onto
    a bottle Helen does not buy would propose a drink she cannot make.
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
    ("white creme de cacao", "white crème de cacao"),  # accents flattened on the way in
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
    """`hers_to_apply` generics are excluded: those styles are Helen's to apply
    and are never typed in from a source's own words.
    """
    assert rp.resolve("caramel-forward Jamaican rum", *tables) is None


# =============================================================================
# TIER 2, THE THIRD DICTIONARY -- a source's wording Helen has ruled on
# =============================================================================
# `_data/cocktails/source_wordings.yml`: Helen's answers to source wordings
# that the two dictionaries above do not settle.

@pytest.mark.parametrize("words,expected", [
    # As Difford's prints them, and as an ingest trims them.
    ("Light white rum (charcoal-filtered 1-4 years old)", "lightly aged and filtered rum"),
    ("light white rum", "lightly aged and filtered rum"),
    ("Rosso vermouth", "sweet vermouth"),
    ("Green Chartreuse", "Chartreuse Verte"),
    ("Aperitivo Luxardo (Aperol-style liqueur)", "Aperol"),
    ("Red bitter (Campari-style liqueur)", "Campari"),
    ("Dry Curaçao liqueur", "dry orange Curaçao"),
    ("dry curacao liqueur", "dry orange Curaçao"),      # folded
    ("Kummel liqueur", "kümmel"),
    ("Sugar cane syrup (from juice)", "cane sugar syrup 2:1"),
])
def test_a_wording_helen_ruled_on_resolves(words, expected, tables):
    got = rp.resolve(words, *tables)
    assert got, f"{words!r} is in source_wordings.yml and must resolve"
    assert got["tier"] == 2
    assert got["generic"] == expected
    assert got["suggestion"] == [], (
        "a wording names a CATEGORY. A source's name for a bottle is an alias "
        "on that bottle in bottles.yml, which Tier 1 reads"
    )
    assert got.get("via"), (
        "the report must say this came from her rulings and not from the "
        "vocabulary, so a wrong entry can be traced to the file that holds it"
    )


def test_every_wording_lands_on_a_generic_the_vocabulary_declares(tables):
    """A typo in a value would type a pour with a generic no drink may carry.

    `hers_to_apply` is excluded from `declared_generics()`, so a wording that
    points at a style Helen applies herself fails here too, on purpose.
    """
    _, generics = tables
    declared = set(generics.values())
    wordings = rp.source_wordings()
    assert wordings, (
        "source_wordings.yml loaded no entries, so every test of it above is "
        "checking an empty table"
    )
    import yaml
    raw = yaml.safe_load((rp.DATA / "source_wordings.yml").read_text(encoding="utf-8"))
    bad = sorted(f"{words!r} -> {generic!r}"
                 for words, generic in raw["wordings"].items()
                 if generic not in declared)
    assert not bad, (
        "source_wordings.yml points at generic(s) ingredients.yml does not "
        "declare:\n  " + "\n  ".join(bad)
    )


def test_no_wording_shadows_a_dictionary_that_already_answers(tables):
    """A key that is already a bottle or a generic can never be reached.

    The resolver reads the two dictionaries first, so such an entry is dead
    while reading as though it did work. When a wording becomes a declared
    generic or a bottle's alias, delete it from the file in the same commit.
    """
    bottles, generics = tables
    shadowed = sorted(key for key in rp.source_wordings()
                      if key in bottles or key in generics)
    assert not shadowed, (
        "source_wordings.yml holds wording(s) the dictionaries already "
        "answer, so the entry is never read:\n  " + "\n  ".join(shadowed)
    )


def test_two_wordings_do_not_fold_to_one_key_with_two_answers():
    """`fold` flattens case and accents, so two entries can collide."""
    import yaml
    raw = yaml.safe_load((rp.DATA / "source_wordings.yml").read_text(encoding="utf-8"))
    seen = {}
    clash = []
    for words, generic in raw["wordings"].items():
        key = rp.fold(words)
        if key in seen and seen[key] != generic:
            clash.append(f"{words!r}: {generic!r} against {seen[key]!r}")
        seen[key] = generic
    assert not clash, "one wording, two answers:\n  " + "\n  ".join(clash)


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
    # Deliberately left out of source_wordings.yml:
    "Cherry (brandy) liqueur",   # ruled drink by drink, "one by one" -- not a rule
    "Cuban rum",                 # an ingest's own word for Havana Club 3, not a source's
    "port",                      # tawny or ruby? the source's BOTTLE says, the word does not
    # This list asserts that a bottle is NOT known, so declaring a bottle in
    # `bottles.yml` can falsify an entry here and turn `main` red (#1108).
    # Declaring a bottle means checking this list in the same commit.
])
def test_words_nobody_can_resolve_are_left_alone(words, tables):
    """Words the dictionaries do not answer resolve to nothing and keep their `QQ`.

    The matching is exact so that this list is possible. Every entry is a
    phrase a source prints and a model could answer confidently and wrongly:
    `blackstrap rum` most of all, one plausible step from a bottle the repo
    does know. An exact read cannot take that step.
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
    """The file the script writes is run through the two guards in
    test_cocktails.py that judge a proposal, with the real vocabulary behind
    them, so the writer and the suite cannot disagree about the schema.
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
