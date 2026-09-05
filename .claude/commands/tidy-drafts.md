---
description: Tidy the mechanical half of _food_drafts/ and _cocktail_drafts/ -- quoting, dashes, typography, accents, the #429 meta block -- and report everything that needs Helen instead.
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

## Both collections, since 2026-09-05

`python3 scripts/tidy_drafts.py` covers `_food_drafts/` **and**
`_cocktail_drafts/`, each recursively, so `to-promote/` is in. Helen asked for
the widening in those words: *"Widen please — cocktail drafts passing will save
me a lot of time."* `--site food` or `--site cocktails` does one alone; an
absent private repo is announced and skipped, and only BOTH absent is a refusal.

**The drinks boundary is much narrower than food's, because a drink's front
matter is mostly not prose.** What the pass does on a drink:

| | |
|---|---|
| **fixes** | an unquoted `title`/`tagline`/`source`/`source_url`/`to_serve`; `--` → em dash; `->` → →; `3-4` → `3–4`; accents from `_data/accented_words.yml` |
| **but only in** | `title`, `tagline`, `to_serve`, a `notes` entry's `label`/`text`, an ingredient's `note` — Helen's own writing and nothing else |

What it will **not** touch on a drink, and why each one is a decision rather
than an oversight:

- **A `QQ` line**, by the *suite's* predicate rather than the food one. On a
  drink the marker sits behind a key — `tagline: "QQ"`, `text: "QQ - ..."` — and
  the food pattern, which allows only a list dash and a quote in front of it,
  matches none of those. The script asks `conftest.checkable_text`.
- **`item`, `suggestion`, `source`, `source_url`** — somebody else's words
  (`test_cocktails.VERBATIM_KEYS`). The drinks suite blanks them before it
  looks, so it is not asking for them either.
- **`glass`, `garnish`, `mood`, `generic`, `character`** — closed vocabularies
  declared in `_data/cocktails/` and enforced against those declarations. An
  accent or a dash written into one is a change to the vocabulary, which is a
  question for `_data/`.
- **A `method` step** — `methods.yml` holds the canonical steps and a
  `proposals` mechanism for changing one. Editing a step in a drink file
  quietly de-canonicalises it.
- **An `amount`** — and this one is a *recorded harm*, not a principle.
  anitas-attitude-adjuster said `amount: "Top (30-45) ml"` with a `QQ` note
  quoting that string back verbatim; en-dashing the amount would have
  desynchronised the note from the value it describes. The drinks suite checks
  amounts and is right to — they render — so a range in one is **reported** in
  the second section and left for Helen.
- **A non-house spelling** (`demarara` → `demerara`) or a temperature missing
  its `°`. Reported, never auto-fixed, on either collection: a spelling is a
  word, not a character.

Food's own two rules stay food's: the `main_ingredients`/`tags` flow quoting and
the #429 `meta:` migration run on `_food_drafts/` and nowhere else. A drink's
`meta:` is five keys in its own order and nobody asked to migrate it.

`tests/test_tidy_drafts.py` is the proof, on a fixture drink under `tmp/` and
never on Helen's files: it asserts the whole output byte for byte, so "fixed the
six faults" cannot pass while something also happened to the other thirty lines.

## Procedure

1. **Report first, always.** `python3 scripts/tidy_drafts.py` writes nothing.
   Read the three sections it prints: what it would change, what it is reporting
   and never touching, and what it deliberately did not look at.

2. **Check whether the drafts repo is clean.** `_food_drafts/`
   (`helen-triages-food-private`) and `_cocktail_drafts/`
   (`helen-triages-cocktails-private`) are separate private repos with their own
   `main`, and the CLAUDE.md branch rules apply to each exactly as they do here.
   Helen edits drafts constantly, so expect uncommitted work and **do not stash,
   commit or discard it** — ask her. `--apply` refuses on either dirty tree.

   **If she is proofreading, do not run `--apply` over that collection at all.**
   `meta.proofread: true` means she has read what is in the file; a tidy pass
   afterwards is a change she has not read, and while she is mid-pass the file
   she is looking at may not be the file on disk. Report, hand her the list,
   wait.

3. **Branch in the drafts repo**, never commit to its `main`:

       cd _food_drafts && git checkout -b tidy/<what-this-pass-is>
       cd _cocktail_drafts && git checkout -b tidy/<what-this-pass-is>

4. **Apply**: `python3 scripts/tidy_drafts.py --apply`. It refuses on a dirty
   tree unless you pass `--allow-dirty`, and that refusal is deliberate: the
   whole safety story is that the diff afterwards shows exactly what the script
   did, and mixed in with Helen's own edits it does not.

   Use `--only quoting,meta,dashes,typography,accents` to do one class at a
   time if the full pass is too much to review in one go.

5. **Verify, and not by reading the diff.** Run the suite for the half you
   touched:

       pytest -m food
       pytest -m cocktails

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

- **Everything on a drink that is not Helen's own prose** — an `amount`, a
  method step, a vocabulary value, an `item` or a `suggestion`. The section
  above lists them with a reason each; the script's report names the ones the
  drinks suite will still fail on, so a decline never looks like a miss.
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

On the drinks side the equivalent question is **whose words is this?** The three
answers are Helen's (fix it), somebody else's (`VERBATIM_KEYS`, and a `QQ` line
anywhere), and `_data/cocktails/`'s (a closed vocabulary, or a canonical method
step — change the declaration, then the files, never one file). A rule that
cannot be sorted into one of those three is not a formatting rule.
`model_instructions/PUBLISHING_A_DRINK.md` step 2 remains the human pass over a
drink, and this script does not replace it.
