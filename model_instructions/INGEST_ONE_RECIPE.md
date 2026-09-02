# Ingest one recipe — for a Claude with no repository

**You are being handed a recipe Helen found in the wild** — a photograph, a
screenshot, a URL, or pasted text — and asked to turn it into a file for her
recipe site. You do **not** have her repository, her test suite, or her data
files. Everything you need is in this document.

**Hand back two things, in this order:**

1. **One complete `.md` file, in a single code block**, ready to save into
   `_food_drafts/`. Give the filename on the line above it.
2. **A short "what I could not know" list** — every place you left a `QQ`, every
   figure you took on trust, anything the source cut off. Four or five bullets,
   not an essay. This is the part that makes the file cheap for her to finish.

**The bar is not perfection.** A file she can cook from is the goal; a file she
can cook from after two minutes' tidying is a fine result. Her repository has a
test suite and a formatter that will catch mechanical faults the moment the file
lands, so **spend your care on the things a machine cannot fix**: not inventing,
not garbling, and the quality of the rewritten method.

---

## 1. The one rule that matters more than the rest

> **IS THE ANSWER IN THE SOURCE, OR IN HELEN'S HEAD?**
>
> In the source — the fan temperature, "large eggs", "unsalted butter", "golden
> caster sugar" — writing it down is READING, not judgement. Do it, unasked. You
> are the only one who will ever have this page open.
>
> In her head — her voice, her palate, whether she liked it, whether it freezes
> — leave it, and write `QQ`.
>
> **A silence in the source is never filled from general cooking knowledge.**

That last line is the whole risk. A wrong "whole milk" looks exactly as
confident as a right one. `QQ` is Helen's own placeholder, it costs nothing, and
she would far rather answer a question than discover an invention.

**Never reconstruct a truncated recipe.** A screenshot that stops below the
ingredient list, a photograph that ends mid-sentence — these do not announce
themselves, and the sibling recipes on the same page ending the same way is not
evidence. Transcribe what is in frame, then say in your list where the frame
ended.

---

## 2. The file

```yaml
---
title: "Lemony Cavolo Nero and Butter Bean Soup"
tagline: "It's fun to have a one-pot stew that is bright and acidic."
source: "Adapted from Good Food, January 2026"
source_type: publication
serves: "4"
prep_time: "20 mins"
cook_time: "1 hr 30 mins"
main_ingredients: ["cavolo nero", "butter beans", "lemon"]
star_ingredient: "greens"
tags: ["soup"]
ingredient_groups:
  - name: soup
    items:
    - amount: "400 g"
      item: "butter beans, drained"
      note: "Jarred are worth it here."
    - amount: "2 large"
      item: "onions, sliced"
method:
  - "QQ original Heat the oven to 180C fan and grease a 20cm tin."
  - "QQ Claude Heat the oven to 180°C fan. Grease a 20cm tin."
method_short:
  - ""
notes:
  - "Anything worth saying that is not a step."
meta:
  rewritten: false
  awaiting_fix: false
  proofread: false
---
```

**The filename** is the title's head clause — the part before any "with …" —
lowercased, hyphenated, ASCII only, `.md`. "Charred Asparagus and Fennel Salad
with Crispy Prosciutto" → `charred-asparagus-fennel-salad.md`. Accents are
stripped in a filename even though they are kept in the title.

### Field by field

