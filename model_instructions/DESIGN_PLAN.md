# DESIGN PLAN — where the 2026-09-02 design review got to, and what is next

Written 2026-09-02 at the end of one long session with Helen, for whoever
picks the design work up next. It is a status board and a queue, in priority
order. Everything else is a decision Helen has made but not built, or a
question she has not answered. Do not re-litigate the decisions; do build them.

**§1 IS THE STATUS, NOT THIS HEADER.** This line said "PRs #660–#663 and the
mechanical PR before them" and stayed there while §1 grew rows dated 2026-09-03
and 2026-09-04 — the drink page rebuild, the heading ramp, the universe section
coming off food. **Read the table; add a row when you ship; do not restate the
tally up here**, because a header that has to be edited in step with a table is
a second copy of it, and this is what a second copy does.

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
| Index greys fail contrast | ingredient line 12%, pantry 14% lightened from clear-text; both clear 4.5:1 | `_sass/food/_recipe-list.scss` |
| Lists read with hands full | ingredients and method at weight 400 | `_sass/food/_recipe-ingredients-method.scss` |
| Dead space under the back arrow | title margin closed where the arrow renders | `_sass/food/_recipe-header.scss` |
| DONENESS reads as a fourth section | 1.35rem, single violet rule | `_sass/food/_temperature-chart.scss` |
| Ship mark is a private code | "ship it?" legend beside the survivor count | `cocktails/index.html`, `_filters.scss` |
| About dividers look like broken headings | the footer's dashed hairline (Helen overrode the earlier decision) | `_sass/food/_about.scss` |
| Nothing edible above the fold | **tighten**: section gap 0.75rem, label gap 0.5rem, filter headings 1.05rem / 1.2rem, panel padding 0.3rem; **the universe says…**: one random row cloned above the panel with "deal again", both sites. **Off food since 2026-09-04** (Helen: the panel of choices is the fold on a triage site); on cocktails it is a whole card dealt into the right-hand column with the label on the left, a first pass she means to refine | `_sass/shared/_tokens.scss`, `_sass/shared/_rule.scss`, `assets/js/universe.js`, `_sass/cocktails/_universe.scss` |
| Punched lettering never worked dark-on-light | four tiers (display / heading / label / plain); food's highlight is a mid grey and its shadow faint; HELEN TRIAGES and the recipe title hard, other headings soft, everything under 1rem edge-only; FAQ questions match SERVES/PREP/COOK; [ COCKTAILS ] wears [ FOOD ]'s tape lettering | `_sass/shared/_rule.scss`, both `_rule.scss`, `LETTERING.md` |
| Second typeface without a rule | Plex is for numbers you act on: amounts on both sites, chart readouts and ticks, calculator inputs and results; note labels back to Courier; Plex 700 dropped | `_sass/shared/_fonts.scss`, both palettes |
| Drink page half-inverted, colours off-job | rebuilt to Helen's brief: glass large in the margin, name on the card tape, glass/garnish/ship it? meta, card chips, yvette-over-absinthe under Ingredients and Method and under each ingredient name, lagoon on Notes and its cards, pink suggestions, ink numerals, read it / make it slider, shared ship include | `_layouts/cocktail.html`, `_sass/cocktails/_cocktail.scss`, `_includes/cocktails/ship.html`, `assets/js/cocktail-make.js` |
| Section greens read as green on green (critical #4); headings smudged (#680); drink-page headings too small (#679 pt 4) | **2026-09-03.** A reposado-to-yvette ramp through pink (coral, hot pink derived in OKLCH) under the five index headings, ONE bar, the shared absinthe bar gone; each section's colour also on its chosen filter word and on the chip or band it lit on a card, so "magenta means matched everywhere" is reversed and cosmopolitan means HAS TO HAVE again; index headings 1.4rem / weight 400 / 0.14em, drink-page section headings 1.8rem / 400, punch kept on both. The mechanism: bold light-on-dark stems bloom into the punched highlight. `index-section-label` gained `$weight`. | `_sass/cocktails/_palette.scss`, `_sass/cocktails/_rule.scss` (heading-rule is single-bar now), `_sass/cocktails/_filters.scss`, `_sass/cocktails/_cards.scss`, `_sass/cocktails/_cocktail.scss`, `_sass/shared/_rule.scss` |
| Drink page top (#679: title too big, no spare tape, meta crammed, headings small) | **2026-09-03.** Root cause of the first two: the h1 at `display: contents` still took the UA's `2em`, so the title rendered at double and the tape's em padding at half. Fixed with `font-size: 1em`; title 3.2rem (the rendered size Helen chose), the card's horizontal tape padding with 0.5em vertical, meta gap 5rem, glass absinthe / stroke 3 / floor 14rem, section headings absinthe over yvette (NOTES over lagoon), one yvette band under each ingredient name. Unseen on iPad until deployed. | `_sass/cocktails/_cocktail.scss` |
| The universe section (#719 umbrella: #714 the card, #693 "deal again", #692 the pool) | **2026-09-05, four candidate rounds on the real index.** The card is gone: it is **one line** — a tiny glass, the name on its tape, the ingredients in round brackets — in a three-column grid with `deal again` at the far right, which *is* the fix for #693 (the control under the label read down the page as "the universe says deal again"). Deals only from ship `yes` / `oh gods yes` (#692), naming the rungs rather than borrowing `data-chaos`. No box, no ship, no moods, no square brackets, never full width: *"I want it to be a happy invitation."* The glass breaks the card's scaling rule deliberately — one height for all 27 drawings in a fixed 2.3rem slot, so the tape cannot move on redeal. | `cocktails/index.html`, `_sass/cocktails/_universe.scss`, `_sass/cocktails/_filters.scss` |
| The shortlist toggle was never styled on cocktails (#729/#730) | **2026-09-05.** Not a taste question: food styled its `.btn-shortlist-only` and cocktails never did, so it shipped as a raw grey system button. Now `%drink-btn-base`'s pill — the shape `.btn-pool` already wears — on its own row under the count, with the "ship it?" legend brought down beside it so it is not left hovering over the card grid. Food's took the same shape and placement, in food's colours, on Helen's ask the same day. | `_sass/cocktails/_shortlist.scss`, `_sass/food/_shortlist.scss`, both indexes |
| Two mis-diagnosed index bugs (#675, #698) | **2026-09-05, and neither was what it looked like.** #675 "a space is required between 125 and survivors" was raised as (copy) and was a layout fault: **a flex container discards whitespace between its items**, so the word space died the day `.drink-count` went flex for the legend. Deleted rather than patched, because moving the legend out made the container non-flex again. #698 "no dot before the first chip" was never chip one — the `& + &` rule already covered that — it was the first chip of the **second row**, on 61% of drinks. Fixed by measuring `offsetTop`. | `_sass/cocktails/_filters.scss`, `assets/js/chip-rows.js`, `_sass/cocktails/_cards.scss` |

## 2. Decided, not yet built

1. ~~"Deal again" icon.~~ **The universe section came off food on 2026-09-04**
   — Helen, having seen it deployed and then a styled row and two card
   treatments on the real page: "I think it's the feature, not your work…
   I don't think anyone (and certainly not me) opens a triage website to
   click on a random recipe." **And the question is closed on cocktails too,
   2026-09-05**: the control kept its words and moved to the far right of the
   universe row (#693), which is where an icon would have been the alternative
   answer. It still carries `↻` after the words. Nothing left to decide.
2. **Leopard.** Round one she chose L3 (sheen). Round two (five patterns ×
   four placements) she has not decided, and said "leave leopard with me…
   don't ship anything." `model_instructions/LEOPARD.md` has the generator,
   every value and the rules. When she decides: solve the tile at build
   time from the palette, place per §5 of that file.
3. **#650 has one answer already, on one element.** The issue asks whether the
   27 glass drawings, all judged against paper, still work on black — and the
   universe line's tiny glass had to answer a piece of it early: at 1.4rem the
   card's stroke weight of 1 is proportionally about seven times heavier,
   because `vector-effect: non-scaling-stroke` means a fixed number of SCREEN
   pixels. Helen chose 0.7 there off a switch carrying 0.5 / 0.7 / 1. That is a
   ruling about one ornament at one size, **not** about the artwork, and #650's
   real question — the drawings on the new ground at card and drink-page size —
   is untouched. The cheap version is still a dev page putting all 27 on black
   at both sizes and letting her look.

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
   hover. `_sass/food/_recipe-list.scss`, `_sass/food/_badges.scss`,
   `_sass/food/_active-filter-states.scss`.
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
   `_sass/shared/_rule.scss` (`overlapping-rule-double-last-line`),
   `_sass/food/_recipe-header.scss`, `_layouts/default.html`.
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
   rule alone, grey, like cocktails. `_sass/food/_palette.scss`,
   `_sass/food/_category-labels.scss`, `_sass/food/_buttons.scss`.
7. ~~The card's green bottom rule reads as a progress bar~~ **Done
   2026-09-04**: four treatments on the real index; Helen, "Agree, no mark,
   end of." Nothing at rest, since the absinthe glass already carries the
   column's green; the magenta brackets stay hover-only. `_sass/cocktails/_cards.scss`.
8. **Tablet — PARKED by Helen, 2026-09-04.** Nothing in this review was seen
   on an iPad. Breakpoints: 400, 600, 720, 820, 1180. She cooks and mixes at
   1024 landscape and 768 portrait; the drink page's inline-glass layout
   below 1180 is the least verified path. A page of iframes at 768 and 1024
   was built (`tmp/mock/tablet.py`, the §11.2.1 pattern) and she declined to
   use it: "viewport wrangling is never as good as just looking at it... It's
   not a showstopper to deploy something ugly, basically, as we can just fix
   it when we have real data." So: ship, look on the iPad, fix what she sees.
   Do not raise this again until she has looked.

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
