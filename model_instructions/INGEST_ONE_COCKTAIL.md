# Ingest one cocktail — for a Claude with no repository

**You are being handed a drink Helen found in the wild** — a photograph of a
book page, a screenshot, a URL, or pasted text — and asked to turn it into a
file for her cocktail site. You do **not** have her repository or her data
files. Everything you need is in this document.

**Hand back two things:**

1. **One complete `.md` file, in a single code block**, ready to save into
   `_cocktail_drafts/`. Give the filename on the line above it.
2. **A short "what I could not know" list.** Four or five bullets.

**This document has a sibling, `INGEST_ONE_RECIPE.md`, for food.** They are not
interchangeable: a recipe is a procedure, a cocktail is a formula plus a build,
and the schemas share almost nothing.

---

## 0. How to hand this back

Helen pastes what you write into a GitHub Issue on her private drafts
repository, `helen-triages-cocktails-private`, titled `ingest: <slug>` and
labelled `ingest`. A script there parses it, so the shape matters: anything
missing is a rejection rather than a guess. `INGEST_INBOX_DESIGN.md` §6 is the
reference and this is the short form.

Four parts, in this order, and nothing else at the top level:

1. `<!-- ingest v1 cocktail -->`, as the first non-blank line. Exactly that.
2. **One** fenced `yaml` block, and only one — the complete file, front matter
   and all, beginning `---`.
3. A `## What I could not know` heading with your list under it. If there is
   genuinely nothing, write "nothing"; the heading is never absent.
4. A `## Fingerprint` heading, then ONE line: the title lowercased, then every
   amount in build order, separated by ` | `. For the worked example in §9 that
   is `jungle bird | 45 ml | 22.5 ml | 15 ml | 15 ml | 45 ml`.

**The fingerprint is what compares the FORMULA rather than the name**, which is
the whole of §6's Sazerac trap made mechanical, so the amounts must be the ones
in the file, in the file's own order.

---

## 1. What is different about a cocktail, and it is the whole document

A food ingest can fill in nearly everything, because the vocabularies are small
enough to print. **A cocktail has two fields whose vocabularies are not, and
they are the two that matter most:**

- **`generic`** — what CATEGORY of spirit a pour is: "moderately aged Jamaican
  rum", "lightly aged and filtered rum", "blanc vermouth". 171 declared terms.
- **`suggestion`** — the specific bottle. 107 declared, and none outstanding.

**Leave both as `QQ`. Always. This is Helen's own standing ruling**, made on
2026-08-31 when a book named eleven bottles she did not own:

> "I will update these when I make the drinks, so QQ is right. These won't get
> promoted until I've made them."

It is not a size problem — it is that **a bottle's category is not derivable
from the ingredient printed beside it.** "Appleton Estate Signature" does not
tell you it is moderately aged Jamaican; you have to know. A wrong `generic`
looks exactly as confident as a right one, and it is the field the drink page,
the cards and the search all read.

So: **transcribe faithfully, convert the units, canonicalise the build, and
`QQ` every judgement.** That is a genuinely useful drink file, and it is what
an in-repo photo ingest produces too.

---

## 2. The file

```yaml
---
title: "Smokestack Lightning"
tagline: "QQ"
glass:
  - "old fashioned"
garnish:
  - "lime wedge"
ingredients:
  - amount: "52.5 ml"
    item: "Patron Reposado tequila"
    generic: "QQ"
  - amount: "7.5 ml"
    item: "Peated Scotch whisky"
    generic: "QQ"
  - amount: "15 ml"
    item: "agave syrup"
    generic: "QQ"
  - amount: "4 drops"
    item: "Difford's Margarita bitters"
    generic: "QQ"
serve:
  ice: "cubed"          # how the drink is ICED IN THE GLASS. §4a. OMIT the
                        # whole `serve:` key if the source does not say.
method:
  - "Shake all ingredients with ice."
  - "Fine strain."      # the TECHNIQUE only — never "over ice", never
                        # "into a chilled glass". §5a.
  # A step is a string, OR a `{step, note}` pair. USED SPARINGLY — the note is
  # an aside about how Helen does the step, never part of the instruction:
  #   - step: "Muddle the lime chunks hard with the sugar."
  #     note: "my giant spiky muddler not the polite smooth one"
to_serve: ""
mood: []
notes:
  - label: "QQ"
    text: "QQ - `generic` and `suggestion` not filled in; the source names bottles, not categories."
source: "Difford's"
source_url: "https://..."
meta:
  ship: "QQ"
  date_last_edited: "2026-09-02"
  rewritten: false
  awaiting_fix: false
  proofread: false
---
```

