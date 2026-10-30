# Source attribution — the spec

GitHub issue #406. Every ruling below is Helen's.

**If you are ingesting food recipes, this is the contract.** Every recipe
carries two front matter keys, `source` and `source_type`, and they must agree.

```yaml
source: "Adapted from Gordon Ramsay's Ultimate Cookery Course"
source_type: book
```

`tests/test_source_attribution.py` checks every published recipe and every
draft, drafts included on purpose: a draft that drifts is a promotion that
drifts. `source_type` is in `REQUIRED` in `tests/test_front_matter.py`, so a
recipe without one fails too. Each rule below says where the test holds it; a
rule marked "by hand" has no check and is still the rule.

A magic-bag entry carries neither key: it is Helen's own dish, and none of the
eight types means "I made it up".

---

## The eight types

`source_type` is one of exactly these. It is not free text. `magazine` is the
near-miss: it is `publication`.

| `source_type` | What it is | `source` shape | Example |
|---|---|---|---|
| `publication` | A print issue, always dated | `Adapted from <title>, <date>` | `Adapted from Good Food, January 2026` |
| `publication` | …with a named author | `Adapted from <title>, <date>, <Firstname Lastname>` | `Adapted from Good Food, January 2026, Sarah Cook` |
| `book` | A named book | `Adapted from <title>, <Firstname Lastname>` | `Adapted from French Provincial Cooking, Elizabeth David` |
| `book` | …whose author owns the title | `Adapted from <Author>'s <title>` | `Adapted from Delia Smith's Book of Cakes` |
| `book` | …read as an extract in a magazine | either book shape, then `, via <magazine>, <date>` | `Adapted from Chilli Notes, Thomasina Miers, via Good Food, March 2015` |
| `website` | A site or blog, never dated | `Adapted from <site>, recipe <Firstname Lastname>` | `Adapted from RecipeTin Eats, recipe Nagi` |
| `website` | …author not recorded | `Adapted from <site>` | `Adapted from indianhealthyrecipes.com` |
| `author` | A published cook, work not recorded | `Adapted from <Name>` | `Adapted from Delia Smith` |
| `person` | Someone Helen knows | a bare label | `Henry`, `Grandma Kath`, `Good friend Daniel` |
| `place` | A place | a bare label | `France` |
| `joke` | The experience that produced the recipe | free text | `Bitter experience` |
| `unknown` | Nobody has established it yet | exactly `QQ` | `QQ` |
| `unknown` | …and Helen has ruled that nobody will | exactly `unknown` | `unknown` |

### A book names its author, in one shape or the other

    Adapted from Feed Your Soul, Wagamama          title, then author
    Adapted from Delia Smith's Book of Cakes       author, possessively, then title

Both shapes carry the author. Use whichever reads as English: `Delia Smith's
Book of Cakes`, never `Book of Cakes, Delia Smith`.

**There is no authorless-book form and no exception list.** Helen: *"I can't
imagine knowing the name of a book but not its author."* `Adapted from
Wagamama Feed Your Soul` is a publisher glued to a title with the author
nowhere, and it is wrong. If a book seems to have no author, first check that
it is a book: a one-off section of a magazine is not one, and with no date it
is a `website` (rule 2). Ask Helen before accommodating it.

The test accepts a comma followed by text, or a possessive followed by text. A
title that merely contains a possessive (`The Baker's Year`) satisfies it
without naming anyone, so that case is yours to catch.

### A magazine page: whose credit, and which month

Helen's rulings, 2026-10-30:

- **A book extract keeps the book's shape and adds where it was read**:
  `Adapted from Mary Berry's Absolute Favourites, via Good Food, March 2015`.
  It is a `book`.
- **A credit has to be on the page.** A page with none is the magazine's
  alone, `Adapted from Good Food, November 2026`, even inside a feature
  extracted from a book: the box two pages on does not reach it.
- **A first-name-only credit is not an author.** "Juliet's tip" leaves the
  page the magazine's.
- **The date is the issue's cover month**, even where the page footers name a
  season or a feast ("Christmas 2026" in the November issue).

---

## The rules

**1. "Adapted from" prefixes published work, and only published work.**
`publication`, `book`, `website` and `author` all take it. `person`, `place`,
`joke` and `unknown` are bare labels and must not. Enforced both ways.

