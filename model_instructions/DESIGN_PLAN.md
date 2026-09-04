# DESIGN PLAN — where the 2026-09-02 design review got to, and what is next

Written 2026-09-02 at the end of one long session with Helen, for whoever
picks the design work up next. It is a status board and a queue, in priority
order. Everything marked **done** is merged to `main` (PRs #660–#663 and the
mechanical PR before them). Everything else is a decision Helen has made but
not built, or a question she has not answered. Do not re-litigate the
decisions; do build them.

## 0. How this work is done, because it is different from data work

**Helen decides by looking, never by argument.** Every decision below was made
on a candidates page: the real page, the real compiled CSS, the real fonts and
artwork, with two to five treatments switchable from a bar at the top. Build
the candidates, publish them, let her pick. Three tools make that cheap:

- `scripts/mock_bundle.py` — bundles a page from a local Jekyll build
  (`bundle exec jekyll build --config _config.yml,_config_local.yml -d
  tmp/site-mock`) into one self-contained HTML file: compiled CSS with the
  fonts inlined, every script inlined, every SVG under `assets/img` embedded
  so `decorations.js` finds its tapes without a network. Add candidate CSS
  as `extra_style` keyed off `html[data-x="…"]`, a switcher as
  `extra_scripts`, and publish the file as an Artifact.
- **Syntax-check the switcher before publishing** (`node -e` with `new
  Function(src)`): one apostrophe in a description killed an entire round of
  leopard samples and she saw "none at all". Use `json.dumps` for any text
  that goes into the script.
- The artifact viewer lets `<main>` run full width; the bundler pins it to
  the site's 900px column so margin layouts (the drink page's glass) behave.
  Her screenshots come in at odd device-pixel ratios; measure against the
  900px column, not the viewport.

A worktree has no `_cocktail_drafts/`: clone it over SSH
(`git@github.com:DeckOfPandas/helen-triages-cocktails-private`) into the
worktree, it is gitignored, and serve with `bundle exec jekyll serve --config
_config.yml,_config_local.yml --port 4019` so she can see the branch beside
her own 4018 build of `main`.

**Delegation that worked:** the build work went to Sonnet agents with a
precise spec (values, files, lines, the house comment style, the branch
check before every commit) and was reviewed by diff. What did not work:
letting an agent tidy `tmp/` — it removed the mock scripts with an
over-broad `rm -rf`. Tell agents to delete only what they created.

## 1. Done and merged

