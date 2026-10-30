"""House style for food recipes: time words, typography, spelling, accents and
the closed lists of ingredient qualifiers. Run: pytest tests/test_style.py

Time words are tighter in metadata than in prose:

    prep_time / cook_time  ->  mins, hrs
    prose                  ->  mins, hours, seconds

Only numeric quantities are abbreviated. "a minute", "at the last minute" and
"ten minutes of glory" are English, not inconsistency, and are left alone.
"""
from __future__ import annotations

import re

import pytest

from conftest import where, checkable_raw, checkable_prose
# The corpus-agnostic rules live in conftest so the cocktails suite reaches them
# without importing the food suite (#670). Other modules import several of
# these names from HERE, so the imports below are also this module's exports.
from conftest import (
    ALL_DRAFTS, ALL_MAGIC_BAG, ALL_RECIPES, ISO_DATE, NUMBER_RANGE,
    SHARED_TYPOGRAPHY, SPELLINGS, accent_problems, accented_words,
    degreeless_temperatures, note_is_a_sentence, note_problems, notes_of,
    number_range_hits, spelling_problems,
)

# Aliases: tests/test_prose_pages.py and scripts/build_ingest_vocab.py import
# these names from this module.
_accented_words = accented_words
_accent_problems = accent_problems

pytestmark = pytest.mark.food

TIME_FIELDS = ("prep_time", "cook_time")

# Word forms that stay spelled out because a number does not precede them.
IDIOM = re.compile(r"(?<![0-9])\s*(minutes?|hours?|seconds?)\b", re.I)


def test_no_estimated_timings(recipe):
    """No published time says `Estimated N mins`.

    An estimate is a drafting aid: fine in _food_drafts/, but once published it
    is indistinguishable from a measured time.
    """
    offenders = {f: recipe.fm[f] for f in TIME_FIELDS
                 if isinstance(recipe.fm.get(f), str)
                 and "estimated" in recipe.fm[f].lower()}
    assert not offenders, (
        f"{where(recipe)} has estimated timing(s): "
        + "; ".join(f"{f}: {v!r}" for f, v in offenders.items())
        + ".\nReplace with a real time before this recipe is published. "
          "Estimates are a drafting aid, not a published value."
    )


QQ = re.compile(r"\bQQ\b")


def test_no_qq_placeholder(recipe):
    """No `QQ` survives into `_food_recipes/`, in any field.

    `QQ` is Helen's placeholder for "not decided or written yet": never an
    error in `_food_drafts/`, but a published recipe carrying one is not
    finished. It is the only draft marker; never add a second (MANUAL §10.1).
    """
    hits = QQ.findall(recipe.raw)
    assert not hits, (
        f"{where(recipe)} still contains {len(hits)} `QQ` placeholder(s).\n"
        f"Fine in _food_drafts/, not fine here — replace with the real "
        f"content before this recipe counts as published."
    )


@pytest.mark.parametrize("field", TIME_FIELDS)
def test_metadata_time_format(recipe, field):
    """Metadata uses the terse forms: `20 mins`, `1 hr 30 mins`, `2 hrs`."""
    value = recipe.fm.get(field)
    if not isinstance(value, str) or not value.strip():
        return
    if value.strip() in ("QQ", "None", "Until done"):
        return
    bad_units = re.findall(r"(?<=[0-9])\s*(minutes?|hours?|h)\b", value)
    assert not bad_units, (
        f"{where(recipe)} `{field}: {value!r}` uses {sorted(set(bad_units))}. "
        f"Metadata fields use the terse forms `mins` and `hrs` "
        f"(e.g. '20 mins', '1 hr 30 mins', '2 hrs'). "
        f"The spelled-out forms belong in prose, not here."
    )


def test_prose_abbreviates_minutes_only(recipe):
    """Prose uses `mins`, but `hours` and `seconds` spelled out."""
    problems = []
    for location, text in checkable_prose(recipe):
        for match in re.finditer(r"(?<=[0-9])\s*(minutes?|hrs?|secs?)\b", text):
            word = match.group(1)
            wanted = {"minute": "min", "minutes": "mins",
                      "hr": "hour", "hrs": "hours",
                      "sec": "second", "secs": "seconds"}[word.lower()]
            snippet = text[max(0, match.start() - 25):match.end() + 10]
            problems.append(f"{location}: …{snippet}… — use '{wanted}'")
    assert not problems, (
        f"{where(recipe)} breaks the prose time convention "
        f"(mins abbreviated; hours and seconds spelled out):\n  "
        + "\n  ".join(problems)
    )


# --- method-step notes read as sentences, unlike ingredient notes -----------
# #174. A note on a `method`/`method_groups` step is an aside in sentence form:
# capital first letter, trailing full stop. The opposite of an ingredient
# item's `note:`, which is a lowercase fragment with no full stop and has its
# own test (test_ingredient_notes_are_lowercase_fragments, test_taxonomy.py).
def test_method_step_notes_are_sentences(recipe):
    bad = []
    for step in recipe.fm.get("method") or []:
        if isinstance(step, dict) and step.get("note"):
            bad.append(step["note"])
    for group in recipe.fm.get("method_groups") or []:
        for step in group.get("steps") or []:
            if isinstance(step, dict) and step.get("note"):
                bad.append(step["note"])
    problems = [
        n for n in bad
        if not (n[0:1].isupper() and n.rstrip().endswith("."))
    ]
    assert not problems, (
        f"{where(recipe)} has method-step note(s) not styled as a sentence "
        f"(capital letter, trailing full stop): {problems!r}."
    )


