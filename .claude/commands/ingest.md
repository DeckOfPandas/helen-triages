---
description: Ingest recipes or drinks from photos, screenshots or pasted text into _food_drafts/ or _cocktail_drafts/ -- transcribe, do everything the source answers, and hand Helen one list of everything it does not.
---

Helen has new material to ingest. `scripts/ingest_preflight.py` is the engine
for the reporting half; this file is the procedure around it.

**Read HANDOVER §4 (food schema and the ingest contract), §9.2.1 (ingesting
from photographs) and §9.3 (cocktail schema) before the first file.** This
command deliberately does not restate them -- two copies of a schema drift, and
the handover is the one the tests are written against.

**AND `model_instructions/PUBLISHING_A_DRINK.md` IF THE DRINK IS GOING ANYWHERE
NEAR `to-promote/`.** That file is the six steps a drink goes through, the word
"final" and what it promises, and the one-working-copy rule. This command gets a
drink INTO the drafts; that one gets it out.

## The boundary, in one line

> **IS THE ANSWER IN THE SOURCE, OR IN HELEN'S HEAD?**

In the source -- the fan figure, "large eggs", "unsalted butter", the citation
-- writing it down is READING, not judgement, and this is the only session that
will ever have the page open. Do it, unasked.

In her head -- her voice, her palate, whether she liked it -- leave it and write
`QQ`. **A silence in the source is never filled from general cooking
knowledge.** A wrong "whole milk" looks exactly as confident as a right one.

## THE `QQ` CONVENTIONS -- every shape, in one place

`QQ` is Helen's own marker. She searches for the two letters, so **the shape is
what makes it findable, and there are exactly these:**

| where | what to write |
|---|---|
| a `tagline` she has not written | `tagline: "QQ"` |
| a drink's `generic` / `suggestion` | `"QQ"`, always, both sites of the pour -- her standing ruling, not a size problem |
| a drink's `meta.ship` | `"QQ"` -- she has not drunk it |
| a food method step | the PAIR: `QQ original <verbatim>` then `QQ Claude <the rewrite>` |
| any note an ingest ADDS | `- label: "QQ"` / `text: "QQ - …"` -- **both fields set, both beginning `QQ`** |
| an amount with no unit in the source | the figure as it stands, plus a note whose text says `QQ - no unit in the source` |
| a citation nobody has established | `source: "QQ"` with `source_type: unknown` |
| a truncated step, a missing infusion, a frame that ended | a note saying where it stopped -- **never a reconstruction** |

