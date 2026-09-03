---
description: Ingest recipes or drinks from photos, screenshots or pasted text into _food_drafts/ or _cocktail_drafts/ -- transcribe, do everything the source answers, and hand Helen one list of everything it does not.
---

Helen has new material to ingest. `scripts/ingest_preflight.py` is the engine
for the reporting half; this file is the procedure around it.

**Read HANDOVER §4 (food schema and the ingest contract), §9.2.1 (ingesting
from photographs) and §9.3 (cocktail schema) before the first file.** This
command deliberately does not restate them -- two copies of a schema drift, and
the handover is the one the tests are written against.

## The boundary, in one line

> **IS THE ANSWER IN THE SOURCE, OR IN HELEN'S HEAD?**

In the source -- the fan figure, "large eggs", "unsalted butter", the citation
-- writing it down is READING, not judgement, and this is the only session that
will ever have the page open. Do it, unasked.

In her head -- her voice, her palate, whether she liked it -- leave it and write
`QQ`. **A silence in the source is never filled from general cooking
knowledge.** A wrong "whole milk" looks exactly as confident as a right one.

---

## Where a new file goes

**Food.** New ingests land in `_food_drafts/` root. That is the pool. The
staging folders are HELEN'S, and she moves files through them herself:

    _food_drafts/                 the pool -- everything lives here
      to-rewrite/                 she has picked these to work on next
      to-cook/                    she has rewritten them enough to cook from
      to-promote/                 cooked, amended, ready for a Claude proofread
                                  then her proofread, then _food_recipes/

**Never move a file between these folders unless asked.** They record where SHE
is with a recipe, which no flag can say -- all four files in `to-cook/` today
are `rewritten: false`, because "readable enough to cook from" sits below "the
prose is mine". The folders and the flags answer different questions and are not
expected to agree.

**Cocktails.** `_cocktail_drafts/` is flat, and nothing has ever been promoted
to `_cocktail_recipes/`. There is no staging.

---

## A FILE THAT ARRIVES FROM A REPO-LESS SESSION

**Helen finds things away from her desk.** She pastes
`model_instructions/INGEST_ONE_RECIPE.md` or `INGEST_ONE_COCKTAIL.md` into
claude.ai along with the recipe, and gets back a draft file plus a short "what
I could not know" list. **That file is 90% of an ingest and is missing exactly
the parts that need this repository.** Finishing it is a different job from a
photo batch and it is much smaller.

**WHICH PROCEDURE, AND IT DEPENDS ON HOW IT ARRIVED.** If she pasted it into
the chat, **this is still the procedure** — read on. If she put it in an
`ingest` issue on the private drafts repo, **run `/ingest-inbox` instead**:
`scripts/ingest_inbox.py` parses the envelope, checks the fingerprint against
every existing draft and writes the file, and then hands back to the same
finishing pass below. The two paths differ only in who copies the code block.

**Ask her for the hand-back list.** It names every `QQ` and every guess, and it
is faster to read than the file. If she has lost it, the `QQ` notes inside the
file say the same things.

**THE FINISHING PASS, in order:**

1. **Save the file** into `_food_drafts/` or `_cocktail_drafts/` root. Branch
   the drafts repo first -- never commit to its `main`.
2. **COCKTAILS ONLY: `python3 scripts/derive_cocktail_moods.py --write`.** The
   file arrives with `mood: []` because the derivation needs `taxonomy.yml`,
   which that session did not have. **Without this the suite fails**, on
   `test_every_drinks_moods_match_the_derivation`, and it is the expected
   failure rather than a fault in the file. Run it dry first if you want to see
   what it will add.
3. **Run `pytest`.** Everything mechanical shows up here -- quoting, dashes,
   accents, an undeclared tag, a missing glass.
4. **`/tidy-drafts`** for the food side if the quoting or typography needs it.
   It never touches a `QQ` line, so the transcription is safe.
