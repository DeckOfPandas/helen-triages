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

## 1. What is different about a cocktail, and it is the whole document

A food ingest can fill in nearly everything, because the vocabularies are small
enough to print. **A cocktail has two fields whose vocabularies are not, and
they are the two that matter most:**

- **`generic`** — what CATEGORY of spirit a pour is: "moderately aged Jamaican
  rum", "lightly aged and filtered rum", "blanc vermouth". 224 declared terms.
- **`suggestion`** — the specific bottle. 70 declared, plus 30 unresolved.

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
method:
  - "Shake all ingredients with ice."
  - "Fine strain over ice."
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
| `method` | An ORDERED list. The steps are sequential and reordering makes a different drink. §5. |
| `to_serve` | Presentation, not a further instruction. `"Straw."`, `"Two straws."` A terse noun phrase, or `""`. |
| `notes` | A bare string, or `{label, text}`. Use one to record what the source could not give you. |
| `source` / `source_url` | Free text here, unlike food. `"Difford's"`, `"Death & Co"`. `source_url` may be `""`. |
| `meta.ship` | Helen's rating. **Always `"QQ"`** — you have not drunk it and neither has she. |
| `meta.date_last_edited` | Today's date, `YYYY-MM-DD`. |

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
`dash` · `dashes` · `drop` · `drops` · `cube` · `cubes` · `pinch` · `each` ·
`leaf` · `leaves` · `sprig` · `strip` · `g`
<!-- vocab:measures end -->

So `"1 barspoon"` and `"1 sugar cube"` are not yet readable, however sensible
they look. Write the source's own words, and say in your list that the unit is
undeclared — that is a one-line data edit for Helen, and much cheaper than a
figure you invented.

**NEVER WRITE A BARE NUMBER.** An amount with no unit cannot be read. If the
source really gives one, write it as it stands **and add a note saying the
source had no unit** — the ladders 30/22.5/15/7.5 and 0.75/0.5 are thirty
times apart and a wrong guess looks exactly as confident as a right one.

**`item` is what the source called it, brand and all.** `generic` is the
category, and it is always `QQ` from you. Do not put the quantity in `item`.

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
half an empty passion fruit shell ·
passion fruit shell filled with overproof rum · pineapple and brandied cherry

**Cherries:** brandied cherry · maraschino cherry · Luxardo maraschino cherry ·
skewered maraschino cherry · cherry flag ·
fruit stick (skewered pineapple cubes and a maraschino cherry)

**Herbs and leaves:** mint sprig · mint bouquet · rosemary sprig ·
kaffir lime leaves · cucumber wheels · edible violet

**Spice and other:** grated nutmeg · cinnamon stick · three coffee beans ·
half-rim of sugar · cocktail umbrella · 3 dashes red creole-style bitters ·
5 drops of olive oil
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

**Strain:** `Strain.` · `Double strain.` · `Fine strain.` ·
`Strain into a chilled glass.` · `Double strain into a chilled glass.` ·
`Fine strain into a chilled glass.` · `Strain into an ice-filled glass.` ·
`Fine strain into an ice-filled glass.` · `Strain over ice.` ·
`Fine strain over ice.` · `Strain over crushed ice.`

**Build:** `Add the remaining ingredients.` ·
`Fill the pitcher half full with ice cubes.` · `Fill with crushed ice.` ·
`Top with champagne.` · `Top with more crushed ice.`
<!-- vocab:method end -->

Four things that will catch you out:

- **NEVER NAME THE GLASS IN A STRAIN STEP.** `glass:` already carries it and
  draws an icon. "Fine strain into a chilled coupe" says coupe twice. Write
  `Fine strain into a chilled glass.`
- **"Shake all ingredients" and "Shake" mean different things.** After a build
  step — a muddle, a rinse, an "add the rest" — "Shake with ice." means *shake
  what is in the shaker*, and that is a different instruction. **Read the step
  above before choosing.** If a rinse came first, the form is "Shake the
  remaining ingredients with ice."
- **A step may not start with "Serve" or "Garnish".** Those belong in
  `to_serve` and `garnish`. "Serve with a straw" becomes `to_serve: "Straw."`
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
chèvre · comté · consommé · crème · crémeux · crêpe · crêpes · éclair ·
éclairs · entrecôte · flambé · fraîche · frisée · gâteau · glacé · gougère ·
gougères · gruyère · jalapeño · jalapeños · marinière · niçoise · pâté ·
pâtisserie · pâtissière · piña · purée · puréed · purées · ragù · rösti ·
sauté · sautés · sautéed · soufflé · soufflés · velouté
<!-- vocab:accents end -->

---

## 8. Never do these

- **Never guess a `generic` or a `suggestion`.** Both are `QQ`, every time.
- **Never invent `meta.ship`** — that is Helen's rating of a drink she has
  drunk.
- **Never write a `mood:`** — derived or hers.
- **Never leave a US unit**, and never convert a non-volumetric one.
- **Never write a bare number as an amount** without flagging it.
- **Never name the glass inside a method step.**
- **Never reconstruct a truncated method**, however obvious the pattern.
- **Never assume a familiar name means a familiar drink.**

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
method:
  - "Shake all ingredients with ice."
  - "Strain over crushed ice."
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
double old-fashioned glass filled with crushed ice" became `glass: ["double old
fashioned"]` plus `"Strain over crushed ice."`** — the glass moved to the field
that draws the icon, and the step stopped naming it twice. **"Garnish with…"
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
