"""House style: time words, typography, spelling.

The rule that catches the most is the split convention agreed 2026-07-25:
tighter for metadata than for prose.

    prep_time / cook_time  ->  mins, hrs
    prose                  ->  mins, hours, seconds

Only numeric quantities are abbreviated. "a minute", "at the last minute" and
"ten minutes of glory" are English, not inconsistency, and are left alone.
"""
from __future__ import annotations

import re

import pytest

from conftest import where

TIME_FIELDS = ("prep_time", "cook_time")

# Word forms that stay spelled out because a number does not precede them.
IDIOM = re.compile(r"(?<![0-9])\s*(minutes?|hours?|seconds?)\b", re.I)


def test_no_estimated_timings(recipe):
    """`Estimated N mins` values were invented by an earlier Claude.

    They are fine in _food_drafts/ but must never reach _food_recipes/ — an estimate that
    survives to publication is indistinguishable from a measured time.
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
    """`QQ` is Helen's own placeholder for "not decided/written yet" — see
    HANDOVER_v26.md §4 and §12. Fine anywhere in `_food_drafts/`, and never to
    be treated as an error there. But a `QQ` surviving into `_food_recipes/`
    means the recipe isn't actually finished, whatever field it's hiding in
    (a tagline link target, a cook_time, an ingredient amount, or an
    un-rewritten method step from ingest — `QQ - rewrite: ...`) — the same
    "drafting aid, not a published value" logic as `test_no_estimated_timings`
    above, generalised to the one marker Helen actually uses for "not yet".

    A second marker, `PLACEHOLDER`, briefly existed alongside this one
    (found 2026-08-09 in roast-beef-fillet.md's method) and was retired
    2026-08-10 at Helen's direction: one marker for everything, not two —
    see HANDOVER_v26.md §4's ingest paragraph. Don't reintroduce it.
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
    for location, text in recipe.prose:
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


TYPOGRAPHY = [
    ("slash fractions", r"(?<![\d/])(1/2|1/4|3/4|1/3|2/3|1/8|3/8|5/8|7/8)(?![\d/])",
     "use Unicode fractions: ½ ¼ ¾ ⅓ ⅔ ⅛ ⅜ ⅝ ⅞"),
    ("double hyphen", r"(?<!-)--(?!-)", "use an em dash —"),
    ("ASCII arrow", r"->", "use →"),
    ("wikilink", r"\[\[[^\]]+\]\]",
     "cross-recipe links are markdown, relative: [display text](../slug/)"),
    ("reversed link brackets", r"\([^()\n]+\)\[[^\]\n]*\]",
     "markdown links are [display text](../slug/), not (display text)[...] — "
     "the (text)[url] order never renders as a link, in any field"),
    ("ampersand in title", None, None),  # handled separately below
]


@pytest.mark.parametrize("name,pattern,fix",
                         [(n, p, f) for n, p, f in TYPOGRAPHY if p])
def test_typography(recipe, name, pattern, fix):
    hits = re.findall(pattern, recipe.raw)
    assert not hits, (
        f"{where(recipe)} contains {len(hits)} instance(s) of {name}: "
        f"{sorted(set(h if isinstance(h, str) else h[0] for h in hits))[:5]}. "
        f"Fix: {fix}."
    )


def test_no_ampersand_in_title(recipe):
    for field in ("title", "short_name"):
        value = str(recipe.fm.get(field, ""))
        assert "&" not in value, (
            f"{where(recipe)} `{field}: {value!r}` contains an ampersand. "
            f"Titles use the word 'and'."
        )


SPELLINGS = {
    r"\bdemarara\b": "demerara",
    r"\byogurt\b": "yoghurt",
    r"\bcreme fraiche\b": "crème fraîche",
    r"\bgruyere\b": "gruyère",
    r"\bpuree\b": "purée",
    r"\bsaute\b": "sauté",
    r"\bbain marie\b": "bain-marie",
}


def test_spellings(recipe):
    problems = []
    for pattern, correct in SPELLINGS.items():
        if re.search(pattern, recipe.raw, re.I):
            problems.append(f"{pattern.strip(chr(92) + 'b')} -> {correct}")
    assert not problems, (
        f"{where(recipe)} uses non-house spellings: " + "; ".join(problems)
    )


def test_temperatures_use_degree_c(recipe):
    bad = re.findall(r"\b(\d{2,3})\s*(?:oC|C\b)(?!\w)", recipe.raw)
    assert not bad, (
        f"{where(recipe)} writes temperature(s) {bad} without the degree sign. "
        f"Always °C, e.g. 200°C."
    )


# --- butter, sugar, flour: closed list of qualifiers ------------------------
# GitHub issue #74's main_ingredients spot-check (2026-08-10) turned this
# into a real closed-list rule, not just "isn't bare" -- Helen: outside an
# incidental use (melted butter for greasing a tin), butter is always
# "salted butter" or "unsalted butter", full stop, and sugar/flour each have
# their own short list of allowed names. See HANDOVER_v26.md for the
# reasoning behind each list.
#
# Supersedes two narrower tests: the old test_flour_and_sugar_specify_type
# only caught a totally bare name ("caster sugar" passed it fine, since it
# isn't bare), and the old brown-sugar-only test had a real gap -- it only
# fired when the name contained the word "brown", so bare "muscovado sugar"
# or "light muscovado sugar" (missing "brown" entirely) slipped through
# unnoticed. Found by running this same check against real data
# (sticky-marmalade-ham.md, a draft) before writing the replacement.
#
# Checked as a whole-word phrase anywhere in the name, not just a prefix or
# suffix -- real data has qualifiers wrapped in all directions: "melted
# salted butter", "knob of salted butter, optional", "~2 tbsp dark brown
# muscovado sugar", "dusting as preferred: icing sugar, cocoa powder...".
# A plain substring check would be too loose (e.g. "salted" inside
# "unsalted"), but \b...\b isn't fooled by that -- there's no word boundary
# between "un" and "salted" in "unsalted".
_QUALIFIED_BUTTER = {"salted butter", "unsalted butter"}
_QUALIFIED_FLOUR = {"plain flour", "self-raising flour", "rice flour", "gluten-free flour"}
_QUALIFIED_SUGAR = {
    "golden caster sugar", "golden granulated sugar", "white caster sugar",
    "light brown soft sugar", "dark brown soft sugar",
    "light brown muscovado sugar", "dark brown muscovado sugar",
    "demerara sugar", "icing sugar", "coconut palm sugar", "palm sugar",
}

# Ingredients that merely contain the word but aren't the ingredient itself
# -- a butter bean isn't butter, sugar snap peas aren't sugar. Out of scope
# entirely, not something that needs a qualifier.
_COMPOUND_EXCLUDE = {
    "butter": re.compile(
        r"\b(butter beans?|peanut butter|almond butter|cashew butter"
        r"|pistachio butter|all-butter)\b", re.I,
    ),
    "sugar": re.compile(r"\bsugar snap\b", re.I),
    "flour": None,
    "cloves": re.compile(r"\bgarlic\b", re.I),
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
            if not allowed_pattern.search(name):
                bad.append(f"{field} {v!r}")
    return bad


def test_butter_specifies_salted_or_unsalted(recipe):
    """GitHub issues #74/#140. Only two names allowed, full stop -- not a
    style preference, salted-vs-unsalted actually changes the recipe.
    """
    bad = _unqualified(recipe, "butter", _QUALIFIED_BUTTER)
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
    """GitHub issues #74/#79. Bare "sugar", "caster sugar" (needs "golden"),
    "brown sugar" (needs light/dark and soft/muscovado) etc. all leave the
    cook guessing. "white caster sugar" is deliberately its own allowed name,
    distinct from "golden caster sugar" -- lemon-meringue-pie.md uses it
    specifically for the meringue, where a whiter sugar keeps the meringue
    from picking up a cream tint golden caster sugar would give it.
    """
    bad = _unqualified(recipe, "sugar", _QUALIFIED_SUGAR)
    assert not bad, (
        f"{where(recipe)} has unqualified sugar: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_SUGAR))}."
    )


# --- mustard, soy sauce, ginger, mixed/five-spice powder ---------------------
# GitHub issues #143/#142/#136/#137 -- same closed-list pattern and the same
# _unqualified() helper as butter/sugar/flour above, just different words and
# allowed sets. Mustard needed no data fixes at all when this was written --
# every real instance already used one of the six allowed names.
_QUALIFIED_MUSTARD = {
    "english mustard", "english mustard powder", "dijon mustard",
    "french mustard", "wholegrain mustard", "whole mustard seeds",
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


def test_ginger_specifies_fresh_ground_or_paste(recipe):
    """GitHub issue #136. Checked in both fields, not just main_ingredients
    -- Helen's call: the ingredient list needs the literal word too, not
    just a prep description ("grated ginger" -> "grated fresh ginger"),
    since a prep word alone doesn't say which kind was used.
    """
    bad = _unqualified(recipe, "ginger", _QUALIFIED_GINGER)
    assert not bad, (
        f"{where(recipe)} has unqualified ginger: {bad!r}. "
        f"Allowed: {', '.join(sorted(_QUALIFIED_GINGER))}."
    )


def test_mixed_spice_and_five_spice_say_powder(recipe):
    """GitHub issue #137. Sold and used as a powder -- the ingredient name
    should say so, not just "mixed spice" / "five-spice".
    """
    bad = _unqualified(recipe, "mixed spice", {"mixed spice powder"})
    bad += _unqualified(recipe, "five-spice", {"five-spice powder"})
    assert not bad, (
        f"{where(recipe)} has {bad!r} without \"powder\". "
        f"Allowed: mixed spice powder, five-spice powder."
    )


# --- nutmeg, cinnamon, cloves, vanilla ---------------------------------------
# GitHub issue #151. Same closed-list pattern again. "cloves" excludes garlic
# cloves via _COMPOUND_EXCLUDE -- a completely unrelated ingredient that
# happens to share the word, same shape of problem as butter beans earlier.
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


# --- vinegar ------------------------------------------------------------------
# GitHub issue #150. Needed zero data fixes for bare "vinegar" -- every real
# instance already named a type. Only real change was consolidating "rice
# wine vinegar" into "rice vinegar" (both named the same product; picked one).
# White wine and malt vinegar are in the allowed list pre-emptively -- common
# UK types, just not used by any current recipe.
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


# --- chocolate: type, plus a cacao percentage on the recipe page only -------
# GitHub issue #139. Helen: dark-family chocolate needs a cacao percentage on
# the recipe page's own ingredient list so a cook knows what to buy -- dark
# 70%, very dark 90%, unsweetened 100% -- but main_ingredients stays a plain
# type name with no percentage, the same vocabulary-vs-presentation split as
# everywhere else main_ingredients appears. Milk and white chocolate never
# get a percentage -- the distinction that matters for them isn't cacao
# content. Chip/shaving forms need a type word ("dark chocolate chips") but
# no percentage -- they're a mix-in or garnish, not the recipe's defining
# chocolate.
_CHOCOLATE_PERCENT = {
    "dark chocolate": "70",
    "very dark chocolate": "90",
    "unsweetened chocolate": "100",
}
_CHOCOLATE_NO_PERCENT = {"milk chocolate", "white chocolate"}
_ALL_CHOCOLATE_TYPES = set(_CHOCOLATE_PERCENT) | _CHOCOLATE_NO_PERCENT
_CHOCOLATE_FORM_EXEMPT = re.compile(r"\b(chips|shavings)\b", re.I)

# A prepared/branded product, not a bar of chocolate to type -- exempt
# entirely, same treatment as peanut butter/butter beans earlier.
_CHOCOLATE_COMPOUND_EXCLUDE = re.compile(r"\bchocolate (syrup|beans)\b", re.I)


def test_chocolate_specifies_type(recipe):
    """GitHub issue #139. Every chocolate mention, in either field, names
    one of the five allowed types.
    """
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
    """GitHub issue #139. main_ingredients names the type only -- "dark
    chocolate", never "dark chocolate, 70% cacao". The percentage belongs on
    the recipe page's own ingredient list, not the index-page pill.
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
    """GitHub issue #139. On the recipe page's own ingredient list (not
    main_ingredients), dark/very dark/unsweetened chocolate must carry the
    percentage that identifies which of the three it is -- 70/90/100. Chip
    and shaving forms are exempt (type word only, per Helen's call). A
    missing or mismatched percentage is exactly the kind of thing that looks
    fine at a glance: bens-chocolate-ice-cream.md said "very dark chocolate,
    100% cacao" for real, until this was caught and fixed 2026-08-10 --
    100% is unsweetened, not very dark.
    """
    bad = []
    for item in recipe.ingredient_items:
        name = re.split(r"[,(]", item)[0].strip()
        if not re.search(r"\bchocolate\b", name, re.I):
            continue
        if _CHOCOLATE_COMPOUND_EXCLUDE.search(name) or _CHOCOLATE_FORM_EXEMPT.search(item):
            continue
        # Longest phrase first and stop at the first match -- "very dark
        # chocolate" also contains "dark chocolate" as a substring, so
        # checking every entry would test a "very dark" item against plain
        # dark's 70% too and wrongly flag a correct "..., 90% cacao".
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


# --- accents ----------------------------------------------------------------

def _accented_words() -> dict:
    import yaml
    from conftest import SHARED_DATA_DIR
    path = SHARED_DATA_DIR / "accented_words.yml"
    if not path.exists():
        pytest.skip(
            "_data/accented_words.yml is missing. It is the curated list of "
            "culinary words whose correct spelling carries an accent."
        )
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("words") or {}


def _accent_check_fields(recipe) -> list[tuple[str, str]]:
    """Every field an accent might need to appear in, beyond recipe.prose.

    GitHub issues #46/#48/#82: "glace cherries" (an ingredient item name AND
    a main_ingredients entry), "Creme Brulee" (a title), "cafe" (found in
    henrys-quick-bulletproof-hollandaise-sauce.md's free-text body content,
    the long-form write-up added after HANDOVER's "exactly one file uses this"
    note was written) -- none of these are in .prose, which was built for the
    typography/time-word tests and only ever covered front-matter running
    text, not names or body content. title/short_name/main_ingredients/
    star_ingredient/ingredient item names/body content all get the same
    treatment as prose does; slugs, filenames and `source:` still don't --
    see test_accents_in_prose's docstring for why.
    """
    out = list(recipe.prose)
    if recipe.fm.get("title"):
        out.append(("title", recipe.fm["title"]))
    if recipe.fm.get("short_name"):
        out.append(("short_name", recipe.fm["short_name"]))
    for i, ing in enumerate(recipe.fm.get("main_ingredients") or [], 1):
        out.append((f"main_ingredients {i}", str(ing)))
    if recipe.fm.get("star_ingredient"):
        out.append(("star_ingredient", str(recipe.fm["star_ingredient"])))
    if recipe.body:
        out.append(("body content", recipe.body))
    for i, item in enumerate(recipe.ingredient_items, 1):
        out.append((f"ingredient item {i}", item))
    return out


def _accent_problems(fields: list[tuple[str, str]], words: dict) -> list[str]:
    problems = []
    for location, text in fields:
        for plain, accented in words.items():
            if re.search(rf"\b{re.escape(plain)}\b", text, re.I):
                problems.append(f"{location}: '{plain}' should be '{accented}'")
    return problems


def test_accents_in_prose(recipe):
    """Culinary words that take an accent should have one.

    Checked against the curated list in _data/accented_words.yml rather than by
    detection, because no detector can tell a missing accent from a word that
    never had one.

    Scope is title/short_name/main_ingredients/star_ingredient/ingredient item
    names plus everything in .prose (tagline, method, notes, ingredient
    notes) -- never slugs or filenames, which must stay ASCII, and never
    `source:`, where a citation is reproduced as the publication spells it.
    """
    words = _accented_words()
    if not words:
        return
    problems = _accent_problems(_accent_check_fields(recipe), words)
    assert not problems, (
        f"{where(recipe)} uses unaccented spelling(s):\n  " + "\n  ".join(problems)
        + "\n\nIf the word genuinely takes no accent in British usage, add it to "
          "the `no_accent` list in _data/accented_words.yml so nobody 'fixes' it "
          "back."
    )


def test_accents_in_drafts():
    """Same rule as test_accents_in_prose, for _food_drafts/.

    Same reasoning as test_no_main_ingredient_spelling_collisions in
    test_taxonomy.py: a draft carries its spelling forward when it's
    promoted to _food_recipes/, so it's worth catching before that happens
    rather than after.
    """
    from conftest import ALL_DRAFTS

    words = _accented_words()
    if not words:
        return
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
    """GitHub issue #95: "7-inch" not "seven-inch", same for an ingredient
    size like "4-cm piece of ginger". Unlike time words ("ten minutes of
    glory" is fine, per this file's own docstring), a size describing a
    physical dimension is a measurement, not prose, and reads the same way
    every other measurement on this site already does -- digits.

    Same field set as the accent checks (title/short_name/main_ingredients/
    star_ingredient/ingredient item names, plus prose): a size can appear as
    an ingredient's own name ("4-cm piece of ginger") just as easily as in
    a method step ("a 7-inch tin").
    """
    problems = _size_problems(_accent_check_fields(recipe))
    assert not problems, (
        f"{where(recipe)} spells out a size instead of using digits:\n  "
        + "\n  ".join(problems)
    )


def test_pan_and_ingredient_sizes_use_digits_in_drafts():
    """Same rule as test_pan_and_ingredient_sizes_use_digits, for
    _food_drafts/ -- same reasoning as test_accents_in_drafts.
    """
    from conftest import ALL_DRAFTS

    problems = []
    for draft in ALL_DRAFTS:
        for p in _size_problems(_accent_check_fields(draft)):
            problems.append(f"_food_drafts/{draft.slug}.md — {p}")
    assert not problems, (
        "Spelled-out size(s) in drafts:\n  " + "\n  ".join(problems)
        + "\n\nFix now so it's already right when the draft is promoted."
    )


# --- oven temperature: fan required ------------------------------------------
# GitHub issue #146. House style has been fan-only for a while
# (HANDOVER_v26.md §5: "always fan oven only, never conventional or gas
# mark"), but the word "fan" isn't actually written next to every existing
# temperature yet. Helen's explicit call: don't assume the numbers already
# there are confirmed fan figures just because house style says they should
# be -- leave this test failing on every one that's missing the word, and
# she'll confirm each against its original source recipe and add "fan" by
# hand as she gets to it, rather than have the test silently pass on
# unverified numbers. This is deliberately a checklist, not a guard that's
# expected to be green.
_OVEN_WORD_RE = re.compile(r"\b(?:bake|roast|blast|oven)\w*\b", re.I)
_OVEN_TEMP_RE = re.compile(r"\d{2,3}(?:[–-]\d{2,3})?\s*°C(\s*fan)?\b", re.I)
_INTERNAL_TEMP_RE = re.compile(r"internal temperature\s+of\s*$", re.I)


def test_oven_temperature_says_fan(recipe):
    """GitHub issue #146. A °C figure only counts as an oven temperature when
    its step also mentions baking/roasting/blasting/the oven -- deliberately
    excludes stovetop and tempering readings (chocolate-ganache.md's
    cooling-stage figures, chocolate-mousse.md's "still warm" check) and
    internal-doneness checks (teriyaki-salmon.md's "internal temperature of
    57°C"), none of which are an oven setting "fan" does or doesn't apply to.

    Known gap, not a false pass: gordons-christmas-five-spice-roast-goose.md
    has a "Calculate the cooking time: 10 mins at 240°C, then reduce to
    190°C..." step that restates the same figures as the actual method step
    below it, without an oven word of its own -- this test won't catch that
    one, so check it by hand when you get to this recipe.
    """
    bad = []
    for step in recipe.method_steps:
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