# --- notes are sentences -----------------------------------------------------
# #711. The rule and its helpers live in conftest so the cocktails suite holds
# a drink to the same one. An exception is declared here with its reason, so
# the test still bites on the next note; the staleness test below stops an
# entry outliving its note.
NOTE_EXCEPTIONS = {
    # A continuation, not a missing capital: the ellipsis joins the note to
    # the sentence above it.
    "...goat's cheese and cherry tomato.":
        "leading ellipsis: the note continues the sentence above it",
}


def _note_exempt(text: str) -> bool:
    return (text or "").strip() in NOTE_EXCEPTIONS


def test_notes_are_sentences(recipe):
    """A note starts with a capital and ends with a full stop -- #711.

    Covers what `notes_of` returns, which for a recipe is its `notes:` list.
    Method-step notes have `test_method_step_notes_are_sentences` above.
    """
    problems = [
        f"{where_note}: {text!r} ({', '.join(note_problems(text))})"
        for where_note, text in notes_of(recipe.fm)
        if not _note_exempt(text) and not note_is_a_sentence(text)
    ]
    assert not problems, (
        f"{where(recipe)} has note(s) not styled as a sentence "
        f"(capital letter, trailing full stop):\n  " + "\n  ".join(problems)
    )


def test_no_note_exception_is_stale():
    """A declared exception must still name a note that exists.

    An exemption that outlives its note quietly exempts that exact string for
    whoever writes it next.

    In CI `_food_drafts/` is absent, so ALL_DRAFTS is empty and an exemption
    naming a draft-only note fails there as stale. Make such an exemption name
    a published recipe, or move this test to SKIPS_WITHOUT_DRAFTS.
    """
    live = set()
    for entry in ALL_RECIPES + ALL_DRAFTS + ALL_MAGIC_BAG:
        live.update((text or "").strip() for _, text in notes_of(entry.fm))
    stale = [note for note in NOTE_EXCEPTIONS if note not in live]
    assert not stale, (
        f"{len(stale)} NOTE_EXCEPTIONS entr(ies) name a note no recipe has any "
        f"more:\n  " + "\n  ".join(repr(s) for s in stale)
        + "\n\nThe work is done -- delete the line."
    )


TYPOGRAPHY = [
    ("slash fractions", r"(?<![\d/])(1/2|1/4|3/4|1/3|2/3|1/8|3/8|5/8|7/8)(?![\d/])",
     "use Unicode fractions: ½ ¼ ¾ ⅓ ⅔ ⅛ ⅜ ⅝ ⅞"),
    # Shared with the cocktails suite; the entries around it are food's own.
    *SHARED_TYPOGRAPHY,
    ("wikilink", r"\[\[[^\]]+\]\]",
     "cross-recipe links are markdown, relative: [display text](../slug/)"),
    ("reversed link brackets", r"\([^()\n]+\)\[[^\]\n]*\]",
     "markdown links are [display text](../slug/), not (display text)[...] — "
     "the (text)[url] order never renders as a link, in any field"),
    ("ampersand in title", None, None),  # handled separately below
]

# --- en dashes in number ranges ----------------------------------------------
# #413. The rule is `number_range_hits` in conftest: a digit on both sides of a
# hyphen, with ISO dates blanked first because `2026-08-12` matches a range
# pattern exactly. `1-inch`, `criss-cross` and other ordinary hyphens do not
# fire.


def test_number_ranges_use_en_dashes(recipe):
    """`3–4 mins`, not `3-4 mins` -- #413.

    Scoped by what a reader sees, so it reads the whole file, not .prose: a
    metadata time, an ingredient amount and a method step all reach the page.
    It reads `checkable_raw`, so it stops at a `QQ` line (#426): a draft's
    source wording awaiting a rewrite is not corrected.
    """
    hits = number_range_hits(checkable_raw(recipe))
    assert not hits, (
        f"{where(recipe)} writes {len(hits)} number range(s) with a hyphen: "
        f"{sorted(set(hits))[:5]}. Ranges take an en dash — 3–4 mins, "
        f"170–180°C, 36–40% fat."
    )


@pytest.mark.parametrize("name,pattern,fix",
                         [(n, p, f) for n, p, f in TYPOGRAPHY if p])
def test_typography(recipe, name, pattern, fix):
    hits = re.findall(pattern, checkable_raw(recipe))
    assert not hits, (
        f"{where(recipe)} contains {len(hits)} instance(s) of {name}: "
        f"{sorted(set(h if isinstance(h, str) else h[0] for h in hits))[:5]}. "
        f"Fix: {fix}."
    )


def test_no_ampersand_in_title(recipe, taxonomy):
    """Titles use 'and', never '&' -- except a real proper noun that is
    itself spelled with an ampersand ("Ben & Jerry's"), where swapping in
    'and' would misspell the name rather than restyle it.

    _data/food/taxonomy.yml's ampersand_proper_nouns is the allow-list,
    declared by exact phrase, so a stylistic '&' still fails and a new brand
    name needs an explicit entry.
    """
    allowed = taxonomy.get("ampersand_proper_nouns") or []
    value = str(recipe.fm.get("title", ""))
    if "&" not in value:
        return
    remainder = value
    for phrase in allowed:
        remainder = remainder.replace(phrase, "")
    assert "&" not in remainder, (
        f"{where(recipe)} `title: {value!r}` contains an ampersand that "
        f"isn't part of a declared proper noun. Titles use the word "
        f"'and' -- if this is a real brand/proper name, add the exact "
        f"phrase to ampersand_proper_nouns in _data/food/taxonomy.yml."
    )


def test_spellings(recipe):
    problems = spelling_problems(checkable_raw(recipe))
    assert not problems, (
        f"{where(recipe)} uses non-house spellings: " + "; ".join(problems)
    )


def test_temperatures_use_degree_c(recipe):
    bad = degreeless_temperatures(checkable_raw(recipe))
    assert not bad, (
        f"{where(recipe)} writes temperature(s) {bad} without the degree sign. "
        f"Always °C, e.g. 200°C."
    )


