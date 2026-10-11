---
description: Ingest recipes from photos, screenshots or pasted text into _food_drafts/ or _cocktail_drafts/ -- transcribe, do everything the source answers, and hand Helen one list of everything it does not.
---

Helen has new material to ingest. `scripts/ingest_preflight.py` is the engine
for the reporting half; this file is the procedure around it.

**Read MANUAL §4 (food schema and the ingest contract), §9.2.1 (ingesting
from photographs) and §9.3 (cocktail schema) before the first file.** This
command does not restate them: the manual is the copy the tests are written
against.

This command gets a recipe into the drafts. Getting a cocktail out of them, from
`4-promote/` to the live site, is `model_instructions/PUBLISHING_A_COCKTAIL.md`;
read it before touching anything in `4-promote/`.

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
| a COCKTAIL's `tagline` | `tagline: "QQ"`, bare, and **nothing drafted** -- Helen: *"Let's stop Claude drafting taglines. It turns out me doing them in batches works the best."* Her own line, if she gives one for that drink, goes in as she gave it with no `QQ`. Her reason: *"a drink without a tagline written by me gets a QQ, so I protect my voice in the public content"* |
| a FOOD `tagline` | where the source has an intro, the PAIR on one line: `"QQ original <the intro, verbatim> QQ Claude <a plain rewrite of it>"` -- Helen: *"QQ original yes, then QQ claude rewrite, then I'll do my own and delete the other two."* Where it has none, `"QQ"` alone. Never a line of the ingest's own |
| butter the source does not specify | `item: "QQ butter"` -- Helen: *"Write QQ butter in the ingredients list where it isn't specified."* Never "salted" by default and never plain "butter" |
| a `generic` the vocabulary does not settle outright | `generic: "QQ <the source's words>"` -- see the block below |
| a `suggestion` | `suggestion: []` unless a DECLARED bottle names it; the bottle the source names goes in that ingredient's `note` as `"Originally <bottle>."` |
| a cocktail's `meta.ship` | `"who knows"`, never `"QQ"` -- `QQ` is not a ship value (`test_meta_ship_is_a_rung_or_who_knows`); `meta.made_before: false` beside it says she has not made it |
| a food method step | the PAIR: `QQ original <verbatim>` then `QQ Claude <the rewrite>` |
| any note an ingest ADDS | `- label: "QQ"` / `text: "QQ - …"` -- **both fields set, both beginning `QQ`**. A note with no label is titled "note" on the page and looks finished, so this is what stops an unread note publishing unnoticed |
| an amount with no unit in the source | the figure as it stands, plus a note whose text says `QQ - no unit in the source` |
| a citation nobody has established | `source: "QQ"` with `source_type: unknown` |
| a truncated step, a missing infusion, a frame that ended | a note saying where it stopped -- **never a reconstruction** |

**A note is always a `{label, text}` pair, never a bare string**, on both sites
(Helen: *"It's annoying for me to remember how to type YAML every time"*;
`test_note_dicts_have_label_and_text_when_dict` refuses a bare one). She
searches for `QQ`, replaces the label with a real heading and the text with her
words, and never has to recall the shape. **A draft with no notes carries one
empty pair** — `label: ""` with `text: ""` — never `notes: []`; neither layout
prints it, and it gives her somewhere to type. Text with an empty label is not a
shape either: imported text is labelled `"QQ"`. `scripts/ingest_inbox.py` writes
the empty pair itself when an envelope says `notes: []`, and `python3
scripts/tidy_drafts.py --only notes --apply` writes both for a file that arrived
any other way.

**A cocktail's `generic` is typed where the vocabulary settles it, and is `QQ`
plus the source's words where it does not.** Helen: *"if it's not obvious write
QQ then whatever the source said then I have a chance of being able to fix it
myself."* Three tiers, and the boundary between the second and third is the one
that matters:

1. **A bottle `bottles.yml` declares** -- the dictionary's own generic, plus `suggestion`, mechanically. Look it up in the file with a script; never from recall. A bottle it does NOT declare is not yours to declare (TIER 3): its name goes in the ingredient's `note`, and `suggestion` stays `[]`.
2. **Source words that name a declared generic exactly** -- `lime juice`, `vodka`, `orgeat`. A near-match is not exact: `agave nectar` beside `agave syrup` is a judgement call, so type it AND put a `QQ` note on the cocktail saying what you assumed, so that review cannot be skipped.
3. **Everything else** -- `generic: "QQ aged Jamaican rum"`: `QQ`, a space, then the source's own words. **The words go IN `generic` because that is the only field the page, the cards and the search read**; a bare `QQ` leaves her looking at "90 ml QQ" with nothing to fix it from. Never a guess from general knowledge, and never a bare `QQ` where the source gave you words.

