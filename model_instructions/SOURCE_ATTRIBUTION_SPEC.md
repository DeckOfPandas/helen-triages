# Source attribution — the spec

GitHub issue #406. Settled with Helen on 2026-08-20; every ruling below is hers.

**If you are ingesting recipes, this is the contract.** Every recipe carries two
front matter keys, `source` and `source_type`, and they must agree.

```yaml
source: "Adapted from Gordon Ramsay's Ultimate Cookery Course"
source_type: book
```

---

## The eight types

`source_type` is one of exactly these. It is not free text.

| `source_type` | What it is | `source` shape | Example |
|---|---|---|---|
| `publication` | A magazine or periodical | `Adapted from <title>, <Month> <Year>` | `Adapted from Good Food, January 2026` |
| `publication` | …with a named author | `Adapted from <title>, <Month> <Year>, <Firstname Lastname>` | `Adapted from Good Food, January 2026, Sarah Cook` |
| `book` | A named book | `Adapted from <title>, <Firstname Lastname>` | `Adapted from French Provincial Cooking, Elizabeth David` |
| `book` | …author not recorded | `Adapted from <title>` | `Adapted from Healthier Baking` |
| `website` | A site or blog | `Adapted from <site>, recipe <Firstname Lastname>` | `Adapted from RecipeTin Eats, recipe Nagi` |
| `website` | …author not recorded | `Adapted from <site>` | `Adapted from indianhealthyrecipes.com` |
| `author` | A published cook, work not recorded | `Adapted from <Name>` | `Adapted from Delia Smith` |
| `person` | Someone Helen knows | a bare label | `Henry`, `Grandma Kath`, `Good friend Daniel` |
| `place` | A place | a bare label | `France` |
| `joke` | The experience that produced the recipe | free text, exempt from every shape | `Bitter experience` |
| `unknown` | Nobody has established it yet | exactly `QQ` | `QQ` |

---

## The rules

**1. "Adapted from" prefixes published work, and only published work.**
`publication`, `book`, `website` and `author` all take it. `person`, `place`,
`joke` and `unknown` are bare labels and must **not** take it.

Helen's wording: *"Bare labels don't need 'adapted from', only work published by
other people."* And, on why the prefix is always truthful for the rest: *"When
`rewritten == true`, we can always say 'adapted from' truthfully, so that should
always be there."*

**2. Website first, author second. Never the reverse.**
`Adapted from <site>, recipe <person>`. The word `recipe` is the separator and
is what distinguishes a `website` from a `book` — `Adapted from X, Y` is a book
with an author; `Adapted from X, recipe Y` is a site with an author.

**3. No publishers.** A citation names the source, not who printed it.
`(Hodder & Stoughton)` and anything like it comes out.

**4. The date on a `publication` is highly preferred but strictly optional.**
Include the month and year whenever you know them. A citation without one is
legal — two exist (`Adapted from delicious. magazine`) — but see the ratchet
below before adding another.

**5. Jokes are exempt.** Four recipes cite the experience that produced them
rather than a source. They are outside the spec, not in violation of it, and
`source_type: joke` is what marks that. Do not "fix" them.

**6. `QQ` means nobody has established it.** Not `Unknown`, not blank — those
read as a finished answer and as nothing-to-see respectively, and neither is
true. **`QQ` deliberately fails `tests/test_style.py::test_no_qq_placeholder`
and blocks the build.** That is the intended behaviour: an unfinished citation
should be impossible to ignore. Helen: *"QQ should be allowed, but will break a
test and block build, which is fine."*

**7. One work, one spelling.** `Sunlight Cafe` and `Sunlight Café` in two
recipes is a bug. So is a trailing full stop on one of a matched pair.

---

## Why `source_type` exists at all

Because the string cannot be classified by pattern. These two are the same
shape and different kinds of thing:

```
Adapted from Good Food                               → publication, no date
Adapted from Gordon Ramsay's Ultimate Cookery Course → book, complete
```

No regex separates them. So the recipe declares its own type, and the tests read
that rather than guessing.

**`source_type` renders nowhere.** No layout, include, plugin or script reads
it — only tests do. It is listed in `INVISIBLE_KEYS` in
`tests/test_front_matter.py`, which means **adding or changing it does not
invalidate Helen's proofread and must not flip `meta.proofread`**. That
exemption is verified, not merely asserted:
`test_invisible_keys_are_really_invisible` greps the render surface and fails if
anything starts reading the key.

Any *other* edit to a recipe still flips `meta.proofread: false` in the same
commit. See CLAUDE.md.

---

## The current corpus — 82 recipes

| Count | `source_type` |
|---|---|
| 21 | `person` |
| 20 | `website` |
| 17 | `book` |
| 9 | `publication` |
| 8 | `author` |
| 4 | `joke` |
| 2 | `unknown` |
| 1 | `place` |

Two `unknown` recipes (`five-spice-powder`, `pancetta-white-bean-stew`) are
currently blocking the build by design.

Three `publication` citations have no date: `Adapted from Good Food`
(cumin-mint-lamb-skewers) and `Adapted from delicious. magazine` ×2. **If you
are ingesting new recipes, do not add a fourth** — the count is ratcheted, and
a new dateless publication citation fails the build.

---

## For ingestion, the short version

1. Work out which of the eight types it is. If you cannot, use `QQ` /
   `unknown` — **do not guess.** A wrong citation is worse than an absent one,
   and the QQ is designed to be loud.
2. Write `source` in that type's shape, and `source_type` beside it.
3. Published work gets `Adapted from`. People, places, jokes and QQ do not.
4. Site before person, separated by `, recipe `.
5. No publishers.
6. A magazine wants its month and year. Find them if you can.
