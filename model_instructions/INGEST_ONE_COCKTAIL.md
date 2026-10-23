# Ingest one cocktail — for a Claude with no repository

**You are being handed a cocktail recipe Helen found in the wild** — a photograph of a
book page, a screenshot, a URL, or pasted text — and asked to turn it into a
file for her cocktail site. You do **not** have her repository or her data
files. Everything you need is in this document.

**Hand back one envelope per recipe, in the shape §0 fixes.** It carries:

- **One complete `.md` file**, ready to save into `_cocktail_drafts/`.
- **A short "what I could not know" list.** A handful of bullets.
- **A marker line and a fingerprint line**, which let her repository accept
  the file and recognise a duplicate.

**This document has a sibling, `INGEST_ONE_RECIPE.md`, for food.** They are not
interchangeable: a food recipe is a procedure, a cocktail recipe is a formula plus a build,
and the schemas share almost nothing.

---

## 0. How to hand this back

Helen pastes what you write into a GitHub Issue on her private drafts
repository, `helen-triages-cocktails-private`, titled `ingest: <slug>` and
labelled `ingest`. A script there parses it, so the shape matters: anything
missing is a rejection rather than a guess.

These parts, in this order, and nothing else at the top level:

1. `<!-- ingest v1 cocktail -->`, as the first non-blank line. Exactly that.
2. **One** fenced `yaml` block, and only one — the complete file, front matter
   and all, beginning `---`.
3. A `## What I could not know` heading with your list under it, each bullet
   on one unwrapped line: the script reads every non-blank line as an item of
   its own. If there is genuinely nothing, write "nothing"; the heading is
   never absent.
4. A `## Fingerprint` heading, then one line: the title lowercased, then every
   amount in build order, separated by ` | `. For the worked example in §9 that
   is `jungle bird | 45 ml | 22.5 ml | 15 ml | 15 ml | 45 ml`.

**In a chat, show the whole envelope inside one outer fence of four
backticks**, so that its own three-backtick `yaml` fence copies as raw text
instead of closing the block, and put a line reading exactly `ingest: <slug>`
above it. That line is the issue title; the slug is the filename from §2
without its `.md`. The outer fence is there for copying and is not part of the
envelope. §9 shows a complete one.

**The fingerprint is what compares the FORMULA rather than the name**, which is
the whole of §6's Sazerac trap made mechanical, so the amounts must be the ones
in the file, in the file's own order.

**If one message holds several cocktails, hand back one of these per
recipe**, each complete on its own, in the order they appear. One envelope is one
issue; never fold two recipes into one block.

**If you can run code, check each envelope first** with her repository's own
parser, which needs nothing but Python and PyYAML:
`https://raw.githubusercontent.com/DeckOfPandas/helen-triages/main/scripts/envelope.py`.
`python3 envelope.py <file>` prints the filename and fingerprint it accepts,
or the one-line reason it would reject. Hand back nothing it rejects.

---

## 1. What is different about a cocktail, and it is the whole document

A cocktail has two fields that carry its whole identity:

- **`generic`** — what category of ingredient it is: "moderately aged Jamaican rum",
  "blanc vermouth", "lime juice". A closed vocabulary, printed in §3a.
- **`suggestion`** — the specific bottle, from a dictionary you do not have.

**`generic` is the field the recipe page, the cards and the search all read.**
It is the only one a reader sees. So an untyped ingredient must still say
something: write `QQ`, a space, and then **the source's own words** —
`generic: "QQ aged Jamaican rum"`. Helen: *"if it's not obvious
write QQ then whatever the source said then I have a chance of being able to fix
it myself."* A bare `QQ` left her looking at "90 ml QQ" with nothing to fix it
from.

**Type it where §3a settles it and QQ it everywhere else.** An item that names
a declared generic exactly — `lime juice`, `vodka`, `orgeat` — is a lookup, not
a judgement, and copying it is READING. Anything short of an exact match is a
judgement: **a bottle's category is not derivable from the ingredient printed
beside it.** "Appleton Estate Signature" does not tell you it is moderately aged
Jamaican; you have to know, and a wrong `generic` looks exactly as confident as
a right one. Near-misses are judgements too — `agave nectar` beside `agave
syrup` is not a match.