`python3 scripts/resolve_pours.py` does tiers 1 and 2 and refuses tier 3; run it
before typing any generic by hand (the finishing pass, below). A repo-less web
chat follows the same tiers: `INGEST_ONE_COCKTAIL.md` §3a prints every declared
generic, so tier 2 is a lookup it can do, and tier 1 is the only one out of its
reach.

**A typed generic is checked for a price and a strength, and a `QQ` one is
not** -- so typing can turn the suite red on `costs.yml` and `abv.yml`. Do NOT
invent those numbers: a placeholder row at `confidence: low`, with a `basis`
that says it is a placeholder and not shop-checked, and (for a strength) a `qq:`
saying what Helen has to check, is the sanctioned shape, and it goes on her
list. A NEW generic (`ginger beer`, `coconut rhum`) is hers to say: ask, and
register it in `ingredients.yml` -- **its list, `shelf_of`, and a cost row** --
once she has. A generic with no `shelf_of` entry falls to the end of her
shopping list in an unlabelled group, which nothing reports.

**Three things a `QQ` is not.** It is not an error: do not flag it, fix it, or
convert it. It is not a prompt to answer from general knowledge -- that is the
one thing this whole file exists to prevent. And it is not permanent: **a QQ
that has been ANSWERED becomes a plain note recording the answer**, and only a
QQ that was wrong to ask gets deleted. Leaving a settled question in a `QQ` is
how the same thing gets asked a third time.

**House style stops at a `QQ` line and does NOT stop at a `QQ Claude` one.**
The first is somebody else's words awaiting a rewrite; the second is ours and
is held to house style like any other prose. Both `conftest._QQ_LINE` and
`tidy_drafts.py` encode that as `QQ\b(?!\s+Claude\b)` -- MANUAL §5.

---

## Where a new file goes

`model_instructions/PIPELINE.md` §3 owns the folders and what each means. What
an ingest needs from it:

- **A new ingest lands in the ROOT** of `_food_drafts/` or `_cocktail_drafts/`
  -- the pool.
- **The numbered folders are Helen's.** They record where she is with a file,
  which no flag can say. Move a file between them only on her word, and her
  word is one of `rewrite`, `make`, `keep`, `ready` or `bin` followed by the
  slug. Never on your own reading of the file: a file in `2-make/` may say
  `rewritten: false`, because the folders and the flags answer different
  questions.
- **`5-final-proofread/` (cocktails) is the one folder an agent puts a file
  in, because the move is the report.** A cocktail goes there when the
  mechanical pass is done and something still needs a ruling only she can give,
  in the same commit as the list of what it is waiting for. `4-promote/` means
  *waiting on Claude*; this means *waiting on Helen*. `ready ‹slug›` is the way
  back out once she has ruled.

> ### `4-promote/`, `5-final-proofread/` AND `_cocktail_recipes/` ARE THE PUBLISHED TENSE
>
> Two rules bite in those three places and nowhere else (the two folders are
> `STAGED_DIRS` in `tests/test_cocktails.py`). Both are things to FIX when a
> cocktail is moved rather than reasons to refuse the move.
>
> - **Every `suggestion` is a bottle's canonical name, never an alias**
>   (`test_a_staged_drink_writes_a_bottles_canonical_name`). Helen: *"'ED3'
>   isn't a bottle"* — it is a declared alias of `El Dorado 3 year old rum`, so
>   it resolves, and resolving is not the same as being written down. Look each
>   one up in `_data/cocktails/bottles.yml` and write the key. **A draft in the
>   pool follows the opposite rule**: leave the cocktail as she spelled it and
>   add the spelling as an alias (MANUAL §9.3.2). The alias map is what lets an
>   ingest be fast; a finished cocktail has had time to say the real name.
> - **No ingredient still says `QQ`.** A staged cocktail is one Helen is about
>   to publish, and a `QQ` anywhere in `_cocktail_recipes/` fails
>   `test_no_published_drink_carries_a_qq`. Staging is where they get answered,
>   because the source is still in front of her.
>
> **A bottle the repo does not declare is still not yours to declare.** Where it
> is undeclared (Patrón Reposado), the fact goes in a `note:` and `suggestion`
> stays `[]` — TIER 3.