| finding (audit §) | what shipped | where |
|---|---|---|
| Index greys fail contrast | ingredient line 12%, pantry 14% lightened from clear-text; both clear 4.5:1 | `food/_recipe-list.scss` |
| Lists read with hands full | ingredients and method at weight 400 | `food/_recipe-ingredients-method.scss` |
| Dead space under the back arrow | title margin closed where the arrow renders | `food/_recipe-header.scss` |
| DONENESS reads as a fourth section | 1.35rem, single violet rule | `food/_temperature-chart.scss` |
| Ship mark is a private code | "ship it?" legend beside the survivor count | `cocktails/index.html`, `_filters.scss` |
| About dividers look like broken headings | the footer's dashed hairline (Helen overrode the earlier decision) | `food/_about.scss` |
| Nothing edible above the fold | **tighten**: section gap 0.75rem, label gap 0.5rem, filter headings 1.05rem / 1.2rem, panel padding 0.3rem; **the universe says…**: one random row cloned above the panel with "deal again", both sites. **Off food since 2026-09-04** (Helen: the panel of choices is the fold on a triage site); on cocktails it is a whole card dealt into the right-hand column with the label on the left, a first pass she means to refine | `shared/_tokens.scss`, `shared/_rule.scss`, `assets/js/universe.js`, `cocktails/_universe.scss` |
| Punched lettering never worked dark-on-light | four tiers (display / heading / label / plain); food's highlight is a mid grey and its shadow faint; HELEN TRIAGES and the recipe title hard, other headings soft, everything under 1rem edge-only; FAQ questions match SERVES/PREP/COOK; [ COCKTAILS ] wears [ FOOD ]'s tape lettering | `shared/_rule.scss`, both `_rule.scss`, `LETTERING.md` |
| Second typeface without a rule | Plex is for numbers you act on: amounts on both sites, chart readouts and ticks, calculator inputs and results; note labels back to Courier; Plex 700 dropped | `shared/_fonts.scss`, both palettes |
| Drink page half-inverted, colours off-job | rebuilt to Helen's brief: glass large in the margin, name on the card tape, glass/garnish/ship it? meta, card chips, yvette-over-absinthe under Ingredients and Method and under each ingredient name, lagoon on Notes and its cards, pink suggestions, ink numerals, read it / make it slider, shared ship include | `_layouts/cocktail.html`, `cocktails/_cocktail.scss`, `_includes/cocktails/ship.html`, `assets/js/cocktail-make.js` |
| Section greens read as green on green (critical #4); headings smudged (#680); drink-page headings too small (#679 pt 4) | **2026-09-03.** A reposado-to-yvette ramp through pink (coral, hot pink derived in OKLCH) under the five index headings, ONE bar, the shared absinthe bar gone; each section's colour also on its chosen filter word and on the chip or band it lit on a card, so "magenta means matched everywhere" is reversed and cosmopolitan means HAS TO HAVE again; index headings 1.4rem / weight 400 / 0.14em, drink-page section headings 1.8rem / 400, punch kept on both. The mechanism: bold light-on-dark stems bloom into the punched highlight. `index-section-label` gained `$weight`. | `cocktails/_palette.scss`, `cocktails/_rule.scss` (heading-rule is single-bar now), `cocktails/_filters.scss`, `cocktails/_cards.scss`, `cocktails/_cocktail.scss`, `shared/_rule.scss` |
| Drink page top (#679: title too big, no spare tape, meta crammed, headings small) | **2026-09-03.** Root cause of the first two: the h1 at `display: contents` still took the UA's `2em`, so the title rendered at double and the tape's em padding at half. Fixed with `font-size: 1em`; title 3.2rem (the rendered size Helen chose), the card's horizontal tape padding with 0.5em vertical, meta gap 5rem, glass absinthe / stroke 3 / floor 14rem, section headings absinthe over yvette (NOTES over lagoon), one yvette band under each ingredient name. Unseen on iPad until deployed. | `cocktails/_cocktail.scss` |

## 2. Decided, not yet built

1. ~~"Deal again" icon.~~ **The universe section came off food on 2026-09-04**
   — Helen, having seen it deployed and then a styled row and two card
   treatments on the real page: "I think it's the feature, not your work…
   I don't think anyone (and certainly not me) opens a triage website to
   click on a random recipe." Cocktails still has its copy; the icon question
   only matters if that survives.
2. **Leopard.** Round one she chose L3 (sheen). Round two (five patterns ×
   four placements) she has not decided, and said "leave leopard with me…
   don't ship anything." `model_instructions/LEOPARD.md` has the generator,
   every value and the rules. When she decides: solve the tile at build
   time from the palette, place per §5 of that file.

## 3. Open questions from the audit, in the order to raise them

Each of these wants a candidates page, not an argument. Highest impact first.

1. ~~The five section greens on the cocktails index~~ **Done 2026-09-03**,
   see §1. Three rounds on one candidates page: type, then colour, then card
   language. The one loose end is the drink page's ingredient-name underline,
   still yvette over absinthe per Helen's written brief while every heading
   is single-bar; a drink-page bundle with a switch was published for her.
2. ~~Cocktail filter words versus card chips~~ **Done 2026-09-04**: both
   directions shown on the real index; Helen, "100% cards take words". A
   card's moods are bare bold Courier words like the filter list, separated
   by the ingredient line's middle dot, hovering to magenta, underlined in
   the section's colour when matched. Reaches the universe card and the
   drink page's chips through the shared class. `_cards.scss`.
3. ~~Food index hierarchy~~ **Done 2026-09-04.** Title 1.2rem / 700 (a
   punched version "looks fuzzy"); badges stay after the ingredients (the
   ingredient scan "makes the decision about opening the page or not"; a
   right-hand column "makes the rows enormous"); badges rest muted, take the
   old dusty 35% mix when matched, and the lightened hue only on their own
   hover. `food/_recipe-list.scss`, `food/_badges.scss`,
   `food/_active-filter-states.scss`.
4. ~~Wrapped titles stack their rules~~ **Done 2026-09-04** (critical #7).
   Candidates page on the real quiche recipe; Helen: "Last line only please,
   10000%." A small script measures where the lines break and rebuilds the
   element as `.rule-lines` + `.rule-last`, and the mark moves to the last
   line's span — so a wrapped title wears it exactly as a one-line title does.
   The CSS-only alternative was checked and does not work:
   `box-decoration-break: slice` makes the fragments slices of ONE box, each
   keeping its full height, so bottom-anchored bars land under the first line
   only. The element keeps its own double rule as the no-JS fallback, switched
   off by the `rule-split` class the script adds. Reaches the recipe/magic-bag
   title and every recipe, about and reference section heading; the
   cooking-methods protein heading opts out with `data-last-line-rule="skip"`
   because cook-timer.js owns its text. `assets/js/last-line-rule.js`,
   `shared/_rule.scss` (`overlapping-rule-double-last-line`),
   `food/_recipe-header.scss`, `_layouts/default.html`.
5. ~~Card clamps~~ **Done 2026-09-04** (critical #9). All three candidates were
   built on the real index and Helen took two of them plus a refusal:
   *"Let's do: shrink when it's just one short-ish word too long, then two lines
   where it's more than that. The one super-long title we have I'll just
   shorten, and retain that principle. Narrower glass column please. Let's
   stick with two lines of ingredients -- when we get issue #691 done
   (ingredients in importance order) I expect two lines will get the point
   across plus leave some comfy real estate on the cards."*
   - **The glass column is 6.5rem**, down from 7.6rem — the audit's own ~15%.
     One value moves the title's left edge, the foot's left edge, the two panel
     strips and the drawing's width cap together, so nothing else changed; the
     text column gains 17px at every width.
   - **The name rule is a measurement, not a length.** One size step of 0.86
     buys about 14% of the line — four or five Courier characters, which is one
     short-ish word. A name that overflows by less than that steps down and
     nobody sees it; a name that overflows by more wraps to a two-line tape,
     which the absolutely-positioned tape background grows to fit. Never cut.
     `assets/js/card-name-fit.js` measures `scrollWidth` against `clientWidth`,
     re-measures once after stepping (the prediction is linear and type is not)
     and adds one of `drink-card-name--step` / `--wrap`. It runs at load, on
     `document.fonts.ready` and on a debounced resize, and exposes
     `HTF.fitCardNames()` — which `universe.js` calls after each deal, because
     the pick is a wider card and a cloned measurement would be the wrong
     answer. With no JS nothing gets a class and the ellipsis stays, which is
     the behaviour the page had before.
   - **The name's size goes through `--card-name-size` × `--card-name-scale`**,
     so ONE step rule works on a card and on the drink page's 3.2rem title.
     The tape's padding and left bleed are `em` of the title and follow the
     step for free; the right bleed is `rem` and deliberately does not.
   - **The ingredient clamp stays at two lines**, and the fix for a clamped
     line is #691 rather than a third line. The reason is recorded beside the
     clamp so nobody raises it again.

   `_sass/cocktails/_cards.scss`, `_sass/cocktails/_cocktail.scss`,
   `assets/js/card-name-fit.js`, `assets/js/universe.js`,
   `_layouts/default.html`, `_dev/card-glasses.html`.
6. ~~Yellow is the loudest active state and belongs to PRACTICALITIES~~
   **Done 2026-09-04.** Neither of the audit's directions survived looking
   (tints "aren't working for me"; the cobalt swap "very visually
   unbalanced"). Helen's own answer reorders the five: magenta, lime,
   cerulean, orange, aureolin, so the yellow becomes I KNOW WHAT I WANT and a
   hit title wears a highlighter. Cobalt deleted; LEAVE OUT keeps the violet
   rule alone, grey, like cocktails. `food/_palette.scss`,
   `food/_category-labels.scss`, `food/_buttons.scss`.
7. **The card's green bottom rule reads as a progress bar** (refinement).
   Span the card at rest, or run it vertically along the column's inner edge.
8. **Tablet.** Nothing in this review was seen on an iPad. Breakpoints: 400,
   600, 720, 820, 1180. She cooks and mixes at 1024 landscape and 768
   portrait; the drink page's inline-glass layout below 1180 is the least
   verified path. Ask her for captures before changing anything.

## 4. Things that are hers, not yours

- The leopard decision (§2).
- Whether the recipe title should also get the tape (she chose flat display
  lettering; the tape was offered and declined).
- Any new hue. The site has six on food and five on cocktails and both
  palettes argue at length that the count is the design.
- The voice. Do not touch a word of copy.

## 5. Reference

- The audit itself and the candidates pages are Artifacts in Helen's gallery
  (private): the design audit, food and cocktails fold rounds one and two,
  leopard rounds one and two, lettering candidates, drink page candidates.
  They are not in the repo and go stale as the site moves; rebuild rather
  than trust.
- `LETTERING.md` and `LEOPARD.md` are the two references written this
  session; HANDOVER §9.13 was rewritten in place for the drink page.