| Field | Rule |
|---|---|
| `title` | The dish's name. **`and`, never `&`.** Keep the source's own name unless it is unusable. |
| `tagline` | One line of prose, no full stop needed. If the source has an intro sentence worth keeping, adapt it. If not, write `"QQ"` — do **not** invent enthusiasm. |
| `source` / `source_type` | Section 5. Both required, and they must agree. |
| `serves` **xor** `makes` | Never both. `makes` for things you produce (bakes, sauces, a spice blend); `serves` for what you portion out. Free text is fine — `"6–8 as a side"`, `"Depends on appetite"`. |
| `prep_time` / `cook_time` | `"20 mins"`, `"1 hr 30 mins"`, `"2 hrs"`. Not in the source? `"QQ"`. **Never estimate one** — an invented time publishes, a `QQ` does not. `cook_time: "None"` for a genuinely uncooked dish. |
| `main_ingredients` | Section 4. Lowercase, a flat list. |
| `star_ingredient` | Section 4. **Optional** — leave it out rather than force one. |
| `tags` | Section 4. Only from the declared list. |
| `ingredient_groups` | Below. |
| `method` | Section 3 — the part that matters most. |
| `method_short` | Always exactly `[""]`. It means "not written", and Helen writes it herself. |
| `notes` | A list. Each entry is a bare string, or `{label: "Sinking", text: "…"}`. Three at most; more than that and the material wants to be prose. |
| `meta` | Exactly these three keys, in this order, all `false`. See below. |

**`meta:` is three flags, in that order, and on a new file all three are
`false`.** `rewritten` and `proofread` are Helen's own claims about her own
work — you never set either `true`. `awaiting_fix: false` is what lets a page
publish once it is finished, and `false` is the only value that works: a missing
key, or `"false"` in quotes, holds the page back silently. Write
`awaiting_fix`, with an underscore, never a hyphen.

### `ingredient_groups`

```yaml
ingredient_groups:
  - name: dressing              # a bare noun. NOT "for the dressing"
    items:
    - amount: "2 tbsp"          # the quantity ALWAYS goes here
      item: "red wine vinegar"  # never "2 tbsp red wine vinegar"
      note: "Sherry vinegar is better if you have it."
```

Three things to get right, in descending order of how much they cost if wrong:

- **The quantity belongs in `amount:`, never inside `item:` text.** The page
  highlights `amount` and does not scan `item` for a leading number, so
  `item: "~1 tbsp tamarind paste"` renders as flat unstyled text with no error
  anywhere. `item: "zest and juice of 1 lime"` is the same fault — write
  `amount: "1"`, `item: "lime, zest and juice"`.
- **Size words go with the count**: `amount: "2 large"`, `item: "onions"`. Not
  `item: "large onions"`.
- **Split the groups if the source does.** A custard, then a meringue, then the
  assembly. This is cheap while you have the whole recipe in front of you and
  expensive afterwards. One unnamed group is fine if the recipe genuinely has
  one phase — use `name: ""` or omit `name`.

**Write every qualifier the source states.** Sugar type, egg size, butter salted
or unsalted, flour type, milk type, garlic form, ginger form, soy dark or light,
vinegar type, mustard type, chocolate percentage. Two thirds of the drafts
already in her collection are missing one of these, every answer was printed on
the page they came from, and every one now costs her a trip back to a source she
may no longer have. If the source is silent, write what it says and no more.

---

## 3. The method — the half Helen actually cares about

**Every method step is a PAIR of consecutive entries.**

```yaml
method:
  - "QQ original Once the butter has melted and is foaming, add the sage leaves and fry them for 30 seconds or so until they are crisp, then remove them to a plate lined with kitchen paper."
  - "QQ Claude Fry the sage in the foaming butter, 30 seconds, until crisp. Drain on kitchen paper."
```

- **`QQ original` is the source, verbatim.** Same punctuation, same "minutes"
  instead of "mins", same missing degree sign. Do not tidy it. It is there so
  Helen can check your rewrite against what it came from.
- **`QQ Claude` is your rewrite**, and it is held to normal house style.

`QQ` is Helen's marker for "not yet in my voice". It stays on the file
indefinitely; she takes it off one step at a time as she reads. Never remove
one, and never delete a `QQ original` line — pruning those is her own edit,
made when she is about to cook.

### How to write the rewrite

Helen, in her own words: **"short sentences, clear verbs, clear end points, wry
but rarely or never indulgent."** She also said "Gordon Ramsay-style writing",
and meant the terseness rather than the shouting.

**The organising principle is TRUST THE COOK.** Cut the consequence that follows
from the instruction. Cut the warning the verb already carries. Where a term
exists, name the technique instead of describing what it looks like.

