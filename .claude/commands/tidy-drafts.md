---
description: Tidy the mechanical half of _food_drafts/ -- quoting, dashes, typography, accents, the #429 meta block -- and report everything that needs Helen instead.
---

Helen has asked for a drafts tidy-up. Run `scripts/tidy_drafts.py`, which is the
engine; this file is the procedure around it.

**Read `scripts/tidy_drafts.py`'s module docstring before the first run.** It
states what the script will not do and why, and that list is the load-bearing
half of this command.

## The boundary, in one line

The script fixes **formatting**. It never resolves a **judgement**. If a fix
would need Helen's source material, her palate or her voice, it is reported and
left alone — which milk, which flour, which mustard, whether an oven figure is
the fan one, whether a note's first word is a proper noun.

A title disagreeing with its filename is neither: it is **not a finding at all**
on a draft, and the script stopped reporting it on 2026-09-01. A draft's title
is still the source's title while the slug is already the dish, so
`chocolate-fudge-cake` titled "Cassie's Favourite Chocolate Fudge Cake" is the
ingest doing the right thing. The recipe-side test is untouched.

It never touches a `QQ` line. That is the source's own wording awaiting Helen's
rewrite, and correcting its dash or its degree sign is editing someone else's
words (HANDOVER §5, issue #426). Two thirds of the corpus-wide en-dash hits are
inside `QQ` text, so this is not a technicality.

## Procedure

1. **Report first, always.** `python3 scripts/tidy_drafts.py` writes nothing.
   Read the three sections it prints: what it would change, what it is reporting
   and never touching, and what it deliberately did not look at.

2. **Check whether the drafts repo is clean.** `_food_drafts/` is a separate
   private repo (`helen-triages-food-private`) with its own `main`, and the
   CLAUDE.md branch rules apply to it exactly as they do here. Helen edits
   drafts constantly, so expect uncommitted work and **do not stash, commit or
   discard it** — ask her.

3. **Branch in the drafts repo**, never commit to its `main`:

       cd _food_drafts && git checkout -b tidy/<what-this-pass-is>

4. **Apply**: `python3 scripts/tidy_drafts.py --apply`. It refuses on a dirty
   tree unless you pass `--allow-dirty`, and that refusal is deliberate: the
   whole safety story is that the diff afterwards shows exactly what the script
   did, and mixed in with Helen's own edits it does not.

   Use `--only quoting,meta,dashes,typography,accents` to do one class at a
   time if the full pass is too much to review in one go.

5. **Verify, and not by reading the diff.** Run the suite:

       pytest -m food

   A green run is the claim. If anything in `_food_drafts/` no longer parses,
   the front-matter tests fail loudly — which is how the one real bug in this
   script was found, and it had silently broken 341 of 342 files while the diff
   looked entirely plausible.

6. **Report to Helen**, in this order, before committing:
   - the count of mechanical changes, by class;
   - every **report-only** finding, individually — an instruction left in a
     file for Claude, or a `meta:` flag the script would not invent. These are
     hers to decide;
   - anything the script SKIPPED (it says so inline: a value containing a double
     quote, an unrecognised `meta:` key);
   - what is still red in `pytest` and why, so a judgement backlog is not
     mistaken for something the tidy pass missed.

7. **Commit in the drafts repo**, one commit per class if the pass was large.
   `Towards DeckOfPandas/helen-triages#N` — a bare `#N` resolves against the
   drafts repo's own empty tracker, and a cross-repo trailer from a private repo
   does not close or even cross-reference the public issue, so treat closing as
   a separate deliberate step.

8. **Push per `CLAUDE.md`, which changed on 2026-08-29 and this line did not.**
   Pushing `main` in the two PRIVATE drafts repos is fine and needs no ask —
   nothing there triggers a build, and a commit sitting unpushed on one disk is
   the real risk. Everything else is unchanged: `helen-triages` itself is never
   pushed without her explicit confirmation, and COMMITTING to `main` is still
   forbidden in every repo, hook-enforced.

## What this does not cover

- **Cocktail drafts.** Out of scope by decision, 2026-08-29: that schema was
  mid-migration (#544, #571, #573), so tidying it then was work done twice.
  **#571 and #573 have since landed and #544's mechanical half is spent**, so
  the stated reason has largely expired — but the exclusion has not been
  revisited with Helen and the script still only reads `_food_drafts/`. The
  drinks' equivalent pass is step 2 of `model_instructions/PUBLISHING_A_DRINK.md`,
  driven by the suite rather than by this script. Ask before widening.
- **Size words** (108 drafts, moving `large`/`medium` from `item:` to
  `amount:`). Considered and excluded — mechanical in shape, but it rewrites two
  fields per hit and the precedent records fixes that needed an eye.
- **A missing `meta.awaiting_fix`** (2 drafts). The flag fails closed, so
  writing `false` in asserts the recipe is fit to publish. That is Helen's to
  say, not a formatting fix.

## If you are tempted to widen it

`tests/test_drafts.py`'s `NOT_FOR_DRAFTS` is the registry of every recipe rule
not applied to drafts, with a measured count and a reason each. Read the reason
before deciding a rule is mechanical. One entry was mislabelled as a mechanical
gap until 2026-08-29 and would have had a tidy pass inventing 256 note labels
that are meant not to exist.