**`suggestion` is never yours.** You do not have the bottle dictionary, so you
cannot know whether a bottle is declared or how Helen spells it. Write the key
with an empty list — `suggestion: []` — which is what she asked for (*"that
saves me typing YAML when I come to it if I want to note my own suggestion"*),
and put the bottle the source names in that ingredient's `note:`, as
**`"Originally <the bottle, as the source prints it>."`**

**That holds even when Helen tells you in the chat to use the source's
bottles.** The bottles a source names are mostly its sponsors, not her shelf,
and her dictionary does not know them. Her ruling: *"Move all the suggestions
to notes, and I can add my own suggestions where I have them or drop if not.
For notes, just write 'Originally X'."*

Her standing ruling is what all of this serves:

> "I will update these when I make the drinks, so QQ is right. These won't get
> promoted until I've made them."

So: **transcribe faithfully, convert the units, canonicalise the build, type
only what §3a settles outright, and `QQ` every judgement — with the source's
words after it.**

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
meta:
  made_before: false
  ship: "who knows"
  rewritten: false
  awaiting_fix: false
  proofread: false
mood: []
ingredients:
  - amount: "52.5 ml"
    generic: "QQ Patron Reposado tequila"   # a BOTTLE; the category is a
    suggestion: []                          #  judgement, so QQ and the words
    note: "Originally Patron Reposado."
  - amount: "7.5 ml"
    generic: "QQ Peated Scotch whisky"      # `peated` is a CHARACTER, not a
    suggestion: []                          #  generic — so this is not a match
  - amount: "15 ml"
    generic: "agave syrup"                  # an exact match in §3a. Typed.
    suggestion: []
  - amount: "4 drops"
    generic: "QQ Difford's Margarita bitters"
    suggestion: []
    note: "Originally Difford's Margarita Bitters."
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
notes:
  - label: "QQ"
    text: "QQ - three of the four pours carry the source's words behind a `QQ`; the source names bottles, not categories. No `suggestion` is filled in."
source: "Difford's"
source_url: "https://..."
---
```

**The filename** is the drink's name, lowercased, hyphenated, ASCII only:
`smokestack-lightning.md`. Accents are stripped in a filename, kept in a title.

**Write the keys in the order above, which is the order the page prints them,
top to bottom**: `title`, `tagline`, `glass`, `garnish`, `meta`,
`mood`, `ingredients`, `serve`, `serves`, `method`, `to_serve`, `notes`,
`source`, `source_url`. `meta` sits fifth because the page prints her rating
beside the glass and garnish. Leave out a key you are told to omit; never move
one.

| Field | Rule |
|---|---|
| `title` | The drink's name. **If the source is a specific bar or book's version, say so in the title** — `"Sazerac (Death & Co)"`. See §6. |
| `tagline` | **A bare `"QQ"`, and you draft nothing.** This is Helen's voice about a drink she has not made yet, on a page that carries her name. Her rulings: *"a drink without a tagline written by me gets a QQ, so I protect my voice in the public content"*, and *"Let's stop Claude drafting taglines. It turns out me doing them in batches works the best."* **The one exception is HER OWN line, if she gives you one in the chat for that drink**: write it exactly as she gave it, with no `QQ` — `"A Manhattan in a woolly jumper."` — because it is already hers, and add nothing after it. Never the source's line, and never yours. |
| `glass` | **A LIST, not a scalar**, even for one glass. **Required — see the warning below.** Canonical spellings in §4. |
| `mood` | **`mood: []`, unless Helen names a mood for that drink in the chat.** The key is required. Most moods are DERIVED in her repo by a script and you never write one of those. The rest are hers alone, and one she gives you goes in exactly as she said it. Never one of your own. See below. |
| `garnish` | **A LIST.** `[]` means nobody has filled it in; `["no garnish"]` means the drink genuinely takes none. Vocabulary in §4. |
| `ingredients` | The FULL list, untriaged, **in build order**. §3. |
| `ingredients[].amount` | The ONLY quantity field, and **every ingredient has one**. No US units, never a bare number. §3. |
| `ingredients[].generic` | The category. **Typed only where §3a settles it outright; otherwise `QQ` then the source's own words** — `"QQ aged Jamaican rum"`. §1 and §3a. |
| `ingredients[].suggestion` | The bottle — **never yours to write**, because you do not have the dictionary. **ALWAYS A LIST, and always present: `suggestion: []`.** The bottle the source names goes in that ingredient's `note:`, as `"Originally <bottle>."` §3. |
| `ingredients[].note` | One short sentence about that ingredient — a capital letter and a full stop, always. `"Originally Luxardo Maraschino liqueur."`, `"Or génépy liqueur."`, `"Unaged."` **Only what changes how the drink is made or bought**: the source's bottle, an alternative it offers, a qualifier the generic does not carry. Not `"from the freezer"`, not `"freshly squeezed"`, not `"chilled"`: Helen wants less writing. Leave the key out where there is nothing to say. |
| `ingredients[].as` | How the ingredient is used when it is not simply measured in: `"float"`, `"rinse"`, `"muddle"` or `"shell"`. **If your method floats, rinses or muddles an ingredient, that ingredient carries the matching `as:`** — her suite refuses a method that says "Float the port on top." over a port with no `as: "float"`, because the cards and the unit count read the field and not the prose. |
| `ingredients[].character` | Why a drink wants a particular bottle. **Never yours to write** — §3. |
| `serve` | How it is iced, and any rim. **A mapping, and OPTIONAL — omit it entirely if the source does not say.** §4a. |
| `method` | An ORDERED list. The steps are sequential and reordering makes a different drink. §5. A step is a string, or a `{step, note}` pair — **used sparingly**, and almost never from an ingest: the note is her own aside about how she does the step, and a parenthetical that is part of the source's instruction stays in the step. |
| `to_serve` | **Serveware only** — what the drink is served WITH. `"Straw."`, `"Two straws."`, `"Ladle and punch glasses."` A terse noun phrase, or `""`. **Never the ice** — that is `serve.ice`. |
| `notes` | A list. **Every note you add is the `{label, text}` form with BOTH fields set, and both begin `QQ`** — Helen: "It's annoying for me to remember how to type YAML every time." The label is `"QQ"`, or `"QQ"`, a space and a short topic (`"QQ history"`); nothing else. She finds the `QQ`s and replaces the label with a real heading and the text with her own words. **A bare string note is not legal**: her suite refuses one. An empty pair (`label: ""`, `text: ""`) is the placeholder for a note you have nothing to put in yet, and the page does not print it. **If you have no note to add, write exactly that one empty pair — never `notes: []`**: it leaves Helen somewhere to type without recalling the shape. Use a note to record what the source could not give you. |
| `source` / `source_url` | Free text here, unlike food — and `""` is a perfectly good answer, on most cocktails. **But if it IS one of the publications in §6a, spell it the way §6a spells it.** `source_url` may be `""`. |
| a tip printed under the source's own label | **Transcribe the tip; drop the label.** A book or a site that runs its asides under a standing rubric is showing you its furniture, and `source:` already carries the attribution. Keep the label only where it is doing work inside the sentence. **Never carry an unexplained abbreviation across** — a food magazine's `gf tip:` prefix reads as *gluten-free*, which is a false allergen claim. Expand it while the source is in front of you, or drop it. |
| `meta.made_before` | Has Helen made this drink? **Always `false` on a fresh ingest** — unquoted, never `"false"`. A transcription cannot know whether she has poured it, and this is the field that says so. She flips it herself when she makes it. |
| `meta.ship` | Helen's rating. **Always `"who knows"`, never `"QQ"`** — you have not drunk it and neither has she, and `QQ` is not a ship value. Helen: "I think that's clearer than QQ or leaving it unset, because it's a positive presence." The pair reads straight: she has not made it, so she has no idea. |
| `meta.rewritten` / `meta.awaiting_fix` / `meta.proofread` | **Exactly these three, in this order, all `false`, unquoted.** The same publish gate a food recipe carries. `rewritten` and `proofread` are Helen's own claims about her own work and you never set either `true`; `awaiting_fix: false` is what lets a cocktail recipe publish once she has, and `false` unquoted is the only value that works. Underscore, never a hyphen. |

> ### EVERY COCKTAIL MUST NAME A GLASS, and you may not guess one.
>
> Helen: *"All recipes should have a glass."* On a cocktail page the
> glass is the hero — it is drawn as tall as the whole title block — so an
> empty `glass` is not a missing detail, it is a page with a hole where its
> main image goes. Her suite enforces it.
>
> **But which glass a drink wants is her knowledge, not something derivable
> from the ingredients**, and a wrong glass looks exactly as confident as a
> right one. She works it out from the ingredients and the total volume, drink
> by drink.
>
> So: **take the glass from the source if the source names one.** If it does
> not, write `glass: []` and **put it as the FIRST line of your "what I could
> not know" list** — that one answer is what stands between the file and being
> complete, and it is a ten-second question for her.

**`mood: []` — and it is not a gap.** Most moods are derived from the
ingredients by rule, by a script in her repository, and then stored so that
Helen can override one. **Writing a derived mood yourself is worse than leaving
it empty**, because the next run silently reverts it — and a hand-typed mood
that happens to match hides the fact that nobody derived it. The key must be
present; `[]` is the right value.

**The one exception is a mood Helen gives you, in the chat, for that drink.**
These moods describe an occasion or a judgement rather than the liquid, and
only she assigns them: `clear`, `sugar craving`, `tiki`, `aperitivo`,
`nightcap`, `brunch`, `sunny terrace`, `festive`, `signature`,
`so wrong it's right`, `easy peasy`, `on fire`. If she says "Roman Punch is a
sunny terrace drink", write `mood: ["sunny terrace"]`, spelled exactly as in
that list. Her script keeps a mood from that list and adds the derived ones
beside it. **Never offer one, never infer one from the recipe, and never write
a mood that is not in that list** — the same rule as the tagline: hers if she
gave it, otherwise empty.

---

## 3. `ingredients` — and the millilitres rule

```yaml
ingredients:
  - amount: "45 ml"
    generic: "QQ Appleton Estate Signature"  # a bottle. QQ, then the SOURCE's
    suggestion: []                           #  words. Never guess the category.
  - amount: "2 dashes"
    generic: "QQ Angostura bitters"          # a bottle again — `aromatic
    suggestion: []                           #  bitters` would be a judgement
  - amount: "15 ml"
    generic: "lime juice"                    # an exact match in §3a. Typed.
    suggestion: []
    optional: true                           # BOOLEAN. Absent means required.
```

**`amount` is the only quantity field.** Never a separate `ml:` key.

> ### NO US UNITS. EVER. Convert them.
>
> Helen's ruling: *"I don't want any US units, just ml, so please
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
`small pinch` · `each` · `large` · `leaf` · `leaves` · `sprig` · `sprigs` ·
`strip` · `wedge` · `wedges` · `disc` · `cm log` · `thick coin` · `g` · `half` ·
`whole` · `(top)` · `(rinse)` · `(splash)` · `(float)` · `(sprinkle)` ·
`to taste`
<!-- vocab:measures end -->

Things a source prints as if they were units, and what to do instead (Helen's
rulings):

- **A barspoon is `"5 ml"`.** Convert it like a teaspoon; her suite rejects
  the word.
- **The one spoon that stays a spoon is a dry sugar**: "1 tsp powdered sugar"
  is `amount: "1 tsp"`, `generic: "powdered sugar"`. Helen: *"Dry spoons stay
  spoons."* A spoon of anything liquid is still millilitres.
- **"Few" is 2**: "few dashes" is `"2 dashes"`, "few drops" is `"2 drops"`.
  Helen's ruling.
- **A scoop of ice is a volume, and a 7 oz scoop is 200 ml**, not the 210 the
  ounce rule gives. Ice is never an ingredient, so the figure lives in the
  method step, as free text: "Add a 200 ml scoop of crushed ice and blend some
  more."
- **An egg or a sugar cube is an INGREDIENT, not a unit.** `amount: "1 whole"`,
  `generic: "whole egg"`; `amount: "1 cube"`, `generic: "sugar cube"`. Both are
  declared generics and both units are declared, so both are exact matches and
  neither needs a `QQ`. **The count still needs its unit** — `amount: "1"` is a
  bare number and is rejected.
- **Half a fruit is `amount: "half"`** — Helen's ruling, on a Caipirinha's
  lime. `half` and `whole` are units, and a whole fruit is
  COUNTED, never measured: do not turn half a lime into millilitres, because
  the juice a lime gives is a range and a figure here would be precision the
  fruit does not have. The page prints `half`, `1 whole`, `1½ whole`.
- **An unmeasured ingredient is a bracketed noun** (Helen's ruling). The
  ingredient added by a top-up is `amount: "(top)"` and the method carries a
  `Top with …` step; a rinse is `amount: "(rinse)"` with a `Rinse …` step. The
  others are `"(splash)"` (a deliberate small amount that does not fill the
  glass), `"(float)"` (only where no millilitre figure is given — a float
  usually has one) and `"(sprinkle)"` (cinnamon onto a flame).
- **Rum set alight in a fruit shell is a measured ingredient with
  `as: "shell"`** (Helen's ruling). `amount: "25 ml"` unless the source gives its own
  figure, written as the LAST ingredient (only a `"(sprinkle)"` of
  `ground cinnamon` may follow it). The method then ENDS on exactly three
  steps: `Fill the passion fruit shell with the <rum> and set on top of the
  drink.` (or `the lime shell`), `Set alight.`, `Sprinkle the flame with
  cinnamon.` **The shell itself goes in `garnish`** — `half an empty passion
  fruit shell` or `half an empty lime shell`, whichever the method fills — so
  the page names it before the ingredients say "(shell)"; the page does not
  add a "Garnish with…" step for it. Never write the rum as
  `"(garnish)"`, as a float, or as prose in `to_serve` — none of those counts
  its alcohol.

  The bracketed noun sits in the slot where a number would be and names the
  action instead. **The bracketed words are in the measures list above; if it
  and this paragraph ever disagree, the list wins.**
- **`"to taste"` takes no brackets.** The bracketed words name what the maker
  does with an ingredient nobody measured; `to taste` hands the decision to
  the drinker — the Ti' Punch is
  served with lime and sugar on the side so people can roll their own — so it
  reads as English in the amount column because it is an instruction to
  whoever is holding the glass.
- Anything else the source calls a measure and this list does not know:
  write the source's own words, and say in your list that the unit is
  undeclared — that is a one-line data edit for Helen, and much cheaper than
  a figure you invented.

**Never write a bare number.** An amount with no unit cannot be read. If the
source really gives one, write it as it stands **and add a note saying the
source had no unit** — the ladders 30/22.5/15/7.5 and 0.75/0.5 are thirty
times apart and a wrong guess looks exactly as confident as a right one.

**The source's own words go in `generic`, behind the `QQ`, brand and all** —
`generic: "QQ Appleton Estate Signature"`. Do not put the quantity in there; it
has its own field.

**WRITE THE SOURCE'S WORDS FOR A CATEGORY EXACTLY AS IT PRINTS THEM, brackets
and all, and do not tidy, shorten or translate them.** Helen's repository keeps
a table of what each source calls a category and what she calls it — Difford's
"Light white rum (charcoal-filtered 1-4 years old)" is her `lightly aged and
filtered rum`, its "Rosso vermouth" her `sweet vermouth` — and it matches on
the source's exact words. So `generic: "QQ Light white rum (charcoal-filtered
1-4 years old)"` is settled the moment the file lands, where `"QQ light rum"`
or `"QQ Cuban rum"` (a word of yours for the bottle beside it) is a question
she has to answer again. **You cannot see that table and must not try to
reproduce it**: a near-miss you type yourself is still a guess.

