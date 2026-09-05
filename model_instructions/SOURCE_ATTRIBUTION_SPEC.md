# Source attribution — the spec

GitHub issue #406. Settled with Helen on 2026-08-20; every ruling below is hers.

**If you are ingesting recipes, this is the contract.** Every recipe carries two
front matter keys, `source` and `source_type`, and they must agree.

```yaml
source: "Adapted from Gordon Ramsay's Ultimate Cookery Course"
source_type: book
```

**This is enforced.** `tests/test_source_attribution.py` checks every rule below
against **every** recipe and **every** draft — deliberately including drafts,
because a draft that drifts is a promotion that drifts. `source_type` is in
`REQUIRED`, so a recipe without one fails too. You will not get a citation past
the suite by being close enough. (This said "all 82 recipes and all 314 drafts"
until 2026-09-05; there are 86 recipes now, the drafts count moves every week,
and neither number was ever what the test loops over.)

---

## The eight types

`source_type` is one of exactly these. It is not free text. `magazine` is the
near-miss that has already been typed once by hand — it is `publication`.

| `source_type` | What it is | `source` shape | Example |
|---|---|---|---|
| `publication` | A print issue — **always dated** | `Adapted from <title>, <date>` | `Adapted from Good Food, January 2026` |
| `publication` | …with a named author | `Adapted from <title>, <date>, <Firstname Lastname>` | `Adapted from Good Food, January 2026, Sarah Cook` |
| `book` | A named book | `Adapted from <title>, <Firstname Lastname>` | `Adapted from French Provincial Cooking, Elizabeth David` |
| `book` | …whose author owns the title | `Adapted from <Author>'s <title>` | `Adapted from Delia Smith's Book of Cakes` |
| `website` | A site or blog — **never dated** | `Adapted from <site>, recipe <Firstname Lastname>` | `Adapted from RecipeTin Eats, recipe Nagi` |
| `website` | …author not recorded | `Adapted from <site>` | `Adapted from indianhealthyrecipes.com` |
| `author` | A published cook, work not recorded | `Adapted from <Name>` | `Adapted from Delia Smith` |
| `person` | Someone Helen knows | a bare label | `Henry`, `Grandma Kath`, `Good friend Daniel` |
| `place` | A place | a bare label | `France` |
| `joke` | The experience that produced the recipe | free text, exempt from every shape | `Bitter experience` |
| `unknown` | Nobody has established it yet | exactly `QQ` | `QQ` |

---

### A book must name its author, in one shape or the other

**Added 2026-08-21, after the spec's own gap put two wrong citations on the live
site.** There are two shapes, not one, and BOTH carry the author:

    Adapted from Feed Your Soul, Wagamama          title, then author
    Adapted from Delia Smith's Book of Cakes       author, possessively, then title

The possessive form is not a variant to tolerate — it is the more common of the
two here (44 of 89 book citations) and it is ordinary English. Rewriting
`Delia Smith's Book of Cakes` as `Book of Cakes, Delia Smith` would be worse
prose to satisfy a rule, so the rule accommodates it instead.

**WHY THIS HAD TO BE WRITTEN DOWN, and the failure is instructive.** The spec
described only the comma form plus an "author not recorded" fallback that
accepts ANY string. So all 44 possessive citations were passing through the
fallback, which made the fallback look load-bearing when nothing real used it —
and, worse, made the book rule unfalsifiable. `Adapted from Wagamama Feed Your
Soul` is a publisher's name glued to a title with the author nowhere, and it
passed as "a title with no author", on two published pages, until Helen asked
why the rule allowed it.

**A rule that accepts everything is not a lenient rule, it is an absent one.**

**THE RULE IS UNCONDITIONAL: there is no authorless-book form.** Helen,
2026-08-21: *"I can't imagine knowing the name of a book but not its author."*
Exactly one citation appeared to contradict her — `Adapted from Healthier
Baking`, on `sweet-potato-chocolate-brownies.md` — and it was about to be
written down as a declared exception when she recognised it: *"it's from Good
Food, from a special one-off section."* Not a book. Retyped as a dateless
`website`, and the exception was deleted before it existed.

