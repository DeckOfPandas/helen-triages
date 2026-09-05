# LETTERING — the four tiers of punched-tape type

Written 2026-09-02, the day the tiers shipped, after Helen looked at a
candidates page and diagnosed why dark-on-light punched lettering had never
actually worked on food. Read the whole thing before adding a consumer or
touching a value.

## 1. What punched lettering is, and where it lives

A label-maker letter reads as raised because it catches light on one edge and
drops a shadow on the other. On this site that is drawn with two dials that
compose:

- **`-webkit-text-stroke`** sets the WEIGHT of the edge. It is identical on
  every side of the glyph, so on its own it reads as a soft outline —
  "detached from the background", genuinely nice — but never as *raised*,
  because there is no direction in a uniform stroke.
- **`text-shadow`**, two hard-offset copies (no blur — a blurred copy reads as
  a drop shadow floating above the page, the opposite of punched), sets the
  DIRECTION: a light copy up-and-left where the light falls, a darker copy
  down-and-right where it does not.

Both dials are proportions of the type they sit on (the stroke is an `em`,
the offset is a whole pixel, deliberately not scaled — see
`_sass/shared/_rule.scss`'s own long comment on why), not fixed widths, which
is the thing most likely to be got wrong when adding a new consumer by hand.

**Where it lives:**

- `_sass/shared/_rule.scss` — `$emboss-stroke`, `$emboss-offset`,
  `$emboss-offset-large`, the `--emboss-*` custom properties, `@mixin
  punched($style, $offset)`, and the subject of this document, `@mixin
  lettering($tier, $offset)`.
- `_sass/food/_rule.scss` and `_sass/cocktails/_rule.scss` re-point the tier
  custom properties to each site's own values (§3 below).
- `punched()` is the older, untiered primitive. It still has exactly one
  direct caller: `_sass/cocktails/_cocktail.scss`'s drink-page headings,
  briefed and maintained separately from the rest of this system — see §7.
  Everything else reads a tier.

## 2. The physics, and the finding that fixed it

The system existed before the tiers and was tuned twice — once for dark type
on food's light page, once for light type on cocktails' dark one — because the
two are genuinely inverse problems (a dark shadow on a dark ground is
invisible; a light highlight on a light ground is invisible). Both got
custom-property treatment so a site could re-point them (see
`_sass/shared/_rule.scss`'s "THE TWO GROUNDS" note). What neither tuning pass fixed,
because nobody had named it as the problem, was that **the dark-on-light
numbers were solving for the wrong motif.**

Helen, looking at a candidates page (`tmp/mock/lettering.html`, not in the
repo — `tmp/` is gitignored):

> "off black front letter with a very thin darker outline, and a lighter
> black (or even light grey) up and left... similar aggression, without
> asking physics to go lighter than white"

The old dark-on-light values used `$color-white` for the highlight and
`rgba(ink, 0.68)` for the shadow — a highlight *lighter than the page* and a
shadow *two-thirds ink*. On a page whose ground already **is** `$color-bg`,
a highlight painted in that exact colour is invisible (no headroom above the
paper to be seen against), so the shadow alone did the work and read as a
second, slightly offset letterform. Helen's name for the effect on the FAQ
questions: **"dissolving in acid."**

**The physics, stated plainly.** A raised dark letter under a top-left light
source has a lit edge that is *lighter than the letter but darker than the
paper* — it is still ink catching a glancing light, not the paper itself —
and a cast shadow only *slightly* darker than the paper it falls on, because a
1px sliver of shadow is a thin thing, not a hole. Asking the highlight to be
lighter than the page and the shadow to be dramatically darker than the
letter both describe the punched-tape *motif* the mixin is named for (an
actual channel cut into black tape, lit from inside — which is genuinely how
`.site-logo-word`, light type on black tape, works) rather than what the
device draws everywhere else on food: dark ink standing slightly proud of a
light page. One set of numbers had been asked to do both jobs.

The fix moves the highlight **down**, off pure white to a mid grey, and the
shadow **up**, off two-thirds ink to a faint wash — both toward the paper,
from opposite directions.

## 3. The four tiers

A tier names a **role**, not a size. A consumer says what it *is* — "this is
a heading" — and the mixin resolves that to numbers, rather than a fresh
value copied from whatever's nearby, which is how the pre-tier system
drifted apart in the first place (`$emboss-stroke` and `$emboss-offset`'s own
history in `_sass/shared/_rule.scss` records two elements independently converging
on almost-but-not-quite the same ratio before either was named).

| tier | where | stroke width | offset |
|---|---|---|---|
| display | HELEN TRIAGES, and the recipe title (`.recipe-title-text`, which the reference-page titles share) | 0.016em (`$emboss-stroke`) | 1px (`--emboss-offset`); the title passes `--emboss-offset-lg` |
| heading | every other heading ≥ 1rem | 0.016em | 1px, or `--emboss-offset-lg` for the 1.8rem section headings |
| label | every punched element < 1rem | 0.016em | n/a — no shadow |
| plain | no edge at all | 0 | n/a |

**The colour values, per tier, per site** (stroke colour, highlight, shadow —
label has no highlight/shadow, plain has none of the three):

| tier | food stroke | food highlight | food shadow | cocktails stroke | cocktails highlight | cocktails shadow |
|---|---|---|---|---|---|---|
| display | `darken($color-text,12%)` ≈ `#000` | `lighten($color-text,53%)` ≈ `#aaa4a7` | `rgba($color-text,0.24)` | `$color-label-stroke` | `#fdfbfe` | `rgba(5,5,5,0.9)` |
| heading | `darken($color-text,5%)` ≈ `#141213` | `lighten($color-text,65%)` ≈ `#c9c4c7` | `rgba($color-text,0.16)` | `$color-label-stroke` | `$color-white` | `rgba($color-paper,0.06)` |
| label | `$color-label-stroke` | — | — | `$color-label-stroke` | — | — |

Food's display/heading values are computed directly from `$color-text` by the
shared defaults in `_sass/shared/_rule.scss` — food never re-points them,
because food **is** the site those formulas were solved against (checked in
the compiled CSS, not assumed: the custom properties are byte-identical
whether or not `_sass/food/_rule.scss` touches them). Cocktails re-points all three
sets in its own `_rule.scss`, because the same formulas plugged into
cocktails' near-white `$color-text` produce something illegible on a dark
ground — the two are inverse problems, same as the pre-tier system already
was. Cocktails' heading/display numbers are the numbers `--emboss-stroke-c` /
`--emboss-shadow` already gave it before the tiers existed; nothing changed
in substance for cocktails, only in name.

**The 1rem threshold.** The same line `$emboss-offset-large`'s own history
already drew: an element big enough that the offset's proportion of the
glyph needs help (a title, a section heading) gets the fuller heading
treatment; everything smaller gets stroke only. Below 1rem, **a shadow copy
cannot clear the stroke to be seen at all** — a 1px offset on an
already-small glyph has nowhere left to read as raised, so trying to give it
one only produces the "dissolving in acid" read the whole finding was named
from. This is why `label` has no shadow at all rather than a smaller one.
Helen's own words for the tier, when she chose it over the fuller treatment
for every element this size:

> "T2 wordmark, T1 large headings. Surprisingly T1 is good on the small
> headings too, but I prefer T3, flat with edge, so let's do that."

(T1 = heading, T2 = display, T3 = label, in that conversation's numbering.)

## 4. `@mixin lettering($tier, $offset: var(--emboss-offset))`

```scss
@include lettering(heading);
@include lettering(heading, var(--emboss-offset-lg));  // the two display-size headings
@include lettering(label);
@include lettering(display);   // .site-logo-top only
@include lettering(plain);     // rare — see the pattern it names, §6
```

That is the whole interface. It sets `-webkit-text-stroke` and `text-shadow`
together; nothing else about an element (font, size, colour, letter-spacing,
the blocky rule underneath it) is this mixin's concern.

**Why it doesn't call `punched()`,** even though `display` and `heading` are
both a stroke plus a two-copy raised shadow — exactly what `punched()` draws.
`punched()` reads `var(--emboss-light)` / `var(--emboss-shadow)`, shared
inherited custom properties. Routing a tier through it would mean locally
*redeclaring* those two properties on every display/heading element so
`punched()` picks up the right pair — and a locally redeclared custom
property inherits into every descendant of that element, not just into
`punched()`'s own text-shadow line. Nothing today reads `--emboss-light` or
`--emboss-shadow` inside a heading, but they are shared, general-purpose
names, and a future component doing so would have no reason to expect a
heading was silently rebinding them underneath it. `lettering()` duplicates
`punched()`'s two-line raised-shadow arithmetic instead, reading each tier's
own four properties directly — four lines, and the trap is gone.

**Why it has no `$style` argument.** Every tiered consumer is `raised`;
nothing reaches a tier wanting `pressed` (letters punched *down*).
`punched()` keeps `$style`, for `_cocktail.scss` and any future direct
caller that genuinely wants the inverted read.

## 5. Every consumer, its tier, and why

| element | file : line | size | tier |
|---|---|---|---|
| `.site-logo-top` (HELEN TRIAGES) | `_sass/shared/_layout.scss:521` | 2rem | **display** |
| `h1, h2, h3` (unstyled fallback) | `_sass/shared/_base.scss:69` | browser default (≥1rem) | heading |
| `.recipe-title-text` | `_sass/food/_recipe-header.scss:269` | 2.2rem | display (offset-lg) — Helen, later the same day: "recipe title goes hard like the wordmark" |
| `.recipe-section-heading` | `_sass/food/_recipe-header.scss:430` | 1.8rem | heading (offset-lg) |
| `.recipe-meta li strong` (SERVES/PREP/COOK) | `_sass/food/_recipe-header.scss:358` | 0.85rem | label |
| `.category-label` (index filter heading) | `_sass/food/_category-labels.scss:136` | 1.05rem | heading |
| `.ct-field > span` (timings field label) | `_sass/food/_timings.scss:94` | 0.7rem | label |
| `.ct-card-name` | `_sass/food/_timings.scss:280` | 1rem | heading — boundary case, see §5.1 |
| `.tc-row-label` (temperature chart row) | `_sass/food/_temperature-chart.scss:108` | 0.78rem | label |
| `.doneness-label` | `_sass/food/_temperature-chart.scss:385` | 0.7rem | label |
| `.recipe-body-content h2:not(.recipe-section-heading)` | `_sass/food/_recipe-notes-body.scss:143` | 1rem | heading — boundary case |
| `.recipe-body-content h3` (bare reference-page h3) | `_sass/food/_recipe-notes-body.scss:210` | 0.78rem | label |
| Tips label (`li > strong:first-child`) | `_sass/food/_recipe-notes-body.scss:353` | `$font-size-body-sm` (0.92rem) | label |
| Failure/diagnostic name (`ol > li > strong:first-child`) | `_sass/food/_recipe-notes-body.scss:441` | 1.06rem | heading — boundary case |
| `.recipe-group-heading` | `_sass/food/_recipe-notes-body.scss:558` | 1rem | heading — boundary case |
| `.about-faq-item h3` (FAQ question) | `_sass/food/_about.scss:241` | 0.85rem | label |
| `.cocktail-section-heading` (INGREDIENTS/METHOD/NOTES — the drink page) | `_sass/cocktails/_cocktail.scss:465` | 1.35rem | heading |

### 5.1 The four boundary cases

Four elements sit at or barely past exactly 1rem, where the table's own
threshold falls, and each was judged rather than only measured:

- **`.ct-card-name` (1rem).** Reads more like a card's own name than a field
  label sitting beside it — the sibling `.ct-total` on the same row is the
  same size and weight — so the size call and the "what is this" call agree.
  Heading.
- **`.recipe-body-content h2:not(.recipe-section-heading)` (1rem)** and
  **`.recipe-group-heading` (1rem).** Both are unambiguous headings (a
  fallback for an un-opted-in section heading; "For the dressing:" and
  similar group headings) that happen to sit exactly on the line rather than
  comfortably above it. Heading, on both counts.
- **Failure/diagnostic name (1.06rem).** The one size in that file's longform
  prose that isn't `$font-size-body-sm` — already singled out by its own
  comment as reading like a heading "whatever size it is set at": uppercase
  Courier wearing a violet rule, one tier below a section heading. Heading.

None of the four was a coin flip against the table — in each case the
element's own role agreed with which side of 1rem it happened to sit on.

## 6. `plain` — the tier that pre-existed itself

`plain` (`-webkit-text-stroke: 0; text-shadow: none;`) was never rare — it is
the pattern that resets a punched heading's inherited stroke/shadow on a
nested interactive element (a button inside a section heading, the method
toggle), so the element doesn't wear its parent's edge on top of its own.
It was named as a fourth tier in the same commit that introduced the other
three, rather than migrated call-by-call, because the risk of a migration
pass touching a *reset* rule is higher than the value of one fewer hand-written
line — a `plain` call site and a hand-written `stroke: 0; shadow: none;` are
visually identical, so this document names the pattern without insisting on
a mechanical sweep.

## 7. What is deliberately NOT tiered

- **`.site-logo-word`** (`_sass/shared/_layout.scss`), the bracketed word on the
  header tape — `[ FOOD ]` / `[ COCKTAILS ]`. Light type on a black tape SVG,
  the one genuinely different physical case (a real punched channel, not ink
  on paper), and excluded from the shared treatment since issue #122
  (2026-08-10) and reconfirmed by Helen on 2026-08-12: "please note in the
  docs that [ FOOD ] is handled differently — I think it needs the special
  treatment." It carries its own hand-tuned four-copy shadow
  (`--wordmark-word-shadow`) and no stroke by default. As of 2026-09-02
  (#469), both sites render this same four-copy default — see §8.
- **`.drink-card-tape-word`** (`_sass/cocktails/_cards.scss:427`), a drink card's
  own title-on-tape. Two near-whites, one tight pair, no softening shadow,
  plus the shared heading stroke — deliberately NOT the header tape's
  four-copy version, because at a card title's 1rem the four-copy shadow
  reads as two overlapping letterforms (HANDOVER §9.13, "The card title sits
  on punched tape", #469). Its own file's comment (`_cards.scss:212`)
  explains all four load-bearing decisions in full; this document doesn't
  repeat them.
- **`_sass/cocktails/_cocktail.scss`**'s drink-page headings (lines 236, 357),
  which call `punched(raised, var(--emboss-offset-lg))` directly. That file
  is briefed and maintained separately from this pass — see its own header —
  and was deliberately left untouched so `punched()` itself had to keep
  working exactly as it always has. This is also why `punched()` was not
  folded into `lettering()` or deleted: it has a real caller today.

## 8. HELEN TRIAGES and the two tape words — one settled question, one open one

**HELEN TRIAGES = display tier, on both sites, settled 2026-09-02.** This
element spent most of its life as a documented, deliberate exception (issue
#477): a wordmark is a logo, not a heading, and when Helen was shown a
version matching the shared heading treatment on 2026-08-26 she kept the old,
heavier numbers instead — "I prefer the old HELEN TRIAGES... I like the
drama." That decision was correct **relative to the headings it was compared
against**, and stopped being the last word once §2's finding fixed those
headings: display's numbers (`darken 12%` / `lighten 53%` / `rgba 0.24`) are
heading's own formula (`darken 5%` / `lighten 65%` / `rgba 0.16`) pushed
further in the same three directions — the same construction, one tier
harder — which is what let Helen reopen it the same day the tiers shipped:
"HELEN TRIAGES is not treated the same way as the other headings and should
be." See `_sass/shared/_layout.scss`'s own "#477" comment for the full three-state
history.

**`[ FOOD ]` and `[ COCKTAILS ]` (the header tape word) = the shared
four-copy tape default, on both sites, also settled 2026-09-02.** For part of
that day cocktails' tape word instead matched *its own* HELEN TRIAGES
("please make the punched font treatment the same for HELEN TRIAGES and
[ COCKTAILS ]") — superseded once food's own tape word entered the
comparison: "Please treat [ COCKTAILS ] the same way we now treat [ FOOD ]."
Food's tape word has never taken a tier or an override; matching it means
falling through to the same untiered default, which is what
`_sass/cocktails/_rule.scss` now does by removing its `--wordmark-word-stroke` /
`--wordmark-word-shadow` overrides rather than re-pointing them.

**The card tape word stays split from the header tape word, and that is not
an open question** — see §7's third bullet. Two different sizes were never
going to want one number; the two-copy/four-copy divergence tracks size, not
site.

## 9. How to add a consumer

Say the tier. Never write `-webkit-text-stroke` and `text-shadow` by hand for
a punched element:

1. Decide the role, not just read the size: is this a heading, or a label
   that happens to sit near 1rem? See §5.1 if it's close.
2. `@include lettering(<tier>)` — add the offset argument only if the element
   is display-scale and needs `--emboss-offset-lg` (rare; ask whether it
   really is before reaching for it).
3. If the element is on cocktails and needs a treatment its own
   `--lettering-*` values don't already give it, that is a new decision, not
   a bug — bring it to Helen the way every other divergence in this document
   was decided, don't invent a value.

## 10. Traps

- **The base `h1, h2, h3` rule used to hardcode the stroke colour.**
  `_sass/shared/_base.scss` read `-webkit-text-stroke: var(--emboss-stroke-w)
  $color-text;` literally, because only the ten palette-contract variables
  may be named in `shared/`. That is fixed by `@include lettering(heading)`
  reading a custom property instead of a hardcoded value, but the general
  shape of the trap — a shared file wanting to reach for a site's own softer
  colour and being unable to name it directly — is still how every
  `_rule.scss` re-point exists at all. Any new shared consumer that wants a
  site-specific colour needs the same custom-property indirection, not a new
  hardcoded fallback.
- **Custom properties inherit, so a context class can re-point a subtree.**
  This is the entire reason the tier values are custom properties rather than
  Sass variables — a site's `_rule.scss` re-points three property sets once,
  and every migrated consumer picks up the change with no specificity fight
  and no list of selectors to maintain (see `_sass/shared/_rule.scss`'s "THE TWO
  GROUNDS" section, and the now-removed `.on-dark` class's own postmortem in
  the same file for the mechanism worked out in full). It also means a
  mixin that locally redeclares `--emboss-light` / `--emboss-shadow` (which
  `lettering()` deliberately does NOT do — see §4) would leak that
  redeclaration into every descendant, not just the one shadow line meant to
  read it.
- **Anything below 1rem must be `label` or `plain`.** Giving a small element
  the heading or display treatment doesn't fail loudly — it compiles, it
  renders, and it reads as a smudge or a second faint letterform, because the
  shadow copy cannot clear the stroke at that size. This is not a rule of
  thumb to override with a bigger offset; §3's physics section explains why
  more offset doesn't fix it either.
- **`--emboss-stroke-c` / `--emboss-light` / `--emboss-shadow` are aliases of
  the heading tier now, not independent values.** They exist so
  `_sass/cocktails/_cocktail.scss` and `_sass/cocktails/_cards.scss` (unmigrated, see §7)
  keep rendering exactly as before. Do not re-point them directly to fix a
  heading-tier problem — re-point `--lettering-heading-*` instead, or the two
  unmigrated consumers will silently pick up a value meant for something
  else. Delete the alias block in `_sass/shared/_rule.scss` once nothing reads the
  old names directly (grep `var(--emboss` across `_sass/` to check).
- **Cocktails' `h1, h2, h3` stroke override in `_rule.scss` is gone, on
  purpose, not lost.** It used to restate `--emboss-stroke-w` /
  `--emboss-stroke-c` a second time to win a specificity fight with a
  hardcoded shared default; now `_sass/shared/_base.scss` reads the same
  `--lettering-heading-stroke-c` cocktails already re-points, so the two
  declarations always agreed and the override stopped doing anything. See
  that file's own comment for the shape to bring back if a genuine divergence
  (a heading-tier stroke *width* different from `--emboss-stroke-w`, which no
  site currently wants) ever needs it again.

## 11. Decisions log

- **2026-08-12.** Helen: "Did your heading lettering change touch all
  headings on the whole site? That is what I want." — the reason
  `_sass/shared/_base.scss`'s h1/h2/h3 rule exists at all, pre-dating the tiers.
- **2026-08-24 to 2026-08-26.** The dark-on-light and light-on-dark value
  pairs tuned separately (`_sass/shared/_rule.scss`'s "THE TWO GROUNDS" note); issue
  #477 raised and settled the first time ("I prefer the old HELEN TRIAGES...
  I like the drama").
- **2026-09-01, #469.** Cocktails goes black-on-black; its heading values
  become what `--emboss-stroke-c` / `--emboss-shadow` had already been
  solving for `.on-dark`, adopted as the site's own defaults.
- **2026-09-02, the day the tiers shipped.** In order:
  1. Helen, on the candidates page: "off black front letter with a very thin
     darker outline, and a lighter black (or even light grey) up and left...
     without asking physics to go lighter than white" — §2's finding.
  2. "T2 wordmark, T1 large headings. Surprisingly T1 is good on the small
     headings too, but I prefer T3, flat with edge, so let's do that." — the
     three sizeable tiers (this document adds `plain` as the fourth, already
     an existing pattern).
  3. "HELEN TRIAGES is not treated the same way as the other headings and
     should be" — #477 reopened; resolved as display tier, §8.
  4. "please make the punched font treatment the same for HELEN TRIAGES and
     [ COCKTAILS ]" — briefly matched the tape word to cocktails' own
     wordmark-top, same day.
  5. "Please treat [ COCKTAILS ] the same way we now treat [ FOOD ]" —
     superseded (4); the tape word falls back to the shared four-copy default
     on both sites instead, §8.
  6. "FAQ headings need to be darker, possibly simply matching SERVES / PREP
     / COOK even though they're on different pages" — `.about-faq-item h3`'s
     own label-tier override, `_sass/food/_about.scss:241`.
  7. Later the same evening, on Beef Wellington at 4019: "recipe title goes
     hard like the wordmark please, thanks for letting me change my mind" —
     `.recipe-title-text` moves from heading to display, so the page runs
     three strengths of one construction: hard on wordmark and title, soft on
     section headings, edge only below 1rem.