**Never a bare string note from an ingest** (Helen, 2026-09-04: *"It's annoying
for me to remember how to type YAML every time"*). A note that ALREADY exists
keeps whatever shape it has.

**Three things a `QQ` is not.** It is not an error: do not flag it, fix it, or
convert it. It is not a prompt to answer from general knowledge -- that is the
one thing this whole file exists to prevent. And it is not permanent: **a QQ
that has been ANSWERED becomes a plain note recording the answer**, and only a
QQ that was wrong to ask gets deleted. Leaving a settled question in a `QQ` is
how the same thing gets asked a third time.

**House style stops at a `QQ` line and does NOT stop at a `QQ Claude` one.**
The first is somebody else's words awaiting a rewrite; the second is ours and
is held to house style like any other prose. Both `conftest._QQ_LINE` and
`tidy_drafts.py` encode that as `QQ\b(?!\s+Claude\b)` -- HANDOVER §5.

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

**Cocktails.** New ingests land in `_cocktail_drafts/` root — that is the pool,
and it is where nearly everything still is. There is now ONE staging folder,
and it is Helen's in exactly the way the food ones are:

    _cocktail_drafts/             the pool -- everything lives here
      to-promote/                 she has made it, amended it, and it ships;
                                  waiting on her proofread, then
                                  _cocktail_recipes/

**Never move a drink into `to-promote/` unless asked.** It records that she has
MADE the drink and decided it ships, which no flag says.

> ### `to-promote/` AND `_cocktail_recipes/` ARE THE PUBLISHED TENSE
>
> Two rules bite in those two places and nowhere else — Helen's rulings,
> 2026-09-04, reading Fish House Punch. Both are enforced
> (`test_a_staged_drink_writes_a_bottles_canonical_name`,
> `test_a_staged_drink_carries_no_transcription_field`), and both are things to
> FIX when a drink is moved rather than reasons to refuse the move.
>
> - **Every `suggestion` is a bottle's canonical name, never an alias.**
>   *"'ED3' isn't a bottle"* — it is a declared alias of `El Dorado 3 year old
>   rum`, so it resolves, and resolving is not the same as being written down.
>   Look each one up in `_data/cocktails/bottles.yml` and write the key.
>   **This does not change the rule for a DRAFT**, which is the opposite one and
>   stays: leave a drink as she spelled it and add the spelling as an alias
>   (HANDOVER §9.3.2). The alias map is what lets an ingest be fast; a finished
>   drink has had time to say the real name.
> - **No ingredient carries `item`.** *"This has 'item' everywhere too."* It is
>   the source's own wording, drafts-only since 2026-09-02 (§9.10), and nothing
>   renders it. **Read each one before deleting it:** if it says something
>   `generic`, `suggestion` and `amount` do not already say — "Strong cold black
>   breakfast tea" beside `black tea`, "pear, sliced" beside `pear` — that fact
>   moves to a `note:` on the same ingredient. If it merely restates the generic,
>   which is the usual case, delete the line.
>
> **A bottle named only in `item` is still not yours to declare.** Where the
> bottle is undeclared (Patrón Reposado), the fact goes in a `note:` and the
> `suggestion` field is left for Helen — TIER 3, unchanged.

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

## FIXING A DRAFT THE SUITE IS COMPLAINING ABOUT

Not an ingest, and the commonest job after one. The boundary is the same one
`PUBLISHING_A_DRINK.md` step 2 draws, and the two must not drift:

**MECHANICAL -- fix it, silently, and say what you fixed.** A spelling one of
the vocabularies already declares (a glass, a garnish, a generic, a canonical
method step, a bottle alias). A missing required key. A hyphen that should be an
en dash. A quoted boolean. A `meta:` block out of order. `mood:` disagreeing
with the derivation. A US unit. **The test names the value it wanted; the data
file holds the spelling.** Look it up -- never a guess that merely turns the
test green.

**NON-MECHANICAL -- list it, one line each, and let Helen rule.** Anything the
vocabularies do NOT already declare: a bottle nobody has declared, a generic
that would need coining, a glass the source did not name, a tagline, a
`meta.ship`. A `QQ` of any kind. An amount that looks wrong against a source.
**Bring them ONCE, grouped by decision** -- `ingest_preflight.py` exists to
build exactly that list.

The order to work in:

1. `python3 scripts/derive_cocktail_moods.py` -- dry, for a drink; `--write`
   only if it reports a difference.
2. `pytest` (never two sessions at once -- HANDOVER §1).
3. `/tidy-drafts` for the food side, if the quoting or typography needs it.
4. `python3 scripts/ingest_preflight.py` for a drink.
5. One list to Helen. Then commit.

**A red test is not always yours.** `cd _<site>_drafts && git fetch origin &&
git rev-list --count HEAD..origin/main` first: a non-zero answer means the
failure is probably work someone else has already done (HANDOVER §9.1).

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
- **THE 2026-09-04 SHAPE RULINGS, all Helen's, all in `methods.yml` and
  `ingredients.yml` -- look them up, do not retype them from here:**
  - **one big cube is `giant`**, never large/big/rock/block, and those steps
    name no glass either ("strain into a rocks glass over a big cube" is
    `Strain over a giant ice cube.`);
  - **never write an `Express …` step.** A garnish naming a citrus twist makes
    `_layouts/cocktail.html` append it, and `test_no_method_step_opens_with_express`
    refuses one that tries. Put the twist in `garnish:` and write nothing;
  - **a step may be a `{step, note}` pair** -- used sparingly, and the note is
    how Helen does the step, not part of the instruction;
  - **`half` and `whole` are UNITS**: a whole fruit is counted, never measured,
    so half a lime is `amount: "half"` and never a millilitre figure;
  - **a barspoon is `5 ml`**; an egg or a sugar cube is an INGREDIENT with
    `amount: "1"`, not a unit;
  - **every ingredient has an amount, and for some it is a verb** -- `to top`,
    `to rinse`, `1 small pinch`, each declared in `measures:` and each with its
    matching method step saying WHEN.
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

**ONE EXCEPTION TO `meta.rewritten`, AND ONLY ONE:** a drink Helen has MOVED
into `_cocktail_drafts/to-promote/`. The move is how she claims the words, so
the mechanical pass flips `rewritten: true` there -- her standing instruction,
2026-09-04, `PUBLISHING_A_DRINK.md` step 2. Not in the pool, not on food, and
never `proofread`, which stays hers everywhere.

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
- **Resolving a drink's `suggestion` and `generic`, Helen's rulings of
  2026-09-04** (HANDOVER §9.3.2 has the long form; `unresolved_suggestions`
  in bottles.yml is empty and must stay so):
  - a HOUSE is not a bottle: declare the product she owns by its name and
    retype the drink to it; a house is an alias only where it can mean one
    thing in the collection (Luxardo → Luxardo Maraschino);
  - a spirit type beside its own generic is not a suggestion; it goes;
  - a syrup's suggestion may name what it is made from (Acacia honey);
  - generics are named by what substitutes for what: never a `flavoured X`
    that spans non-substitutable members; `honey water` is one flat generic
    and bare `honey` is the raw thing you cook with; `lavender-forward
    bitters`, not `lavender bitters`; `bonded rye` and `rye` are distinct;
  - spelling: **in the POOL**, leave the drink as she wrote it and add the
    spelling as an alias -- never retype a pooled drink to a canonical bottle
    name. **In `to-promote/` and `_cocktail_recipes/` the rule inverts** and
    every `suggestion` is the canonical name; see the box above. The two are
    not in tension: an alias is a reading convenience, and a finished drink has
    had time to write the real name.
- **Every note an ingest ADDS is `{label, text}` with both fields set, each
  beginning `QQ`** — never a bare string. Helen, 2026-09-04: "It's annoying
  for me to remember how to type YAML every time." She searches for `QQ`,
  replaces the label with a real heading and the text with her words, and
  never has to recall the shape. Both sites, both standalone documents say
  the same. A note that already exists keeps whatever shape it has.
