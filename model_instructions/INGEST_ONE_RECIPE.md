# Ingest one recipe — for a Claude with no repository

**You are being handed a recipe Helen found in the wild** — a photograph, a
screenshot, a URL, or pasted text — and asked to turn it into a file for her
recipe site. You do **not** have her repository, her test suite, or her data
files. Everything you need is in this document.

**Hand back one envelope per recipe, in the shape §0 fixes.** It carries:

- **One complete `.md` file**, ready to save into `_food_drafts/`.
- **A short "what I could not know" list** — every place you left a `QQ`, every
  figure you took on trust, anything the source cut off. A handful of bullets,
  not an essay. This is the part that makes the file cheap for her to finish.
- **A marker line and a fingerprint line**, which let her repository accept
  the file and recognise a duplicate.

**The bar is not perfection.** A file she can cook from is the goal; a file she
can cook from after two minutes' tidying is a fine result. Her repository has a
test suite and a formatter that will catch mechanical faults the moment the file
lands, so **spend your care on the things a machine cannot fix**: not inventing,
not garbling, and the quality of the rewritten method.

---

## 0. How to hand this back

Helen pastes what you write into a GitHub Issue on her private drafts
repository, `helen-triages-food-private`, titled `ingest: <slug>` and labelled
`ingest`. A script there parses it, so the shape matters: anything missing is a
rejection rather than a guess.

These parts, in this order, and nothing else at the top level:

1. `<!-- ingest v1 food -->`, as the first non-blank line. Exactly that.
2. **One** fenced `yaml` block, and only one — the complete file, front matter
   and all, beginning `---`.
3. A `## What I could not know` heading with your list under it, each bullet
   on one unwrapped line: the script reads every non-blank line as an item of
   its own. If there is genuinely nothing, write "nothing"; the heading is
   never absent.
4. A `## Fingerprint` heading, then one line: the title lowercased, then every
   amount in ingredient order, separated by ` | `. For the worked example in §9
   that is `crispy sage butter gnocchi | 500 g | 60 g | 12 | 1 | 30 g`.

**In a chat, show the whole envelope inside one outer fence of four
backticks**, so that its own three-backtick `yaml` fence copies as raw text
instead of closing the block, and put a line reading exactly `ingest: <slug>`
above it. That line is the issue title; the slug is the filename from §2
without its `.md`. The outer fence is there for copying and is not part of the
envelope. §9 shows a complete one.

**The fingerprint is how her repo tells a real duplicate from two dishes
sharing a name**, so the amounts must be the ones in the file, in the file's
own order, and an ingredient with no amount contributes nothing.

**If one message holds several recipes, hand back one of these per recipe**,
each complete on its own, in the order they appear. One envelope is one issue;
never fold two recipes into one block.

**If you can run code, check each envelope first** with her repository's own
parser, which needs nothing but Python and PyYAML:
`https://raw.githubusercontent.com/DeckOfPandas/helen-triages/main/scripts/envelope.py`.
`python3 envelope.py <file>` prints the filename and fingerprint it accepts,
or the one-line reason it would reject. Hand back nothing it rejects.

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
tagline: "QQ original If you love a one-pot stew, this bright and acidic number is a fun one to have up your sleeve. QQ Claude A one-pot stew that is bright and acidic."
source: "Adapted from Good Food, January 2026"
source_type: publication
serves: "4"
prep_time: "20 mins"
cook_time: "1 hr 30 mins"
main_ingredients: ["cavolo nero", "butter beans", "lemon"]
star_ingredient: "greens"
tags: ["soup"]
ingredient_groups:
  - name: "soup"
    items:
    - amount: "400 g"
      item: "butter beans, drained"
      note: "Jarred are worth it here."
    - amount: "2 large"
      item: "onions, sliced"
method:
  - "QQ original Heat the oven to 180C fan and grease a 20cm tin."
  - "QQ Claude Heat the oven to 180°C fan. Grease a 20 cm tin."
method_short:
  - ""
notes:
  - label: "QQ"
    text: "QQ - anything worth saying that is not a step."
meta:
  rewritten: false
  awaiting_fix: false
  proofread: false