Where the source prints a BOTTLE with its category in brackets — "Aperitivo
Luxardo (Aperol-style liqueur)" — the whole string goes behind the `QQ`, and
the bottle goes in the note as well: `note: "Originally Aperitivo Luxardo."`

**Write the bottle as the source spells it, and do not tidy it.** Helen's
bottle dictionary resolves spellings by alias, and her standing rule is that a
cocktail keeps her spelling and the dictionary learns it, never the other way
round. What you can get right from the source alone: a HOUSE is not a bottle (Briottet, Monin, Gabriel Boudier make many
things — if the source names the product, write the product), and a spirit
TYPE printed beside its own name is not a bottle at all (a source's
"aguardiente" next to aguardiente is the generic, not a suggestion).

### There is no `item` field. Do not write one.

The line a reader sees is built from `generic` and `suggestion`, so a
transcription sitting in a third field is invisible on the page, to the cards
and the search, and to costing and ABV. Helen: *"Data can be read straight into
generic/suggestion with or without QQs, and anything genuinely unclear added to
a page note for me."*

**So the source's words go where they can be seen: `generic`, behind a `QQ `.**
A fact that none of `amount`, `generic` or `suggestion` carries goes in that
ingredient's `note:`.

### `suggestion` is ALWAYS a list, and always present

`suggestion: []` on every ingredient, because you do not have the bottle
dictionary. Helen asked for the empty key rather than no key — *"that saves me
typing YAML when I come to it if I want to note my own suggestion."*

Where a bottle is named, it is `["Beefeater"]`, never `"Beefeater"`. One bottle
or five, the shape is the same, and her suite enforces it.

### `character` — the field that is never yours

`character` is the flavour property that made a drink want this bottle:
`blackstrap` on a rum, `peated` on a whisky, the botanical a gin pushes. Helen:
*"Blackstrap is only ever given as a character for another rum, like this:
Moderately aged (character: blackstrap)."* It rides alongside a settled
`generic` and never replaces one, and its vocabulary is declared in her
repository, where you cannot see it.

