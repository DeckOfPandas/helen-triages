"""Draft-scoped structural and style checks.

`_food_drafts/` is deliberately unfinished: a blank tagline, an absent
`method:` and `QQ` anywhere are normal there and are not tested. What is
tested is the set of rules that are wrong at any stage of a recipe's life: a
key typo, a value the template cannot parse, an undeclared tag or star, a
formatting convention that carries no information.

Most tests delegate to the recipe-side rule. A recipe rule that does not run
on drafts is named in NOT_FOR_DRAFTS with its reason; do not port one without
asking. Run: `pytest -q tests/test_drafts.py`, with the `_food_drafts/` clone
present.
"""
from __future__ import annotations

import re
import sys

import pytest

import drafts_schema
from conftest import where_draft, is_qq, ALL_RECIPES, ALL_DRAFTS
import test_front_matter as _fm
import test_style as _st
import test_taxonomy as _tx
from test_front_matter import REQUIRED
from test_style import TYPOGRAPHY

# --- one rule, one definition --------------------------------------------------
# Most tests below are a two-line delegation to the recipe version of the same
# rule, so there is one implementation of each. `Recipe` is one class for both
# collections and `where()` reads the path from the file, so a draft passed to
# a recipe-side rule reports `_food_drafts/...` correctly.
# To add a rule to drafts, write the delegation. To decline one, put its name
# in NOT_FOR_DRAFTS with a reason. A rule that genuinely differs is declared in
# DIVERGENT_ON_PURPOSE.

# The rules that are genuinely different for a draft, and why. A name here is a
# claim that the recipe version would be WRONG applied to an unfinished file --
# not that nobody has got round to sharing it.
DIVERGENT_ON_PURPOSE = {
    "test_method_xor_method_groups":
        "a recipe must have exactly one; a draft may legitimately have NEITHER "
        "yet, so this asserts 'not both' rather than xor",
    "test_method_short_is_a_list":
        "`method_short:` is required on a recipe and optional on a draft, so "
        "this returns early when the key is absent",
    "test_metadata_time_format":
        "same rule, but a draft's value may be `QQ 30 minutes` rather than a "
        "bare `QQ`, and the recipe version is parametrised per field while this "
        "reports both fields in one message",
    "test_no_ampersand_in_title":
        "same rule; kept separate only because the draft corpus is where new "
        "brand names arrive, and its message points at ampersand_proper_nouns "
        "as the first thing to try rather than the last",
    "test_meta_block_complete":
        "#429 REACHED _food_drafts/ ON 2026-08-29 and this entry survived it, "
        "narrowed. Every draft is now on the three-flag contract; what is left "
        "is TWO files with no awaiting_fix at all "
        "(bbq-spatchcock-duck-grilled-plum-ketchup, duck-fesenjan). That flag "
        "fails closed, so writing `false` in asserts a recipe is fit to "
        "publish, which is Helen's call and not a migration's. Delete this "
        "entry and delegate once those two have a value. Until 2026-08-29 this "
        "said drafts carried cooked_before/date_last_edited -- all 341 did, "
        "and none does now",
}

pytestmark = pytest.mark.food


def test_the_food_drafts_clone_is_in_step():
    """This checkout's rules and `_food_drafts/`'s data agree (#624).

    The first test to read when a food run goes red with drafts in it;
    tests/drafts_schema.py explains the handshake. Food schema 1 is the
    baseline and required no migration.
    """
    if not drafts_schema.present("_food_drafts"):
        pytest.skip(
            "`_food_drafts/` is not on this machine, so there is no clone to "
            "be in step with. Clone it to check this -- MANUAL 9.1."
        )
    problem = drafts_schema.mismatch("_food_drafts")
    assert problem is None, problem