# "A squeeze" of citrus is written as a fraction of the fruit (DECISIONS §5).
# The verb is fine ("squeeze out the gelatine"), and so is "freshly squeezed".
_SQUEEZE_MEASURE = re.compile(
    r"\bsqueeze of\b|^\s*-?\s*(?:item|amount):.*\bsqueeze\b", re.I | re.M)


def test_citrus_is_measured_not_squeezed(recipe):
    hits = [m.group(0).strip() for m in
            _SQUEEZE_MEASURE.finditer(checkable_raw(recipe))]
    assert not hits, (
        f"{where(recipe)} measures citrus as a squeeze: {hits[:3]}. Write "
        f"the fruit, e.g. amount \"¼\", item \"lemon, juiced\", or in a step "
        f"\"¼ lemon, juiced\"."
    )


# --- butter, sugar, flour: closed list of qualifiers ------------------------
# #74. Each is a closed list of allowed names, not merely "isn't bare":
# "caster sugar" and "muscovado sugar" are qualified and still wrong.
#
# An allowed name is matched as a whole-word phrase anywhere in the item, since
# qualifiers wrap in all directions ("melted salted butter", "~2 tbsp dark
# brown muscovado sugar"). `\b` matters: a substring check would find "salted"
# inside "unsalted".
_QUALIFIED_BUTTER = {"salted butter", "unsalted butter"}
# A line that is butter for the tin and nothing else. "plus extra" means the
# line is an ingredient of the dish too, so it does not match.
_ONLY_FOR_GREASING = re.compile(r"^(?!.*\bplus\b).*,\s*(?:extra,\s*)?(?:for greasing|to grease)\b", re.I)
_QUALIFIED_FLOUR = {"plain flour", "self-raising flour", "rice flour", "gluten-free flour"}
_QUALIFIED_SUGAR = {
    "golden caster sugar", "golden granulated sugar", "white caster sugar",
    "light brown soft sugar", "dark brown soft sugar",
    "light brown muscovado sugar", "dark brown muscovado sugar",
    "demerara sugar", "icing sugar", "coconut palm sugar", "palm sugar",
}

# Ingredients that contain the word but are not the ingredient: a butter bean
# is not butter. Out of scope, not in need of a qualifier.
_COMPOUND_EXCLUDE = {
    "butter": re.compile(
        r"\b(butter beans?|peanut butter|almond butter|cashew butter"
        r"|pistachio butter|all-butter)\b", re.I,
    ),
    "sugar": re.compile(r"\bsugar snap\b", re.I),
    "flour": None,
    "cloves": re.compile(r"\bgarlic\b", re.I),
    "milk": re.compile(r"\bmilk chocolate\b", re.I),
}


def _unqualified(recipe, word: str, allowed: set[str]) -> list[str]:
    exclude = _COMPOUND_EXCLUDE.get(word)
    allowed_pattern = re.compile(
        "|".join(rf"\b{re.escape(phrase)}\b" for phrase in allowed), re.I,
    )
    fields = [
        ("main_ingredients", [str(x) for x in (recipe.fm.get("main_ingredients") or [])]),
        ("ingredient", recipe.ingredient_items),
    ]
    bad = []
    for field, values in fields:
        for v in values:
            name = re.split(r"[,(]", v)[0].strip()
            if not re.search(rf"\b{word}\b", name, re.I):
                continue
            if exclude and exclude.search(name):
                continue
            # The word-presence gate above cuts at the first comma OR paren,
            # so the word in a later clause does not fire. The allowed-phrase
            # check cuts at the first comma only: a qualifier may sit in a
            # trailing parenthetical, as in "milk (any kind)".
            qualify_scope = v.split(",", 1)[0].strip()
            if not allowed_pattern.search(qualify_scope):
                bad.append(f"{field} {v!r}")
    return bad


def test_butter_specifies_salted_or_unsalted(recipe):
    """#74, #140. Butter is "salted butter" or "unsalted butter" and nothing
    else: the choice changes the recipe. Butter only for greasing is exempt;
    "plus extra for greasing" is not, because that line is also in the dish.
    """
    bad = [b for b in _unqualified(recipe, "butter", _QUALIFIED_BUTTER)
           if not _ONLY_FOR_GREASING.search(b)]
    assert not bad, (
        f"{where(recipe)} has unqualified butter: {bad!r}. "
        f"Allowed: salted butter, unsalted butter."
    )


def test_flour_specifies_type(recipe):
    """GitHub issue #74. Bare "flour" leaves the cook guessing which one."""
    bad = _unqualified(recipe, "flour", _QUALIFIED_FLOUR)
    assert not bad, (
        f"{where(recipe)} has unqualified flour: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_FLOUR))}."
    )


def test_sugar_specifies_type(recipe):
    """#74, #79. Bare "sugar", "caster sugar" (needs "golden" or "white") and
    "brown sugar" (needs light/dark and soft/muscovado) leave the cook
    guessing. "white caster sugar" is its own allowed name on purpose: a
    meringue made with golden caster sugar picks up a cream tint.
    """
    bad = _unqualified(recipe, "sugar", _QUALIFIED_SUGAR)
    assert not bad, (
        f"{where(recipe)} has unqualified sugar: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_SUGAR))}."
    )


# --- mustard, soy sauce, ginger, mixed/five-spice powder ---------------------
# #143, #142, #136, #137. The same closed-list pattern as butter, sugar and
# flour. "mustard oil" is a distinct ingredient, a cooking oil pressed from
# mustard seeds, not a kind of condiment mustard.
_QUALIFIED_MUSTARD = {
    "english mustard", "english mustard powder", "dijon mustard",
    "french mustard", "wholegrain mustard", "whole mustard seeds",
    "mustard oil",
}
_QUALIFIED_SOY_SAUCE = {"dark soy sauce", "light soy sauce"}
_QUALIFIED_GINGER = {"fresh ginger", "ground ginger", "ginger paste"}