---
```

**The filename** is the whole title, any "with …" clause included, lowercased,
hyphenated, ASCII only, `.md`.
"Charred Asparagus and Fennel Salad with Crispy Prosciutto" →
`charred-asparagus-and-fennel-salad-with-crispy-prosciutto.md`. Accents and
apostrophes are stripped in a filename even though they are kept in the
title. Her repo derives the same slug from your `title:` regardless, so the
name you give is a courtesy rather than a contract.

### Field by field

| Field | Rule |
|---|---|
| `title` | The dish's name. **`and`, never `&`.** Keep the source's own name unless it is unusable. **Keep its accents, and add any §6 lists that it lacks**: "Rich ragu" is titled "Rich Ragù". Helen: *"Accents in titles should be preserved, or added if missing."* |
| `tagline` | One line, **and it always begins `QQ `, because it is never yours.** **If the source has an intro, the tagline is a PAIR on one line, the same pair a method step is**: `"QQ original <the intro, verbatim> QQ Claude <your plain rewrite of it>"`. Helen: *"QQ original yes, then QQ claude rewrite, then I'll do my own and delete the other two."* The rewrite says what the intro says, shorter, by §3's rules — **it is not a joke, a pitch or a line of your own**, and you do not invent enthusiasm. **If the source has no intro, write `"QQ"` alone and draft nothing.** The tagline is Helen's voice on a published page, and the `QQ` is what stops somebody else's copy, or yours, reaching it under her name (her ruling: *"a drink without a tagline written by me gets a QQ, so I protect my voice in the public content"*). |
| `source` / `source_type` | Section 5. Both required, and they must agree. |
| `serves` **xor** `makes` | Never both. `makes` for things you produce (bakes, sauces, a spice blend); `serves` for what you portion out. Free text is fine — `"6–8 as a side"`, `"Depends on appetite"`. **Anything made as a batch is `makes`, even where the source prints "Serves 12"** over a tin of brownies. **A `makes` that opens with a number NAMES THE THING, straight after it: `"12 muffins"`, `"16 large brownies or 32 bite-sized"`, `"one 8-inch cake"`, never a bare `"12"`.** The scaler and the shopping list print that word. |
| `serves_estimate` | **An integer, PEOPLE, unquoted, and REQUIRED unless `serves:` opens with a number or `makes:` opens with a count of a named thing.** A `makes:` like "16 slices", "2 loaf cakes", "one 8-inch cake" or "950 ml" scales by itself and needs none: write the line that way where the source allows. "Depends on appetite", "Some" and a bare "12–16" or "9 or 16" name nothing countable and need one. **One figure, not an alternative:** "9 large or 16 small biscuits" reads as nine of something called "large", so write the one the source leads with ("9 biscuits"). Estimate from the recipe: a round cake is 12, a loaf 10, 18 cookies is 9 (two each). **`makes` is never read as people** however numeric it looks. **Where the source gives little to go on, estimate anyway and say so in your list**: the session with her repository confirms every estimate with her when the file lands — her rule: "Claudes can check with me if unsure." |
| `prep_time` / `cook_time` | `"20 mins"`, `"1 hr 30 mins"`, `"2 hrs"`. **Not in the source? Estimate it, as `"Estimated 20 mins"`, and say so in your list** — Helen: *"I would like "Estimated 10 mins" to be written, then our tidying scripts block promotion for recipes with estimated times."* Her repository refuses to promote a recipe whose time still says `Estimated`, so a guess never publishes. Write `"QQ"` only where you cannot estimate at all. `cook_time: "None"` for a genuinely uncooked dish. |
| `main_ingredients` | Section 4. Lowercase, a flat list. |
| `star_ingredient` | Section 4. **Optional** — leave it out rather than force one. |
| `tags` | Section 4. Only from the declared list. |
| `ingredient_groups` | Below. |
| `method` **xor** `method_groups` | Section 3 — the part that matters most. Flat `method:` for a recipe with one phase, `method_groups:` when the source has more. **Never both** — the layout renders one and silently drops the other. |
| `method_short` | Always exactly `[""]`. It means "not written", and Helen writes it herself. |
| `notes` | A list. **Every note you add is the `{label, text}` form with BOTH fields set, and both begin `QQ`** — Helen: "It's annoying for me to remember how to type YAML every time." The label is `"QQ"`, or `"QQ"`, a space and a short topic (`"QQ nutrition"`, `"QQ freezing"`); nothing else. She finds the `QQ`s, replaces the label with a real heading and the text with her own words, and never has to recall the shape. **A bare string note is not legal**: her suite refuses one. An empty pair (`label: ""`, `text: ""`) is the placeholder for a note you have nothing to put in yet, and the page does not print it. **If you have no note to add, write exactly that one empty pair — never `notes: []`**: it leaves Helen somewhere to type without recalling the shape. Three at most; more than that and the material wants to be prose. |
| a tip printed under the source's own label | **Transcribe the tip; drop the label.** Good Food runs its asides under a standing `gf tip` rubric, which on her page is an abbreviation nobody can expand, or one that reads as *gluten-free*: a false allergen claim. `source:` already carries the attribution. Keep the label only where it is doing work inside the sentence (*"the magazine likes Kallo"* stays). **Never carry an unexplained abbreviation across**: expand it while the source is in front of you, or drop it. |
| a nutrition box, or badges | **Ignore them entirely**: kcal, fat, carbs, "per serving", and badges such as "gluten free", "iron", "2 of 5-a-day", "V". Not a note, not a line in your list. Helen: *"Drop them and add clear instructions for ingestion to ignore these."* |
| a dietary claim — vegan, vegetarian, gluten-free, dairy-free | **Helen does not mark dietary restrictions.** Helen: *"I don't mark dietary restrictions."* Never add a tag, a note or a field for one, and never ask her to: there is no such filter and none is planned. A claim inside an intro you are quoting verbatim stays in that `QQ original`; it is not a question for your list. |
| a "you will need" list | **Ignore it.** Cake rings, thermometers, palette knives and foil are never an ingredient group or a note. Helen: *"the rule is "trust the cook"."* |
| page furniture | **Drop anything that sells something**: a show appearance, a ticket line or phone number, a book plug, a TV listing, a "next month" teaser, a web pointer, a "what to drink" box with bottles and prices. **Keep writing about the dish**: an essay, a bio of the cook, a boxed aside, which go in the body below the front matter. Helen: *"Drop ads, keep essays."* |
| a sidebar box with no list | A box such as "Kale crisps" or "Mastering perfect mash" becomes a file in the usual shape (quantities lifted from its text, per §2) and **has no body**: its words are already in the `QQ original` lines, and a body repeating them would publish the book's text unmarked. |
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
  - name: "dressing"              # a bare noun. NOT "for the dressing"
    items:
    - amount: "2 tbsp"          # the quantity ALWAYS goes here
      item: "red wine vinegar"  # never "2 tbsp red wine vinegar"
      note: "Sherry vinegar is better if you have it."
```