# --- rules that are not applied to drafts, and why ----------------------------
# Every per-recipe rule in the main suite is either delegated in this file or
# named here. `test_every_recipe_rule_is_adopted_or_declined` enforces that,
# so a new recipe rule cannot skip the draft corpus unnoticed.
NOT_FOR_DRAFTS = {
    # -- Needs Helen's judgement or her source material, per recipe: the
    # answer is not in the file.
    "test_butter_specifies_salted_or_unsalted": "content judgement; 92 drafts",
    "test_cardamom_specifies_type": "content judgement; 17 drafts",
    "test_chocolate_percentage_matches_type": "content judgement; 18 drafts",
    "test_chocolate_specifies_type": "content judgement; 14 drafts",
    "test_egg_size_is_stated": "content judgement; 103 drafts",
    "test_flour_specifies_type": "content judgement; 30 drafts",
    "test_garlic_specifies_form": "content judgement; 33 drafts",
    "test_ginger_specifies_fresh_ground_or_paste": "content judgement; 58 drafts",
    "test_homemade_pastry_has_salt": "content judgement; 4 drafts",
    "test_loomi_specifies_colour": "content judgement; 1 draft",
    "test_milk_specifies_type": "content judgement; 36 drafts -- the original "
                                "of this category, issue #167",
    "test_mixed_spice_and_five_spice_say_powder": "content judgement; 14 drafts",
    "test_mustard_specifies_type": "content judgement; 9 drafts",
    "test_nutmeg_cinnamon_cloves_vanilla_specify_type": "content judgement; 42 drafts",
    "test_soy_sauce_specifies_dark_or_light": "content judgement; 24 drafts",
    "test_soy_sauce_as_tamari_alternative_specifies_dark_or_light":
        "content judgement; 4 drafts",
    "test_sugar_specifies_type": "content judgement; 117 drafts",
    "test_unsalted_butter_has_salt_or_a_note": "content judgement; 19 drafts",
    "test_vinegar_specifies_type": "content judgement; 19 drafts",
    "test_oven_temperature_says_fan":
        "39 drafts, and NOT mechanically fixable -- which figure of a "
        "fan/conventional pair is the fan one needs the original source, and "
        "they are not always in the same order (MANUAL 5)",
    "test_no_estimated_timings":
        "an ingest writes `Estimated N mins` for an unprinted time (DECISIONS "
        "§4), so the pool is full of them on purpose; "
        "test_no_estimated_time_reaches_promotion holds them at 4-promote/",
    "test_ingredient_notes_are_lowercase_fragments":
        "9 drafts, and flag-only even for recipes -- Helen: 'I'll look at "
        "violations myself because I care about tone of voice'",
    "test_ingredient_group_order_matches_title": "6 drafts; flag-only for recipes too",
    "test_spice_order_within_group": "16 drafts; content judgement, MANUAL 10",
    "test_no_oven_conversions":
        "20 drafts, and it fires on exactly the un-rewritten QQ source text "
        "the marker exists to protect -- stripping a gas mark there is editing "
        "content, not formatting. The long-standing exclusion (#426 is the "
        "same argument applied per line rather than per test)",

    # -- Meaningless or wrong for an unfinished file.
    "test_no_qq_placeholder":
        "221 drafts, and correctly so: QQ is what a draft is for",
    "test_tagline_is_not_blank":
        "17 drafts. A blank tagline is normal here; only the KEY is required",
    "test_required_field_present":
        "the draft twin checks key presence only, deliberately, without the "
        "'and it must be written' half",
    "test_meta_block_is_exactly_the_three_flags_in_order":
        "5 drafts, down from 341 -- the #429 migration landed 2026-08-29 and "
        "this is no longer a TODO. Three legitimately carry claude_rewritten, "
        "which #418 allows on a draft and this rule forbids outright; two have "
        "no awaiting_fix, which is Helen's to set. Both remainders are real "
        "divergences now, not a backlog",
    "test_internal_temp_ref_resolves":
        "wiring a temperature is wasted work until Helen has cooked it "
        "(MANUAL 14); the test catches each draft on the day it is promoted",
    "test_doneness_names_a_real_level": "same reasoning as internal_temp_ref",
    "test_no_recipe_says_cooking_temperatures":
        "0 drafts; about a published page's own cross-link wording",
    "test_title_and_slug_dont_diverge":
        "19 drafts, and NOT a gap -- Helen's ruling, 2026-09-01: 'let's not run "
        "the title matches slug-ish test over drafts'. This entry said 'GAP; 20 "
        "drafts' until then, which had it exactly backwards. A DRAFT'S TITLE IS "
        "STILL THE SOURCE'S TITLE and the slug is already the dish: 'Cassie's "
        "Favourite Chocolate Fudge Cake' / chocolate-fudge-cake, 'Bronte's "
        "Swedish Meatballs' / swedish-meatballs, 'Malty NYC-style Choc Chunk "
        "Cookies' / choc-chunk-cookies. The divergence IS the ingest doing the "
        "right thing, and it closes itself at promotion when Helen writes the "
        "title she wants -- she strips a possessive unless the name is famous "
        "or family, so most of these titles are going to change anyway. The "
        "recipe-side rule is untouched and still fires where it means "
        "something: on a published page, where the title is hers",

    # -- Would apply cleanly: mechanical gaps, paid for at promotion instead.
    # (The first entry is not a gap; its reason says so.)
    "test_note_dicts_have_label_and_text":
        "divergent on purpose -- a bare-string note is correct in a draft "
        "(the recipe rule's own docstring says so); the narrower twin "
        "test_note_dicts_have_label_and_text_when_dict is what applies here",
    "test_size_word_is_with_the_count_not_the_item":
        "GAP; 108 drafts, scripted 2026-09-24 as `tidy_drafts.py --only size` "
        "(#577, option 1); what the script refuses -- an `or` remainder, "
        "`baby` -- needs an eye",
    "test_internal_recipe_links_resolve": "GAP, mechanical; 7 drafts",
    "test_main_ingredients_egg_count_agrees": "GAP; 3 drafts",

    # -- Clean across the drafts when listed, so twinning one is free.
    "test_accents_in_prose": "0 drafts failing -- but test_accents_in_drafts "
                             "already covers the corpus by another route",
    "test_chocolate_main_ingredients_has_no_percentage": "0 drafts failing",
    "test_ingredient_group_names_do_not_repeat_for_the": "0 drafts failing",
    "test_internal_link_text_matches_target_title": "0 drafts failing",
    "test_method_step_notes_are_sentences": "0 drafts failing",
    "test_pan_and_ingredient_sizes_use_digits":
        "0 drafts failing; test_pan_and_ingredient_sizes_use_digits_in_drafts "
        "already covers the corpus by another route",
    "test_same_page_fragment_links_land_somewhere":
        "0 drafts failing; reads ids from layouts a draft never renders through",
}