def test_mustard_specifies_type(recipe):
    """GitHub issue #143."""
    bad = _unqualified(recipe, "mustard", _QUALIFIED_MUSTARD)
    assert not bad, (
        f"{where(recipe)} has unqualified mustard: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_MUSTARD))}."
    )


def test_soy_sauce_specifies_dark_or_light(recipe):
    """GitHub issue #142."""
    bad = _unqualified(recipe, "soy sauce", _QUALIFIED_SOY_SAUCE)
    assert not bad, (
        f"{where(recipe)} has unqualified soy sauce: {bad!r}. "
        f"Allowed: dark soy sauce, light soy sauce."
    )


def test_soy_sauce_as_tamari_alternative_specifies_dark_or_light(recipe):
    """A soy sauce offered as an alternative to tamari says dark or light -- #142.

    `_unqualified()` cuts each value at the first comma or paren, so "tamari
    (or low-sodium soy sauce)" reaches test_soy_sauce_specifies_dark_or_light
    as "tamari" and passes. This scans the whole string, and fires only on an
    item that names tamari.
    """
    bad = []
    for field, values in (
        ("main_ingredients", [str(x) for x in (recipe.fm.get("main_ingredients") or [])]),
        ("ingredient", recipe.ingredient_items),
    ):
        for v in values:
            if not re.search(r"\btamari\b", v, re.I):
                continue
            for m in re.finditer(r"\bsoy sauce\b", v, re.I):
                prefix = v[: m.start()]
                if not re.search(r"\b(dark|light)\s*$", prefix, re.I):
                    bad.append(f"{field} {v!r}")
    assert not bad, (
        f"{where(recipe)} offers soy sauce as a tamari alternative without "
        f"saying dark or light: {bad!r}."
    )


def test_ginger_specifies_fresh_ground_or_paste(recipe):
    """#136. Checked in the ingredient list as well as main_ingredients: a
    prep word alone ("grated ginger") does not say which kind was used, so
    the literal word is required ("grated fresh ginger").
    """
    bad = _unqualified(recipe, "ginger", _QUALIFIED_GINGER)
    assert not bad, (
        f"{where(recipe)} has unqualified ginger: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_GINGER))}."
    )


def test_mixed_spice_and_five_spice_say_powder(recipe):
    """#137. Sold and used as a powder, so the ingredient name says so."""
    bad = _unqualified(recipe, "mixed spice", {"mixed spice powder"})
    bad += _unqualified(recipe, "five-spice", {"five-spice powder"})
    assert not bad, (
        f"{where(recipe)} has {bad!r} without \"powder\". "
        f"Allowed: mixed spice powder, five-spice powder."
    )


# --- nutmeg, cinnamon, cloves, vanilla ---------------------------------------
# #151. "cloves" excludes garlic cloves via _COMPOUND_EXCLUDE.
_QUALIFIED_NUTMEG = {"whole nutmeg", "ground nutmeg"}
_QUALIFIED_CINNAMON = {"cinnamon stick", "cinnamon sticks", "ground cinnamon"}
_QUALIFIED_CLOVES = {"whole cloves", "ground cloves"}
_QUALIFIED_VANILLA = {"vanilla extract", "vanilla essence", "vanilla pod"}


def test_nutmeg_cinnamon_cloves_vanilla_specify_type(recipe):
    """GitHub issue #151."""
    bad = _unqualified(recipe, "nutmeg", _QUALIFIED_NUTMEG)
    bad += _unqualified(recipe, "cinnamon", _QUALIFIED_CINNAMON)
    bad += _unqualified(recipe, "cloves", _QUALIFIED_CLOVES)
    bad += _unqualified(recipe, "vanilla", _QUALIFIED_VANILLA)
    assert not bad, (
        f"{where(recipe)} has unqualified spice(s): {bad!r}. "
        f"Allowed: nutmeg ({', '.join(sorted(_QUALIFIED_NUTMEG))}), "
        f"cinnamon ({', '.join(sorted(_QUALIFIED_CINNAMON))}), "
        f"cloves ({', '.join(sorted(_QUALIFIED_CLOVES))}), "
        f"vanilla ({', '.join(sorted(_QUALIFIED_VANILLA))})."
    )


# --- cardamom -----------------------------------------------------------------
# Always green or black, always pods, powder or seeds. The singular forms are
# allowed because a recipe can call for one pod.
_QUALIFIED_CARDAMOM = {
    "green cardamom pod", "green cardamom pods", "green cardamom powder",
    "green cardamom seed", "green cardamom seeds",
    "black cardamom pod", "black cardamom pods", "black cardamom powder",
    "black cardamom seed", "black cardamom seeds",
}


def test_cardamom_specifies_type(recipe):
    """Always green or black, always pods/powder/seeds."""
    bad = _unqualified(recipe, "cardamom", _QUALIFIED_CARDAMOM)
    assert not bad, (
        f"{where(recipe)} has unqualified cardamom: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_CARDAMOM))}."
    )


# --- vinegar ------------------------------------------------------------------
# #150. "rice vinegar" is the one name for rice wine vinegar.
_QUALIFIED_VINEGAR = {
    "apple cider vinegar", "balsamic vinegar", "red wine vinegar",
    "rice vinegar", "sherry vinegar", "white wine vinegar", "malt vinegar",
}


def test_vinegar_specifies_type(recipe):
    """GitHub issue #150."""
    bad = _unqualified(recipe, "vinegar", _QUALIFIED_VINEGAR)
    assert not bad, (
        f"{where(recipe)} has unqualified vinegar: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_VINEGAR))}."
    )