Her own edits to earlier rewrites, which are the best calibration available:

| Too much | Hers |
|---|---|
| "Coat the tofu in cornflour, shaking off the excess, then fry until crisp and golden all over" | **"Coat the tofu in cornflour. Fry until crisp."** |
| "Scatter over the greens and serve immediately, while the coating is still crisp" | **"Top with the greens, and serve immediately."** |
| "Strain the stock through a fine sieve and discard the vegetables and bones" | **"Strain, discarding the solids."** |
| "Taste the stock and dilute it with water if it is very salty" | **"Taste the stock and dilute if needed."** |
| "Cook the butter until it smells nutty and turns golden brown, but not as far as beurre noisette" | **"Get 9/10 of the way to beurre noisette."** |
| "Stir in the yoghurt and warm through gently, taking care not to let it boil or it will split" | **"Stir in the yoghurt to warm."** |
| "Take off the heat, cover, and leave to stand for 4–6 minutes" | **"Stand covered off the heat. 4–6 mins."** |
| "After an hour, check the potatoes — if they have sunk below halfway, move them up" | **"After an hour, check the potatoes sit higher than half way."** |

Note what survives every cut: **the end point**. "Until crisp", "until the
juices run clear at the thickest part", "until a knife slides into the core".
Those are the sentences that make a recipe cookable, and they are never
scaffolding. What goes is the explanation of why, the reassurance, and the
remedy for a problem the instruction already prevents.

A step may be two short sentences. It is often better as two.

### What the rewrite must NOT change

- **Never invent a temperature, a time or a quantity the source does not give.**
  If the source says only "heat the oven", your rewrite says only "heat the
  oven", and you note it in your list.
- **Never convert a temperature.** Whatever pair the source prints, keep. If it
  gives 170°C and gas 3, keep both as it has them. If it gives 350°F, keep
  350°F. Guessing which figure of a pair is the fan one needs the original, and
  they are not always in the same order.
- **Weights: old-style recipes and almost all baking keep their ounces.**
  Helen's ruling. Delia in particular. Do not convert a baking recipe to metric.
- **Never merge or reorder steps.** One source step, one pair.
- **A step that is really a note stays a step.** Freezer guidance mid-method is
  arguably misfiled, but moving it is restructuring somebody else's recipe.

### If the source is broken

Some sources are spliced, repeat themselves, or list an ingredient twice with
two different quantities. **Do not paraphrase a corrupted step** — deciding what
it meant is writing the recipe rather than rewriting it. Write the
`QQ original` line as it stands, write **no** `QQ Claude` line for it, and say
so clearly in your list. Three files in her collection are in exactly this
state and it is the correct outcome for them.

---

## 4. The closed vocabularies — these are complete, invent nothing

An undeclared tag or star ingredient fails her test suite. These lists are the
whole vocabulary. If nothing fits, **leave the field out** rather than coin a
term.

### `tags` — pick from these 22 and no others

**Mood** — *what you feel like eating, a craving:*
<!-- vocab:tags:mood start -->
`bakes`, `carbs party`, `cheese-tastic`, `dessert`, `drinks`, `fakeaway`,
`hot snack`, `ice cream`, `nibbles`, `one-handed food`, `salad`, `showstopper`,
`soup`, `sweets`, `virtuous`
<!-- vocab:tags:mood end -->

**Practicalities** — *what the occasion demands of you, regardless:*
<!-- vocab:tags:practicalities start -->
`breakfast`, `extras`, `festive`, `freezable`, `make-ahead`, `no-cook`,
`starter`
<!-- vocab:tags:practicalities end -->

Meanings you would not guess:

- **`one-handed food`** — eat it curled on the sofa. Anything that rolls, spills
  or has to be chased is out. Thick spoonable soups are in; noodle soups are not.
- **`no-cook`** answers "can I put this on the table without cooking?" A spice
  blend is uncooked and a useless answer to that question, so it stays untagged.