def test_every_recipe_rule_is_adopted_or_declined():
    """Every per-recipe rule either runs against drafts or says why it does not.

    A recipe rule with no draft twin is a cost paid at promotion. That may be
    right, but it must be a decision: NOT_FOR_DRAFTS records it, and a stale or
    doubly-listed name fails too.
    """
    import inspect
    import test_front_matter, test_style, test_taxonomy

    mine = {n for n, _ in inspect.getmembers(sys.modules[__name__],
                                             inspect.isfunction)
            if n.startswith("test_")}
    rules = {}
    for mod in (test_front_matter, test_style, test_taxonomy):
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            if getattr(fn, "__module__", "") != mod.__name__:
                continue
            if list(inspect.signature(fn).parameters)[:1] == ["recipe"]:
                rules[name] = mod.__name__

    assert rules, (
        "No per-recipe rules were found in the main suite at all. Either they "
        "moved, or this scan has stopped matching -- and an empty scan passes "
        "while checking nothing (MANUAL 12)."
    )

    undeclared = sorted(n for n in rules if n not in mine and n not in NOT_FOR_DRAFTS)
    assert not undeclared, (
        "Recipe rule(s) neither applied to drafts nor declined:\n  "
        + "\n  ".join(f"{n}  ({rules[n]})" for n in undeclared)
        + "\n\nAdd a two-line delegation above if it should hold for drafts "
          "too, or an entry in NOT_FOR_DRAFTS saying why it should not. "
          "Silence is the one option that is not available: a rule with no "
          "draft twin is a cost paid at promotion instead, and until this test "
          "existed nothing recorded whether that was on purpose."
    )

    stale = sorted(n for n in NOT_FOR_DRAFTS if n not in rules)
    assert not stale, (
        "NOT_FOR_DRAFTS names rule(s) that no longer exist:\n  "
        + "\n  ".join(stale)
        + "\n\nA declined rule that has been renamed or deleted leaves an "
          "entry that excuses nothing, and the next real gap hides behind it."
    )

    both = sorted(set(NOT_FOR_DRAFTS) & mine & set(rules))
    assert not both, (
        "Rule(s) both delegated above AND listed in NOT_FOR_DRAFTS: "
        + ", ".join(both) + ". Pick one."
    )