# --- garlic: form, not the amount/item split ---------------------------------
# #171. Not the shared _unqualified() helper, which reads item text only:
# garlic's counting unit is "clove", so `amount: 3 cloves, item: garlic,
# minced` is complete. The ingredient list is checked as amount plus item;
# main_ingredients has no amount, so the form must be in the string itself.
_QUALIFIED_GARLIC_FORM = re.compile(
    r"\bcloves?\b|\bhead\b|\bpaste\b|\bpur[ée]e\b|\bpowder\b|\bgranulated\b|\bwild garlic\b", re.I,
)


def test_garlic_specifies_form(recipe):
    bad = []
    for m in (recipe.fm.get("main_ingredients") or []):
        name = str(m)
        if not re.search(r"\bgarlic\b", name, re.I):
            continue
        if not _QUALIFIED_GARLIC_FORM.search(name):
            bad.append(f"main_ingredients {name!r}")
    for group in recipe.fm.get("ingredient_groups") or []:
        for item in group.get("items") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("item", ""))
            base = re.split(r"[,(]", name)[0].strip()
            if not re.search(r"\bgarlic\b", base, re.I):
                continue
            combined = f"{item.get('amount', '')} {name}"
            if not _QUALIFIED_GARLIC_FORM.search(combined):
                bad.append(f"ingredient {name!r}")
    assert not bad, (
        f"{where(recipe)} has unqualified garlic: {bad!r}. State the form -- "
        f"cloves, head, paste, purée, powder, or granulated."
    )


# --- loomi: colour, since black and white/yellow are different products ----
# #173.
_QUALIFIED_LOOMI = {"black loomi", "white loomi", "yellow loomi"}


def test_loomi_specifies_colour(recipe):
    bad = _unqualified(recipe, "loomi", _QUALIFIED_LOOMI)
    assert not bad, (
        f"{where(recipe)} has unqualified loomi: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_LOOMI))}."
    )


# --- milk: type -- deliberately a standing checklist -------------------------
# #167. A checklist, not a guard expected to be green: which milk a recipe
# specified is confirmed from its source, never defaulted to "whole milk".
# "milk (any kind)" is a real answer, for a recipe that does not care; it is
# recognised only as a trailing parenthetical (see _unqualified).
_QUALIFIED_MILK = {
    "whole milk", "semi-skimmed milk", "skimmed milk", "buttermilk",
    "oat milk", "almond milk", "soya milk", "coconut milk", "evaporated milk",
    "condensed milk", "sweetened condensed milk", "goat's milk", "any kind",
}


def test_milk_specifies_type(recipe):
    """Milk names its type, or says "(any kind)" -- #167.

    If an ingredient line states "milk (any kind)", a bare "milk" in
    main_ingredients describes that same answered choice and is exempt. The
    exemption only removes a main_ingredients hit, never an ingredient one.
    """
    bad = _unqualified(recipe, "milk", _QUALIFIED_MILK)
    if any(re.search(r"\bmilk\s*\(any kind\)", item, re.I) for item in recipe.ingredient_items):
        bad = [b for b in bad if not b.startswith("main_ingredients")]
    assert not bad, (
        f"{where(recipe)} has unqualified milk: {bad!r}. Confirm from the "
        f"original source rather than assuming whole milk -- "
        f"allowed: {', '.join(sorted(_QUALIFIED_MILK))}."
    )


# --- chocolate: type, plus a cacao percentage on the recipe page only -------
# #139. Dark-family chocolate carries a cacao percentage on the recipe's
# ingredient list, so a cook knows what to buy; main_ingredients stays a plain
# type name. Milk and white chocolate never take a percentage. Chips and
# shavings need a type word but no percentage.
_CHOCOLATE_PERCENT = {
    "dark chocolate": "70",
    "very dark chocolate": "90",
    "unsweetened chocolate": "100",
}
_CHOCOLATE_NO_PERCENT = {"milk chocolate", "white chocolate"}
_ALL_CHOCOLATE_TYPES = set(_CHOCOLATE_PERCENT) | _CHOCOLATE_NO_PERCENT
_CHOCOLATE_FORM_EXEMPT = re.compile(r"\b(chips|shavings)\b", re.I)

# A prepared product, not a bar of chocolate to type: exempt entirely.
_CHOCOLATE_COMPOUND_EXCLUDE = re.compile(r"\bchocolate (syrup|beans)\b", re.I)


def test_chocolate_specifies_type(recipe):
    """#139. Every chocolate mention, in either field, names an allowed type."""
    allowed_pattern = re.compile(
        "|".join(rf"\b{re.escape(t)}\b" for t in _ALL_CHOCOLATE_TYPES), re.I,
    )
    fields = [
        ("main_ingredients", [str(x) for x in (recipe.fm.get("main_ingredients") or [])]),
        ("ingredient", recipe.ingredient_items),
    ]
    bad = []
    for field, values in fields:
        for v in values:
            name = re.split(r"[,(]", v)[0].strip()
            if not re.search(r"\bchocolate\b", name, re.I):
                continue
            if _CHOCOLATE_COMPOUND_EXCLUDE.search(name):
                continue
            if not allowed_pattern.search(name):
                bad.append(f"{field} {v!r}")
    assert not bad, (
        f"{where(recipe)} has unqualified chocolate: {bad!r}. "
        f"Allowed: {', '.join(sorted(_ALL_CHOCOLATE_TYPES))}."
    )


def test_chocolate_main_ingredients_has_no_percentage(recipe):
    """#139. main_ingredients names the type only: "dark chocolate", never
    "dark chocolate, 70% cacao". The percentage belongs on the recipe page's
    ingredient list, not the index-page pill.
    """
    bad = []
    for v in (recipe.fm.get("main_ingredients") or []):
        name = str(v)
        if not re.search(r"\bchocolate\b", name, re.I):
            continue
        if re.search(r"\d+\s*%", name):
            bad.append(name)
    assert not bad, (
        f"{where(recipe)} has a percentage in main_ingredients: {bad!r}. "
        f"Percentages belong on the recipe page's ingredient list, not here."
    )