**The filename** is the drink's name, lowercased, hyphenated, ASCII only:
`smokestack-lightning.md`. Accents are stripped in a filename, kept in a title.

| Field | Rule |
|---|---|
| `title` | The drink's name. **If the source is a specific bar or book's version, say so in the title** — `"Sazerac (Death & Co)"`. See §6. |
| `tagline` | One line of prose. **Almost always `"QQ"`** — this is Helen's voice about a drink she has not made yet. |
| `glass` | **A LIST, not a scalar**, even for one glass. **Required — see the warning below.** Canonical spellings in §4. |
| `mood` | **Always `mood: []`.** The key is required and the value is DERIVED in her repo by a script. Never write a mood yourself. |
| `garnish` | **A LIST.** `[]` means nobody has filled it in; `["no garnish"]` means the drink genuinely takes none. Vocabulary in §4. |
| `ingredients` | The FULL list, untriaged, **in build order**. §3. |
| `ingredients[].item` | What the SOURCE called the pour, brand and all. **A drafts-only field with a DEATH DATE** — §3. |
| `ingredients[].suggestion` | The bottle. **ALWAYS A LIST**, even for one bottle: `["Beefeater"]`. §3. |
| `ingredients[].character` | Why a drink wants a particular bottle. **Never yours to write** — §3. |
| `serve` | How it is iced, and any rim. **A mapping, and OPTIONAL — omit it entirely if the source does not say.** §4a. |
| `method` | An ORDERED list. The steps are sequential and reordering makes a different drink. §5. A step is a string, or a `{step, note}` pair — **used sparingly** (Helen, 2026-09-04), for an aside about how she does the step rather than part of the instruction. |
| `to_serve` | **Serveware only** — what the drink is served WITH. `"Straw."`, `"Two straws."`, `"Ladle and punch glasses."` A terse noun phrase, or `""`. **Never the ice** — that is `serve.ice`. |
| `notes` | A list. **Every note you add is the `{label, text}` form with BOTH fields set, and both begin `QQ`** — Helen, 2026-09-04: "It's annoying for me to remember how to type YAML every time." She finds the `QQ`s and replaces the label with a real heading and the text with her own words. A bare string is legal in the schema but not for an ingest. Use one to record what the source could not give you. |
| `source` / `source_url` | Free text here, unlike food. `"Difford's"`, `"Death & Co"`. `source_url` may be `""`. |
| `meta.ship` | Helen's rating. **Always `"QQ"`** — you have not drunk it and neither has she. |
| `meta.date_last_edited` | Today's date, `YYYY-MM-DD`. |
| `meta.rewritten` / `meta.awaiting_fix` / `meta.proofread` | **Exactly these three, in this order, all `false`, unquoted.** The same publish gate a food recipe carries (since 2026-09-02). `rewritten` and `proofread` are Helen's own claims about her own work and you never set either `true`; `awaiting_fix: false` is what lets a drink publish once she has, and `false` unquoted is the only value that works. Underscore, never a hyphen. |

> ### EVERY DRINK MUST NAME A GLASS, and you may not guess one.
>
> Helen, 2026-08-27: *"All recipes should have a glass."* On a drink page the
> glass is the hero — it is drawn as tall as the whole title block — so an
> empty `glass` is not a missing detail, it is a page with a hole where its
> main image goes. Her suite enforces it.
>
> **But which glass a drink wants is her knowledge, not something derivable
> from the ingredients**, and a wrong glass looks exactly as confident as a
> right one. When she filled in the last sixteen herself she did it from the
> ingredients and the total volume, drink by drink.
>
> So: **take the glass from the source if the source names one.** If it does
> not, write `glass: []` and **put it as the FIRST line of your "what I could
> not know" list** — that one answer is what stands between the file and being
> complete, and it is a ten-second question for her.

**`mood: []`, always — and it is not a gap.** Moods are derived from the
ingredients by rule and then STORED, so that Helen can override one. The rules
live in her `taxonomy.yml` and a script applies them:

```
python3 scripts/derive_cocktail_moods.py --write
```