**So leave the field out.** If the source names a property beside an
ingredient, it is already in the `QQ <the source's words>` you transcribed, and
one line in your list is what turns it into a `character` when she makes the
drink.

---

## 3a. The generic vocabulary — the whole of it

**These are every category an ingredient may be declared as.** An item that names one
of them EXACTLY is a lookup, not a judgement: write it, with no `QQ`. Anything
else — a bottle, a brand, a near-miss, a category you think you recognise but
cannot find below — is `QQ` and then the source's own words.

**Exactly, and nothing looser.** `agave nectar` is not `agave syrup`. `rye
whiskey` is not `rye`. `chartreuse` is neither `Chartreuse Verte` nor
`Chartreuse Jaune` and you cannot know which. `peach liqueur` is not
`crème de pêche`. Every one of those is a wrong guess that has really been
made.

**Some of these are proper nouns and that is deliberate** — Campari, Cynar,
Bénédictine, Becherovka. Where nothing generalises a bottle, the bottle IS the
category; they are not suggestions that wandered into the wrong field.

**A ratio is part of the name** (`cane sugar syrup 2:1`), and where the source
does not give one you cannot pick: that is a `QQ`.

<!-- vocab:generics start -->
**Rum styles:** `moderately aged Jamaican rum` ·
`caramel-forward Jamaican rum` · `lightly aged and filtered rum` ·
`moderately aged rum` · `aged Demerara rum` ·
`overproof Demerara rum, lightly aged` · `overproof Jamaican rum, unaged` ·
`rhum agricole blanc` · `rhum agricole vieux` · `Clairin Vaval` ·
`Clairin Casimir` · `Clairin Communal` · `Clairin Sajous` ·
`clear blended multi-region rum` · `pineapple-infused rum` ·
`blended overproof rum`

**Gin styles:** `London dry gin` · `Old Tom gin` · `Plymouth gin` ·
`New Western dry gin` · `genever` · `navy strength gin` · `speciality` ·
`gin liqueur` · `sloe gin`

**Whisky styles:** `rye` · `bonded rye` · `bourbon` · `blended scotch whisky` ·
`single malt scotch whisky` · `Irish whiskey` · `Japanese whisky`

**Agave styles:** `blanco tequila` · `reposado tequila` · `añejo tequila` ·
`mezcal`

**Brandy styles:** `cognac` · `armagnac` · `calvados` · `pisco` · `grappa` ·
`tsipouro` · `apple brandy` · `eau de vie` · `aguardiente` · `kirschwasser` ·
`peach brandy`

**Cane and palm spirits:** `cachaça` · `Batavia arrack` ·
`coconut-flower arrack`

**Other base spirits:** `vodka` · `vanilla vodka` · `pineapple vodka` ·
`lemon vodka` · `bison grass vodka` · `absinthe` · `aquavit`

**Liqueurs:** `triple sec` · `orange Curaçao` · `dry orange Curaçao` ·
`Grand Marnier` · `blue Curaçao` · `Créole Shrubb` · `maraschino liqueur` ·
`crème de mûre` · `crème de cassis` · `crème de pêche` · `crème de banane` ·
`crème de violette` · `brown crème de cacao` · `white crème de cacao` ·
`coconut rum-based liqueur` · `coconut rhum-based liqueur` · `crème de menthe` ·
`cherry liqueur` · `cherry brandy` · `apricot liqueur` · `coffee liqueur` ·
`ginger liqueur` · `passion fruit liqueur` · `gentian liqueur` ·
`apple schnapps` · `peach schnapps` · `mastiha liqueur` · `allspice dram` ·
`black raspberry liqueur` · `crème de myrtille` · `kümmel` · `tomato liqueur` ·
`amaretto`

**Herbal liqueurs:** `Chartreuse Verte` · `Chartreuse Jaune` · `Bénédictine` ·
`Galliano` · `Strega` · `Jägermeister` · `liqueur de sapin` ·
`Swedish flaggpunsch` · `Becherovka`

**Amari:** `Campari` · `Aperol` · `Cynar` · `fernet` · `Amaro Nonino` ·
`Amaro Ciociaro`

**Fortified and aromatised:** `sweet vermouth` · `dry vermouth` ·
`blanc vermouth` · `rosé vermouth` · `amber vermouth` · `quinquina` ·
`americano` · `fino sherry` · `amontillado sherry` · `oloroso sherry` ·
`tawny port` · `ruby port`

**Wine and sparkling:** `champagne` · `prosecco` · `red wine` · `white wine` ·
`sake` · `cider`

**Bitters:** `aromatic bitters` · `orange bitters` · `orange-forward bitters` ·
`Créole bitters` · `chocolate bitters` · `tiki bitters` ·
`lavender-forward bitters` · `peppermint bitters` · `daiquiri bitters` ·
`grapefruit bitters` · `peach bitters` · `wood smoke bitters` ·
`warm-spiced bitters` · `margarita bitters` · `pimento bitters`

**Syrups:** `cane sugar syrup 1:1` · `cane sugar syrup 2:1` ·
`demerara sugar syrup 2:1` · `turbinado sugar syrup 2:1` · `grenadine` ·
`ginger syrup` · `passion fruit syrup` · `cinnamon syrup` · `pineapple syrup` ·
`hazelnut syrup` · `agave syrup` · `vanilla syrup` · `raspberry syrup` ·
`lemongrass syrup` · `pear, apricot and rosemary syrup` · `orgeat` ·
`falernum` · `lime cordial` · `ginger and lemongrass cordial`

**Honeys:** `honey` · `honey water` · `honey water 1:1` · `honey water 2:1` ·
`honey water 3:1`

**Sugars:** `white sugar` · `raw sugar` · `golden caster sugar` ·
`molasses sugar` · `palm sugar` · `sugar cube` · `powdered sugar`

**Juices:** `lime juice` · `lemon juice` · `orange juice` ·
`blood orange juice` · `pineapple juice` · `grapefruit juice` ·
`ruby grapefruit juice` · `pink grapefruit juice` · `cranberry juice` ·
`cranberry juice drink` · `apple juice`

**Fruit and herbs:** `lime` · `pineapple` · `passion fruit` · `raspberries` ·
`blackberries` · `pear` · `dried apricots` · `lemon zest` · `grapefruit zest` ·
`lime zest with flesh` · `mint` · `basil` · `rosemary` · `fruit purée` ·
`maraschino cherry` · `orange slice` · `cucumber` · `kaffir lime leaves`

**Other:** `soda water` · `ginger beer` · `coconut water` · `birch water` ·
`natural yoghurt` · `water` · `black tea` · `espresso` · `cola` ·
`coconut cream` · `Coco mix` · `egg white` · `orange flower water` ·
`vanilla extract` · `xanthan gum` · `salt` · `ground cinnamon` ·
`cider vinegar` · `olive oil` · `cream` · `milk` · `whole egg`
<!-- vocab:generics end -->

---

## 4. The closed vocabularies you can use

These are complete. Anything outside them fails her test suite, so if nothing
fits, use the source's own words and flag it in your list.

### `glass` — use these spellings

<!-- vocab:glass start -->
`coupe` · `sour` · `collins` · `flute` · `highball` · `hurricane` ·
`nick and nora` · `piña colada` · `punch bowl` · `tiki mug` · `julep cup` ·
`mug` · `mule mug` · `martini` · `wine` · `pilsner` · `sling` · `margarita` ·
`absinthe` · `goblet` · `chalice` · `hollowed pineapple` · `coconut shell` ·
`old fashioned` · `double old fashioned` · `brandy glass`
<!-- vocab:glass end -->