def test_chocolate_percentage_matches_type(recipe):
    """#139. On the ingredient list, dark, very dark and unsweetened chocolate
    carry the percentage that identifies which it is: 70, 90, 100. A
    mismatch looks fine at a glance ("very dark chocolate, 100% cacao" is
    unsweetened). Chips and shavings are exempt.
    """
    bad = []
    for item in recipe.ingredient_items:
        name = re.split(r"[,(]", item)[0].strip()
        if not re.search(r"\bchocolate\b", name, re.I):
            continue
        if _CHOCOLATE_COMPOUND_EXCLUDE.search(name) or _CHOCOLATE_FORM_EXEMPT.search(item):
            continue
        # Longest phrase first, stopping at the first match: "very dark
        # chocolate" contains "dark chocolate", so checking every entry
        # would hold a correct 90% item to plain dark's 70%.
        for choc_type in sorted(_CHOCOLATE_PERCENT, key=len, reverse=True):
            if re.search(rf"\b{re.escape(choc_type)}\b", name, re.I):
                pct = _CHOCOLATE_PERCENT[choc_type]
                if not re.search(rf"\b{pct}%\s*cacao\b", item, re.I):
                    bad.append(item)
                break
    assert not bad, (
        f"{where(recipe)} has {bad!r} without its required cacao percentage "
        f"(dark 70%, very dark 90%, unsweetened 100%)."
    )


# --- eggs: size, count agreement, weight for bakes ---------------------------
# #144, #145, #147. The rules are about whole eggs: yolks and whites are
# excluded throughout.
_EGG_SIZE_RE = re.compile(r"\b(small|medium|large|extra large)\b", re.I)


def _whole_egg_items(recipe):
    out = []
    for group in recipe.fm.get("ingredient_groups") or []:
        for item in group.get("items") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("item", ""))
            if re.search(r"\begg", name, re.I) and not re.search(r"\b(yolks?|whites?)\b", name, re.I):
                out.append(item)
    return out


def test_egg_size_is_stated(recipe):
    """#144, #145. Every whole-egg ingredient states a UK size
    (small/medium/large/extra large) in its `amount:` field, not in `item:`
    ("large eggs, lightly beaten" with amount: "3" fails).
    """
    bad = []
    for item in _whole_egg_items(recipe):
        amount = str(item.get("amount", ""))
        if not _EGG_SIZE_RE.search(amount):
            bad.append(item.get("item"))
    assert not bad, (
        f"{where(recipe)} has egg ingredient(s) with no UK size in `amount:`: "
        f"{bad!r}. State small/medium/large/extra large, e.g. amount: "
        f'"2 large".'
    )


def test_main_ingredients_egg_count_agrees(recipe):
    """#147. main_ingredients says "egg" for a single egg and "eggs" for more
    than one, checked against the total count in the ingredient list.
    """
    main = [str(m) for m in (recipe.fm.get("main_ingredients") or [])]
    egg_entries = [m for m in main if re.search(r"\begg", m, re.I)
                   and not re.search(r"\b(yolks?|whites?)\b", m, re.I)]
    if not egg_entries:
        return
    items = _whole_egg_items(recipe)
    total = 0
    for item in items:
        count_match = re.match(r"\s*(\d+)", str(item.get("amount", "")))
        if count_match:
            total += int(count_match.group(1))
    if total == 0:
        return
    wanted = "egg" if total == 1 else "eggs"
    bad = [e for e in egg_entries if not re.search(rf"\b{wanted}\b", e, re.I)]
    assert not bad, (
        f"{where(recipe)} main_ingredients {bad!r} doesn't agree with the "
        f"actual egg count ({total}) -- should say {wanted!r}."
    )


# --- size belongs with the count, not prefixed onto the item ----------------
# #149. Scoped to a bare numeric count. A weight ("400 g large open
# mushrooms") keeps its size as an adjective, and "small bunch" with no number
# is itself the amount. scripts/tidy_drafts.py imports the pattern from here.
_LEADING_SIZE_WORD = re.compile(r"^(small|medium|large|extra large|baby)\s+", re.I)


def test_size_word_is_with_the_count_not_the_item(recipe):
    """"2 large cooking apples" as amount: "2", item: "large cooking apples"
    means the highlighter only picks up "2": the size sits unstyled in the
    item text with no error anywhere (#149). Bare numeric counts only; see
    the comment above for what is excluded.
    """
    bad = []
    for group in recipe.fm.get("ingredient_groups") or []:
        for item in group.get("items") or []:
            if not isinstance(item, dict):
                continue
            amount = str(item.get("amount", ""))
            name = str(item.get("item", ""))
            if re.fullmatch(r"\d+", amount) and _LEADING_SIZE_WORD.match(name):
                bad.append(item.get("item"))
    assert not bad, (
        f"{where(recipe)} has size word(s) prefixed onto the item instead of "
        f"the amount: {bad!r}. e.g. amount: \"2 large\", item: \"cooking "
        f"apples, chopped\", not amount: \"2\", item: \"large cooking "
        f"apples, chopped\"."
    )


# --- homemade pastry needs salt ----------------------------------------------
# #135. Detected by an ingredient GROUP named for pastry, dough or choux: not
# "has flour and butter", which a cake batter also has, and not the word
# pastry anywhere, which a recipe buying it ready-made would trip.
_PASTRY_GROUP_NAME = re.compile(r"\b(pastry|dough|choux)\b", re.I)