That is one command in her repo and it fills the field in. **Writing a mood
yourself is worse than leaving it empty**, because the next run silently
reverts it — and a hand-typed mood that happens to match hides the fact that
nobody derived it. The key must be present; `[]` is the right value.

---

## 3. `ingredients` — and the millilitres rule

```yaml
ingredients:
  - amount: "45 ml"
    item: "Appleton Estate Signature"   # what the SOURCE called it
    generic: "QQ"                        # the category. Never guess it.
  - amount: "2 dashes"
    item: "Angostura bitters"
    generic: "QQ"
  - amount: "15 ml"
    item: "lime juice"
    generic: "QQ"
    optional: true                       # BOOLEAN. Absent means required.
```

**`amount` is the only quantity field.** Never a separate `ml:` key.

> ### NO US UNITS. EVER. Convert them.
>
> Helen's ruling, 2026-08-31: *"I don't want any US units, just ml, so please
> convert for me as part of ingestion."*
>
> **1 oz = 30 ml. 1 tsp = 5 ml. 1 tbsp = 15 ml. 1 cl = 10 ml.**
>
> That is bar-standard rounding, not 29.5735, and it is deliberate: it keeps
> the ratios clean. So `1½ oz` → `"45 ml"`, `¾ oz` → `"22.5 ml"`, `½ oz` →
> `"15 ml"`, `¼ oz` → `"7.5 ml"`, `2 oz` → `"60 ml"`.

**Non-volumetric amounts are NOT converted and must not be.** `"2 dashes"`,
`"1 drop"`, `"1 pinch"` — these have no millilitre figure and inventing one is
worse than leaving them. These are the units her suite knows, and an amount
whose unit is not one of them (and is not `ml`, `cl`, `oz` or `tsp`) fails a
test rather than rendering:

<!-- vocab:measures start -->
`dash` · `dashes` · `drop` · `drops` · `cube` · `cubes` · `pinch` ·
`small pinch` · `each` · `leaf` · `leaves` · `sprig` · `strip` · `g` · `half` ·
`whole` · `to top` · `to rinse`
<!-- vocab:measures end -->