What to get right, in descending order of how much it costs if wrong:

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
  one phase — use `name: ""` or omit `name`. **With more than one group,
  EVERY group needs a name, the first included**: a main block left unnamed
  above a `to serve` prints as an unlabelled list followed by labelled ones,
  and her suite refuses it. **An unheaded first block is named for the dish or
  its main component**, so it reads "For the beef:", "For the pie:": `curry`,
  `pie`, `salad`, `beef`, `cake`. It is not a question for your list.

**How a group's `name` is printed, which is what decides how to write it.**
The page puts "For the " in front and a colon after, so `name: dressing` reads
"For the dressing:". Say the name after those two words before you write it.

- **A bare noun for a component**: `dressing`, `filling`, `white sauce`. Never
  `for the dressing` (it prints "For the for the dressing:").
- **`to …` for what happens at the end, and it is the one shape that prints as
  itself**: `to serve`, `to finish`, `to decorate`, `to garnish` read "To
  serve:", "To finish:", with no "For the". Use it where the source does
  ("To finish", "To decorate"), all lowercase. Do not turn it into a noun.
- **Not a bare verb.** `assemble` prints "For the assemble:". If the source
  heads a block of ingredients that way, `to assemble` is the name.

**Write every qualifier the source states.** Sugar type, egg size, butter salted
or unsalted, flour type, milk type, garlic form, ginger form, soy dark or light,
vinegar type, mustard type, chocolate percentage. The answer is printed on the
page in front of you, and one left off costs her a trip back to a source she
may no longer have. If the source is silent, write what it says and no more.

**Butter is the one qualifier whose silence you mark.** Where the source says
"butter" and not which, the item is `QQ butter` — Helen: *"Write QQ
butter in the ingredients list where it isn't specified."* Salted or unsalted
changes a bake and she always has to decide it, so the `QQ` puts the question
where she will see it. **Never choose for her**, in either direction: not
"salted" because it is a savoury dish, not plain "butter" because it is a
precise bake. Where the source does say — "unsalted butter", "slightly salted
butter" — that is reading, and you write it.

**The ingredient list is the source's own list. Never add to it from the
method.** Helen: *"We shouldn't list incidentals. We can trust the
cook."* "Pour over 75 ml boiling water" in step 1, "a pinch of salt", flour for
dusting the worktop, a bare "season": none of them becomes an ingredient line,
with a quantity or without one. The step still says it, in both halves of its
pair, and that is where the cook reads it. Everything the source's own list
prints is kept.

