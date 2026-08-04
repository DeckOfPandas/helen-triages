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
    (a tagline link target, a cook_time, an ingredient amount) — the same
    "drafting aid, not a published value" logic as `test_no_estimated_timings`
    above, generalised to the marker Helen actually uses for "not yet".
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


def test_flour_and_sugar_specify_type(recipe):
    """GitHub issue #79: bare "flour" or "sugar" as an ingredient name, with
    no type in front of it (plain, self-raising, caster, icing...), leaves
    the cook guessing. Only checks the ingredient's own name, not method
    text -- "add the flour" there correctly refers back to an already-typed
    ingredient.
    """
    bad = [i for i in recipe.ingredient_items if re.match(r"^(flour|sugar)\b", i.strip(), re.I)]
    assert not bad, (
        f"{where(recipe)} has ingredient(s) {bad!r} with no type specified. "
        f"Say which flour or sugar, e.g. `plain flour`, `caster sugar`."
    )


# Helen: "light brown muscovado sugar" and "dark brown muscovado sugar" are
# both permitted alongside the default "soft brown sugar" -- muscovado is a
# real, distinct product, not just a wordier way of saying the same thing.
# Allowed as the ingredient's own name, optionally after a leading quantity
# ("~2 tbsp dark brown muscovado sugar") that isn't in a proper `amount:`
# field -- that's a separate, unrelated data-placement question.
_BROWN_SUGAR_OK = re.compile(
    r"(?:^|\d[\d./½¼¾⅓⅔]*\s*(?:tbsp|tsp|g|kg|ml|l|oz|lb)?\s+)"
    r"(soft brown sugar|light brown muscovado sugar|dark brown muscovado sugar)$",
    re.I,
)


def test_brown_sugar_is_soft_brown_sugar(recipe):
    """GitHub issue #79: "light brown sugar", "light soft brown sugar"...
    everything except the three names in _BROWN_SUGAR_OK is non-standard.
    Checks the ingredient's own name (up to the first comma/parenthesis),
    not just that an allowed phrase appears somewhere in it -- "light soft
    brown sugar" contains "soft brown sugar" as a substring but is still a
    different, non-standard name.
    """
    bad = []
    for item in recipe.ingredient_items:
        name = re.split(r"[,(]", item)[0].strip()
        if re.search(r"\bbrown\b", name, re.I) and re.search(r"\bsugar\b", name, re.I):
            if not _BROWN_SUGAR_OK.search(name):
                bad.append(item)
    assert not bad, (
        f"{where(recipe)} has non-standard brown sugar name(s) {bad!r}. "
        f"Allowed: soft brown sugar, light brown muscovado sugar, dark "
        f"brown muscovado sugar."
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


def test_accents_in_prose(recipe):
    """Culinary words that take an accent should have one.

    Checked against the curated list in _data/accented_words.yml rather than by
    detection, because no detector can tell a missing accent from a word that
    never had one.

    Scope is prose only — never slugs or filenames, which must stay ASCII, and
    never `source:`, where a citation is reproduced as the publication spells it.
    """
    words = _accented_words()
    if not words:
        return
    problems = []
    for location, text in recipe.prose:
        for plain, accented in words.items():
            if re.search(rf"\b{re.escape(plain)}\b", text, re.I):
                problems.append(f"{location}: '{plain}' should be '{accented}'")
    assert not problems, (
        f"{where(recipe)} uses unaccented spelling(s):\n  " + "\n  ".join(problems)
        + "\n\nIf the word genuinely takes no accent in British usage, add it to "
          "the `no_accent` list in _data/accented_words.yml so nobody 'fixes' it "
          "back."
    )