---

## A FILE THAT ARRIVES FROM A REPO-LESS SESSION

**Helen finds things away from her desk.** She hands the recipe to a claude.ai
chat that reads `model_instructions/INGEST_ONE_RECIPE.md` or
`INGEST_ONE_COCKTAIL.md` (`model_instructions/CLAUDE_WEB_INGEST.md` is the setup
and the loop), and gets back one envelope per recipe: a draft file plus a short
"what I could not know" list. **That file is most of an ingest and is missing
exactly the parts that need this repository.** Finishing it is a different job
from a photo batch and it is much smaller.

**Which procedure depends on how it arrived.** If she pasted it into the chat,
this is the procedure — read on. If she put it in an `ingest` issue on the
private drafts repo, run `/ingest-inbox` instead: `scripts/ingest_inbox.py`
parses the envelope, checks the fingerprint against every existing draft and
writes the file, and then hands back to the same finishing pass below. The two
paths differ only in who copies the code block.

**Ask her for the hand-back list.** It names every `QQ` and every guess, and it
is faster to read than the file. If she has lost it, the `QQ` notes inside the
file say the same things.

**THE FINISHING PASS, in order.** The order is the one the scripts need: the
moods read the generics `resolve_pours.py` writes, and the suite fails on a
cocktail until the moods and the key order are in. Each script writes nothing
without its flag, so run it dry first if you want to see what it will do.

1. **Save the file** into the root of `_food_drafts/` or `_cocktail_drafts/`.
   Branch the drafts repo first (Procedure, step 2) -- never commit to its
   `main`.
2. **Cocktails: `python3 scripts/resolve_pours.py --apply`.** It reads every
   ingredient whose `generic` is still a `QQ`, looks the source's words up in
   `bottles.yml`, in the vocabulary and in
   `_data/cocktails/source_wordings.yml`, and writes only what an EXACT match
   settles: tiers 1 and 2, never tier 3. `source_wordings.yml` holds a source's
   wording for a category that Helen has already ruled is one of her generics,
   such as Difford's "Rosso vermouth" for `sweet vermouth`. When she answers a
   "which category?" and the answer is a rule rather than a call about one
   drink, add the wording to that file in the same commit. **Run this before
   typing a generic by hand**: a bottle resolved from recall is a chance to be
   confidently wrong.
3. **Cocktails: `python3 scripts/derive_cocktail_moods.py --write`.** A file
   from a web chat arrives with `mood: []`, and
   `test_every_drinks_moods_match_the_derivation` fails until this runs. It
   supplies the derived moods and keeps a hand-assigned one already in the
   file, which an envelope carries only where Helen named it in the chat.
4. **Food, only if the file has no `main_ingredients`:** `python3
   scripts/derive_main_ingredients.py --derive --only <slug>`. Read its
   docstring before trusting the result; a list of hers is better than the
   derivation. Without `--derive` the script only reorders an existing list
   into Helen's stated order and changes no membership.
5. **Tidy.** A cocktail always gets `python3 scripts/tidy_drafts.py --site
   cocktails --only order --apply`, which puts its keys in page order by moving
   whole blocks and editing no line;
   `test_a_draft_drinks_keys_are_in_page_order` fails until it has. Then
   `/tidy-drafts`, either collection, if the quoting or typography needs it. It
   never touches a `QQ` line, so the transcription is safe.
6. **`pytest`**, once. Everything mechanical shows up here -- quoting, dashes,
   accents, an undeclared tag, a missing glass.
7. **Work whatever is left against the three tiers.** What steps 2 to 6 left
   is tier 3: a missing glass, a `tagline`, a category the vocabulary does not
   settle. Ask; never fill in.
8. **`python3 scripts/ingest_preflight.py`**, which reports the undeclared
   bottles, near-miss garnishes and silences in the source as one list. With no
   arguments it reads what this branch changed; it never writes.