def test_homemade_pastry_has_salt(recipe):
    for group in recipe.fm.get("ingredient_groups") or []:
        name = (group.get("name") or "") if isinstance(group, dict) else ""
        if not _PASTRY_GROUP_NAME.search(name):
            continue
        items = [str(it.get("item", "")) if isinstance(it, dict) else str(it)
                 for it in (group.get("items") or [])]
        has_salt = any(re.search(r"\bsalt\b", it, re.I) for it in items)
        assert has_salt, (
            f"{where(recipe)} has a homemade pastry group ({name!r}) with no "
            f"salt among its ingredients."
        )
        method_text = " ".join(recipe.method_steps)
        assert re.search(r"\bsalt\b", method_text, re.I), (
            f"{where(recipe)} has salt in the {name!r} ingredient list but "
            f"the method never mentions it -- season the pastry."
        )


# --- unsalted butter needs salt somewhere, or an explicit note --------------
# #138. The method need not say "salt" where a catch-all step covers every
# ingredient ("Blend everything together"). A bare "all" is not one: "mix all
# the flour in" names one ingredient, and would excuse any method.
_SALT_WORD = re.compile(r"(?<!un)salt", re.I)
_CATCH_ALL_METHOD = re.compile(
    r"\beverything\b|\ball (?:of )?(?:the )?ingredients\b", re.I)


def test_unsalted_butter_has_salt_or_a_note(recipe):
    items = recipe.ingredient_items
    if not any(re.search(r"\bunsalted butter\b", it, re.I) for it in items):
        return
    has_salt_ingredient = any(_SALT_WORD.search(it) for it in items)
    if has_salt_ingredient:
        method_text = " ".join(recipe.method_steps)
        assert _SALT_WORD.search(method_text) or _CATCH_ALL_METHOD.search(method_text), (
            f"{where(recipe)} uses unsalted butter and lists salt as an "
            f"ingredient, but the method never mentions it (and isn't a "
            f"single catch-all step that already covers every ingredient)."
        )
        return
    notes = recipe.fm.get("notes") or []
    note_text = " ".join((n.get("text", "") if isinstance(n, dict) else str(n)) for n in notes)
    assert _SALT_WORD.search(note_text), (
        f"{where(recipe)} uses unsalted butter with no salt ingredient and "
        f"no note explaining it doesn't need one -- add salt, or a note."
    )


# --- accents ----------------------------------------------------------------
# The word list and the matcher are shared from conftest (#670). Which fields
# to look in is food's own: `_accent_check_fields` below.


def _accent_check_fields(recipe) -> list[tuple[str, str]]:
    """Every field an accent might need to appear in: recipe.prose plus the
    title, main_ingredients, star_ingredient, ingredient item names and body
    content (#46, #48, #82).

    .prose covers front-matter running text only, not names or body content.
    Slugs, filenames and `source:` are left out; test_accents_in_prose's
    docstring says why.
    """
    out = list(recipe.prose)
    if recipe.fm.get("title"):
        out.append(("title", recipe.fm["title"]))
    for i, ing in enumerate(recipe.fm.get("main_ingredients") or [], 1):
        out.append((f"main_ingredients {i}", str(ing)))
    if recipe.fm.get("star_ingredient"):
        out.append(("star_ingredient", str(recipe.fm["star_ingredient"])))
    if recipe.body:
        out.append(("body content", recipe.body))
    for i, item in enumerate(recipe.ingredient_items, 1):
        out.append((f"ingredient item {i}", item))
    return out


def test_accents_in_prose(recipe):
    """Culinary words that take an accent should have one.

    Checked against the curated list in _data/accented_words.yml rather than by
    detection, because no detector can tell a missing accent from a word that
    never had one.

    Scope is `_accent_check_fields` -- never slugs or filenames, which must
    stay ASCII, and never `source:`, where a citation is reproduced as the
    publication spells it.
    """
    words = _accented_words()
    # Asserted, not `if not words: return`: an empty or mis-keyed
    # accented_words.yml would silence this check on every recipe and report
    # green.
    assert words, (
        "_data/accented_words.yml has no `words:` map, so there is nothing to "
        "check any recipe against. That file IS this test's specification -- "
        "an empty one means the accent rule is unenforced, not satisfied."
    )
    problems = _accent_problems(_accent_check_fields(recipe), words)
    assert not problems, (
        f"{where(recipe)} uses unaccented spelling(s):\n  " + "\n  ".join(problems)
        + "\n\nIf the word genuinely takes no accent in British usage, add it to "
          "the `no_accent` list in _data/accented_words.yml so nobody 'fixes' it "
          "back."
    )


def test_accents_in_drafts():
    """Same rule as test_accents_in_prose, for _food_drafts/.

    A draft carries its spelling forward when it is promoted.

    Skips without the drafts (#378): this reads _food_drafts/ and nothing
    else, so in CI, where that private repo is absent, ALL_DRAFTS is empty and
    it would report green having looked at nothing.
    """
    from conftest import ALL_DRAFTS, DRAFTS_PRESENT, NO_DRAFTS_REASON
    if not DRAFTS_PRESENT:
        pytest.skip(NO_DRAFTS_REASON)

    words = _accented_words()
    assert words, (
        "_data/accented_words.yml has no `words:` map, so there is nothing to "
        "check any draft against -- see test_accents_in_prose above for why "
        "this asserts rather than returning quietly."
    )
    problems = []
    for draft in ALL_DRAFTS:
        for p in _accent_problems(_accent_check_fields(draft), words):
            problems.append(f"_food_drafts/{draft.slug}.md — {p}")
    assert not problems, (
        "Unaccented spelling(s) in drafts:\n  " + "\n  ".join(problems)
        + "\n\nFix now so it's already right when the draft is promoted."
    )


# --- pan/ingredient sizes ----------------------------------------------------

_SIZE_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12",
}
_SIZE_UNIT = r"(?:inch(?:es)?|cm|centimet(?:re|er)s?|mm|millimet(?:re|er)s?)"