5. **Work the hand-back list, and treat every item as a TIER 3 question.**
   These are the things that session could not know, which is nearly always
   because the answer is in Helen's head rather than in the source. A missing
   glass, a `generic`, a `tagline`: ask, do not fill in.
6. **Run `python3 scripts/ingest_preflight.py`** for a drink, which reports the
   undeclared bottles and near-miss garnishes in the same shape as a photo
   batch.

**WHAT NOT TO DO TO IT.** Do not rewrite its prose, do not re-derive its
`main_ingredients`, and do not "improve" a `QQ Claude` line -- a rewrite pass
has already happened and redoing it burns Helen's review twice. Do not fill in
a `generic` or a `suggestion`: those are `QQ` by her standing ruling until she
makes the drink, and that is not relaxed by the file arriving from elsewhere.

---

## TIER 1 -- do it at ingest, unasked, both sites

- **Every qualifier the source states.** Sugar, butter, flour, milk, eggs,
  garlic, ginger, chocolate, mustard, vinegar. Source silent → `QQ`, never a
  default.
- **The fan oven temperature**, from the printed pair. Check WHICH is the fan
  figure; they are not always in the same order.
- **Quantities in their own `amount:` key**, never inside `item:` text. The
  highlighter reads `item.amount` and never scans text, so a quantity in the
  wrong field renders unstyled with no error anywhere.
- **Size words with the count** -- `amount: "2 large"`, not `item: "large
  onions"`.
- **Split `ingredient_groups` and `method_groups`** -- once, here, and never
  again afterwards. Phases are usually obvious from the source and re-reading
  the recipe later to find them is the expensive way.
- **House style** -- en dashes, `°C`, unicode fractions, quoting, accents.
  Outside `QQ` lines, always.
- **The citation**, per `model_instructions/SOURCE_ATTRIBUTION_SPEC.md`. For
  food that is `source` + `source_type`; a dated magazine is a `publication`, an
  undated one is a `website`, and that distinction catches everyone out. For
  cocktails `source` is free text and empty is fine.