**What not to do to it.** Do not rewrite its prose, and do not "improve" a
`QQ Claude` line -- a rewrite pass has already happened and redoing it burns
Helen's review twice. Do not REPLACE a `main_ingredients` list that already
exists. And do not type a `generic` or a `suggestion` that step 2 declined:
what it leaves alone, it leaves alone because no dictionary settles it, and
that is not relaxed by the file having arrived from elsewhere.

---

## FIXING A DRAFT THE SUITE IS COMPLAINING ABOUT

Not an ingest, and the commonest job after one. The boundary is the same one
the mechanical pass in `PUBLISHING_A_COCKTAIL.md` draws, and the two must not
drift:

**MECHANICAL -- fix it, and say what you fixed.** A spelling one of the
vocabularies already declares (a glass, a garnish, a generic, a canonical
method step, a bottle alias). A missing required key. A hyphen that should be an
en dash. A quoted boolean. A `meta:` block out of order. A cocktail draft's
top-level keys out of page order. `mood:` disagreeing with the derivation. A US
unit. **The test names the value it wanted; the data file holds the spelling.**
Look it up -- never a guess that merely turns the test green.

**NON-MECHANICAL -- list it, one line each, and let Helen rule.** Anything the
vocabularies do NOT already declare: a bottle nobody has declared, a generic
that would need coining, a glass the source did not name, a tagline, a
`meta.ship`. A `QQ` of any kind. An amount that looks wrong against a source.
**Bring them ONCE, grouped by decision** -- `ingest_preflight.py` exists to
build exactly that list.

**Work in the finishing pass's order, steps 2 to 8**, running each script dry
first and writing only where it reports a difference. Then one list to Helen,
then commit.

**A red test is not always yours.** Fetch first, with `--keep-head` (Procedure,
step 1): a non-zero "behind" count means the failure is probably work someone
else has already done (MANUAL §9.1).

---

## TIER 1 -- do it at ingest, unasked, both sites

- **Every qualifier the source states.** Sugar, butter, flour, milk, eggs,
  garlic, ginger, chocolate, mustard, vinegar. Source silent → `QQ`, never a
  default.
- **The fan oven temperature**, from the printed pair. Check WHICH is the fan
  figure; they are not always in the same order. **A `QQ Claude` line gives the
  fan figure alone; its `QQ original` keeps everything the source printed.**
  Where the pair is not labelled, the rewrite keeps the pair and the question
  goes on her list.
- **The ingredient list is the source's own list; never add to it from the
  method.** Helen: *"We shouldn't list incidentals. We can trust the cook."*
  "Pour over 75 ml boiling water", "a pinch of salt", flour for dusting: none
  becomes a line, with a quantity or without. The one exception is a source
  with no ingredient list at all, where the method's quantities are lifted into
  one group and her list says so.