def _size_problems(fields: list[tuple[str, str]]) -> list[str]:
    problems = []
    for location, text in fields:
        for word, digit in _SIZE_NUMBER_WORDS.items():
            m = re.search(rf"\b{word}[- ]{_SIZE_UNIT}\b", text, re.I)
            if m:
                unit = re.split(r"[- ]", m.group(0), maxsplit=1)[1]
                problems.append(f"{location}: {m.group(0)!r} should be '{digit}-{unit}'")
    return problems


def test_pan_and_ingredient_sizes_use_digits(recipe):
    """#95. "7-inch", not "seven-inch"; "4-cm piece of ginger". A physical
    dimension is a measurement, not prose, so it takes digits (unlike "ten
    minutes of glory").

    Same field set as the accent checks: a size can be in an ingredient's
    name as easily as in a method step.
    """
    problems = _size_problems(_accent_check_fields(recipe))
    assert not problems, (
        f"{where(recipe)} spells out a size instead of using digits:\n  "
        + "\n  ".join(problems)
    )


def test_pan_and_ingredient_sizes_use_digits_in_drafts():
    """Same rule as test_pan_and_ingredient_sizes_use_digits, for
    _food_drafts/. Skips when the private drafts are absent (#378), for the
    reason test_accents_in_drafts gives.
    """
    from conftest import ALL_DRAFTS, DRAFTS_PRESENT, NO_DRAFTS_REASON
    if not DRAFTS_PRESENT:
        pytest.skip(NO_DRAFTS_REASON)

    problems = []
    for draft in ALL_DRAFTS:
        for p in _size_problems(_accent_check_fields(draft)):
            problems.append(f"_food_drafts/{draft.slug}.md — {p}")
    assert not problems, (
        "Spelled-out size(s) in drafts:\n  " + "\n  ".join(problems)
        + "\n\nFix now so it's already right when the draft is promoted."
    )


# --- oven temperature: fan required ------------------------------------------
# #146. House style is fan oven only (MANUAL §5).
_OVEN_WORD_RE = re.compile(r"\b(?:bake|roast|blast|oven)\w*\b", re.I)
_OVEN_TEMP_RE = re.compile(r"\d{2,3}(?:[–-]\d{2,3})?\s*°C(\s*fan)?\b", re.I)
# The phrasings that mark a °C figure as an INTERNAL temperature, so the fan
# rule does not demand "fan" on a thermometer reading. "out at" is the site's
# own wording for it (never "pull at"), so it has to be on this list.
_INTERNAL_TEMP_RE = re.compile(
    r"(?:(?:internal|thigh|breast|core|centre|center)\s+temp(?:erature)?\s+of"
    r"|(?:take\s+(?:it|them)\s+)?out\s+at"
    r"|reads?|reach(?:es)?)"
    r"(?:\s+(?:at least|about|around))?\s*$",
    re.I,
)


def test_oven_temperature_says_fan(recipe):
    """#146. An oven temperature says "fan".

    A °C figure counts as an oven temperature only when its step also
    mentions baking, roasting, blasting or the oven: stovetop, tempering and
    internal-doneness readings have no fan setting. Blind spot: a step that
    restates oven figures with no oven word of its own is not checked.
    """
    bad = []
    for step in recipe.method_steps:
        # Markdown links are unwrapped first. _INTERNAL_TEMP_RE reads the words
        # immediately before the figure, and a linked temperature (#260) puts a
        # "[" in that gap: "reads [74–75°C](#doneness)" would otherwise count
        # as an oven temperature missing its "fan".
        step = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", step)
        if not _OVEN_WORD_RE.search(step):
            continue
        for m in _OVEN_TEMP_RE.finditer(step):
            if _INTERNAL_TEMP_RE.search(step[: m.start()][-40:]):
                continue
            if not m.group(1):
                bad.append(m.group(0))
    assert not bad, (
        f"{where(recipe)} has oven temperature(s) without \"fan\": {bad!r}. "
        f"House style is fan-only -- confirm from the original recipe and "
        f"add \"fan\", e.g. \"180°C fan\"."
    )


def test_no_recipe_says_cooking_temperatures(recipe):
    """"internal temperatures chart", never "cooking temperatures". Issue #352.

    The chart measures the inside of the meat; "cooking temperatures" names
    the oven, a different number and the wrong one to check doneness against
    (#338). A copy rule, so nothing else catches it: the page builds and the
    link works.
    """
    body = recipe.path.read_text(encoding="utf-8")
    assert "cooking temperature" not in body.lower(), (
        f"{where(recipe)} says 'cooking temperatures'. Use 'internal "
        f"temperatures chart' -- '(check [internal temperatures chart]"
        f"(#doneness))' in body copy, and the metadata box adds its own "
        f"'but check ...' via _layouts/recipe.html. See #352 and #338."
    )


def test_ingredient_group_names_do_not_repeat_for_the(recipe):
    """The layout supplies "For the ...", so a group must not supply it too.

    #329. A group named "for the sauce" renders as "For the for the sauce:",
    and only on a page with more than one ingredient group: a single-group
    recipe prints no heading, so the mistake can sit unseen.

    A group named `variation: ...` skips the prefix on purpose (#342): "For
    the ..." promises something the reader has to make.
    """
    groups = recipe.fm.get("ingredient_groups") or []
    bad = [g.get("name") for g in groups
           if isinstance(g, dict) and isinstance(g.get("name"), str)
           and g["name"].strip().lower().startswith("for the")]
    assert not bad, (
        f"{where(recipe)} has ingredient group name(s) starting with 'for "
        f"the': {bad!r}. The layout already adds it, so this renders as 'For "
        f"the for the ...'. Name the group for its part alone, or prefix it "
        f"'variation: ' if it is optional (#329)."
    )