- **The one exception is a source with no ingredient list at all**, where the
  quantities exist only in the method. Lift them into one group, in the order
  the method meets them, and say in your list that you did.
- **A fat or flour the source's own list prints only for the tin or the pan
  keeps its line and gains `incidental: true`**: "butter, for greasing", "oil,
  for frying", "flour, for dusting". A real line with the use tacked on
  ("175 g butter, softened, plus extra for the tin") is not flagged: write it
  without the tail ("butter, softened"). Deep-frying oil is not flagged
  either: write it with no amount, as "vegetable oil, for deep frying".

  ```yaml
  ingredient_groups:
    - name: ""
      items:
      - item: "QQ butter, for greasing"
        incidental: true
  ```

  Her page and her shopping list then leave it out, while a reader avoiding
  butter can still find the dish. **Only those**: icing sugar to dust and
  mustard to brush are things a cook may have to buy, and they stay ordinary
  lines. A real ingredient with the use tacked on ("175 g butter, plus extra
  for the tin") is an ordinary line too. Never put a flagged item in
  `main_ingredients`.

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

### One `QQ original` per source step; split the rewrite where it is dense

**A source step is one `QQ original` line, however many actions it holds, and
as many `QQ Claude` lines under it as it needs.** Helen: *"I would like Claude
to split out method lines where the written method is unhelpfully dense, so
multiple QQ CLAUDE lines will be very helpful."* So a step that makes a dough,
proves it and lines a tin is one `QQ original` line holding the whole step,
verbatim, then a `QQ Claude` line for each thing a cook would stop and do.

- **The `QQ original` line is the source's whole step**, exactly as printed,
  however long. Never cut it.
- **Split the `QQ Claude` rewrite only where the step is dense.** A short step
  keeps one `QQ Claude` line; a step holding three stages gets three. Break at
  the points a cook would pause, not at every clause.
- **Never the other direction, and never a new order.** Two source steps are
  never merged under one `QQ original`, and nothing moves ahead of what the
  source put before it.
- **`method_groups` is grouping, not splitting.** A source step sits whole,
  with all its `QQ Claude` lines, inside the group it belongs to.

### `method_groups` — split the phases here, or nobody ever will

**If the source's method has phases, split it once, now.** A custard then a
meringue then the assembly; a marinade then a grill; a dough that proves while
a filling is made. This is the same rule the ingredient groups follow and for
the same reason: it is cheap while the whole recipe is in front of you and
expensive afterwards, when it means re-reading a page that may be gone.

`method_groups:` replaces `method:`; never write both. Every group needs a
`name` and a non-empty `steps`, and the pairs work exactly as they do above:

```yaml
method_groups:
  - name: "custard"
    steps:
    - "QQ original Whisk the yolks and sugar together until pale, then pour on the hot milk in a thin stream, whisking all the time."
    - "QQ Claude Whisk the yolks and sugar pale. Pour on the hot milk in a thin stream, whisking."
  - name: "assemble"
    steps:
    - "QQ original Spoon the custard over the sponge and leave it to set in the fridge for at least four hours."
    - "QQ Claude Spoon the custard over the sponge. Set in the fridge, 4 hours."
```

**`name:` is a bare noun** — `custard`, not `for the custard`. The template
supplies "For the " itself, so an article there renders as "For the for the
custard". `steps`, plural: a `step:` typo produces a group with no content and
no error.

**The trigger, because this is the field that gets skipped.** Named ingredient
groups above a flat method are common in her drafts, and the reverse almost
never happens. The cause is the schema: `ingredient_groups:` is the only
container for ingredients, so naming a second group is a small edit, while
grouping the method means switching fields. Left alone, the path of least
resistance writes grouped ingredients and a flat method every time.

So: **if you wrote more than one named ingredient group, the method almost
certainly has the same phases. Write `method_groups:` and give the groups the
same names.** A recipe whose ingredients split into `ragù` and `white sauce`
does not have a one-phase method.

**One phase means flat `method:`.** Do not invent a second group to use the
field, and do not split a recipe the source ran as one sequence — that is
restructuring somebody else's recipe, which §3's rules forbid everywhere else.
One unnamed ingredient group and a flat `method:` is the matching pair, and it
is correct for plenty of recipes.

### What the rewrite must NOT change

- **Never invent a temperature, a time or a quantity the source does not give.**
  If the source says only "heat the oven", your rewrite says only "heat the
  oven", and you note it in your list.
- **Never convert a temperature, and never guess which figure is the fan
  one.** The `QQ original` line keeps whatever the source prints, all of it.
  **The `QQ Claude` line gives the FAN figure alone, where the source LABELS
  one** — "200C/180C fan/gas 6" becomes "180°C fan" (Helen's ruling). **An
  unlabelled pair 20 degrees apart is conventional and fan**, whichever order
  it is printed in: "180C/160C/gas 4" becomes "160°C fan". Helen: *"Oven
  pairings when one temp is 20 degrees lower than the other mean conventional
  / fan, I'm just so sure."* Any other unlabelled pair, a single figure, or
  350°F: the rewrite keeps what the source has and your list says so.
  **The exception is a source Helen has ruled on**: check §5's list first.
- **Weights: old-style recipes and almost all baking keep their ounces.**
  Helen's ruling. Do not convert a baking recipe to metric. **A source in §5's
  list says which figure of a printed pair to keep**, and that wins, baking
  included.
- **Never merge, split or reorder steps.** A source step becomes exactly one
  pair — never fewer, never more, and never out of order.
- **A step that is really a note stays a step.** Freezer guidance mid-method is
  arguably misfiled, but moving it is restructuring somebody else's recipe.

### If the source is broken

Some sources are spliced, repeat themselves, or list an ingredient twice with
two different quantities. **Do not paraphrase a corrupted step** — deciding what
it meant is writing the recipe rather than rewriting it. Write the
`QQ original` line as it stands, write **no** `QQ Claude` line for it, and say
so clearly in your list. That is the correct outcome for such a file.

---

## 4. The closed vocabularies — these are complete, invent nothing

An undeclared tag or star ingredient fails her test suite. These lists are the
whole vocabulary. If nothing fits, **leave the field out** rather than coin a
term.

### `tags` — pick from these and no others

**Mood** — *what you feel like eating, a craving:*
<!-- vocab:tags:mood start -->
`bakes`, `carbs party`, `cheese-tastic`, `dessert`, `drinks`, `fakeaway`,
`fiddly and fun`, `herbivore-ish`, `hot snack`, `ice cream`, `knife and fork`,
`nibbles`, `one-handed food`, `salad`, `showstopper`, `soup`, `sweet snack`,
`virtuous`
<!-- vocab:tags:mood end -->

**Practicalities** — *what the occasion demands of you, regardless:*
<!-- vocab:tags:practicalities start -->
`breakfast`, `extras`, `festive`, `freezable`, `main`, `make-ahead`, `no-cook`,
`side`, `starter`
<!-- vocab:tags:practicalities end -->

Meanings you would not guess:

- **`main`** — this could be dinner. **Work it out by subtraction, last, once
  the other tags are chosen.** With any of `dessert`, `sweet snack`,
  `ice cream`, `drinks` or `nibbles`: never. With none of those and none of
  `bakes`, `extras`, `side`, `starter`, `breakfast` or `hot snack`: add
  `main`. With one of that second six, it depends on the dish (a quiche is a
  bake and dinner; a starter for two may be a main; a sauce is not), so decide
  and say which way you went in the hand-back list. **Savoury pancakes are
  breakfast or a snack, never `main`.** A frittata, baked eggs, a vegetable
  fritter or a griddle cake may be a `main`: decide, and say which way you
  went.
- **`side`** is a dish served beside a main: mash, a gratin, rice, roast veg,
  a slaw. **`extras`** is what is not a dish at all: a sauce, a stock, a
  pickle, a dough.
- **A star stays blank where the dish has two leads** (chicken and prawns).
  **`fruit` goes on a cake only where the fruit is the point**, never on a
  sponge that is only flavoured with lemon or orange.
- **`one-handed food`** — eat it curled on the sofa. Anything that rolls, spills
  or has to be chased is out. A soup never takes it, however thick.
- **`no-cook`** answers "can I put this on the table without cooking?" A spice
  blend is uncooked and a useless answer to that question, so it stays untagged.
  Melting chocolate is prep, not cooking: a fridge cake is `no-cook`.
- **`make-ahead`** — all or most of the dish can be made in advance of when
  you eat it: a convenience. **What is left on the day may be cooking, if it
  is no more than cooking**: roast potatoes boiled and coated the day before
  are make-ahead however long they roast. **A bake that merely keeps is not
  make-ahead** ("will keep three days in a tin" describes leftovers), and
  **an overnight marinade is not make-ahead** (the dish still has to be made
  at serving time).
- **`freezable`** and **`make-ahead`** are separate axes. Neither implies the
  other.
- **`drinks`** is anything drinkable that is not a cocktail — a cordial, a hot
  chocolate, a frappé.
- **`virtuous`** is narrow: lean protein, or genuinely veg-forward with a wine
  or citrus sauce doing the work. Not "contains a vegetable".
- **`herbivore-ish`** — a main where a vegetable, a pulse or a mushroom is the
  point of the dish and the reason to cook it: a whole roast celeriac,
  chargrilled radicchio, a leek tart. **Mains only: it is never on a side or
  an `extras` dish, and it requires `main`.** Not a promise of vegetarian:
  anchovy, bacon or chorizo in a supporting role is fine. Wider than
  `virtuous`; a dish can be both.
- **`knife and fork`** — a sit-down dinner eaten with a knife and fork and
  cooked properly: a roast, a braise, a whole fish, a vegetable centrepiece.
  About how it is eaten, not what is on the plate: it needs no animal.
- **`ice cream`** implies `dessert` and `make-ahead` — write all three.
  `herbivore-ish` implies `main`.

And the plainer ones, as Helen means them:

- **`bakes`** — a baked good out of the oven: cake, biscuit, bread, pastry.
  Not anything that merely goes in the oven. Her tests: *"would this appear on
  Great British Bake Off?"*, and is it what you make in cosy baking mode. A
  quiche, a tarte tatin, a baked cheesecake, a baked pudding, a crumble and
  pizza dough are in. A soufflé, a Wellington, a microwave mug cake and
  anything set in the fridge are not.
- **`dessert`** — a pudding course you serve at the table.
- **`sweet snack`** — small sweet things eaten by hand outside a meal:
  brownies, biscuits, fudge, truffles, a fairy cake, a scone, a muffin. Her
  test: *"would I serve it on a cake plate at 4 o clock after a long
  improving walk?"* **It has to be made as individual pieces: a whole cake
  served in slices is not one.**
- **`fiddly and fun`** — you make it because you want to potter: several
  components or stages, hands-on work, some precision. The PROCESS is the
  point. Pastry from scratch, anything piped, rolled or filled one at a time,
  an emulsion you have to mind. Slow is not fiddly: a six-hour stew is not.
- **`showstopper`** — it makes people gasp when it lands on the table. The
  RESULT, however little work it took. A dish may be this, `fiddly and fun`,
  both or neither.
- **`carbs party`** — the starch is the point: pasta, rice, potatoes, pies,
  dumplings.
- **`cheese-tastic`** — cheese is the pleasure of the dish, not a garnish.
  Feta does not count; burrata does.
- **`fakeaway`** — a home version of something you would order in.
- **`hot snack`** — small, hot and eaten between meals: toasties, fritters,
  things on toast.
- **`nibbles`** — finger food to pass round with drinks.
- **`breakfast`** — eaten in the morning.
- **`extras`** — not a dish by itself: sides, sauces, stocks, pickles, doughs.
- **`festive`** — Christmas, or another named feast, where the dish is the
  feast's own. **A Christmas feature or a December issue does not make a dish
  festive**, and the tag is used outside Christmas too: judge the dish, never
  the page it was printed on.
- **`starter`** — works as a first course at a dinner party.

**Two or three tags is normal. None is legitimate.** Being wrong here is cheap
for her to fix, so propose rather than agonise — but propose only from the list.

### `star_ingredient` — one of these, or omit

<!-- vocab:stars start -->
`beef`, `chocolate`, `duck`, `eggs`, `fruit`, `game`, `greens`, `lamb`,
`legumes`, `mushrooms`, `oily fish`, `pork`, `poultry`, `root veg`, `shellfish`,
`white fish`
<!-- vocab:stars end -->

**It is the one thing the recipe is ABOUT, and about a quarter of her collection
correctly leaves it blank.** A plain sponge, a dressing, a spice blend has no
hero. Egg as a binder or a leavening mechanism is not `eggs`; a dish that is
literally about the egg is. Squash and potatoes count as `root veg`. `greens`
is leaves, brassicas and beans eaten whole in the pod (kale, cabbage, sprouts,
broccoli, cauliflower, chard, spinach; green, fine and runner beans,
mangetout, sugar snaps); a tomato, courgette, pepper or leek dish has no star,
and a shelled bean, lentil or chickpea one is `legumes`. A pod-bean dish is
starred `greens` and the legumes filter finds it too, by itself. **If you find yourself
arguing for one, that is the signal to omit it.**

### `main_ingredients`

The findability index, and the one field where **generosity is right**.

- **Sweet and baking — the completeness test.** Everything whose absence breaks
  the recipe. No cap. Flour, butter, eggs and sugar go in.
- **Savoury — the substitution test.** Not "would this fail without it" but
  "would I improvise around a gap here": the protein, the fat or liquid that
  defines the character, anything you would have to go out and buy, the
  vegetable that is the point. **Herbs, citrus, cream or wine that the dish
  tastes of go in too**, however small the amount: they are what people skip.

**Be generous.** Helen's own recipes run to fourteen entries; ingested ones
average five, and she then adds to them by hand, which she has called "plainly
silly". A long spice list that defines a curry belongs in full.

Lowercase throughout. Cheeses use the bare name — `cheddar`, `feta`, `comté` —
keeping "cheese" only where the qualifier means nothing without it (`blue
cheese`, `cream cheese`). Butter is `butter`, never salted or unsalted (the
kind is settled at promotion), and a `QQ butter` line still earns it. Leave
out frying and greasing oil.

---

## 5. Citation — `source` and `source_type` must agree

`source_type` is one of exactly these words. `magazine` is not one of them; a
magazine is a `publication`.

<!-- vocab:source_types start -->
`author` · `book` · `joke` · `person` · `place` · `publication` · `unknown` ·
`website`
<!-- vocab:source_types end -->

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
looking at a magazine's one-off special. Cite the magazine: a `publication` if
you have its date, a `website` if you do not.

**Reproduce a publication's name as it spells itself.** `Cafe Delites` keeps its
missing accent — accenting it would misquote the title.

**Drop a page reference to a book nobody here holds** ("see page 167" off a
website). Keep one that points into the same book the recipe came from.

### Sources Helen has ruled on — read yours before you ask

Each of these settles a question for every recipe from that source, so it is
never a line in your list. Follow it, and say nothing about it. If a whole
batch comes from one of them, the index may say so once.

<!-- vocab:food_sources start -->
**Riverford Companions** — a `source:` containing "Riverford Companions":
- One oven figure is printed, with its gas mark (190°C/Gas 5). It is the conventional figure, so the fan figure is 20 lower: the rewrite says 170°C fan. Helen: *"Conventional: fan is 20 less"*

**Good Food** — a `source:` containing "Good Food":
- Both units are printed (100g/4oz). Write the metric figure only, bakes included, and do not list the dropped imperial. Helen: *"Metric only, bakes too"*
- An aside under the standing "gf tip" rubric is transcribed without the label: it is Good Food's tip, not gluten-free. Helen: *"Good Food tip, the magazine source I use a lot?"*

**Delia Smith** — a `source:` containing "Delia":
- Keep the ounces. Never convert a Delia recipe to metric.
<!-- vocab:food_sources end -->

---

## 6. House style — outside `QQ original` lines only

- **Quote every scalar string, and every list member.** `serves: "4"`, not
  `serves: 4`. `tags: ["soup"]`, not `tags: [soup]`. This applies to `title`,
  `tagline`, `source`, `prep_time`, `cook_time`, `star_ingredient`, `makes`,
  `serves`, to every entry in `main_ingredients` and `tags`, **and to every
  group's `name`** on both sides — `- name: "dressing"`, `- name: "Make the
  custard"`, never `- name: dressing`. It does not
  apply to `source_type`, or to the three booleans under `meta:` — quoting a
  boolean turns it into the *string* `"false"`, which breaks the publish gate.
- **En dash for a number range**: `3–4 mins`, `170–180°C`, `36–40% fat`. Not a
  hyphen. This one is by far the most common thing to get wrong.
- **Unicode fractions**: `½`, `¼`, `¾`. Not `1/2`.
- **A space between a number and its unit**, imperial included: `15 ml`,
  `400 g`, `20 cm`, `9 in`, `2 tbsp`. Not `15ml`. A temperature takes none:
  `180°C`.
- `°C` with the degree sign. Em dash for `--` in prose. `→` for arrows.
- **British spellings** throughout, and `yoghurt` with its h.
- **Times**: `20 mins`, `1 hr 30 mins`, `2 hrs` in the metadata fields;
  `mins` / `hours` / `seconds` in prose. Only numeric quantities abbreviate.
  **So a `QQ Claude` line says "1 hour 30 mins" and never "1 hr 30 mins".**
- Cross-recipe links, if you write one at all, are relative markdown:
  `[display text](../other-slug/)`. Never root-relative.
- **Accents on food words** — the two lists below. In prose and in the title,
  never in the filename and never in `source`.

**The accented spellings her house style declares:**

<!-- vocab:accents start -->
açaí · aïoli · béarnaise · béchamel · brûlée · café · canapé · canapés ·
chèvre · comté · consommé · crème · crémeux · créole · crêpe · crêpes ·
crudités · éclair · éclairs · entrecôte · flambé · fraîche · frisée · gâteau ·
glacé · gougère · gougères · gruyère · jalapeño · jalapeños · marinière ·
niçoise · pâté · pâtisserie · pâtissière · piña · purée · puréed · purées ·
ragù · rösti · sauté · sautés · sautéed · soufflé · soufflés · velouté
<!-- vocab:accents end -->

**And the words that keep NO accent**, which is the half worth reading twice —
every one of them looks French enough to accent, and accenting one is a
correction somebody then has to undo:

<!-- vocab:no_accent start -->
echalion · chorizo · gratin · julienne · vinaigrette · dauphinoise · mornay ·
confit · mole · poblano
<!-- vocab:no_accent end -->

Anything not on either list, leave as the source spells it.

**All of this is mechanically fixable in her repo and none of it is worth
agonising over.** Get it right where it is easy; do not let it slow down section 3.

---

## 7. Never do these

- **Never write an estimated time without the word `Estimated`.** A bare
  `"30 mins"` the source did not print reads as measured and publishes.
- **Never set `meta.rewritten` or `meta.proofread` to `true`.** Those are
  Helen's claims about her own reading, not yours.
- **Never remove a `QQ`**, of any kind, or delete a `QQ original` line.
- **Never coin a tag or a star ingredient.**
- **Never fill a silence in the source from general cooking knowledge.**
- **Never draft a tagline of your own.** An intro becomes the `QQ original` /
  `QQ Claude` pair; no intro is a bare `QQ`.
- **Never decide which butter.** Unstated is `QQ butter`.
- **Never split a source step into several pairs**, and never add an
  ingredient line the source's own list does not print.
- **Never reconstruct a truncated method**, even when the pattern is obvious.
- **Never convert a baking recipe's ounces to grams**, or a source's
  temperature to a different scale.

---

## 8. What happens to your file afterwards

Worth knowing, because it tells you where to spend effort and where not to.

Helen saves it into `_food_drafts/`, where it is private and unpublished. Her
test suite then checks the schema, the citation, the tags, the typography and
the ingredient spellings, and a formatter fixes quoting, dashes, unit spaces,
accents and the `meta:` block mechanically. It formats the dashes, unit
spaces and accents of your `QQ original` lines too, so transcribe those
exactly as printed and leave the formatting to it. **So a mechanical fault
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

**What you hand back.** The file is `crispy-sage-butter-gnocchi.md`, so the
line above the envelope is its issue title:

`ingest: crispy-sage-butter-gnocchi`

````
<!-- ingest v1 food -->

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
  - label: "QQ"
    text: "QQ - the source stops after the garlic. Nothing tells you when the parmesan goes in, or how the gnocchi and the butter meet."
meta:
  rewritten: false
  awaiting_fix: false
  proofread: false
---
```

## What I could not know

- **The recipe is cut off.** The source ends mid-build: the gnocchi are drained, the butter is made, and no step brings them together or uses the parmesan. Flagged in a note rather than finished.
- **No `tagline`.** The source has no intro, so a bare `QQ` and nothing drafted in its place.
- **The salted water in step 1 is not an ingredient line.** The method names it and the source's list does not, so it stays in the step. "Salt and pepper" is in the source's list, and is kept.
- **No `star_ingredient`.** Gnocchi is not on the list and nothing else is the hero.
- **`carbs party` is a proposal.** `cheese-tastic` is arguable on 30 g of parmesan; I did not add it.
- **"Medium heat" is the source's own**, and there is no oven, so no fan-temperature question arises here.

## Fingerprint

crispy sage butter gnocchi | 500 g | 60 g | 12 | 1 | 30 g
````

Each bullet is one line, as §0 asks. "Salt and pepper" has no amount, so the
fingerprint skips it.

Note what the rewrites did: dropped "large pot", "according to the packet
instructions", and the entire warning about burning the garlic — which "until
fragrant, 30 seconds" already prevents. Kept every end point: *until they
float*, *until crisp*, *until fragrant*.