- **A fat or flour the source's list prints only for the tin or the pan keeps
  its line and gains `incidental: true`** ("butter, for greasing", "oil, for
  frying", "flour, for dusting"). Only those: icing sugar to dust and mustard
  to brush stay ordinary lines, and so does a real ingredient with the use
  tacked on ("175 g butter, plus extra for the tin").
- **Quantities in their own `amount:` key**, never inside `item:` text. The
  highlighter reads `item.amount` and never scans text, so a quantity in the
  wrong field renders unstyled with no error anywhere.
- **Size words with the count** -- `amount: "2 large"`, not `item: "large
  onions"`.
- **`serves_estimate:` on any FOOD recipe whose `serves:` does not open with a
  number** -- an integer, PEOPLE, unquoted, sitting under the
  `serves:`/`makes:` line it estimates from. `makes: "About 750 ml"`,
  `makes: "one 8-inch cake"` and `serves: "Depends on appetite"` all need one;
  **`makes:` is never read as people** however numeric it looks. The shopping
  list divides by this, and a recipe without one gets no scaler at all. Read it
  off the recipe: a round cake 12, a loaf 10, a 950 ml tub of ice cream 8,
  18 cookies 9 (two each), 12 Yorkshire puddings 6. **Where the source does not
  support one -- `serves: QQ`, "Some", "however many you make" -- this becomes
  a TIER 3 question rather than a guess.** Helen: *"Claudes can check with me
  if unsure."*
- **Split `ingredient_groups` and `method_groups`** -- once, here, and never
  again afterwards. Phases are usually obvious from the source and re-reading
  the recipe later to find them is the expensive way.
  - **The method side is the one that gets skipped, and the schema is why.**
    `ingredient_groups:` is the only container for ingredients, so naming a
    second group is a small edit from where you are. `method:` and
    `method_groups:` are mutually exclusive fields, so grouping the method
    means switching fields, and the path of least resistance writes grouped
    ingredients and a flat method.
  - **So use this trigger: if you wrote more than one NAMED ingredient group,
    the method almost certainly has the same phases.** Write `method_groups:`
    and **give the groups the same names**. A recipe whose ingredients split
    into `ragù` and `white sauce` does not have a one-phase method.
  - The converse still holds and is not a licence: one phase means one unnamed
    ingredient group and a flat `method:`. Do not split a sequence the source
    ran as one.
  - **An ingredient group's name is read after "For the", so say it that way
    before writing it.** `dressing` prints "For the dressing:". **The one shape
    that prints as itself is a name opening with `to `**: `to serve`, `to
    finish`, `to decorate`, `to garnish` read "To finish:" with no "For the".
    So keep the source's "To finish" as `to finish`, lowercase, and never
    nounify it. A bare verb is the other trap: `assemble` prints "For the
    assemble:", so a block the source heads that way is `to assemble`. A method
    group prints its name bare, with no prefix at all, which is why a narrative
    phase is fine there.
  - **Quote every group name, on both sides**: `- name: "dressing"`,
    `- name: "Make the dressing"`. Quoted and bare parse to the same string, so
    this is only about every file reading the same way; `/tidy-drafts`
    (`--only quoting`) fixes a bare one.
- **House style** -- en dashes, `°C`, unicode fractions, quoting, accents, and
  **a space between a number and its unit** (`15ml` -> `15 ml`). The units are
  `kg`, `g`, `ml`, `cl`, `cm`, `mm`, `oz`, `tsp`, `tbsp`; a temperature is NOT
  one of them, because `180C` wants a degree sign and spacing it would half-fix
  it. `scripts/tidy_drafts.py --only units` is the same rule for a drafts pass.
  Outside `QQ` lines, always.
- **The citation**, per `model_instructions/SOURCE_ATTRIBUTION_SPEC.md`. For
  food that is `source` + `source_type`; a dated magazine is a `publication`, an
  undated one is a `website`, and that distinction catches everyone out. For
  cocktails `source` is free text and empty is fine.
- **Name the file from the whole title**, lowercased and hyphenated, so slug
  and title cannot diverge. Existing files are not renamed.

### Food only

- **EVERY METHOD STEP IS A PAIR.**

      method:
        - "QQ original Heat the oven to 180C fan and grease a 20cm tin."
        - "QQ Claude Heat the oven to 180°C fan and grease a 20 cm tin."

  `QQ original` is **verbatim** -- the source's own punctuation, its "minutes",
  its degree-sign habits. Never tidy or house-style one; it will read as broken
  house style and that is the point. `QQ Claude` is the paraphrase and IS held
  to house style like any other prose.

  She keeps both so she can judge the rewrite rather than trust it blind.

  **One source step is one pair, however many actions it holds.** The `QQ
  original` line is the source's whole step, verbatim; the `QQ Claude` line
  rewrites all of it, in several short sentences where it needs them. Never
  split a step, never merge two, never reorder.

  **WHAT HER OWN REWRITE LOOKS LIKE, once she's actually cooked from a `QQ
  Claude` line** (`sticky-squidge-ginger-loaf.md`). She asked for the
  comparison herself and it holds four real patterns, worth aiming for on the
  NEXT `QQ Claude` line rather than waiting for her to fix this one:

  - **Don't re-narrate what the ingredient list already says.** Mine: "Whisk
    the milk and beaten eggs..." Hers: "Whisk the milk with the eggs..." -- the
    `item:` line already says `eggs, beaten`, so the method doesn't say it
    again. Same logic collapsed a full re-listing of five ground spices down
    to "Grind the whole spices to a fine powder."
  - **Draw step boundaries at physical stages, not at clauses.** She merged
    two of mine ("whisk the dry ingredients" + "pour the wet in and whisk")
    into one continuous action, but split one of mine (cooling, then
    wrapping-and-storing) into two -- because those are two things you might
    actually stop and do separately. Not "fewer steps" or "more steps": one
    step per thing you'd pause at. Inside a `QQ Claude` line that is a matter
    of where the sentences break, since the pair itself follows the source's
    step.
  - **State the expected result plainly instead of hedging with a check.**
    Mine: "Check it early -- a skewer inserted into the centre should come out
    with a few sticky, wet crumbs attached. Don't overbake." Hers: "It will
    still be slightly sticky inside." She still tells the cook what to expect
    -- she doesn't cut that -- but as a flat fact rather than a cautionary
    test.
  - **Cut flourish, keep function.** I ended a step with "the texture
    transforms into a sticky, dense ginger loaf" -- pure scene-setting, and
    she cut it. She kept "still be slightly sticky inside" a few lines
    earlier, because that one changes what the cook does next (keep it in the
    oven, don't panic) and the ending flourish didn't.

  None of this is a licence to write a `QQ Claude` line closer to her *voice*
  in the Tier 3 sense -- it's still her call when a step needs her own
  judgement or her own kitchen experience (the saucepan-size note she added
  here is exactly that, and isn't something to try to anticipate). It's about
  writing tighter and less hedged, which is a paraphrase quality question, not
  a judgement one.

  **Building the file one step-pair at a time avoids an output-filter refusal.**
  A single large write containing a whole method's worth of verbatim book prose
  has triggered one; incremental edits have not.

### Cocktails only

- **Write the keys in the order the page prints them, top to bottom.** The
  list is `TOP_LEVEL_KEYS_IN_ORDER` in `tests/test_cocktails.py`, which a test
  derives from `_layouts/cocktail.html` -- read it there; it is not retyped
  here. A file that arrives in another order is fixed by `python3
  scripts/tidy_drafts.py --site cocktails --only order --apply`. Drafts only:
  never reorder a file in `_cocktail_recipes/`.
- **Millilitres. Never a US unit.** Helen: *"I don't want any US units, just
  ml."* 1 oz = 30 ml, 1 tsp = 5 ml, from `measures:` in `ingredients.yml`.
  Transcribe the DRINK, not the page's units. `test_no_amount_uses_a_us_unit`
  enforces it on amounts; **convert method prose too**, which that test does
  not read.
- **A qualified measure keeps its figure and loses its adjective to a note.** A
  scant or heaping ounce is `30 ml` plus `note: "the source asks for a heaping
  measure"`. MANUAL §9.4.1 -- the site states one figure and does not hedge it.
- **Method steps use the canonical forms in `_data/cocktails/methods.yml`** where
  one exists. A cocktail's method has no `QQ original` / `QQ Claude` pairs: the
  mechanical spine is a closed vocabulary and the tail is free text.
- **The shape rulings, all Helen's, all in `methods.yml`, `serve.yml` and
  `ingredients.yml` -- look the spellings up there:**
  - **the ice in the glass is `serve.ice`, never a method step** (MANUAL
    §9.10a): "strain into a rocks glass over a big cube" is `Strain.` +
    `glass: ["old fashioned"]` + `serve: {ice: "large cube"}`, and the page
    composes the sentence. A strain step names neither glass nor ice;
    `test_serve_ice_is_not_restated_in_the_method` refuses one that does;
  - **never write an `Express …` step.** A garnish naming a citrus twist makes
    `_layouts/cocktail.html` append it, and `test_no_method_step_opens_with_express`
    refuses one that tries. Put the twist in `garnish:` and write nothing;
  - **a step may be a `{step, note}` pair** -- used sparingly, and the note is
    how Helen does the step, not part of the instruction;
  - **`half` and `whole` are UNITS**: a whole fruit is counted, never measured,
    so half a lime is `amount: "half"` and never a millilitre figure;
  - **a barspoon is `5 ml`**; an egg or a sugar cube is an INGREDIENT, not a
    unit, and its count still needs a unit: `amount: "1 whole"` with `generic:
    "whole egg"`, `amount: "1 cube"` with `generic: "sugar cube"`. A bare
    `amount: "1"` is rejected;
  - **every ingredient has an amount, and an unmeasured one is a BRACKETED
    NOUN** -- `(top)`, `(rinse)`, `(splash)`, `(float)`, `(sprinkle)`, plus
    counts like `1 small pinch`. A bracketed noun reads as the slot where a
    number would be. Each is declared in `measures:` and each carries its
    matching method step saying WHEN. There is no `(garnish)`: an ingredient
    used as a garnish has a millilitre amount and names its use in `as:`.
    **`to taste` is the exception and is not bracketed**, because it hands the
    decision to the DRINKER rather than naming what the maker does.
- **`method` / `to_serve` / `garnish`** -- an ACTION in sequence, a NOUN PHRASE
  about how it reaches the table, and a THING on the drink. The test: *can you
  write it as a bare noun and lose nothing?* "with a straw" → `Straw.` loses
  nothing. "Top with crushed ice to serve" loses WHEN, so it is a method step.
- **Run the finishing pass, steps 2 to 8, after writing the files**:
  `resolve_pours.py`, then the moods, then the key order.

## TIER 2 -- fill in, and say plainly they are proposals

`main_ingredients`, `tags`, `star_ingredient`. Cheap for her to correct and
expensive to originate. **Not a cocktail's `mood`**: the derived moods come from
`derive_cocktail_moods.py --write` and a hand edit to one is reverted on the
next run, and the hand-assigned ones (`moods_by_hand` in
`_data/cocktails/taxonomy.yml`) are Helen's alone, so a new cocktail lacks those
until she is asked. Nothing can be invented -- an undeclared tag or star fails
the suite. **Be generous with `main_ingredients`**: the cap of eight is a guide
that has been read as a budget, and her own recipes run to fourteen.

## TIER 3 -- never, at ingest or after

Rewriting a method step into her voice. `incidental:` on anything but the
tin-and-pan fats and flour TIER 1 names. The case-by-case tags
(`freezable`, `virtuous`, `one-handed food`). Inventing a time or temperature --
`Estimated N mins` is banned outright. Setting `meta.rewritten` or
`meta.proofread` to `true`, or choosing a `meta.ship`. **Reconstructing a
truncated step**, even when every sibling recipe on the page ends the same way.
**Declaring a bottle in `bottles.yml`** from the ingredient beside it.

**The bottle rule is about inference, not about typing.** What is banned is
turning an ingredient into a bottle by deduction -- the cocktail says blanco
tequila, so presumably she owns one. A bottle Helen NAMES is hers to add: her
spelling is the key, her unaccented forms become aliases, and the cocktail keeps
her spelling while the dictionary learns it, never the other way round.

**Removing a bottle is also hers, and it is a move rather than a delete.** It
goes to `not_reached_for` WITH the reason she gave, which is what stops a later
pass re-adding it on noticing a thin category.

**Either way, `_data/cocktails/costs.yml` moves with it.** Every declared bottle
carries a price and a size there, and
`test_every_declared_bottle_carries_a_price` fails in BOTH directions -- a
bottle with no price, and a price naming no bottle. See MANUAL §9.3.5.

**An agent never writes `rewritten: true`, anywhere, on either site, and no
folder implies it.** On a cocktail the flag is a leg of the publish gate, so it
belongs exactly where `proofread` is: hers to type. If a cocktail staged for
promotion still says `rewritten: false`, it will not publish: **say so and let
her flip it.**

---

## Procedure

1. **Fetch the drafts repo before anything you will act on.**

       sh scripts/git-fetch-agent.sh _cocktail_drafts helen-triages-cocktails-private
       sh scripts/git-fetch-agent.sh _food_drafts helen-triages-food-private

   That leaves the clone detached on the fetched `main`, ready to branch from.
   Mid-work on a branch, add `main --keep-head`: it fetches, stays put and
   prints how far behind you are. A non-zero count means the next red test is
   probably not yours. Fetch again before any run whose result you will act
   on; a clone is stale the moment anyone merges.

2. **Branch in the drafts repo**, never commit to its `main`. A bare `git
   checkout -b` would branch the public repo, so use the wrapper:

       sh scripts/git-drafts.sh _cocktail_drafts checkout -b content/<what-this-batch-is>
       sh scripts/git-drafts.sh _food_drafts checkout -b content/<what-this-batch-is>

   `scripts/git-drafts.sh` runs every local git command inside a drafts clone;
   its header lists the verbs it accepts.

3. **Open every photo.** Resolve each recipe by looking at its own file -- never
   from a prior pass's count, a filename, or an assumption that a folder is one
   book. Batches routinely hold pages from several sources, and edge-of-frame
   captures Helen did not mean to include.

4. **Check whether it already exists**, and compare the FORMULA, not the title.
   A cocktail already in the collection may share a name and be a
   different drink.

5. **Transcribe.** Tier 1 unasked, tier 2 as proposals, tier 3 never. Say in the
   file where the frame ended if a capture stops mid-recipe -- a screenshot that
   ends mid-list looks exactly like a complete one.

6. **Run the finishing pass, steps 2 to 8.** It ends with the pre-flight, which
   is the whole point of doing this in a batch.

7. **Bring Helen the report ONCE.** Not a gap at a time -- that is the failure
   the pre-flight exists to fix. Group her decisions and ask them together.

8. **Run `python3 scripts/verify.py`, every time, before the commit is
   pushed.** It runs `pytest` and then the JS suite, drafts checks included,
   and nothing else ever runs those: CI checks out the public repo alone, where
   the per-file draft checks are never created (`PIPELINE.md` §3). If a public
   test was touched, simulate CI too (MANUAL, "What CI runs, and what it
   lacks").

9. **Commit in the drafts repo**, checking the branch in a call of its own
   first:

       sh scripts/git-drafts.sh _cocktail_drafts branch --show-current
       sh scripts/git-drafts.sh _cocktail_drafts add -- .
       sh scripts/git-drafts.sh _cocktail_drafts commit -F tmp/commit-msg.txt

   Tag any issue the batch touches in the full form, `Towards
   DeckOfPandas/helen-triages#N`: a bare `#N` resolves against the drafts
   repo's own tracker. Then push, per `CLAUDE.md`, with no ask:

       sh scripts/git-push-agent.sh <branch>:<branch> helen-triages-cocktails-private _cocktail_drafts

   Report what is still `QQ` and why.

---

## Traps

- **A capture that ends mid-recipe looks exactly like a complete one.** Count
  every ingredient the method names; that proves nothing is missing that is
  USED, not that nothing follows. Say so in a note and ask.
- **The source is the best audit the collection ever gets.** Transcribing a page
  beside a cocktail already derived from it has found a missing citation, a wrong
  ice instruction and an amount out by a factor of 24. **Record all of it and
  change none of it** -- the site is canon, her figures stand, the source is
  noted beside them. Once she has ruled, the `QQ` becomes a plain note recording
  the answer.
- **Never house-style a verbatim block.** A `QQ original` line, a quoted
  alternative recipe in a note, or Helen's own note describing an experiment.
- **Resolving a cocktail's `suggestion` and `generic`** (MANUAL §9.3.2 has the
  long form; `unresolved_suggestions` in `bottles.yml` is empty and must stay
  so):
  - a HOUSE is not a bottle: declare the product she owns by its name and
    retype the cocktail to it; a house is an alias only where it can mean one
    thing in the collection (Luxardo → Luxardo Maraschino);
  - a spirit type beside its own generic is not a suggestion; it goes;
  - a syrup's suggestion may name what it is made from (Acacia honey);
  - generics are named by what substitutes for what: never a `flavoured X`
    that spans non-substitutable members; `honey water` is one flat generic
    and bare `honey` is the raw thing you cook with; `lavender-forward
    bitters`, not `lavender bitters`; `bonded rye` and `rye` are distinct;
  - spelling: in the pool the cocktail stays as she wrote it and the spelling
    becomes an alias; in the published tense every `suggestion` is the
    canonical name (the box under "Where a new file goes").
- **A source's own label on a tip is the source's furniture. Transcribe the
  tip; drop the label.** Both sites. Good Food prints its asides under a
  standing `gf tip` rubric, which in `notes:` reads as an abbreviation nobody
  can expand. **`source:` already carries the attribution**, so the label adds
  nothing and costs a note that no longer reads as a sentence.
  - The note keeps the tip's own words, capital to full stop, like any other.
  - **Keep the label only where it is doing work inside the sentence** -- a
    tip that says *"the magazine likes Kallo"* is naming its source as part of
    the advice, and that stays.
  - The general rule: **an unexplained abbreviation transcribed out of a
    source will be expanded by guess later, and the guess will be believed.**
    `gf` has been read as *gluten-free*, which would have printed a false
    allergen claim on a recipe page. If a label must be kept, expand it now,
    while the source is in front of you.
