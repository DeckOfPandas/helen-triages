"""Draft-scoped structural and style checks.

`_food_drafts/` is deliberately unfinished, and most of the recipe suite
(test_front_matter.py, test_style.py, test_taxonomy.py) correctly leaves it
alone: a blank tagline, an absent `method:`, a bare-string note, `meta.
cooked_before: false`, and `QQ`/`PLACEHOLDER` anywhere are all completely
normal here (HANDOVER_v26.md §4/§9/§12) and none of that is tested.

What IS tested below is the narrower set of rules that are wrong at ANY
stage of a recipe's life, draft or published — a key typo, a value that
doesn't parse the way the template expects, a tag or star that doesn't
exist, a formatting convention (a degree sign, an em dash, a terse time
unit) that carries no information either way. These are structural/
formatting bugs, not unfinished content, so a draft has no more excuse for
them than a published recipe does. Every one of these was seeded from a
real bug found by hand in the drafts folder on 2026-08-11 — see the
individual docstrings for which file(s) caught it.

Two tests here were deliberately allowed to start red, the same "standing
checklist, not a guard that's expected to be green" shape
test_oven_temperature_says_fan (test_style.py) used: an undeclared retired
star_ingredient value and a leftover CLAUDE marker both needed Helen's own
judgement to resolve, not a mechanical fix. Both backlogs have since been
worked through and both tests are green — see their own docstrings below.
A checklist that has gone green has become a regression guard: a failure
in either one now is a real problem to investigate, not a known backlog to
wave past. Don't go near a future violation unprompted all the same — the
judgement call that made these unsuitable for a mechanical fix in the
first place is still real, it's just that there's currently nothing
outstanding to apply it to.

Deliberately NOT ported here, and why — don't add these without asking:

- The closed-list ingredient-qualification rules (salted/unsalted butter,
  dark/light soy sauce, chocolate percentage, etc., test_style.py) and
  test_spice_order_within_group (test_taxonomy.py) — real content-judgement
  work that a fresh ingest isn't expected to have done yet (38 spice-order
  violations across 14 files alone, checked by hand 2026-08-11), not a
  structural bug. This is exactly the tidy-up-to-promote work this file
  exists to reduce, not something a raw draft should already satisfy.
- test_ingredient_notes_are_lowercase_fragments, test_ingredient_group_order_matches_
  title (test_taxonomy.py) — both explicitly flag-only even for published
  recipes ("I'll look at violations myself", HANDOVER_v26.md §10), and the
  proper_nouns list they lean on was seeded from the recipe corpus, not the
  much larger draft one, so porting them risks a flood of false positives
  from ordinary draft-only proper nouns rather than real bugs.
- test_no_oven_conversions (test_taxonomy.py) — bans gas marks/conventional-
  oven restatements, which is correct for published house style but would
  fire on exactly the unrewritten `QQ`/`PLACEHOLDER` source text those
  markers exist to protect (checked by hand: 3 current drafts still carry a
  gas mark inside an un-rewritten step). Stripping it there would be editing
  content, not formatting — HANDOVER_v26.md §4's ingest paragraph is about
  rewriting the step, not scrubbing units out of the original source first.
"""
from __future__ import annotations

import re
import sys

import pytest

from conftest import where_draft, is_qq, ALL_RECIPES, ALL_DRAFTS
import test_front_matter as _fm
import test_style as _st
import test_taxonomy as _tx
from test_front_matter import REQUIRED
from test_style import TYPOGRAPHY