**These spellings are WRONG and will be corrected against you** — write the
right-hand form:

| the source will say | write |
|---|---|
<!-- vocab:glass_corrections start -->
| rocks, old-fashioned, old-fashioned glass | **old fashioned** |
| double rocks, double old-fashioned | **double old fashioned** |
| champagne saucer | **coupe** |
| snifter | **brandy glass** |
| martini glass | **martini** |
| pineapple | **hollowed pineapple** |
| coconut | **coconut shell** |
| pina-colada, pina colada | **piña colada** |
| julep tin, julep stainless steel cup | **julep cup** |
| zombie glass | **tiki mug** |
<!-- vocab:glass_corrections end -->

If the source names no glass, use `glass: []` **and lead your list with it** —
see the warning in §2. Do not infer one.

### `garnish` — the declared vocabulary

<!-- vocab:garnish start -->
**Citrus peel:** lemon twist · lemon twist (discarded) · orange twist ·
orange twist (discarded) · orange or lemon twist · grapefruit twist ·
flamed orange zest coin · length of lime peel · lime twist ·
lime twist (discarded) · flamed orange twist · lemon spiral ·
lemon spiral or mint bouquet ·
orange peel over the rim (cut to look like a beak)

**Citrus cut:** lime wedge · lime wedge on rim · lime wheel ·
lime wheel or wedge · lemon wheel · lemon slice · orange slice ·
orange slice or orange twist · orange wheel · grapefruit crescents ·
citrus wheel · dehydrated lime slice wheel · half an empty lime shell ·
grapefruit wedge · dehydrated blood orange slice wheel ·
lemon wheel and skewered maraschino cherry (like a sail)

**Fruit:** pineapple wedge ·
pineapple wedge (cut to resemble a bird's plumage) · pineapple wedge on rim ·
pineapple wedge on rim or edible flower · apricot wedge on rim ·
pineapple wheel · blackberry · blackberries · dried cranberries ·
dried apple slice · apple slice · banana chip · skewered raspberry ·
skewered blueberry · three skewered maraschino cherries and a pineapple frond ·
raspberries · fruit wedges · half an empty passion fruit shell

**Cherries:** brandied cherry · maraschino cherry · Luxardo maraschino cherry ·
skewered maraschino cherry · skewered brandied cherry ·
fruit stick (skewered pineapple cubes and a maraschino cherry) ·
fruit stick (skewered pineapple cube, raspberry and Luxardo maraschino cherry) ·
fresh cherries

**Herbs and leaves:** mint sprig · mint bouquet · rosemary sprig ·
rosemary sprig with dried cranberries, or orange slice · pineapple frond ·
kaffir lime leaves · cucumber wheels · edible violet · edible orchid ·
mint leaf · thyme sprig · basil leaf (floated) · thin cucumber slice (floated) ·
length of cucumber peel

**Spice and other:** grated nutmeg · grated chocolate · Angostura bitters ·
whipped cream · cinnamon stick · ginger wheel · stem ginger slice ·
skewered crystallised ginger · desiccated coconut · star anise (floated) ·
skewered green olive · skewered black olives ·
small stuffed dead Norwegian Blue · three coffee beans · cocoa powder ·
icing sugar · ice cone
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
  silent — that is the honest answer. A source that prints "N/A" has decided:
  `["no garnish"]`.
- **"Either of these" is ONE string with the "or" inside it** (`orange slice or
  orange twist`), because the list means all of them. Write the declared string
  if there is one, and the source's words if not. An "optionally" garnish is
  listed as normal; Helen trims at rewrite.
- **A garnish the method dusts on** (`cocoa powder`, `icing sugar`) is in the
  list and also gets the step `Dust with the <garnish>.` after the strain.

> ### A GARNISH IS NOT AN INGREDIENT, A RIM, OR SERVEWARE
>
> Things that look like garnishes and are not:
>
> - **Anything with an amount is an ingredient.** "3 dashes red creole-style
>   bitters", "5 drops of olive oil". Those go in `ingredients` with their
>   amount, and a method step puts them on top — "Drop the bitters on the top."
>   Helen wants units of alcohol counted, and nothing can count an ingredient
>   hiding in `garnish`.
> - **A rim is `serve.rim`.** "half-rim of sugar" is done to the glass before
>   the drink is built. But `lime wedge on rim` IS a garnish — that is a
>   placement, and a placement carries information.
> - **Serveware is `to_serve`.** Umbrellas, straws, stirrers, ladles, plastic
>   giraffes.
> - **Do not restate a method step.** One cocktail's garnish read "passion fruit
>   shell filled with overproof rum" while its own method already said "Fill
>   the passion fruit shell with rum and set on top of the drink." The garnish
>   is the OBJECT — `half an empty passion fruit shell` — never what is done
>   to it.

### `to_serve` — the declared items

One string, made of these items, separated by commas or full stops and ending
on a full stop: `"Straw."`, `"Plastic giraffes, paper umbrella, teeny
flamingos, more fire, more cinnamon sparkles."` Capitalise the first word;
the match ignores case. If the source serves the drink with something not
listed, write the source's words and flag it in your list.

<!-- vocab:to_serve start -->
**Serveware:** `straw` · `two straws` · `straws` · `stirrer` ·
`ladle and punch glasses`

**Decorations:** `plastic giraffes` · `paper umbrella` · `teeny flamingos` ·
`zero umbrellas` · `british flag`

**Fire:** `more fire` · `more cinnamon sparkles` · `optional fire if tiki mug`

**On the side:** `lime and sugar on the side` · `assemblage au choix`
<!-- vocab:to_serve end -->

**An ingredient is never a `to_serve` item.** "Shell filled with overproof rum" is an
ingredient with `as: "shell"` (§3); "champagne on the side" is an ingredient
with a `note`. What `to_serve` may say about fire is the flourish — `more
fire`, `optional fire if tiki mug` — never the rum.

---

## 4a. `serve` — how it is iced

**The ice that goes in the GLASS, never the ice in the shaker.** That
distinction is the whole of this field: "Shake all ingredients with ice" says
nothing about how the drink is served.

```yaml
serve:
  ice: "crushed"
```

**These values, and nothing else is legal:**

<!-- vocab:serve_ice start -->
- `none` — Served up, in an empty glass.
- `cubed` — Ordinary cubes, an ice-filled glass.
- `crushed` — Crushed or pebble ice.
- `cracked` — Cracked ice: cubes broken into large pieces, coarser than crushed.
- `large cube` — One big rock.
- `block` — A large block, in a punch bowl or a pitcher.
- `blended` — The ice is IN the drink, not under it.
<!-- vocab:serve_ice end -->

**OMIT THE WHOLE `serve:` KEY IF THE SOURCE DOES NOT SAY.** Absent means nobody
has decided; `ice: "none"` means somebody decided it is served up. Exactly the
distinction `garnish` draws between `[]` and `["no garnish"]`, and it is a real
one: one punch in the collection strains into a bowl and never says whether ice
goes in, where both its siblings say a large block. That is a question for
Helen, not a blank to fill with a default.

**`rim` is free text and rare.** `rim: "half-rim of sugar"`. Only if the source
rims the glass.

**There is no `chill` key and you must not invent one.** Helen: *"I
think it's implied that glasses should be chilled (except hot drinks
obviously). I am the user after all."* If the source does something MORE than
chilling — freezing a glass, rinsing it with absinthe — that is a method step in
its own right, which is what those cocktails already do.