Helen: *"Bare labels don't need 'adapted from', only work published by other
people."* And on why the prefix is always truthful for the rest: *"When
`rewritten == true`, we can always say 'adapted from' truthfully, so that should
always be there."*

**2. The date is what separates a publication from a website.** This is the
rule most likely to catch you out.

- A `publication` must carry a date: a month and year, or a year alone
  (`Adapted from Good Food, 2025`).
- A `website` must not.

Helen: *"Online magazines don't have a publication schedule like print ones
do."* `Good Food` is both a print magazine and a site. **If you have no date,
it is the website.**

Enforced both ways. The test's idea of a date is a month name followed by a
year, or any bare year from 1900 to 2099, anywhere in the string, so a site
whose own name contains a year reads as dated.

**3. Website first, author second, separated by `, recipe `.**
`Adapted from <site>, recipe <person>`. `Adapted from X, Y` is a book and its
author; `Adapted from X, recipe Y` is a site and the person who wrote the
recipe on it. Without the separator the two shapes are identical. Enforced: a
`website` source containing a comma must contain `, recipe `, and a `book`
source must not.

**4. Name a site by its bare domain or its name, not a full URL.**
`kitchenofdebjani.com`, not `https://kitchenofdebjani.com/`. `_layouts/recipe.html`
prints the source as plain text, not a link, so a protocol and a trailing
slash are noise on the page. By hand.

**5. No publishers.** A citation names the source, not who printed it.
`(Hodder & Stoughton)` and anything like it comes out. The test rejects any
source ending in a bracket, whatever its type.

**6. Jokes are exempt from the shapes.** A `joke` cites the experience that
produced the recipe rather than a source. It is outside the shapes, not in
violation of them; do not "fix" one. It is still a bare label (rule 1) and
still may not end in a bracket (rule 5).

**7. `QQ` means nobody has established it.** Not `Unknown`, not blank: the
first reads as a finished answer and the second as nothing to see, and neither
is true. `source: "QQ"` and `source_type: unknown` go together, each requiring
the other. On a published recipe `QQ` fails `test_no_qq_placeholder`
(`tests/test_style.py`), and a red suite stops the deploy. That is intended: an
unfinished citation should be impossible to ignore. Helen: *"QQ should be
allowed, but will break a test and block build, which is fine."*

**7a. `unknown` means Helen has established that nobody knows.**
`source_type: unknown` takes exactly one of two strings: `QQ` while the
question is open, `unknown` once she has closed it. Only she closes it, and
`unknown` is the only unknown-typed value that may reach `_food_recipes/`.
Lowercase, no `Adapted from`: it is a bare label in her voice, not a citation.

**8. One work, one spelling.** `Sunlight Cafe` and `Sunlight Café` in two
recipes is a bug. So is a trailing full stop on one of a matched pair. By
hand: look at how the work is already cited before typing it.

---

## Why `source_type` exists at all

Because the string cannot be classified by pattern. These two are the same
shape and different kinds of thing:

```
Adapted from Good Food                               → the website
Adapted from Gordon Ramsay's Ultimate Cookery Course → a book, complete
```

No regex separates them. So the recipe declares its own type, and the tests read
that rather than guessing.

**`source_type` renders nowhere.** No layout, include, plugin or script reads
it; only tests do. It is listed in `INVISIBLE_KEYS` in
`tests/test_front_matter.py`, so a commit that changes nothing in a recipe but
`source_type` does not invalidate Helen's proofread and must not flip
`meta.proofread`. `test_invisible_keys_are_really_invisible` greps the render
surface and fails if anything starts reading the key.

Any other edit to a recipe, `source` included, sets `meta.proofread: false` in
the same commit. See CLAUDE.md.

---

## For ingestion, the short version

1. Work out which of the eight types it is. If you cannot, write `source: "QQ"`
   with `source_type: unknown`. Do not guess: a wrong citation is worse than
   an absent one, and the `QQ` is designed to be loud.
2. Dated magazine → `publication`. Undated → `website`. No exceptions.
3. Write `source` in that type's shape, and `source_type` beside it.
4. Published work gets `Adapted from`. People, places, jokes and `QQ` do not.
5. Site before person, separated by `, recipe `. Bare domain, no `https://`.
6. A book names its author. No publishers.