Four things a source prints as if they were units, and what to do instead
(Helen's rulings, 2026-09-03):

- **A barspoon is `"5 ml"`.** Convert it like a teaspoon; her suite rejects
  the word.
- **An egg or a sugar cube is an INGREDIENT, not a unit.** `amount: "1"`,
  `generic: "QQ"`, `item: "whole egg"` (or `"sugar cube"`), the same as any
  other pour.
- **Half a fruit is `amount: "half"`** — Helen's ruling, 2026-09-04, on a
  Caipirinha's lime. `half` and `whole` are units, and a whole fruit is
  COUNTED, never measured: do not turn half a lime into millilitres, because
  the juice a lime gives is a range and a figure here would be precision the
  fruit does not have. The page prints `half`, `1 whole`, `1½ whole`.
- **"Top" is not an amount on its own** — the ingredient added by a top-up is
  `amount: "to top"`, and the method carries a `Top with …` step. Likewise a
  rinse is `amount: "to rinse"` with a `Rinse …` step.
- Anything else the source calls a measure and this list does not know:
  write the source's own words, and say in your list that the unit is
  undeclared — that is a one-line data edit for Helen, and much cheaper than
  a figure you invented.

**NEVER WRITE A BARE NUMBER.** An amount with no unit cannot be read. If the
source really gives one, write it as it stands **and add a note saying the
source had no unit** — the ladders 30/22.5/15/7.5 and 0.75/0.5 are thirty
times apart and a wrong guess looks exactly as confident as a right one.

**`item` is what the source called it, brand and all.** `generic` is the
category, and it is always `QQ` from you. Do not put the quantity in `item`.

**Write the bottle as the source spells it, and do not tidy it.** Helen's
bottle dictionary resolves spellings by alias, and her standing rule
(2026-09-04) is that a drink keeps her spelling and the dictionary learns it,
never the other way round. Two things you can get right from the source
alone: a HOUSE is not a bottle (Briottet, Monin, Gabriel Boudier make many
things — if the source names the product, write the product), and a spirit
TYPE printed beside its own name is not a bottle at all (a source's
"aguardiente" next to aguardiente is the generic, not a suggestion).

### `item` is a transcription field, and it lives only in the drafts

**It does not render on a published drink page, and a promoted drink will not
carry it.** The line a reader sees is built from `generic` and `suggestion`;
`item` is the source's own wording, held so that Helen can see what the page
said when she comes to fill those two in. She deletes it at that point, which
is the same moment she stops guessing about the bottle.

So: **write it on every pour, and do not treat it as the answer.** A file whose
`item` fields are perfect and whose `generic` fields are all `QQ` is exactly
what this document is asking for. A file that resolved the categories and lost
the source's words is worse, in both directions at once.

**THE DEATH DATE IS NOW ENFORCED, AND IT IS WHY THIS FIELD STILL EXISTS.**
`tests/test_cocktails.py::test_item_is_gone_once_the_generic_is_filled_in`
refuses an `item` on any pour whose `generic` is no longer `QQ`. The rule is
CONDITIONAL, which is the point: your file, with `QQ` on every pour, is exactly
right and passes. What is forbidden is the field outliving the answer it was
holding a place for.

It had to become a test. The lifecycle above was written down and then not
followed: by 2026-09-05 every one of 683 pours had a real category and 215 still
carried the `item` that had been a placeholder for it. Helen: *"we agreed to
drop item, but then I was persuaded to allow it back as somewhere to hold
incoming data, but it's become a dumping ground again."* Emptying it turned up
57 bottles the page had never been able to show, 23 of which existed nowhere
else in the repository — so the field had been quietly hoarding, not holding.

### `suggestion` is ALWAYS a list

`suggestion: ["Beefeater"]`, never `suggestion: "Beefeater"`. One bottle or
five, the shape is the same, and a test enforces it.

Liquid treats a bare string as a one-item sequence, so both shapes rendered
correctly and nothing complained while 194 pours used one and 18 used the
other. That is precisely why it needed a rule: everything downstream — the
alcohol-units work, costing, the scaler — would otherwise handle two shapes
forever.

**`generic` is deliberately NOT held to this**, and the difference is worth
understanding. There a bare string means "this category" and a list means
"either of these would do", so the two shapes mean DIFFERENT things. On
`suggestion` they mean the same thing and differ only in how many bottles are
named.

### `character` — the field that is never yours

`character` is the flavour property that made a drink want THIS bottle:
`blackstrap` on a rum, `peated` on a whisky, the botanical a gin pushes. Helen,
2026-08-24: *"Blackstrap is only ever given as a character for another rum, like
this: Moderately aged (character: blackstrap)."* So it rides ALONGSIDE a real
`generic` and never replaces one — a pour still needs its category, and the
character says why that particular bottle.

**Which means you cannot write one, because you are not writing `generic`
either.** A character with no category under it is a property attached to
nothing, and for rum and whisky the vocabulary is closed and declared in her
repository, where you cannot see it. Leave the field out. If the source names a
property beside a pour, it is already in `item` where you transcribed it, and
one line in your list is what turns it into a `character` when she makes the
drink.

---

## 4. The two closed vocabularies you CAN use

These are complete. Anything outside them fails her test suite, so if nothing
fits, use the source's own words and flag it in your list.

### `glass` — use these spellings

<!-- vocab:glass start -->
`coupe` · `sour` · `collins` · `flute` · `highball` · `hurricane` ·
`nick and nora` · `punch bowl` · `tiki mug` · `mug` · `mule mug` · `martini` ·
`martini glass` · `wine` · `pilsner` · `sling` · `absinthe` · `goblet` ·
`chalice` · `pineapple` · `hollowed pineapple` · `coconut` · `coconut shell` ·
`old fashioned` · `double old fashioned` · `brandy glass`
<!-- vocab:glass end -->

**These spellings are WRONG and will be corrected against you** — write the
right-hand form:

| the source will say | write |
|---|---|
<!-- vocab:glass_corrections start -->
| rocks, old-fashioned, old-fashioned glass | **old fashioned** |
| double rocks, double old-fashioned | **double old fashioned** |
| champagne saucer, champage saucer | **coupe** |
| snifter | **brandy glass** |
<!-- vocab:glass_corrections end -->

If the source names no glass, use `glass: []` **and lead your list with it** —
see the warning in §2. Do not infer one.

### `garnish` — the declared vocabulary

<!-- vocab:garnish start -->
**Citrus peel:** lemon twist · lemon twist (discarded) ·
lemon twist after expressing over cocktail · orange twist ·
orange twist (discarded) · orange or lemon twist · grapefruit twist ·
flamed orange zest coin

**Citrus cut:** lime wedge · lime wedge on rim · lime wheel · lemon wheel ·
lemon slice · orange slice · orange crescent · grapefruit crescents ·
citrus wheel · dehydrated lime slice wheel · half lime shell

**Fruit:** pineapple wedge ·
pineapple wedge (cut to resemble a bird's plumage) · pineapple wheel ·
blackberry · dried apple slice · banana chip · raspberries ·
half an empty passion fruit shell · pineapple and brandied cherry

**Cherries:** brandied cherry · maraschino cherry · Luxardo maraschino cherry ·
skewered maraschino cherry · cherry flag ·
fruit stick (skewered pineapple cubes and a maraschino cherry)

**Herbs and leaves:** mint sprig · mint bouquet · rosemary sprig ·
kaffir lime leaves · cucumber wheels · edible violet

**Spice and other:** grated nutmeg · cinnamon stick · three coffee beans
<!-- vocab:garnish end -->

Four rules that decide the awkward cases:

- **A twist IS a strip of zest.** Write `lemon twist`, never `lemon zest
  twist`. But keep the tail: `orange twist (discarded)` says it does not stay
  in the drink, and that is information.
- **The list is CONJUNCTIVE — every entry is wanted.** Cobra's Fang takes a
  mint sprig AND a lime wheel, so it has two entries. **"Either of these, the
  maker chooses" is therefore ONE STRING, not two**: `orange or lemon twist`.
- **A count stays only where the count is the spec.** `three coffee beans` is
  the Espresso Martini. "12 raspberries" is just how many that punch wanted —
  write `raspberries`.
- **`["no garnish"]` means decided; `[]` means unfilled.** The marker must
  appear alone, never beside a real garnish. Use `[]` if the source is simply
  silent — that is the honest answer.

> ### A GARNISH IS NOT A POUR, A RIM, OR SERVEWARE
>
> The field had absorbed all three by 2026-09-05, because two of them had no
> home until then. Four things that look like garnishes and are not:
>
> - **Anything with an amount is a POUR.** "3 dashes red creole-style bitters",
>   "5 drops of olive oil". Those go in `ingredients` with their amount, and a
>   method step puts them on top — "Drop the bitters on the top." Helen wants
>   units of alcohol counted (#297), and nothing can count a pour hiding in
>   `garnish`.
> - **A rim is `serve.rim`.** "half-rim of sugar" is done to the glass before
>   the drink is built. But `lime wedge on rim` IS a garnish — that is a
>   placement, and a placement carries information.
> - **Serveware is `to_serve`.** Umbrellas, straws, stirrers, ladles, plastic
>   giraffes.
> - **Do not restate a method step.** One drink's garnish read "passion fruit
>   shell filled with overproof rum" while its own method already said "Fill
>   the passion fruit shell with rum and set on top of the drink."

---

## 4a. `serve` — how it is iced

**The ice that goes in the GLASS, never the ice in the shaker.** That
distinction is the whole of this field. Of 156 mentions of ice in the
collection's method steps, 86 were the shaker's: "Shake all ingredients with
ice" says nothing about how the drink is served.

```yaml
serve:
  ice: "crushed"
```

**Six values, and nothing else is legal:**

| Value | Means |
|---|---|
| `none` | Served up, in an empty glass. The commonest answer by a wide margin. |
| `cubed` | Ordinary cubes — an ice-filled glass. |
| `crushed` | Crushed or pebble ice. Every swizzle. |
| `large cube` | One big rock. |
| `block` | A large block, in a punch bowl or pitcher. |
| `blended` | The ice is IN the drink. Frozen drinks. |

**OMIT THE WHOLE `serve:` KEY IF THE SOURCE DOES NOT SAY.** Absent means nobody
has decided; `ice: "none"` means somebody decided it is served up. Exactly the
distinction `garnish` draws between `[]` and `["no garnish"]`, and it is a real
one: one punch in the collection strains into a bowl and never says whether ice
goes in, where both its siblings say a large block. That is a question for
Helen, not a blank to fill with a default.

**`rim` is free text and rare.** `rim: "half-rim of sugar"`. Only if the source
rims the glass.

**There is no `chill` key and you must not invent one.** Helen, 2026-09-05: *"I
think it's implied that glasses should be chilled (except hot drinks
obviously). I am the user after all."* If the source does something MORE than
chilling — freezing a glass, rinsing it with absinthe — that is a method step in
its own right, which is what those drinks already do.

---

## 5. `method` — the canonical build steps

**A closed vocabulary for the mechanical spine, free text for everything else.**
The test for whether a step belongs in the spine: **does its phrasing carry
information?** "with ice" versus "over ice" carries none. "other than the
champagne" carries all of it. So use a canonical string where one fits exactly,
and write the source's own words where none does.

<!-- vocab:method start -->
**Shake:** `Shake all ingredients with ice.` ·
`Shake all ingredients hard with ice.` · `Shake with ice.` ·
`Shake the remaining ingredients with ice.` ·
`Shake all ingredients other than the champagne with ice.`

**Stir:** `Stir all ingredients with ice.` ·
`Stir the remaining ingredients with ice.` ·
`Stir all ingredients other than the champagne with ice.` · `Stir until cold.` ·
`Stir.`

**Blend and swizzle:** `Blend all ingredients until smooth.` ·
`Swizzle until the glass frosts.`

**Strain:** `Strain.` · `Double strain.` · `Fine strain.` · `Dump.` · `Pour.`

**Build:** `Add the remaining ingredients.` ·
`Fill the pitcher half full with ice cubes.` · `Fill with crushed ice.` ·
`Top with champagne.` · `Top with soda water.` · `Top with more crushed ice.`

**Rinse and rim:** `Rinse the glass with absinthe and dump.` ·
`Rinse the glasses with Campari.` ·
`Dip only half the rim in water (or tequila) then coarse salt.`

**Express:** `Express the twist over the drink and drop it in.` ·
`Express the twist over the drink and discard it.`
<!-- vocab:method end -->

Seven things that will catch you out:

- **A STRAIN STEP IS THE TECHNIQUE AND NOTHING ELSE.** Five strings, and there
  is no sixth: `Strain.` · `Fine strain.` · `Double strain.` · `Dump.` ·
  `Pour.` **Never name the glass, never name the ice.** The glass is in
  `glass:`, which draws the icon; the ice is in `serve.ice` (§4a). So:

  | The source says | You write |
  |---|---|
  | "fine strain into a chilled coupe" | `Fine strain.` + `glass: ["coupe"]` |
  | "strain into an ice-filled highball" | `Strain.` + `serve: {ice: "cubed"}` |
  | "strain into a rocks glass over a big cube" | `Strain.` + `serve: {ice: "large cube"}` |
  | "strain over crushed ice" | `Strain.` + `serve: {ice: "crushed"}` |

  This group held SEVENTEEN strings until 2026-09-05 and every retired one
  named where the drink landed, because the ice had no field. Two of the
  seventeen turned out to be truncated sentences nobody had noticed —
  "Fine strain into a chilled." and "Fine-strain into pre-chilled." — which is
  the argument for the change in one line: prose that varies is prose nobody
  can check.
- **"Shake all ingredients" and "Shake" mean different things.** After a build
  step — a muddle, a rinse, an "add the rest" — "Shake with ice." means *shake
  what is in the shaker*, and that is a different instruction. **Read the step
  above before choosing.** If a rinse came first, the form is "Shake the
  remaining ingredients with ice."
- **A step may not start with "Serve" or "Garnish".** Those belong in
  `to_serve` and `garnish`. "Serve with a straw" becomes `to_serve: "Straw."`
- **A step may not start with "Express" either, and this one is not obvious.**
  Helen's ruling, 2026-09-04: a garnish of any citrus twist makes the drink
  page add `Express the twist over the drink and drop it in.` as the last
  step, on its own — so a drink that writes it says one fact twice. If the
  source's last line expresses a twist, put the twist in `garnish:` and write
  no step. (`orange twist (discarded)` gets `...and discard it.` instead.)
  The two sentences are in the **Express** group above for recognition only;
  you never type either.
- **A step may carry a `note`** — `{step, note}` instead of a string — but
  **used sparingly**, and almost never from an ingest: the note is Helen's own
  aside about how she does the step ("my giant spiky muddler not the polite
  smooth one"), not something a source can give you. If the source's step has
  a parenthetical that is part of the INSTRUCTION, leave it in the step.
- **Everything expressive stays free text.** "Muddle the lime chunks hard with
  the sugar in the bottom of a shaker until the sugar has dissolved" cannot be
  collapsed without losing the drink. Don't try.

---

## 6. What the source cannot give you, and the one trap that has bitten

**A DRINK ALREADY IN THE COLLECTION MAY SHARE A NAME AND NOT BE THE SAME
DRINK.** This is the real hazard, and it caught a session on 2026-08-31.
Helen's Sazerac splits the spirit three ways across rye, bourbon and cognac and
pours absinthe and chilled water into the glass. Death & Co's rinses and
discards the absinthe, has no bourbon and no water, runs 3:1 rye to cognac, and
sweetens with demerara. Two of *her* suggested bottles are *its* specified
ones, which is exactly what made them look like one recipe.

They live side by side now, and her ruling was: *"name it 'Sazerac (Death &
Co)', leaving mine as simply 'Sazerac'."*

**So: compare the FORMULA, never the title.** If you are handed a drink with a
classic name, say plainly in your list that it may already exist in a different
form, and title it with its source in parentheses if the source is a specific
bar or book.

**NEVER RECONSTRUCT A TRUNCATED RECIPE.** A photograph that stops mid-sentence,
a screenshot that ends below the ingredients. These do not announce themselves,
and the sibling drinks on the same page ending the same way is not evidence —
that is *their* wording. Transcribe what is in frame, write a `QQ` note saying
where the frame ended, and say so in your list. Two drinks in her collection
are unmakeable for exactly this reason and are tracked as open issues rather
than guessed at.

**AN INFUSION OR A SYRUP ON ANOTHER PAGE IS MISSING DATA, not a detail.** If a
drink pours "jalapeño-infused blanco tequila" and the infusion recipe is not in
frame, the drink cannot be made from what you have. Say so — steeping time and
chilli count decide whether it is pleasant or inedible, and neither is
inferable.

---

## 7. House style

- **En dash for a number range**: `3–4 dashes`. Not a hyphen.
- **Unicode fractions** in prose: `½`. But amounts are decimal millilitres —
  `"22.5 ml"`, not `"22½ ml"`.
- **Quote every string value**, including every list member: `glass: ["coupe"]`,
  not `glass: [coupe]`. Do **not** quote the boolean `optional: true`.
- British spellings. Em dash for `--` in prose. `°C` with the degree sign.
- **Reproduce a bottle or brand exactly as it spells itself**, accents and all:
  `Bénédictine`, `Cointreau`, `St-Germain`, `Difford's`.

**Accented words her house style declares.** The list is shared with the food
site, so most of it is culinary — but `crème`, `piña` and `purée` all turn up
in a drink, and a missing accent on one of these is a mechanical fault her
formatter would fix on a recipe and does not yet fix on a drink:

<!-- vocab:accents start -->
açaí · aïoli · béarnaise · béchamel · brûlée · café · canapé · canapés ·
chèvre · comté · consommé · crème · crémeux · crêpe · crêpes · crudités ·
éclair · éclairs · entrecôte · flambé · fraîche · frisée · gâteau · glacé ·
gougère · gougères · gruyère · jalapeño · jalapeños · marinière · niçoise ·
pâté · pâtisserie · pâtissière · piña · purée · puréed · purées · ragù · rösti ·
sauté · sautés · sautéed · soufflé · soufflés · velouté
<!-- vocab:accents end -->

---

## 8. Never do these

- **Never guess a `generic` or a `suggestion`.** Both are `QQ`, every time.
- **Never invent `meta.ship`** — that is Helen's rating of a drink she has
  drunk.
- **Never write a `mood:`** — derived or hers.
- **Never write a `character:`** — it hangs off a `generic` you are not writing.
- **Never leave a US unit**, and never convert a non-volumetric one.
- **Never write a bare number as an amount** without flagging it.
- **Never name the glass OR the ice inside a method step.** §5.
- **Never write `suggestion` as a bare string.** Always a list.
- **Never invent a `serve.chill`** — a chilled glass is assumed. §4a.
- **Never put a pour in `garnish`.** Anything with an amount is an ingredient.
- **Never reconstruct a truncated method**, however obvious the pattern. But
  **do say in your list that it looks truncated** — three of these were found
  in one day in 2026-09, all by machine and none by a reader.
- **Never assume a familiar name means a familiar drink.**

> ### FOUR RUM WORDS THAT ARE NOT CATEGORIES
>
> Other people's recipes ask for these constantly. Helen, 2026-09-05: *"there
> is no such thing as navy rum or overproof navy rum"*, and *"there's no such
> thing as black rum, even though it will often be requested by other people's
> recipes."* `dark`, `light`, `gold` and `spiced` are out for the same reason —
> they describe colour or strength, not production, and colour is routinely
> adjusted with caramel.
>
> **This changes nothing about what you write**, because you write `generic:
> "QQ"` regardless. It matters for your `item` and for your list: transcribe
> the source's word faithfully, and **say in your "what I could not know" list
> that the source asked for a category Helen does not use.** If the source also
> names a BOTTLE, say so in the same bullet — her bottle dictionary resolves
> the category from the bottle mechanically, and that is the answer in 13 cases
> out of 22 when it was measured.

---

## 9. A worked example

**Source** (a book page, photographed):

> **JUNGLE BIRD**
> 1½ oz blackstrap rum · ¾ oz Campari · ½ oz lime juice · ½ oz simple syrup ·
> 1½ oz pineapple juice
> Shake all the ingredients over ice. Strain into a double old-fashioned glass
> filled with crushed ice. Garnish with a pineapple wedge and serve with a
> straw.

`jungle-bird.md`

```yaml
---
title: "Jungle Bird"
tagline: "QQ"
glass:
  - "double old fashioned"
garnish:
  - "pineapple wedge"
ingredients:
  - amount: "45 ml"
    item: "blackstrap rum"
    generic: "QQ"
  - amount: "22.5 ml"
    item: "Campari"
    generic: "QQ"
  - amount: "15 ml"
    item: "lime juice"
    generic: "QQ"
  - amount: "15 ml"
    item: "simple syrup"
    generic: "QQ"
  - amount: "45 ml"
    item: "pineapple juice"
    generic: "QQ"
serve:
  ice: "crushed"
method:
  - "Shake all ingredients with ice."
  - "Strain."
to_serve: "Straw."
mood: []
notes:
  - label: "QQ"
    text: "QQ - `generic` and `suggestion` not filled in. The source names one bottle (Campari) and otherwise gives categories, and a category is not derivable from a bottle name."
source: "QQ"
source_url: ""
meta:
  ship: "QQ"
  date_last_edited: "2026-09-02"
  rewritten: false
  awaiting_fix: false
  proofread: false
---
```

**What I could not know:**

- **No `generic` on any pour, per the standing rule.** "Blackstrap rum" is
  close to a category already, but which one it maps to is a lookup I cannot do.
- **`mood: []` needs deriving** — run `python3 scripts/derive_cocktail_moods.py
  --write`. Until you do, one test fails and it is that one.
- **No source recorded** — tell me the book and I will write the citation.
- **Jungle Bird is a well-known drink and may already be in your collection in
  a different form.** Compare the formula, not the name.

Note what the transcription did: **all five amounts converted** (1½ oz → 45 ml,
¾ → 22.5, ½ → 15). **"over ice" became "with ice"**, and **"into a
double old-fashioned glass filled with crushed ice" became THREE fields** —
`glass: ["double old fashioned"]`, `serve: {ice: "crushed"}` and a bare
`"Strain."` One sentence in the source, three facts, and each now lives in the
one place that owns it. **"Garnish with…"
and "serve with a straw" left the method entirely**, into `garnish` and
`to_serve`.

---

## 10. What happens to your file afterwards

Helen saves it into `_cocktail_drafts/`, which is a private repo — nothing there
is published. Then, in order:

1. **`python3 scripts/derive_cocktail_moods.py --write`** fills in `mood`.
2. **`pytest -m cocktails`** checks the glass, the garnish vocabulary, the
   units, the citation and the schema. Every mechanical fault you made shows up
   here and costs seconds.
3. She fills in `generic` and `suggestion` **when she makes the drink**, which
   is the point at which she knows what went in the glass.

**So spend your care on the transcription.** A wrong garnish spelling is caught
by a test; a wrong amount is not, because 45 ml is as plausible as 22.5. The
numbers, the order of the build, and what the source actually said are the
things no machine of hers can recover once the page is gone.