---

## 5. `method` — the canonical build steps

**A closed vocabulary for the mechanical spine, free text for everything else.**
The test for whether a step belongs in the spine: **does its phrasing carry
information?** "with ice" versus "over ice" carries none. "other than the
champagne" carries all of it. So use a canonical string where one fits exactly,
and write the source's own words where none does.

**A sentence with `<X>` in it is a shape: fill the slot with the ingredient AS
THE RECIPE NAMES IT and nothing else changes.** "Shake everything except the
cola with ice" is written `Shake all ingredients other than the cola with ice.`;
"shake the first four" names the one left out instead. One slot only — a step
that needs two is free text.

<!-- vocab:method start -->
**Shake:** `Shake all ingredients with ice.` ·
`Shake all ingredients hard with ice.` · `Shake with ice.` ·
`Shake the remaining ingredients with ice.` ·
`Shake all ingredients other than the champagne with ice.`

**Short shake:** `Short shake all ingredients with three ice cubes.` ·
`Short shake the remaining ingredients with three ice cubes.` ·
`Short shake with three ice cubes.`

**Dry shake:** `Dry shake all ingredients.` · `Pour back into the shaker.` ·
`Dry shake.`

**Stir:** `Stir all ingredients with ice.` ·
`Stir the remaining ingredients with ice.` ·
`Stir all ingredients other than the champagne with ice.` · `Stir until cold.` ·
`Stir.` · `Stir all ingredients together.` ·
`Regal stir all ingredients with ice.` · `Stir until the glass frosts.`

**Churn:** `Churn with a bar spoon.` · `Churn again.` ·
`Repeat until the glass is full.`

**Blend and swizzle:** `Blend all ingredients until smooth.` ·
`Swizzle until the glass frosts.` ·
`Add the bitters then swizzle them into the top.`

**Strain:** `Strain.` · `Double strain.` · `Fine strain.` · `Dump.` · `Pour.`

**Build:** `Add all ingredients.` · `Add the remaining ingredients.` ·
`Fill the pitcher half full with ice cubes.` ·
`Fill the pitcher three-quarters full with ice cubes.` ·
`Fill with ice cubes.` · `Fill with crushed ice.` ·
`Half-fill with crushed ice.` · `Two-thirds fill with crushed ice.` ·
`Top with champagne.` · `Top with soda water.` · `Top with more crushed ice.` ·
`Heap crushed ice on top.`

**Rinse and rim:** `Rinse the glass with absinthe and dump.` ·
`Rinse the glasses with Campari.` ·
`Dip only half the rim in water (or tequila) then coarse salt.`

**Express:** `Express the twist over the drink then drop it in.` ·
`Express the twist over the drink then discard it.`

**Fire:** `Set alight.` · `Sprinkle the flame with cinnamon.`

**With a slot exclusion:**
`Shake all ingredients other than the <X> with ice.` ·
`Stir all ingredients other than the <X> with ice.` ·
`Short shake all ingredients other than the <X> with three ice cubes.` ·
`Dry shake all ingredients other than the <X>.` ·
`Add all ingredients other than the <X>.` ·
`Add the remaining ingredients other than the <X>.`

**With a slot top:** `Top with <X>.`

**With a slot add:** `Add the <X>.`

**With a slot dust:** `Dust with the <X>.`

**With a slot float:** `Float the <X> on top.` · `Drop the <X> on top.` ·
`Float the first <X>.`

**With a slot shell:**
`Fill the passion fruit shell with the <X> and set on top of the drink.` ·
`Fill the lime shell with the second <X> and set on top of the drink.` ·
`Fill the lime shell with the <X> and set on top of the drink.`
<!-- vocab:method end -->

What will catch you out:

- **A strain step is the technique and nothing else.** These strings, and
  there is no other: `Strain.` · `Fine strain.` · `Double strain.` · `Dump.` ·
  `Pour.` **Never name the glass, never name the ice.** The glass is in
  `glass:`, which draws the icon; the ice is in `serve.ice` (§4a). So:

  | The source says | You write |
  |---|---|
  | "fine strain into a chilled coupe" | `Fine strain.` + `glass: ["coupe"]` |
  | "strain into an ice-filled highball" | `Strain.` + `serve: {ice: "cubed"}` |
  | "strain into a rocks glass over a big cube" | `Strain.` + `serve: {ice: "large cube"}` |
  | "strain over crushed ice" | `Strain.` + `serve: {ice: "crushed"}` |

- **"Shake all ingredients" and "Shake" mean different things.** After a build
  step — a muddle, a rinse, an "add the rest" — "Shake with ice." means *shake
  what is in the shaker*, and that is a different instruction. **Read the step
  above before choosing.** If a rinse came first, the form is "Shake the
  remaining ingredients with ice."
- **A step may not start with "Serve" or "Garnish".** Those belong in
  `to_serve` and `garnish`. "Serve with a straw" becomes `to_serve: "Straw."`
- **A step may not start with "Express" either, and this one is not obvious.**
  Helen's ruling: a garnish of any citrus twist makes the recipe
  page add `Express the twist over the drink then drop it in.` as the last
  step, on its own — so a cocktail that writes it says one fact twice. If the
  source's last line expresses a twist, put the twist in `garnish:` and write
  no step. (`orange twist (discarded)` gets `...and discard it.` instead.)
  The two sentences are in the **Express** group above for recognition only;
  you never type either. **The exception is a step that expresses INTO the
  build** — "Express the oils of a coin-size grapefruit zest over the base of
  the stirring glass" — which is making the drink, not garnishing it: write it
  as the source does. Her suite allows "Express" before the stirring glass, the
  mixing glass, the shaker or the tin.
- **A shake means with ice** unless the source says dry: IBA's "Shake well and
  strain" is `Shake all ingredients with ice.`
- **A measured top-up keeps its measure**: "top with 60 ml champagne" is
  `amount: "60 ml"` and the step `Top with champagne.` `(top)` is only for a
  top with no figure.
- **Drop a caveat the cook can judge**, such as "omit if using wet ice" beside
  a water pour. Helen: trust the cook.
- **A step that carries information is free text even when a canonical one is
  close**: "Shake all ingredients other than the soda water with ice for two
  minutes." keeps its two minutes.
- **Everything expressive stays free text.** "Muddle the lime chunks hard with
  the sugar in the bottom of a shaker until the sugar has dissolved" cannot be
  collapsed without losing the drink. Don't try.

---

## 6. What the source cannot give you, and the one trap that has bitten

**A cocktail already in the collection may share a name and not be the same
drink.** This is the real hazard. Helen's Sazerac splits the spirit three ways across rye, bourbon and cognac and
pours absinthe and chilled water into the glass. Death & Co's rinses and
discards the absinthe, has no bourbon and no water, runs 3:1 rye to cognac, and
sweetens with demerara. Two of *her* suggested bottles are *its* specified
ones, which is exactly what made them look like one recipe.

They live side by side now, and her ruling was: *"name it 'Sazerac (Death &
Co)', leaving mine as simply 'Sazerac'."*