- **Name the file from the whole title**, lowercased and hyphenated, so slug
  and title cannot diverge. (Head clause only until 2026-09-03; Helen: "Slug
  the whole title.") Existing files are not renamed.

### Food only

- **EVERY METHOD STEP IS A PAIR.** Helen's default since 2026-09-01, and it was
  a per-batch ask before that, which is exactly why it got missed:

      method:
        - "QQ original Heat the oven to 180C fan and grease a 20cm tin."
        - "QQ Claude Heat the oven to 180°C fan and grease a 20cm tin."

  `QQ original` is **verbatim** -- the source's own punctuation, its "minutes",
  its degree-sign habits. Never tidy or house-style one; it will read as broken
  house style and that is the point. `QQ Claude` is the paraphrase and IS held
  to house style like any other prose.

  She keeps both so she can judge the rewrite rather than trust it blind.

  **Building the file one step-pair at a time avoids an output-filter refusal.**
  A single large write containing a whole method's worth of verbatim book prose
  has triggered one; incremental edits have not.

### Cocktails only

- **MILLILITRES. NEVER A US UNIT.** Helen, 2026-09-01: *"I don't want any US
  units, just ml."* 1 oz = 30 ml, 1 tsp = 5 ml, from `measures:` in
  `ingredients.yml`. Transcribe the DRINK, not the page's units.
  `test_no_amount_uses_a_us_unit` enforces it. **Convert method prose too** --
  three punch steps kept their ounces through a conversion that fixed every
  `amount:` in the collection.
- **A qualified measure keeps its figure and loses its adjective to a note.** A
  scant or heaping ounce is `30 ml` plus `note: "the source asks for a heaping
  measure"`. HANDOVER §9.4.1 -- the site states one figure and does not hedge it.
- **Method steps use the canonical forms in `_data/cocktails/methods.yml`** where
  one exists. Cocktails have no `QQ PLACEHOLDER` convention: the mechanical spine
  is a closed vocabulary and the tail is free text.
- **`method` / `to_serve` / `garnish`** -- an ACTION in sequence, a NOUN PHRASE
  about how it reaches the table, and a THING on the drink. The test: *can you
  write it as a bare noun and lose nothing?* "with a straw" → `Straw.` loses
  nothing. "Top with crushed ice to serve" loses WHEN, so it is a method step.
- **Run `python3 scripts/derive_cocktail_moods.py --write`** after writing the
  files. It supplies the nine derived moods; **the ten hand-assigned ones are
  Helen's and no rule produces them**, so a new drink is missing half the browse
  axes until she looks.

## TIER 2 -- fill in, and say plainly they are proposals

`main_ingredients`, `tags`, `star_ingredient`, cocktail `mood`. Cheap for her to
correct and expensive to originate. Nothing can be invented -- an undeclared tag
or star fails the suite. **Be generous with `main_ingredients`**: the cap of
eight is a guide that has been read as a budget, and her own recipes run to
fourteen.

## TIER 3 -- never, at ingest or after

Rewriting a method step into her voice. `incidental:`. The case-by-case tags
(`freezable`, `virtuous`, `one-handed food`). Inventing a time or temperature --
`Estimated N mins` is banned outright. `meta.rewritten`, `meta.proofread`,
`meta.ship`. **Reconstructing a truncated step**, even when every sibling recipe
on the page ends the same way. **Declaring a bottle in `bottles.yml`** from the
ingredient beside it.

---

## Procedure

1. **Fetch the drafts repo before anything you will act on.**

       cd _cocktail_drafts && git fetch origin && git rev-list --count HEAD..origin/main

   A non-zero answer means the next red test is probably not yours. This fires
   once per MERGE, not once per session.

2. **Branch in the drafts repo**, never commit to its `main`:

       git checkout -b content/<what-this-batch-is>

3. **Open every photo.** Resolve each recipe by looking at its own file -- never
   from a prior pass's count, a filename, or an assumption that a folder is one
   book. Batches routinely hold pages from several sources, and edge-of-frame
   captures Helen did not mean to include.

4. **Check whether it already exists**, and compare the FORMULA, not the title.
   A drink already in the collection may share a name and be a different drink.

5. **Transcribe.** Tier 1 unasked, tier 2 as proposals, tier 3 never. Say in the
   file where the frame ended if a capture stops mid-recipe -- a screenshot that
   ends mid-list looks exactly like a complete one.

6. **Run the pre-flight**, which is the whole point of doing this in a batch:

       python3 scripts/ingest_preflight.py

   With no arguments it reads what this branch changed. It never writes.

7. **Bring Helen the report ONCE.** Not a gap at a time -- that is the failure
   this script exists to fix. Group her decisions and ask them together.

8. **Run both suites**, and simulate CI if a public test was touched:

       pytest -q
       node --test tests/js/*.test.js

9. **Commit in the drafts repo**, tagging any issue the batch resolves, and push
   with her confirmation. Report what is still `QQ` and why.

---

## Traps

- **A capture that ends mid-recipe looks exactly like a complete one.** Count
  every ingredient the method names; that proves nothing is missing that is
  USED, not that nothing follows. Say so in a note and ask.
- **The source is the best audit the collection ever gets.** Transcribing a page
  beside a drink already derived from it has found a missing citation, a wrong
  ice instruction and an amount out by a factor of 24. **Record all of it and
  change none of it** -- the site is canon, her figures stand, the source is
  noted beside them.
- **Then stop tracking it once she has ruled.** A settled question left in a
  `QQ` is an invitation to raise it a third time. A QQ that has been ANSWERED
  becomes a plain note recording the answer; only a QQ that was wrong to ask
  gets deleted.
- **Never house-style a verbatim block.** A `QQ original` line, a quoted
  alternative recipe in a note, or Helen's own note describing an experiment.
  Two files kept their ounces through the 2026-09-01 conversion for exactly
  this reason.
- **`QQ` is never an error.** Do not flag it, fix it, or convert it.