# =============================================================================
# ONE RULE, ONE DEFINITION. 2026-08-21.
# =============================================================================
# Most of what follows is a two-line DELEGATION to the published-recipe version
# of the same rule, not a second copy of it. That is the whole point of this
# file's current shape, and it is worth knowing before you edit anything in it.
#
# WHAT IT REPLACED. This file used to re-implement each rule against the `draft`
# fixture. Measured before the change: 28 test names existed in both this file
# and the main suite, and comparing their ASSERTION LOGIC with fixture names and
# message wording stripped out, 26 of the 28 were the identical rule re-typed.
# 620 lines to express two real differences.
#
# THE DUPLICATION WAS NOT THE DANGEROUS PART. Nothing marked WHICH two differed
# on purpose. A deliberate divergence and a re-typed copy looked exactly alike
# on the page, so editing the recipe version and not this one -- or the reverse
# -- was silent in both directions. The four genuine divergences are now
# declared in DIVERGENT_ON_PURPOSE below, with a reason each, and everything
# else delegates.
#
# WHY DELEGATION RATHER THAN A SHARED rules.py. Moving 24 implementations into a
# new module would have moved their constants, their docstrings and their
# module-local helpers with them, for no gain this design does not already
# get: there is exactly one implementation either way. Delegation also keeps
# every test ID byte-identical, which is what made the migration checkable --
# `pytest --collect-only` before and after produced the same 25,178 IDs.
#
# WHAT MAKES IT SAFE. `Recipe` is the same class for both collections, and
# `where()` derives its path from the file rather than assuming a directory
# (conftest, 2026-08-21), so a draft passed to a recipe-side rule reports
# `_food_drafts/...` correctly. The `QQ` exemption (#426) moved into conftest
# and into the shared rules, having been measured as a no-op on published
# recipes -- `test_no_qq_placeholder` forbids the marker there, so blanking QQ
# lines changes nothing for a recipe and everything for a draft.
#
# TO ADD A RULE TO DRAFTS: write the two-line delegation. To NOT add one, put
# its name in NOT_FOR_DRAFTS with a reason.
# =============================================================================

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

# Suite marker, so `pytest -m food` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.food