**So: compare the FORMULA, never the title.** If you are handed a cocktail recipe with a
classic name, say plainly in your list that it may already exist in a different
form, and title it plainly. **A source in parentheses is only for two drinks
that share a name**, and her repository adds it when that happens: Helen,
*"Let's only use a (source) where we have more than one."* A bracket that
describes the drink rather than its source stays: "Yellow Jacket (gin)".

**NEVER RECONSTRUCT A TRUNCATED RECIPE.** A photograph that stops mid-sentence,
a screenshot that ends below the ingredients. These do not announce themselves,
and the sibling recipes on the same page ending the same way is not evidence —
that is *their* wording. Transcribe what is in frame, write a `QQ` note saying
where the frame ended, and say so in your list. A cocktail she cannot make yet
is the right outcome; a guessed one is not.

**AN INFUSION OR A SYRUP ON ANOTHER PAGE IS MISSING DATA, not a detail.** If a
cocktail recipe pours "jalapeño-infused blanco tequila" and the infusion recipe is not in
frame, the drink cannot be made from what you have. Say so — steeping time and
chilli count decide whether it is pleasant or inedible, and neither is
inferable.

---

## 6a. `source` — the publications, and how each spells itself

**Most cocktails say `source: ""` and that is right.** Helen: *"I sort
of don't care about this. You can't copyright facts, and I am taking no prose
from anywhere. Some will be attributable to a big-name inventor, bar or maybe
hotel, and it's nice to note that, but I'm not going to sweat it."* So this is
never a field to fill in for the sake of filling it in, and there is no coverage
rule here or anywhere.

**It is a SPELLING list, for the handful that recur.** If the source you are
looking at is one of these, write the name exactly as it appears below:

<!-- vocab:sources start -->
- `Difford's` (also seen as Difford's Guide, Diffords, Diffords Guide)
- `Death & Co` (also seen as Death and Co, Death & Company, Death and Company)
- `Punch` (also seen as Punch Drink, punchdrink.com)
- `Alcohol Professor` (also seen as The Alcohol Professor, alcoholprofessor.com)
- `Thrillist` (also seen as thrillist.com)
- `kindredcocktails.com` (also seen as Kindred Cocktails, Kindred)
<!-- vocab:sources end -->

**Anything else is free text and stays free.** A compound attribution names two
sources on purpose — "Henry Craddock, Savoy Hotel, London / Death & Co" — and is
not a misspelling of either. A bar, a person, a book nobody has cited before:
write it as the source writes it.

**`source` is WHO and `source_url` is WHERE.** A URL in `source` is the one
mistake here that is a mistake: the recipe page prints a name where you put it,
and leaves the field that holds links empty beside it.

---

## 6b. Difford's Guide — how its page reads, and the rulings that are its alone

Most of what Helen sends is a paste of a Difford's recipe page. Its layout is
regular enough to be worth knowing, and some of her rulings apply to it and to
nothing else.

**Paste beats fetching.** A fetched page comes back in US fluid ounces with US
bottles, and a community recipe hides its method and garnish from a logged-out
reader. If a paste is missing a section, say so in your list; never fill it
from the fetched page without telling her.

**Ignore the furniture.** The navigation block, "Discerning Drinkers (N)",
"Serves: 1", "Read about cocktail measures and measuring", the brands-in-green
line. **A line beginning "Your notes:" is HELEN'S own note from her account**,
not the source's — it may change the recipe ("Aquavit instead of Kümmel"), so
follow it and say in your list that you did.

**THE GLASS IS THE "Select and pre-chill a ___ GLASS" LINE**, or "Serve in a
___". **Never the "Photographed in a ___" caption**, which names the prop in
the picture and often disagrees. Where the page offers two — "Coconut shell or
Collins glass" — list both.

**Helen's rulings, for Difford's only:**

| Difford's prints | You write |
|---|---|
| "Saline solution" or "Difford's Saline Solution (or merest pinch of salt)", any number of drops | `amount: "1 small pinch"`, `generic: "salt"`. She does not keep saline. Carry an "(optional)" across as `optional: true`. |
| "Sugar syrup 'rich' (2 sugar to 1 water) 65.0°Brix", or "Monin Pure Cane sugar syrup (65.0°brix, equivalent to 2 sugar to 1 water)" | `generic: "cane sugar syrup 2:1"`, no `QQ`, no note. The Brix and the brand are both dropped — this is the one bottle that gets no "Originally". |
| a bottle with its category in brackets, or a bottle alone | the whole printed string behind the `QQ`, and `note: "Originally <bottle>."` §3. |
| "(freshly squeezed)", "(chilled)", "(from freezer)", "(pasteurised)", an ABV or a proof beside an ingredient | dropped, unless it is the only thing that says WHICH category — "Straight rye whiskey (100 proof /50% alc./vol.)" keeps all of it behind the `QQ`, because the proof is what makes it her `bonded rye`. |

**An alternative printed in the ingredient line goes in that ingredient's note**: "Yellow
Chartreuse (or génépy liqueur)" is `note: "Or génépy liqueur."`; "Peychaud's or
other Creole-style bitters" is `note: "Or other Créole-style bitters."`

**Its build lines, and what each becomes:**

- "SHAKE first 4 ingredients with ice" names the ingredients by count. Name
  the one left out instead: `Shake all ingredients other than the <X> with ice.`
  Count carefully, and check that one the method adds later is not shaken too.
- "STRAIN into ice-filled glass (preferably over a large cube or chunk of block
  ice)" is `Strain.` and `serve: {ice: "large cube"}`. Plain "ice-filled glass"
  is `cubed`; "glass filled with crushed ice" is `crushed`; "chilled glass" is
  `none`.
- "EXPRESS … zest twist over the cocktail and use as garnish" is the twist in
  `garnish:` and no step; "…and discard" is the `(discarded)` twist. §5.
- A garnish it describes twice — "Prepare garnish of dehydrated blood orange
  slice wheel" and later "Garnish with orange slice" — takes the more specific
  wording.
- "Serve with a straw" is `to_serve: "Straw."`, never a step.
- "Dry blend … then add a 7oz scoop of crushed ice and blend" then "POUR into
  chilled glass" is `serve: {ice: "blended"}`: the ice is in the drink, whatever
  the pour step says. Helen's ruling.

## 6c. IBA — iba-world.com, the official cocktails

**No source.** Helen: *"No source."* `source: ""` and `source_url: ""`, and
the URL goes nowhere, not even your list.

- **"Chilled cocktail glass" (or "large cocktail glass") is her call per
  drink.** Write `glass: ["coupe", "martini"]` and a note labelled `QQ glass`:
  "QQ - IBA prints \"cocktail glass\". Both declared glasses are listed; Helen
  picks one per drink."
- **A bare "Gin" stays `QQ Gin`** unless the recipe says which. Helen: *"Not
  all IBA gin is London Dry, so QQ every time please unless you happen to know
  which it is!"*
- **"Sugar Syrup" with no ratio is `cane sugar syrup 1:1`**: her repository
  types it from her wordings table, so write `QQ Sugar Syrup` and it resolves.
- **A "N/A" garnish is `["no garnish"]`**: the source has decided.
- **"Cocktail cherry" is `maraschino cherry`.**
- **The ingredients go in build order** even where IBA lists them otherwise:
  its Old Fashioned lists the whiskey first and adds it last, so the whiskey is
  the last line.

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
- **A space between a number and its unit**: `"45 ml"`, never `"45ml"`, which
  her suite rejects.