- **`make-ahead`** — a substantial part of the dish is genuinely finished ahead.
  **A bake that merely keeps is not make-ahead** ("will keep three days in a
  tin" describes leftovers), and **an overnight marinade is not make-ahead**
  (real advance work, but the whole dish is still cooked at serving time).
- **`freezable`** and **`make-ahead`** are separate axes. Neither implies the
  other.
- **`drinks`** is anything drinkable that is not a cocktail — a cordial, a hot
  chocolate, a frappé.
- **`virtuous`** is narrow: lean protein, or genuinely veg-forward with a wine
  or citrus sauce doing the work. Not "contains a vegetable".
- **`ice cream`** implies `dessert` and `make-ahead` — write all three.

**Two or three tags is normal. None is legitimate.** Being wrong here is cheap
for her to fix, so propose rather than agonise — but propose only from the list.

### `star_ingredient` — one of these 14, or omit

<!-- vocab:stars start -->
`beef`, `chocolate`, `duck`, `eggs`, `fruit`, `game`, `greens`, `lamb`,
`oily fish`, `pork`, `poultry`, `root veg`, `shellfish`, `white fish`
<!-- vocab:stars end -->

**It is the one thing the recipe is ABOUT, and about a quarter of her collection
correctly leaves it blank.** A plain sponge, a dressing, a spice blend has no
hero. Egg as a binder or a leavening mechanism is not `eggs`; a dish that is
literally about the egg is. Squash counts as `root veg`. **If you find yourself
arguing for one, that is the signal to omit it.**

### `main_ingredients`

The findability index, and the one field where **generosity is right**.

- **Sweet and baking — the completeness test.** Everything whose absence breaks
  the recipe. No cap.
- **Savoury — the substitution test.** Not "would this fail without it" but
  "would I improvise around a gap here": the protein, the fat or liquid that
  defines the character, anything you would have to go out and buy, the
  vegetable that is the point.

**Be generous.** Helen's own recipes run to fourteen entries; ingested ones
average five, and she then adds to them by hand, which she has called "plainly
silly". A long spice list that defines a curry belongs in full.

Lowercase throughout. Cheeses use the bare name — `cheddar`, `feta`, `comté` —
keeping "cheese" only where the qualifier means nothing without it (`blue
cheese`, `cream cheese`). Leave out frying and greasing oil.

---

## 5. Citation — `source` and `source_type` must agree

`source_type` is one of exactly these words. `magazine` is not one of them; a
magazine is a `publication`.

<!-- vocab:source_type start -->
`author` · `book` · `joke` · `person` · `place` · `publication` · `unknown` ·
`website`
<!-- vocab:source_type end -->

| `source_type` | `source` shape | Example |
|---|---|---|
| `publication` | `Adapted from <title>, <date>` — **always dated** | `Adapted from Good Food, January 2026` |
| `publication` | with an author | `Adapted from Good Food, January 2026, Sarah Cook` |
| `book` | `Adapted from <title>, <Author>` | `Adapted from French Provincial Cooking, Elizabeth David` |
| `book` | or possessively | `Adapted from Delia Smith's Book of Cakes` |
| `website` | `Adapted from <site>, recipe <Author>` — **never dated** | `Adapted from RecipeTin Eats, recipe Nagi` |
| `website` | author not recorded | `Adapted from indianhealthyrecipes.com` |
| `author` | work not recorded | `Adapted from Delia Smith` |
| `person` | someone Helen knows — a bare label | `Henry`, `Grandma Kath` |
| `place` | a bare label | `France` |
| `joke` | free text | `Bitter experience` |
| `unknown` | exactly `QQ` | `QQ` |

**The date is what separates a `publication` from a `website`.** A publication
must carry one; a website must not. A year alone is a complete date. Some
titles are genuinely both — *Good Food* has a print issue and a site — so **if
you have no date, it is the website.**

**A book must name its author**, in one shape or the other. There is no
authorless-book form: Helen's ruling is *"I can't imagine knowing the name of a
book but not its author."* If you have a title and no author, you are probably
looking at a magazine's one-off special, which is a dateless `publication`.

**Reproduce a publication's name as it spells itself.** `Cafe Delites` keeps its
missing accent — accenting it would misquote the title.

**Drop a page reference to a book nobody here holds** ("see page 167" off a
website). Keep one that points into the same book the recipe came from.

---

## 6. House style — outside `QQ original` lines only

- **Quote every scalar string, and every list member.** `serves: "4"`, not
  `serves: 4`. `tags: ["soup"]`, not `tags: [soup]`. This applies to `title`,
  `tagline`, `source`, `prep_time`, `cook_time`, `star_ingredient`, `makes`,
  `serves`, and to every entry in `main_ingredients` and `tags`. It does not
  apply to `source_type`, or to the three booleans under `meta:` — quoting a
  boolean turns it into the *string* `"false"`, which breaks the publish gate.
- **En dash for a number range**: `3–4 mins`, `170–180°C`, `36–40% fat`. Not a
  hyphen. This one is by far the most common thing to get wrong.
- **Unicode fractions**: `½`, `¼`, `¾`. Not `1/2`.
- `°C` with the degree sign. Em dash for `--` in prose. `→` for arrows.
- **British spellings** throughout.
- **Times**: `20 mins`, `1 hr 30 mins`, `2 hrs` in the metadata fields;
  `mins` / `hours` / `seconds` in prose. Only numeric quantities abbreviate.
- Cross-recipe links, if you write one at all, are relative markdown:
  `[display text](../other-slug/)`. Never root-relative.
- **Accents on food words** — the two lists below. In prose only, never in the
  filename and never in `source`.

**The accented spellings her house style declares:**

<!-- vocab:accents start -->
açaí · aïoli · béarnaise · béchamel · brûlée · café · canapé · canapés ·
chèvre · comté · consommé · crème · crémeux · crêpe · crêpes · éclair ·
éclairs · entrecôte · flambé · fraîche · frisée · gâteau · glacé · gougère ·
gougères · gruyère · jalapeño · jalapeños · marinière · niçoise · pâté ·
pâtisserie · pâtissière · piña · purée · puréed · purées · ragù · rösti ·
sauté · sautés · sautéed · soufflé · soufflés · velouté
<!-- vocab:accents end -->

**And the words that keep NO accent**, which is the half worth reading twice —
every one of them looks French enough to accent, and accenting one is a
correction somebody then has to undo:

<!-- vocab:no_accent start -->
echalion · chorizo · gratin · julienne · vinaigrette · dauphinoise · mornay ·
confit
<!-- vocab:no_accent end -->

Anything not on either list, leave as the source spells it.

**All of this is mechanically fixable in her repo and none of it is worth
agonising over.** Get it right where it is easy; do not let it slow down section 3.

---

## 7. Never do these

- **Never write `Estimated 30 mins`** or any invented time. Banned outright.
- **Never set `meta.rewritten` or `meta.proofread` to `true`.** Those are
  Helen's claims about her own reading, not yours.
- **Never remove a `QQ`**, of any kind, or delete a `QQ original` line.
- **Never coin a tag or a star ingredient.**
- **Never fill a silence in the source from general cooking knowledge.**
- **Never reconstruct a truncated method**, even when the pattern is obvious.
- **Never convert a baking recipe's ounces to grams**, or a source's
  temperature to a different scale.

---

## 8. What happens to your file afterwards

Worth knowing, because it tells you where to spend effort and where not to.

Helen saves it into `_food_drafts/`, where it is private and unpublished. Her
test suite then checks the schema, the citation, the tags, the typography and
the ingredient spellings, and a formatter called `/tidy-drafts` fixes quoting,
dashes, accents and the `meta:` block mechanically. **So a mechanical fault
costs her seconds.**

What no machine of hers can recover is a step you garbled, a quantity you
guessed, or a qualifier you invented — because the page it came from is gone by
then, and a confident wrong answer is indistinguishable from a right one. That
asymmetry is the reason for every "never" above.

She reads your rewrites before she cooks from them. Write for that reader: a
competent cook, in her own kitchen, wanting to be told what to do and nothing
else.

---

## 9. A worked example

**Source** (a website, no date, author "Nagi"):

> ### Crispy Sage Butter Gnocchi
> Serves 2. 5 minutes prep, 10 minutes cooking.
> 500g fresh potato gnocchi · 60g unsalted butter · 12 sage leaves ·
> 1 garlic clove, finely minced · 30g finely grated parmesan · salt and pepper
>
> 1. Bring a large pot of water to the boil and add plenty of salt. Add the
>    gnocchi and cook according to the packet instructions, usually about 2 to
>    3 minutes — they are done when they float to the surface. Drain them well.
> 2. Meanwhile, melt the butter in a large frying pan over medium heat. Once the
>    butter has melted and is foaming, add the sage leaves and fry them for 30
>    seconds or so until they are crisp, then remove them to a plate lined with
>    kitchen paper.
> 3. Add the minced garlic to the butter and cook for about 30 seconds until
>    fragrant, being careful not to let it burn or it will turn bitter.

`crispy-sage-butter-gnocchi.md`

```yaml
---
title: "Crispy Sage Butter Gnocchi"
tagline: "QQ"
source: "Adapted from RecipeTin Eats, recipe Nagi"
source_type: website
serves: "2"
prep_time: "5 mins"
cook_time: "10 mins"
main_ingredients: ["gnocchi", "sage", "butter", "parmesan"]
tags: ["carbs party"]
ingredient_groups:
  - name: ""
    items:
    - amount: "500 g"
      item: "fresh potato gnocchi"
    - amount: "60 g"
      item: "unsalted butter"
    - amount: "12"
      item: "sage leaves"
    - amount: "1"
      item: "garlic clove, finely minced"
    - amount: "30 g"
      item: "parmesan, finely grated"
    - item: "salt and pepper"
method:
  - "QQ original Bring a large pot of water to the boil and add plenty of salt. Add the gnocchi and cook according to the packet instructions, usually about 2 to 3 minutes — they are done when they float to the surface. Drain them well."
  - "QQ Claude Boil the gnocchi in well-salted water, 2–3 mins, until they float. Drain well."
  - "QQ original Meanwhile, melt the butter in a large frying pan over medium heat. Once the butter has melted and is foaming, add the sage leaves and fry them for 30 seconds or so until they are crisp, then remove them to a plate lined with kitchen paper."
  - "QQ Claude Meanwhile melt the butter over medium heat. Fry the sage in the foaming butter, 30 seconds, until crisp. Drain on kitchen paper."
  - "QQ original Add the minced garlic to the butter and cook for about 30 seconds until fragrant, being careful not to let it burn or it will turn bitter."
  - "QQ Claude Add the garlic and cook 30 seconds, until fragrant."
method_short:
  - ""
notes:
  - "QQ - the source stops after the garlic. Nothing tells you when the parmesan goes in, or how the gnocchi and the butter meet."
meta:
  rewritten: false
  awaiting_fix: false
  proofread: false
---
```

**What I could not know:**

- **The recipe is cut off.** The source ends mid-build: the gnocchi are drained,
  the butter is made, and no step brings them together or uses the parmesan.
  Flagged in a note rather than finished.
- **No `tagline`.** The source's intro was marketing copy, so `QQ`.
- **No `star_ingredient`.** Gnocchi is not one of the fourteen and nothing else
  is the hero.
- **`carbs party` is a proposal.** `cheese-tastic` is arguable on 30 g of
  parmesan; I did not add it.
- **"Medium heat" is the source's own**, and there is no oven, so no
  fan-temperature question arises here.

Note what the rewrites did: dropped "large pot", "according to the packet
instructions", and the entire warning about burning the garlic — which "until
fragrant, 30 seconds" already prevents. Kept every end point: *until they
float*, *until crisp*, *until fragrant*.