def test_a_draft_twin_delegates_unless_it_is_declared_divergent():
    """A draft test named after a recipe rule calls that rule, or is in
    DIVERGENT_ON_PURPOSE; and every DIVERGENT_ON_PURPOSE entry is such a twin
    that does not call it.
    """
    import inspect
    import test_front_matter, test_style, test_taxonomy

    here = sys.modules[__name__]
    rules = {}
    for alias, mod in (("_fm", test_front_matter), ("_st", test_style),
                       ("_tx", test_taxonomy)):
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("test_") and fn.__module__ == mod.__name__:
                rules[name] = alias
    twins = {n: fn for n, fn in inspect.getmembers(here, inspect.isfunction)
             if n in rules and fn.__module__ == __name__}
    assert twins, "No draft test shares a name with a recipe rule; the scan is broken."

    divergent = {n for n, fn in twins.items()
                 if f"{rules[n]}.{n}(" not in inspect.getsource(fn)}
    undeclared = sorted(divergent - set(DIVERGENT_ON_PURPOSE))
    stale = sorted(set(DIVERGENT_ON_PURPOSE) - divergent)
    assert not undeclared, (
        f"Draft test(s) share a recipe rule's name but do not call it: "
        f"{undeclared}. Delegate, or say why in DIVERGENT_ON_PURPOSE."
    )
    assert not stale, (
        f"DIVERGENT_ON_PURPOSE names {stale}, which no longer diverge (or no "
        f"longer exist). Delete the entry."
    )

# --- front matter shape (test_front_matter.py, structural half only) --------

@pytest.mark.parametrize("field", REQUIRED)
def test_required_field_key_present(draft, field):
    """Key presence only: a draft may leave the value blank or `QQ`. The "and
    it must be written" half (`test_tagline_is_not_blank`) is recipe-only.
    """
    assert field in draft.fm, (
        f"{where_draft(draft)} is missing the required field `{field}:`. "
        f"A draft can leave it blank/QQ, but the key itself should exist — "
        f"every other draft already has all of: {', '.join(REQUIRED)}."
    )


def test_front_matter_has_no_duplicate_keys(draft):
    _fm.test_front_matter_has_no_duplicate_keys(draft)


def test_no_retired_fields(draft):
    _fm.test_no_retired_fields(draft)


def test_scalar_fields_are_quoted(draft):
    _fm.test_scalar_fields_are_quoted(draft)


def test_main_ingredients_entries_are_quoted(draft):
    _tx.test_main_ingredients_entries_are_quoted(draft)


def test_tags_entries_are_quoted(draft):
    _tx.test_tags_entries_are_quoted(draft)


def test_number_ranges_use_en_dashes(draft):
    _st.test_number_ranges_use_en_dashes(draft)


def test_meta_fields_are_nested_not_top_level(draft):
    _fm.test_meta_fields_are_nested_not_top_level(draft)


def test_meta_block_complete(draft):
    """A draft's `meta:` is a mapping carrying `rewritten` and `proofread`.

    Narrower than the recipe version, which also requires `awaiting_fix`: that
    flag fails closed and is Helen's to set, so a draft may not have one yet.
    Declared in DIVERGENT_ON_PURPOSE.
    """
    meta = draft.fm.get("meta")
    assert isinstance(meta, dict), (
        f"{where_draft(draft)} has no `meta:` block, or it is not a mapping."
    )
    missing = [f for f in ("rewritten", "proofread") if f not in meta]
    assert not missing, f"{where_draft(draft)} `meta:` is missing {missing}."


def test_claude_rewritten_is_a_real_boolean(draft):
    _fm.test_claude_rewritten_is_a_real_boolean(draft)


def test_serves_xor_makes(draft):
    _fm.test_serves_xor_makes(draft)


def test_method_xor_method_groups(draft):
    """Unlike the recipe version, "neither present" is fine here — a draft
    can legitimately have ingredients transcribed and no method yet. Only
    "both present" (the second silently dropped by the template) is a bug.
    """
    has_flat = "method" in draft.fm
    has_groups = "method_groups" in draft.fm
    assert not (has_flat and has_groups), (
        f"{where_draft(draft)} has both `method:` and `method_groups:`. "
        f"They are mutually exclusive; the recipe layout renders one or the "
        f"other, and having both means the second is silently dropped."
    )


def test_method_groups_have_name_and_steps(draft):
    _fm.test_method_groups_have_name_and_steps(draft)


def test_method_produces_actual_steps(draft):
    _fm.test_method_produces_actual_steps(draft)