**Accented words her house style declares.** The list is shared with the food
site, so most of it is culinary — but `crème`, `piña` and `purée` all turn up
in a cocktail recipe. A missing accent on one of these is a mechanical fault,
and her formatter fixes it in the fields she writes:

<!-- vocab:accents start -->
açaí · aïoli · béarnaise · béchamel · brûlée · café · canapé · canapés ·
chèvre · comté · consommé · crème · crémeux · créole · crêpe · crêpes ·
crudités · éclair · éclairs · entrecôte · flambé · fraîche · frisée · gâteau ·
glacé · gougère · gougères · gruyère · jalapeño · jalapeños · marinière ·
niçoise · pâté · pâtisserie · pâtissière · piña · purée · puréed · purées ·
ragù · rösti · sauté · sautés · sautéed · soufflé · soufflés · velouté
<!-- vocab:accents end -->

---

## 8. Never do these

- **Never guess a `generic`.** An EXACT match in §3a is a lookup and you write
  it; everything else is `QQ` and then the source's own words. A near-miss is a
  guess.
- **Never write a `suggestion`, and never leave the key out.** `suggestion: []`,
  every ingredient, every time — including when Helen says in the chat to use
  the source's bottles. The bottle the source names goes in that one's `note:`,
  as `"Originally <bottle>."`
- **Never write an `item:`.** There is no such field, and a file carrying one
  fails her schema outright.
- **Never draft a `tagline`.** A bare `"QQ"`, or Helen's own line if she gave
  you one for that drink. It is her voice on a published page and it is never
  yours, and never the source's.
- **Never leave an ingredient's `note` as a fragment.** A capital and a full
  stop.
- **Never float, rinse or muddle an ingredient in the method without its
  `as:`.**
- **Never invent `meta.ship`** — that is Helen's rating of a drink she has
  drunk. `"who knows"` is the only value an ingest writes, and **never `"QQ"`**:
  `QQ` is not in the ship vocabulary at all.
- **Never write `meta.made_before: true`** — same reason, one step earlier. A
  transcription cannot know whether she has poured the drink.
- **Never write a `mood:` of your own** — not a derived one, and not one of hers unless she named it in the chat for that drink (§2).
- **Never write a `character:`** — it hangs off a `generic` you are not writing.
- **Never leave a US unit**, and never convert a non-volumetric one.
- **Never write a bare number as an amount** without flagging it.
- **Never name the glass OR the ice inside a method step.** §5.
- **Never write `suggestion` as a bare string.** Always a list.
- **Never invent a `serve.chill`** — a chilled glass is assumed. §4a.
- **Never put an ingredient in `garnish`.** Anything with an amount belongs in
  `ingredients`.
- **Never give a note you add any label but `QQ`, and never write one as a bare
  string.** Both fields set, both beginning `QQ`. A recipe page titles a note
  with no label "note", which looks finished, so a note nobody has read would
  publish under a heading that says nothing is wrong. `QQ` is the title she can
  see and search for.
- **Never reconstruct a truncated method**, however obvious the pattern. But
  **do say in your list that it looks truncated.**
- **Never assume a familiar name means a familiar drink.**

> ### RUM WORDS THAT ARE NOT CATEGORIES
>
> Other people's recipes ask for these constantly. Helen: *"there
> is no such thing as navy rum or overproof navy rum"*, and *"there's no such
> thing as black rum, even though it will often be requested by other people's
> recipes."* `dark`, `light`, `gold` and `spiced` are out for the same reason —
> they describe colour or strength, not production, and colour is routinely
> adjusted with caramel.
>
> **This changes nothing about what you write**, because none of those words is
> in §3a, so the ingredient is a `QQ` either way. It matters for the WORDS after the
> QQ and for your list: transcribe the source's word faithfully — `generic: "QQ
> navy rum"` — and **say in your "what I could not know" list that the source
> asked for a category Helen does not use.** If the source also
> names a BOTTLE, say so in the same bullet — her bottle dictionary resolves
> the category from the bottle mechanically, and that is often the answer.

---

## 9. A worked example

**Source** (a book page, photographed):

> **JUNGLE BIRD**
> 1½ oz blackstrap rum · ¾ oz Campari · ½ oz lime juice · ½ oz simple syrup ·
> 1½ oz pineapple juice
> Shake all the ingredients over ice. Strain into a double old-fashioned glass
> filled with crushed ice. Garnish with a pineapple wedge and serve with a
> straw.

**What you hand back.** The file is `jungle-bird.md`, so the line above the
envelope is its issue title:

`ingest: jungle-bird`

````
<!-- ingest v1 cocktail -->

```yaml
---
title: "Jungle Bird"
tagline: "QQ"
glass:
  - "double old fashioned"
garnish:
  - "pineapple wedge"
meta:
  made_before: false
  ship: "who knows"
  rewritten: false
  awaiting_fix: false
  proofread: false
mood: []
ingredients:
  - amount: "45 ml"
    generic: "QQ blackstrap rum"
    suggestion: []
  - amount: "22.5 ml"
    generic: "Campari"
    suggestion: []
  - amount: "15 ml"
    generic: "lime juice"
    suggestion: []
  - amount: "15 ml"
    generic: "QQ simple syrup"
    suggestion: []
  - amount: "45 ml"
    generic: "pineapple juice"
    suggestion: []
serve:
  ice: "crushed"
method:
  - "Shake all ingredients with ice."
  - "Strain."
to_serve: "Straw."
notes:
  - label: "QQ"
    text: "QQ - two pours carry the source's words behind a `QQ`. `blackstrap` is a character rather than a category, and `simple syrup` does not say which sugar or what ratio. No `suggestion` is filled in."
source: "QQ"
source_url: ""
---
```

## What I could not know

- **Three ingredients are typed, two are not.** `Campari`, `lime juice` and `pineapple juice` are exact matches in the printed vocabulary, so they are lookups. "Blackstrap rum" is close to a category but `blackstrap` is a character, and "simple syrup" does not say which sugar or what ratio, so both carry the source's words behind a `QQ`.
- **No source recorded.** Tell me the book and I will write the citation.
- **Jungle Bird is a well-known drink and may already be in your collection in a different form.** Compare the formula, not the name.

## Fingerprint

jungle bird | 45 ml | 22.5 ml | 15 ml | 15 ml | 45 ml
````

Each bullet is one line, as §0 asks. `mood: []` gets no bullet: deriving it is
her repository's job (§10), not a question for her.

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
is published. Then, in order, in her repository:

1. **`resolve_pours.py`** types every `QQ` generic whose wording she has ruled
   on before, which is why §3 has you write the source's words exactly.
2. **`derive_cocktail_moods.py`** fills in `mood`, from the generics the first
   step wrote.
3. **Her formatter** puts the keys in page order.
4. **Her test suite** checks the glass, the garnish vocabulary, the units, the
   citation and the schema. Every mechanical fault you made shows up here and
   costs seconds.
5. She settles whatever `generic` is still a `QQ`, and any `suggestion`,
   **when she makes the drink**, which is the point at which she knows what
   went in the glass.

**So spend your care on the transcription.** A wrong garnish spelling is caught
by a test; a wrong amount is not, because 45 ml is as plausible as 22.5. The
numbers, the order of the build, and what the source actually said are the
things no machine of hers can recover once the page is gone.