**An exception list with one entry is worse than no list.** It looks like
diligence and reads, six months later, as proof that the rule has legitimate
exceptions — so the next awkward case gets added instead of questioned. The one
candidate here was a misfiled citation, and asking beat accommodating.

---

## The rules

**1. "Adapted from" prefixes published work, and only published work.**
`publication`, `book`, `website` and `author` all take it. `person`, `place`,
`joke` and `unknown` are bare labels and must **not**.

Helen: *"Bare labels don't need 'adapted from', only work published by other
people."* And on why the prefix is always truthful for the rest: *"When
`rewritten == true`, we can always say 'adapted from' truthfully, so that should
always be there."*

**2. THE DATE IS WHAT SEPARATES A PUBLICATION FROM A WEBSITE.** This is the most
important rule here and the one most likely to catch you out.

- A `publication` **must** carry a date.
- A `website` **must not**.

A year on its own is a complete date — `Adapted from Good Food, 2025`. Helen:
*"Online magazines don't have a publication schedule like print ones do."*

This is not a fudge, it's the actual difference. `Good Food` is genuinely both:
11 drafts cite the October 2025 print issue, and 31 cited the site with no date
at all. **If you have no date, it is the website.** Sixty-four drafts were
retyped on this rule.

**3. Website first, author second, separated by `, recipe `.**
`Adapted from <site>, recipe <person>`. That separator is load-bearing:
`Adapted from X, Y` is a book and its author, `Adapted from X, recipe Y` is a
site and the person who wrote the recipe on it. Without it the two shapes are
identical.

**4. Name a site by its bare domain or its name — not a full URL.**
`kitchenofdebjani.com`, not `https://kitchenofdebjani.com/`. The source line
renders as **plain text, not a link** (`_layouts/recipe.html:142`), so a
protocol and trailing slash are just noise on the page.

**5. No publishers.** A citation names the source, not who printed it.
`(Hodder & Stoughton)` and anything like it comes out.

**6. Jokes are exempt.** Four recipes cite the experience that produced them
rather than a source. They are outside the shapes, not in violation of them, and
`source_type: joke` is what marks that. Do not "fix" them.

**7. `QQ` means nobody has established it.** Not `Unknown`, not blank — those
read as a finished answer and as nothing-to-see respectively, and neither is
true. **`QQ` deliberately fails `test_no_qq_placeholder` and blocks the build.**
That is intended: an unfinished citation should be impossible to ignore. Helen:
*"QQ should be allowed, but will break a test and block build, which is fine."*

**8. One work, one spelling.** `Sunlight Cafe` and `Sunlight Café` in two
recipes is a bug. So is a trailing full stop on one of a matched pair.

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
it — only tests do. It is listed in `INVISIBLE_KEYS` in
`tests/test_front_matter.py`, which means **adding or correcting it does not
invalidate Helen's proofread and must not flip `meta.proofread`**. That
exemption is verified, not asserted: `test_invisible_keys_are_really_invisible`
greps the render surface and fails if anything starts reading the key.

Any *other* edit to a recipe still flips `meta.proofread: false` in the same
commit. See CLAUDE.md.

---

## The current corpus

| `source_type` | Recipes | Drafts |
|---|---|---|
| `website` | 23 | 115 |
| `person` | 22 | 2 |
| `book` | 17 | 42 |
| `author` | 8 | 7 |
| `publication` | 7 | 82 |
| `joke` | 4 | 3 |
| `place` | 1 | 0 |
| `unknown` | 0 | 63 |
| **total** | **82** | **314** |

Zero violations in either collection.

---

## For ingestion, the short version

1. Work out which of the eight types it is. If you cannot, use `QQ` /
   `unknown` — **do not guess.** A wrong citation is worse than an absent one,
   and the QQ is designed to be loud.
2. **Dated magazine → `publication`. Undated → `website`.** No exceptions.
3. Write `source` in that type's shape, and `source_type` beside it.
4. Published work gets `Adapted from`. People, places, jokes and QQ do not.
5. Site before person, separated by `, recipe `. Bare domain, no `https://`.
6. No publishers.
