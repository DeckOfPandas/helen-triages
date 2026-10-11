# LETTERING — the four tiers of punched-tape type

Read this before adding a punched element or touching a value. The mixin and
its numbers are in `_sass/shared/_rule.scss`; where this page and the Sass
disagree, the Sass is right. Section numbers here are cited from the Sass, so
they are kept as they are.

## 1. What punched lettering is, and where it lives

A label-maker letter reads as raised because it catches light on one edge and
drops a shadow on the other. On this site that is drawn with two dials that
compose:

- **`-webkit-text-stroke`** sets the weight of the edge. It is identical on
  every side of the glyph, so on its own it reads as a soft outline and never
  as raised: a uniform stroke has no direction.
- **`text-shadow`**, two hard-offset copies, sets the direction: a light copy
  up and left where the light falls, a darker copy down and right where it
  does not. No blur: a blurred copy reads as a drop shadow floating above the
  page, the opposite of punched.

The stroke is an `em`, so it is a proportion of whatever type it lands on. The
offset is a whole pixel and deliberately not scaled; the comment above
`$emboss-offset` in `_sass/shared/_rule.scss` says why.

**Where it lives:**

- `_sass/shared/_rule.scss` — `$emboss-stroke`, `$emboss-offset`,
  `$emboss-offset-large`, the custom properties `--emboss-stroke-w`,
  `--emboss-offset` and `--emboss-offset-lg`, the three `--lettering-*` colour
  sets, and `@mixin lettering($tier, $offset)`.
- `_sass/food/_rule.scss` and `_sass/cocktails/_rule.scss` re-point the custom
  properties to each site's own values (§3).
- `lettering()` is the only way to draw a punched element. There is no
  `punched()` mixin and there are no `--emboss-*` colour properties; a
  `pressed` treatment (letters punched down) does not exist, because nothing
  has asked for one.

## 2. The physics

A raised dark letter under a top-left light has a lit edge that is lighter
than the letter but darker than the paper: it is still ink catching a
glancing light, not the paper itself. Its cast shadow is only slightly darker
than the paper it falls on, because a 1px sliver of shadow is a thin thing,
not a hole. Helen's description of the target:

> "off black front letter with a very thin darker outline, and a lighter
> black (or even light grey) up and left... similar aggression, without
> asking physics to go lighter than white"

So on food's light page the highlight is a mid grey and the shadow a faint
wash, both close to the paper. A highlight in the page's own colour cannot be
seen, and a heavy shadow left to do the work alone reads as a second, offset
letterform: what Helen called "dissolving in acid".

Light type on a dark ground is the inverse problem. A dark shadow on a dark
ground is invisible, so the light copy does the work. That is why cocktails
has its own values rather than food's formulas, and why the values are custom
properties a site can re-point (the note on the two grounds in
`_sass/shared/_rule.scss`).

## 3. The four tiers