def test_notes_is_a_list(draft):
    _fm.test_notes_is_a_list(draft)


def test_notes_are_sentences(draft):
    """Draft notes are sentences too (#711). The rule and its exemptions are
    the recipe version's, in tests/test_style.py.
    """
    _st.test_notes_are_sentences(draft)


def test_note_dicts_have_label_and_text_when_dict(draft):
    """A draft note is a `{label, text}` mapping with both keys and no others;
    either value may be the empty string.

    A published note must say something; a draft note is a slot Helen has not
    filled, so an empty string is the placeholder, not a fault. A bare string
    is refused, and so is a key typo such as `note:` for `text:`, which
    renders blank with no error.
    """
    for i, note in enumerate(draft.fm.get("notes") or [], 1):
        assert isinstance(note, dict), (
            f"{where_draft(draft)} note {i} is a "
            f"{type(note).__name__}, not a `{{label, text}}` mapping -- "
            f"{note!r}. Every draft note carries both keys, empty if it is "
            f"still a placeholder, so that there is somewhere to type."
        )
        missing = sorted({"label", "text"} - set(note))
        assert not missing, (
            f"{where_draft(draft)} note {i} is missing "
            f"{' and '.join('`' + k + '`' for k in missing)} "
            f"(check for a key typo, e.g. `note:` instead of `text:`) -- "
            f"{note!r}."
        )
        extra = sorted(set(note) - {"label", "text"})
        assert not extra, (
            f"{where_draft(draft)} note {i} carries "
            f"{' and '.join('`' + k + '`' for k in extra)}, which nothing "
            f"renders -- {note!r}. A note is `label` and `text` and nothing "
            f"else; a third key is almost always a misspelling of one of them."
        )
        for key in ("label", "text"):
            assert isinstance(note[key], str), (
                f"{where_draft(draft)} note {i} has `{key}:` as a "
                f"{type(note[key]).__name__}, not a string -- {note[key]!r}."
            )


def test_a_draft_has_a_notes_slot_and_no_unlabelled_note(draft):
    """Every draft has a notes slot, and a note with text has a label (#1258).

    `notes: []` is not allowed on a draft: it carries at least the empty pair,
    which neither layout prints. Imported text is labelled `QQ`, so
    `test_no_qq_placeholder` holds the recipe back until Helen has read it.
    `scripts/tidy_drafts.py --only notes` writes both.
    """
    notes = draft.fm.get("notes")
    assert notes, (
        f"{where_draft(draft)} has `notes: {notes!r}`, so there is nowhere to "
        f"type a note without recalling the YAML shape. Write the empty pair "
        f'-- `- label: ""` / `text: ""` -- or run '
        f"`python3 scripts/tidy_drafts.py --only notes --apply`."
    )
    for i, note in enumerate(notes, 1):
        if not isinstance(note, dict):
            continue                    # the test above names this one
        assert not note.get("text") or note.get("label"), (
            f"{where_draft(draft)} note {i} has text and an empty label -- "
            f"{note!r}. Imported text Helen has not read is labelled `\"QQ\"` "
            f"so that it cannot publish unnoticed; "
            f"`python3 scripts/tidy_drafts.py --only notes --apply` writes it."
        )


def test_method_short_is_a_list(draft):
    ms = draft.fm.get("method_short")
    if ms is None:
        return
    assert isinstance(ms, list), (
        f"{where_draft(draft)} has `method_short:` as a "
        f"{type(ms).__name__}, not a list."
    )


def test_method_short_uses_current_placeholder(draft):
    _fm.test_method_short_uses_current_placeholder(draft)


def test_ingredient_groups_named_when_there_is_more_than_one(draft):
    _fm.test_ingredient_groups_named_when_there_is_more_than_one(draft)


def test_group_names_omit_leading_article(draft):
    _fm.test_group_names_omit_leading_article(draft)


# --- house style (test_style.py) ---------------------------------------------

@pytest.mark.parametrize("name,pattern,fix",
                         [(n, p, f) for n, p, f in TYPOGRAPHY if p])
def test_typography(draft, name, pattern, fix):
    _st.test_typography(draft, name, pattern, fix)