# =============================================================================
# RULES THAT ARE **NOT** APPLIED TO DRAFTS, AND WHY. 2026-08-21.
# =============================================================================
# Every per-recipe rule in the main suite is either delegated above or named
# here. `test_every_recipe_rule_is_adopted_or_declined` enforces that, so a new
# recipe rule cannot quietly skip the draft corpus the way fourteen of these
# did -- including four that failed on the four recipes Helen promoted on
# 2026-08-21, having sat unnoticed in the drafts folder for as long as the
# drafts had.
#
# THE NUMBER ON EACH LINE IS A MEASUREMENT, not an estimate: how many of the
# drafts fail that rule today, taken by running the real recipe-side function
# over the whole draft corpus. Re-measure before acting on any of them; the
# corpus changes daily.
#
# THE THREE CATEGORIES ARE A PROPOSAL FOR HELEN, not a settled ruling. The
# split that matters is whether clearing the backlog needs her judgement or
# only a text edit.
NOT_FOR_DRAFTS = {
    # -- Needs Helen's judgement or her source material, per recipe. These are
    # the ones that were never candidates for a bulk pass, for the same reason
    # test_milk_specifies_type never was: the answer is not in the file.
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
        "they are not always in the same order (HANDOVER 5)",
    "test_no_estimated_timings":
        "8 drafts. Helen's standing rule is that she replaces these by hand "
        "rather than have them converted, so flagging them in drafts would be "
        "asking her to do published-recipe work early",
    "test_ingredient_notes_are_lowercase_fragments":
        "9 drafts, and flag-only even for recipes -- Helen: 'I'll look at "
        "violations myself because I care about tone of voice'",
    "test_ingredient_group_order_matches_title": "6 drafts; flag-only for recipes too",
    "test_spice_order_within_group": "16 drafts; content judgement, HANDOVER 10",
    "test_no_oven_conversions":
        "20 drafts, and it fires on exactly the un-rewritten QQ source text "
        "the marker exists to protect -- stripping a gas mark there is editing "
        "content, not formatting. The long-standing exclusion (#426 is the "
        "same argument applied per line rather than per test)",

    # -- Meaningless or wrong for an unfinished file. A draft IS the thing
    # these rules describe the absence of.
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
        "(HANDOVER 14); the test catches each draft on the day it is promoted",
    "test_doneness_names_a_real_level": "same reasoning as internal_temp_ref",
    "test_no_recipe_says_cooking_temperatures":
        "0 drafts; about a published page's own cross-link wording",

    # -- WOULD APPLY CLEANLY. These are the real gaps: mechanical, no
    # judgement needed, and every one is a tax paid at promotion instead.
    # Phases 3 and 4 of the plan agreed 2026-08-21.
    # NOT A GAP -- this said "GAP, mechanical; 256 drafts" until 2026-08-29 and
    # was the one entry here pointing the wrong way. The rule's own docstring
    # says the opposite: "the bare-string form is still deliberately allowed in
    # _food_drafts/ (HANDOVER §4/§9), which this test never reads." A draft note
    # jotted without a label is correct, and `test_note_dicts_have_label_and_
    # text_when_dict` above is the twin that does apply -- it checks the shape
    # of a note that HAS gone dict, and leaves bare strings alone.
    #
    # The mislabelling mattered in one direction only, and it is the bad one:
    # anything working through this list looking for mechanical wins would have
    # set about inventing 256 labels for notes that are meant not to have them.
    # A registry recording whether a gap is DELIBERATE is worth nothing if an
    # entry can quietly say the opposite of the rule it names.
    "test_note_dicts_have_label_and_text":
        "divergent on purpose -- a bare-string note is correct in a draft "
        "(the recipe rule's own docstring says so); the narrower twin "
        "test_note_dicts_have_label_and_text_when_dict is what applies here",
    "test_size_word_is_with_the_count_not_the_item": "GAP; 108 drafts",
    "test_title_and_slug_dont_diverge": "GAP; 20 drafts, one call each",
    "test_internal_recipe_links_resolve": "GAP, mechanical; 7 drafts",
    "test_main_ingredients_egg_count_agrees": "GAP; 3 drafts",

    # -- Already clean across every draft. Twinning these is free and is the
    # obvious first move of Phase 4: zero backlog, immediate regression cover.
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

    THE GAP THIS CLOSES IS THE ONE NOBODY WAS LOOKING AT. The duplication in
    this file was visible; its mirror image was not. On 2026-08-21, 48 of the
    main suite's 76 per-recipe rules had no draft counterpart, and nothing
    anywhere recorded which of those were deliberate. Four of them failed on
    the four recipes Helen promoted that day -- unquoted main_ingredients,
    unquoted tags, a title/slug divergence -- every one of which had been
    sitting in the drafts folder for as long as the drafts had.

    A test with no draft twin is a rule whose cost is paid at promotion. That
    may be right; it must be a decision.
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
        "while checking nothing (HANDOVER 12)."
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

# --- front matter shape (test_front_matter.py, structural half only) --------

@pytest.mark.parametrize("field", REQUIRED)
def test_required_field_key_present(draft, field):
    """Key presence only — NOT test_tagline_is_not_blank's "and it must be
    written" half, which is deliberately recipe-only. Checked clean across
    every current draft 2026-08-11 after closing a real gap: 19 files were
    missing `tagline:` entirely (not even blank), which is a different,
    worse thing than an empty value — a missing key silently skips
    `recipe.prose`'s tagline entry rather than showing up as blank.
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


# =============================================================================
# ADOPTED 2026-08-29, THE MOMENT THE TIDY PASS TOOK THEM TO ZERO
# =============================================================================
# All four sat in NOT_FOR_DRAFTS as "GAP, mechanical" -- a real rule with a real
# backlog, whose cost was paid one file at a time at promotion. scripts/
# tidy_drafts.py cleared them across 341 drafts in one pass:
#
#     scalar quoting            295 -> 0
#     main_ingredients quoting  279 -> 0
#     tags quoting              248 -> 0
#     en dashes                  58 -> 0
#
# ADOPTING THEM IS THE POINT OF HAVING CLEARED THEM, and this file's own
# "already clean" section says so: zero backlog makes twinning free and buys
# immediate regression cover. Without it the next ingest re-grows the backlog
# quietly and the pass has to be run again for ever. With it, a draft that
# arrives unquoted fails on the day it arrives.

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
    """Drafts still carry the PRE-#429 meta contract, so this cannot delegate.

    `_fm.test_meta_block_complete` requires rewritten/awaiting_fix/proofread,
    which is the published contract as of 2026-08-21. Drafts have not been
    migrated: all 343 still carry `cooked_before` and `date_last_edited`, and
    two carry no `awaiting_fix` at all. Delegating today would fail those two
    for a rename Helen has not asked to be propagated yet.

    DELETE THIS AND DELEGATE the day #429 reaches `_food_drafts/`. It is the
    only entry in DIVERGENT_ON_PURPOSE that is temporary rather than a real
    statement about what a draft is, and it was found by the delegation
    migration itself rather than by anyone reading the two files side by side.
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


def test_note_dicts_have_label_and_text_when_dict(draft):
    """Deliberately looser than the recipe version: a bare string note is
    still allowed here (HANDOVER_v26.md §4) -- what's never fine is a note
    that LOOKS like the dict form but is missing a key, which renders blank
    or unlabelled with no error anywhere. Caught for real, 2026-08-11, in
    six *-rewrite.md files: a `note:` key typo instead of `text:` in two of
    them, and four bare strings sitting in a file whose sibling notes were
    already `{label, text}` (not itself a bug, but the typo was).
    """
    for i, note in enumerate(draft.fm.get("notes") or [], 1):
        if isinstance(note, str):
            continue
        assert isinstance(note, dict) and note.get("label") and note.get("text"), (
            f"{where_draft(draft)} note {i} is a dict but missing `label` "
            f"and/or `text` (check for a key typo, e.g. `note:` instead of "
            f"`text:`) -- {note!r}."
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


# =============================================================================
# UN-REWRITTEN `QQ` TEXT IS NOT CHECKED FOR HOUSE STYLE. Issue #426.
# =============================================================================
# Helen: "don't normalise oven temp, the dash, or 'minutes' -- ideally just skip
# the whole line for simple normalisation tasks", of a step like
#
#     - step: "QQ bake at 150C for 30-40 minutes"
#
# `QQ` is her marker for "not rewritten yet" (HANDOVER_v26.md §4/§12): the line
# is still the SOURCE's wording, sitting in the file waiting to be replaced
# wholesale. Correcting its degree sign or its dash is tidying text that is
# about to be deleted, and it does it by editing someone else's words -- which
# is the one thing the marker exists to stop.
#
# THE SAME ARGUMENT IS ALREADY IN THIS MODULE'S DOCSTRING, for
# test_no_oven_conversions, which was left out of this file entirely because it
# "would fire on exactly the unrewritten `QQ`/`PLACEHOLDER` source text those
# markers exist to protect". #426 is that judgement applied at the granularity
# it should always have had: per LINE, not per test. A test can then keep
# guarding every rewritten step in a file that still has un-rewritten ones,
# instead of being dropped wholesale or firing wholesale.
#
# THIS OVERTURNS ONE EARLIER DECISION, explicitly rather than quietly.
# test_temperatures_use_degree_c's docstring argued a degree sign is "pure
# formatting, no information lost either way -- safe to enforce even inside an
# un-rewritten `QQ`/`PLACEHOLDER` step". That is true about the character and
# wrong about the line: the edit is safe, the habit of editing there is not, and
# Helen has now ruled the other way. The 2026-08-11 bug it was seeded from --
# 14 drafts writing "180C" -- is still caught everywhere it matters.
#
# WHAT IT IS WORTH, measured on the drafts present 2026-08-21: 66 of the 67
# house-style violations in the whole drafts folder were inside QQ lines, and 29
# of the 30 failing files failed for no other reason. The one real failure was
# invisible underneath them.
#
# ONLY AT THE START OF THE VALUE, never anywhere in it. A rewritten step that
# happens to mention QQ mid-sentence is finished prose and gets checked like any
# other. The marker is a prefix, and treating it as a substring would let any
# line opt out of house style by mentioning it.
_QQ_LINE = re.compile(r"""^\s*             # indent
                          (?:-\s*)?        # optional list dash
                          (?:[a-z_]+:\s*)? # optional key, e.g. `step: `
                          (?:['"])?        # optional opening quote
                          QQ\b""", re.X)


def _is_qq(value) -> bool:
    """True if this scalar is un-rewritten source text."""
    return isinstance(value, str) and value.lstrip().startswith("QQ")


def _checkable_raw(draft) -> str:
    """`draft.raw` with every un-rewritten `QQ` line blanked.

    Blanked rather than dropped so line COUNT is preserved: these strings feed
    failure messages, and a report whose line numbers are off by however many
    QQ lines happened to precede it is worse than no line numbers at all.
    """
    return "\n".join("" if _QQ_LINE.match(line) else line
                     for line in draft.raw.split("\n"))


def _checkable_prose(draft) -> list[tuple[str, str]]:
    return [(loc, text) for loc, text in draft.prose if not _is_qq(text)]


# --- house style (test_style.py) ---------------------------------------------

@pytest.mark.parametrize("name,pattern,fix",
                         [(n, p, f) for n, p, f in TYPOGRAPHY if p])
def test_typography(draft, name, pattern, fix):
    _st.test_typography(draft, name, pattern, fix)


def test_no_ampersand_in_title(draft, taxonomy):
    """Same declared-exception shape as the recipe version -- see
    ampersand_proper_nouns in _data/food/taxonomy.yml. Currently red on
    two *-rewrite.md files (Ben & Jerry's Base No. 2/3) left for Helen: her
    call whether to spell it "and" (like Base No. 1) or declare the phrase.
    `short_name` used to be checked here too; retired 2026-08-12, GitHub
    issue #169.
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
    """Same terse-forms rule as the recipe version, both fields at once
    rather than parametrized -- caught for real, 2026-08-11: 7 drafts wrote
    e.g. "2 hours" or "15 minutes" in prep_time/cook_time, which want the
    terse "2 hrs"/"15 mins" metadata form (HANDOVER_v26.md §5).
    """
    problems = []
    for field in ("prep_time", "cook_time"):
        value = draft.fm.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        if _is_qq(value) or value.strip() in ("None", "Until done"):
            continue
        bad_units = re.findall(r"(?<=[0-9])\s*(minutes?|hours?|h)\b", value)
        if bad_units:
            problems.append(f"{field}: {value!r} uses {sorted(set(bad_units))}")
    assert not problems, (
        f"{where_draft(draft)} uses spelled-out time units in metadata: "
        + "; ".join(problems)
        + ". Metadata fields use the terse forms `mins`/`hrs`."
    )


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


def test_internal_links_have_trailing_slash(draft):
    _tx.test_internal_links_have_trailing_slash(draft)


def test_internal_links_are_well_formed(draft):
    _tx.test_internal_links_are_well_formed(draft)


_ALL_SLUGS = {r.slug for r in ALL_RECIPES} | {d.slug for d in ALL_DRAFTS}
_LINK = re.compile(r"\]\(\.\./([a-z0-9-]+)/\)")


def test_internal_recipe_links_resolve_in_drafts(draft):
    """Deliberately checked against recipes AND drafts combined, unlike the
    recipe version (which only checks ALL_RECIPES) -- a draft linking to
    another not-yet-promoted draft is completely normal (chicken-satay.md
    links to peanut-sauce.md, both drafts) and isn't a bug. What's still a
    bug either way is a slug that resolves to nothing at all -- a typo or a
    renamed file the link was never updated for.
    """
    broken = [slug for slug in _LINK.findall(draft.raw) if slug not in _ALL_SLUGS]
    assert not broken, (
        f"{where_draft(draft)} links to recipe slug(s) {broken}, which "
        f"exist in neither _food_recipes/ nor _food_drafts/."
    )