A tier names a **role**, not a size. A consumer says what it is ("this is a
heading") and the mixin resolves that to numbers, so no call site copies a
value from whatever is nearby.

| tier | where | edge | shadow |
|---|---|---|---|
| display | HELEN TRIAGES, and the recipe title (`.recipe-title-text`, which the reference-page titles share) | stroke | two copies |
| heading | every other heading of 1rem or more | stroke | two copies |
| label | every punched element under 1rem | stroke | none |
| plain | resets an inherited edge (§6) | none | none |

**Widths.** The stroke width is `--emboss-stroke-w` for every tier: `0.016em`
(`$emboss-stroke`) on food, re-pointed to `0.010em` on cocktails, because a
stroke on light-on-dark type reads heavier. The offset is `--emboss-offset`,
1px. Two consumers pass `--emboss-offset-lg` instead (§5); it is also 1px
today, and the two stay separate variables so display sizes can diverge again
without touching a call site.

**The colours, per tier, per site** (stroke colour, highlight, shadow):

| tier | food stroke | food highlight | food shadow | cocktails stroke | cocktails highlight | cocktails shadow |
|---|---|---|---|---|---|---|
| display | `darken($color-text,12%)` ≈ `#000` | `lighten($color-text,53%)` ≈ `#aaa4a7` | `rgba($color-text,0.24)` | `$color-label-stroke` | `#fdfbfe` | `rgba(5,5,5,0.9)` |
| heading | `darken($color-text,5%)` ≈ `#141213` | `lighten($color-text,65%)` ≈ `#c9c4c7` | `rgba($color-text,0.16)` | `$color-label-stroke` | `$color-white` | `rgba($color-paper,0.06)` |
| label | `$color-label-stroke` | — | — | `$color-label-stroke` | — | — |

Food's display and heading values are the shared defaults, computed from
`$color-text` in `_sass/shared/_rule.scss`; food re-points only the label
stroke. Cocktails re-points all three sets in its own `_rule.scss`, because
the same formulas applied to a near-white `$color-text` are illegible on a
dark ground. Display is heading's construction pushed further in the same
three directions.

**The 1rem threshold.** An element big enough for a 1px offset to read as
raised gets the heading treatment; everything smaller gets stroke only. Below
1rem a shadow copy cannot clear the stroke to be seen at all, so `label` has
no shadow rather than a smaller one. Helen's name for the label tier is "flat
with edge".

## 4. `@mixin lettering($tier, $offset: var(--emboss-offset))`

```scss
@include lettering(display);                           // .site-logo-top
@include lettering(display, var(--emboss-offset-lg));  // .recipe-title-text
@include lettering(heading);
@include lettering(heading, var(--emboss-offset-lg));  // .recipe-section-heading
@include lettering(label);
@include lettering(plain);                             // a reset, §6
```

That is the whole interface. It sets `-webkit-text-stroke` and `text-shadow`
together; nothing else about an element (font, size, colour, letter-spacing,
the blocky rule under it) is this mixin's concern. An unknown tier is a
compile error.

Each tier reads its own custom properties directly
(`--lettering-<tier>-stroke-c`, `-light`, `-shadow`). It does not route
through shared, general-purpose property names; §10 has the reason. Every
tier is raised, so there is no `$style` argument.

## 5. Every consumer, its tier, and why

Files, not lines: grep the selector.

| element | file | size | tier |
|---|---|---|---|
| `.site-logo-top` (HELEN TRIAGES) | `_sass/shared/_layout.scss` | 2rem; two thirds of that below 600px † | display |
| `h1, h2, h3` (unstyled fallback) | `_sass/shared/_base.scss` | browser default (1rem or more) | heading |
| `.recipe-title-text` | `_sass/food/_recipe-header.scss` | 2.2rem; 1.9rem at 400px and under | display (offset-lg) |
| `.recipe-section-heading` | `_sass/food/_recipe-header.scss` | 1.8rem | heading (offset-lg) |
| `.recipe-meta li strong` (SERVES/PREP/COOK) | `_sass/food/_recipe-header.scss` | 0.85rem | label |
| `.category-label` (index filter heading) | `_sass/food/_category-labels.scss` | 1.4rem | heading |
| `.ct-field > span` (timings field label) | `_sass/food/_timings.scss` | 0.7rem | label |
| `h3.ct-group-name` (timings group name) | `_sass/food/_timings.scss` | 1.15rem | heading |
| `.ct-group-cuts` (the cuts line inside it) | `_sass/food/_timings.scss` | 0.85rem | plain |
| `.fish-name` | `_sass/food/_timings.scss` | 1rem | heading — boundary case, see §5.1 |
| `.tc-row-label` (temperature chart row) | `_sass/food/_temperature-chart.scss` | 0.78rem | label |
| `.doneness-label` | `_sass/food/_temperature-chart.scss` | 0.7rem | label |
| `.recipe-body-content h2:not(.recipe-section-heading)` | `_sass/food/_recipe-notes-body.scss` | 1rem | heading — boundary case |
| `.recipe-body-content h3` (bare reference-page h3) | `_sass/food/_recipe-notes-body.scss` | 0.78rem | label |
| Tips label (`li > strong:first-child`) | `_sass/food/_recipe-notes-body.scss` | `$font-size-body-sm` (0.92rem) | label |
| Failure/diagnostic name (`ol > li > strong:first-child`) | `_sass/food/_recipe-notes-body.scss` | 1.06rem | heading — boundary case |
| `.recipe-group-heading` | `_sass/food/_recipe-notes-body.scss` | 1rem | heading — boundary case |
| `.about-faq-item h3` (FAQ question) | `_sass/food/_about.scss` | 0.85rem | label, matching SERVES/PREP/COOK |
| `.cocktail-section-heading` (INGREDIENTS/METHOD/NOTES on a drink page) | `_sass/cocktails/_cocktail.scss` | 1.5rem | heading, inherited from the `h1, h2, h3` rule |

† Below 600px the whole wordmark lockup (HELEN TRIAGES, the bracketed word's
ceiling, the tape's height and lift) is multiplied by `$wordmark-phone-scale`,
so `.site-logo-top` renders at 1.33rem on a phone. **The tier does not change
with the size**: display is display at any size. The shrink is a `font-size`,
never a `transform: scale()`: the wordmark's grid sizes itself off the rows'
natural widths (MANUAL §13.8), and a transform reports the unscaled box.

### 5.1 The four boundary cases

Four elements sit at or barely past exactly 1rem, where the threshold falls.
Each is judged by role as well as measured:

- **`.fish-name` (1rem).** The name of a fish above its timings: the same
  lettering and single violet rule as `.ct-group-name`, a step smaller.
  Heading.
- **`.recipe-body-content h2:not(.recipe-section-heading)` (1rem)** and
  **`.recipe-group-heading` (1rem).** Both are unambiguous headings (a
  fallback for a section heading that has not opted in; "For the dressing:"
  and similar group headings) that sit exactly on the line. Heading.
- **Failure/diagnostic name (1.06rem).** The one size in that file's longform
  prose that is not `$font-size-body-sm`: uppercase Courier wearing a violet
  rule, one tier below a section heading. Heading.

In each case the element's role agrees with the side of 1rem it sits on.

## 6. `plain`

`plain` is `-webkit-text-stroke: 0; text-shadow: none;`. It resets a punched
heading's inherited stroke and shadow on something nested inside it, so the
nested element does not wear its parent's edge: `.ct-group-cuts` inside
`h3.ct-group-name` is the example. A `plain` call and the same two
declarations written by hand are identical, so existing hand-written resets
are left as they are; new ones say `lettering(plain)`.

## 7. What is deliberately not tiered

- **`.site-logo-word`** (`_sass/shared/_layout.scss`), the bracketed word on
  the header tape: `[ FOOD ]` / `[ COCKTAILS ]`. Light type on a black tape
  SVG, the one physically different case (a real punched channel, not ink on
  paper). Helen: "please note in the docs that [ FOOD ] is handled differently
  — I think it needs the special treatment." It carries its own four-copy
  shadow (the fallback of `--wordmark-word-shadow`) and no stroke. Do not give
  it a tier.
- **`.drink-card-tape-word`** (`_sass/cocktails/_cards.scss`), a cocktail
  card's title on its tape. One tight pair of shadow copies and no wider,
  softer pair, because at a card title's size the header's four copies read as
  two overlapping letterforms (MANUAL §9.13). Its stroke reads the heading
  tier's colour, `--lettering-heading-stroke-c`; that is a colour borrowed,
  not the tier taken, and `@include lettering(heading)` would replace the
  shadow. The comment on the rule in `_cards.scss` has the detail.

## 8. HELEN TRIAGES and the two tape words

- **HELEN TRIAGES is the display tier on both sites.** It is not an exception
  with hand-tuned numbers: it takes the headings' own construction, one tier
  harder, and a site re-points it through `--lettering-display-*`.
- **`[ FOOD ]` and `[ COCKTAILS ]` share the untiered four-copy default on
  both sites** (§7, first bullet). Neither site sets `--wordmark-word-stroke`
  or `--wordmark-word-shadow`; matching the two means leaving both unset.
- **The card tape word stays split from the header tape word** (§7, second
  bullet). The two-copy and four-copy treatments track size, not site.

## 9. How to add a consumer

Say the tier. Never write `-webkit-text-stroke` and `text-shadow` by hand for
a punched element:

1. Decide the role as well as reading the size: is this a heading, or a label
   that happens to sit near 1rem? See §5.1 if it is close.
2. `@include lettering(<tier>)`. Add the offset argument only if the element
   is display-scale and needs `--emboss-offset-lg`.
3. Add the element to §5's table.
4. If the element is on cocktails and needs a treatment its `--lettering-*`
   values do not give it, that is a new decision, not a bug. Bring it to
   Helen on a candidates page (MANUAL §13.11); do not invent a value.

## 10. Traps

- **A shared file cannot name a site's own colour.** Only the palette-contract
  variables may be named in `_sass/shared/`, which is why
  `_sass/shared/_base.scss` says `@include lettering(heading)` and each site's
  `_rule.scss` re-points a custom property. A new shared consumer that wants a
  site-specific colour needs the same indirection, never a hardcoded fallback.
- **Custom properties inherit, so a re-point reaches a whole subtree.** That
  is why the tier values are custom properties rather than Sass variables: a
  site's `_rule.scss` re-points three sets once and every consumer follows,
  with no specificity fight and no list of selectors. The same inheritance is
  a trap from the other side: a mixin that locally redeclares a shared
  property so its own one line reads the right value leaks that redeclaration
  into every descendant. `lettering()` reads each tier's own properties for
  that reason, and the same applies to any shared property a component is
  tempted to rebind locally.
- **Anything below 1rem must be `label` or `plain`.** Giving a small element
  the heading or display treatment does not fail loudly: it compiles, it
  renders, and it reads as a smudge or a second faint letterform, because the
  shadow copy cannot clear the stroke at that size (§3). A bigger offset does
  not fix it.
- **Re-point, never re-value.** Do not fix a tier problem by changing a shared
  name that other consumers also read. Check what else reads the name before
  assuming it is yours to move. `--emboss-stroke-w` and `--emboss-offset` are
  read by every tier.