def test_no_ampersand_in_title(draft, taxonomy):
    """Same declared-exception shape as the recipe version: a title says
    "and" unless the phrase is in `ampersand_proper_nouns` in
    _data/food/taxonomy.yml. Whether to declare a brand name is Helen's call.
    """
    allowed = taxonomy.get("ampersand_proper_nouns") or []
    value = str(draft.fm.get("title", ""))
    if "&" in value:
        remainder = value
        for phrase in allowed:
            remainder = remainder.replace(phrase, "")
        assert "&" not in remainder, (
            f"{where_draft(draft)} `title: {value!r}` contains an "
            f"ampersand that isn't part of a declared proper noun. Titles "
            f"use the word 'and' -- if this is a real brand/proper name, "
            f"add the exact phrase to ampersand_proper_nouns in "
            f"_data/food/taxonomy.yml."
        )


def test_spellings(draft):
    _st.test_spellings(draft)


def test_temperatures_use_degree_c(draft):
    _st.test_temperatures_use_degree_c(draft)


def test_metadata_time_format(draft):
    """Same terse-forms rule as the recipe version, both fields in one
    message: `prep_time`/`cook_time` say `mins`/`hrs`, not "minutes"/"hours"
    (MANUAL §5). A `QQ` value is skipped.
    """
    problems = []
    for field in ("prep_time", "cook_time"):
        value = draft.fm.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        if is_qq(value) or value.strip() in ("None", "Until done"):
            continue
        bad_units = re.findall(r"(?<=[0-9])\s*(minutes?|hours?|h)\b", value)
        if bad_units:
            problems.append(f"{field}: {value!r} uses {sorted(set(bad_units))}")
    assert not problems, (
        f"{where_draft(draft)} uses spelled-out time units in metadata: "
        + "; ".join(problems)
        + ". Metadata fields use the terse forms `mins`/`hrs`."
    )


def test_no_estimated_time_reaches_promotion(draft):
    """A draft in `4-promote/` is copied live next, where an `Estimated` time
    fails `test_no_estimated_timings` and a red `main` stops every deploy
    (DECISIONS §4). Anywhere else in the pool an estimate is expected.
    """
    if "4-promote" not in draft.path.parts:
        return
    _st.test_no_estimated_timings(draft)


def test_prose_abbreviates_minutes_only(draft):
    _st.test_prose_abbreviates_minutes_only(draft)


# --- taxonomy and links (test_taxonomy.py) -----------------------------------

def test_tags_are_declared(draft, taxonomy):
    _tx.test_tags_are_declared(draft, taxonomy)


def test_star_ingredient_is_declared(draft, taxonomy):
    _tx.test_star_ingredient_is_declared(draft, taxonomy)


def test_co_tag_rules(draft, taxonomy):
    _tx.test_co_tag_rules(draft, taxonomy)


def test_no_cook_tag_implies_no_cook_time(draft):
    _tx.test_no_cook_tag_implies_no_cook_time(draft)


def test_no_claude_markers_left(draft):
    _tx.test_no_claude_markers_left(draft)


def test_incidental_not_in_main_ingredients(draft):
    _tx.test_incidental_not_in_main_ingredients(draft)


def test_tin_and_pan_fats_are_flagged_incidental(draft):
    _tx.test_tin_and_pan_fats_are_flagged_incidental(draft)


def test_no_real_line_carries_its_tin_and_pan_extra(draft):
    _tx.test_no_real_line_carries_its_tin_and_pan_extra(draft)


def test_deep_frying_oil_is_listed_without_an_amount(draft):
    _tx.test_deep_frying_oil_is_listed_without_an_amount(draft)


def test_internal_links_have_trailing_slash(draft):
    _tx.test_internal_links_have_trailing_slash(draft)


def test_internal_links_are_well_formed(draft):
    _tx.test_internal_links_are_well_formed(draft)


_ALL_SLUGS = {r.slug for r in ALL_RECIPES} | {d.slug for d in ALL_DRAFTS}
_LINK = re.compile(r"\]\(\.\./([a-z0-9-]+)/\)")


def test_internal_recipe_links_resolve_in_drafts(draft):
    """Checked against recipes and drafts combined, unlike the recipe version:
    a draft linking to another unpromoted draft is normal. A slug that
    resolves to nothing at all is a typo or a renamed file.
    """
    broken = [slug for slug in _LINK.findall(draft.raw) if slug not in _ALL_SLUGS]
    assert not broken, (
        f"{where_draft(draft)} links to recipe slug(s) {broken}, which "
        f"exist in neither _food_recipes/ nor _food_drafts/."
    )
