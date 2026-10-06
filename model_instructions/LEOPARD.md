# LEOPARD — black-on-black print for the cocktails site

First written 2026-09-02, the day Helen saw the first samples and said "oh my
god I'm in love". **Rewritten 2026-10-06, the day it shipped** (#733): five
rounds, and what is on the site is not what round one drew. This is what is
live, how it is drawn, how each choice was made, and what must not happen to
it. Read the whole thing before touching a value.

## 1. What it is, in one paragraph

Helen's premise for the cocktails site is "black on black" (MANUAL §9.13,
#469). Leopard is her favourite texture in real life, and black-on-black
leopard is the texture the site was missing: splodges of fur a step or two
lighter than the ground, visible when you look and gone when you don't. It is
a **texture, never a pattern**: if you can see it from across the room it is
too loud. The glasses stay the line work; the print is the fur they sit on.

## 2. What is live

| what | value | where |
|---|---|---|
| the print | `assets/img/cocktails/leopard-fur.svg`, 2880 × 960px | `body`, in `_sass/cocktails/_leopard.scss` |
| the ground's texture | `assets/img/cocktails/leopard-nap.svg`, 480 × 480px | under the print, same rule |
| the page ground | `$color-paper: #060607` (was `#0e0e10`) | `_sass/cocktails/_palette.scss` |
| header | `$color-chrome-ground: #0c0c0d`, flat, no print | `--chrome-ground`, read by `shared/_layout.scss` |
| footer | a full-width band in the same `#0c0c0d`, flat, no print | `--footer-band`, read by `shared/_layout.scss` |
| cards | untouched, `$color-surface: #17171a` | — |

**Neither SVG has a colour in it.** Both are white at very low alpha, so the
print keeps the same distance from whatever is under it and the page's
darkness is one palette variable. Both files are **generated**:
`python3 scripts/build_leopard.py --write`, never a hand edit. `--check`
compares the committed files with what the generator draws; run it by hand
after touching the generator (the suite does not, on purpose — the script's
docstring says why). The suite does check that the stylesheet lays each tile at
the file's own size
(`test_the_leopard_tiles_are_laid_at_their_own_size`).

The fur tile is 495 KB as written and about 155 KB gzipped, which is more than
all eight font faces together. It is the single heaviest thing a cocktails
page loads. Helen has not been asked to trade any of the look for weight;
§7 says where the weight is if that is ever wanted.

## 3. The generator — `scripts/leopard_splodge.py`

Pure Python, no dependencies, deterministic for a given `seed`. Its docstring
is the spec; this is the shape of it.

1. **Placement.** Rosette centres are placed by rejection sampling in a 960px
   cell, each kept only if it clears every accepted one by `min_gap`. Small
   lone spots are placed afterwards in what is left.
2. **A rosette** is one to three ARC BLOBS round an empty middle — a C, a
   pair, a triple — or a solid bean. A blob is an outline walked out and back
   along an arc: fat in the middle, pinched at the ends, slow noise for the
   lumps, fast jitter for the edge. Nothing is traced from anything; see §4,
   round three.
3. **Tufts.** Short strokes overhang each blob's edge on the side the fur
   leans towards, and not on the other — pile lying one way over a marking.
4. **Each blob has its own strength**, so no two are quite the same black.
5. **The crinkle** inside a blob is `fur`: short straight strokes that all
   lean roughly one way, the lean drifting slowly across the tile. (`scribble`
   and `contour` are the two Helen did not choose and are still in the
   generator.)
6. **The offset repeat.** With `columns=3` the cell one to the right sits a
   third of a cell lower, and the placement wraps on that slanted lattice so
   every seam still joins. The same splodge comes back at the same height
   2880px along instead of 960px. The SVG is three cells wide and one tall,
   and draws the one cell six times with `<use>`, so it costs no extra bytes.
7. **Everything is geometry** — the ragged edges, the tufts, the strokes — so
   the copies at a seam match exactly. (The first generator used a
   displacement filter for raggedness and its seams were only nearly right.)

`ground_tile()` in the same file draws the ground's own texture: `nap`, short
vertical fibres, or `grain`, fine and even. It is a separate, half-kilobyte
tile layered under the print in CSS.

`scripts/leopard_tile.py` is the **first** generator (rounds one and two):
broken rings with a core and a sheen. Nothing ships from it. It stays because
round one's ruling is recorded in its terms.

## 4. The rounds, and what Helen chose

Every choice was made on a candidates page (MANUAL §13.11): the real index and
a real drink page, the real compiled CSS, a bar of switches.
`scripts/leopard_candidates.py` builds it and is round five's state.

- **Round one (2026-09-02).** Six tonal variants of the ring generator, cards
  section only. **L3, sheen**: "The sheen really brings it to life." Then she
  asked for a more extreme pattern, more shades, print in the gutters, a
  leopardy header and footer, and "can you make it... furry?"
- **Round two (2026-09-02).** Five patterns × four placements. Never decided:
  "Leave leopard with me. Write instructions for it, but don't ship anything."
  Parked as #733 on 2026-09-05 — "parked not canned". Its mock script was in
  `tmp/` and was lost; it was rebuilt on 2026-10-06 from the tone table
  (below) for her to look at again.
- **Round three (2026-10-06).** Helen brought two pictures she had had
  Shutterstock's generator draw, which she could not licence on terms she
  wanted, and asked for something like them. **Nothing was traced or copied
  from them.** What was taken was the recipe — lumpy ragged blobs round an
  empty middle, a fine crinkle inside each a step lighter, an uneven ground —
  and a new generator was written to draw its own shapes from a seed. Three
  loudnesses; **"Splodge quiet is great!"**
- **Round four (2026-10-06).** Her asks, in order: relax the rule that a card
  is the darkest thing on the page; "see the whole thing darker"; vary the
  ground "not in blobs, across the whole thing"; a crinkle closer to her
  pictures "or even shorter, stabbier lines, like fur"; more tufting; splodges
  that are not all the same black. Three crinkles × three grounds × three
  ground textures. **"Oh my goodness, it's so ...furry!!!!! ... I choose
  furry, darkest and nap from these, in the page ground."**
- **Round five (2026-10-06).** Two questions she raised from round four.
  The bands: "should we try darkening the header and footer background
  colour? They seemed dark before, but now they really don't. I like the
  cards sitting light on the leopard, so don't touch those." And the repeat:
  "sometimes some of the larger splodges can be seen either side of the card
  grid which makes it clear they're repeated." **"Same as the page, offset,
  and plain. Sold."**
- **After it was built (2026-10-06, before the merge).** The candidates page
  had the nap texture on its two bands; the built bands are flat, and she was
  told. "Ahhh right, I had noticed the napping, but thought I could get an
  idea of the background colour anyway. **I prefer the flat. Let's lift to
  'darker still' please.**" So the bands are `#0c0c0d`, round five's third
  option, not the page's `#060607`: a flat band in the page's own black had
  nothing to tell it from the page but a hairline.

### The rule that went

The first version of this document had one rule about tone: *a card must stay
the darkest thing on the page*, so rosettes could rise to `#151517` and no
further. Helen relaxed it in round four and the site no longer keeps it: the
page is now darker than a card, and a card sits light on the fur. Do not
reinstate it from an old comment.

### The ring generator's tones (rounds one and two; nothing ships from these)

| set | ground | ring | core | sheen | inner | mottle |
|---|---|---|---|---|---|---|
| sheen (round 1's L3) | `#0e0e10` | `#151517` | `#121214` | `#1c1c20` | — | — |
| more shades | `#0e0e10` | `#161619` | `#101012` | `#1d1d22` | `#121214` | `#111113` |
| extreme | `#0e0e10` | `#1b1b1f` | `#0b0b0d` | `#26262b` | `#141416` | `#121214` |
| furry | as "more shades" + `fur=True` | | | | | |
| furry, extreme | as "extreme" + `fur=True, fur_scale=9` | | | | | |

On the header band (`#17171a` then) the sheen set was ring `#1d1d21`, core
`#1a1a1e`, sheen `#25252a`. The other sets' band tones were never recorded;
the 2026-10-06 rebuild derived them by adding the ground's own step (+9, +9,
+10 per channel) to each page tone.

## 5. Where it goes, and where it never goes

- **On `body`, and only there.** `background-repeat: repeat`, each tile at its
  own size in px. **Never scale it with the viewport**; a print has a real
  size, like fur does.
- **Not on the header or the footer.** Helen tried a leopard header in round
  five and chose plain. The two bands are flat: no print, and no nap — "I
  prefer the flat."
- **Never on a card, never behind small text on a card.** Cards stay solid.
  Never on the tape. Never on hover (nothing on a card moves under the cursor
  except colour).
- **The recipe text on a drink page sits directly on the print.** That was in
  front of her in every round and is part of what she chose.
- **Not on paper.** `shared/_print.scss` sets `background: transparent` on
  `html` and `body`, which takes the images with it.
- **Not on food.** Food has no leopard, and the tiles are white on black:
  they would do nothing on a light ground.

## 6. How the two bands work

`shared/_layout.scss` reads two custom properties and falls back to what it
always did, so food compiles to the header and footer it had:

- `.site-header { background: var(--chrome-ground, $color-surface) }`
- `.site-footer { border-image: var(--footer-band, none) }`

Cocktails sets both in `_leopard.scss`. The footer had **no ground at all**
before this, so the print showed straight through it. Its band is a gradient
used as a border-image with a 100vw outset — the first pixel is the rule along
the top, the rest is the ground. It is a border-image rather than a 100vw
pseudo-element because an outset is paint, not layout, and cannot give the
page a sideways scroll. It **replaces the footer's dashed, column-width top
border with a solid full-width one**; that is what Helen saw and chose.

## 7. Traps

- **Do not hand-edit an SVG.** Change the generator, run the build script,
  commit both.
- **`min_gap`** below ~0.85 lets rosettes touch and the print turns to
  camouflage; above ~1.2 it turns to polka dots.
- **`count` and `radius` fight over the same cell.** The sampler gives up
  quietly at its `tries` cap; a sparse tile means it ran out of room.
- **The `contour` crinkle cannot be offset.** It is a stitched noise field,
  periodic in the plain cell, and the generator refuses the combination.
- **A change of `seed` is a different leopard.** Every splodge moves. That is
  a design decision and needs Helen to look at it, not a refactor.
- **Where the weight is**, if it is ever wanted back: about half the fur tile
  is the crinkle strokes (the same tile with the `contour` crinkle, which has
  none, was 256 KB against 497). Fewer strokes per blob
  (`box / 26` in `splodge_tile`) is the cheapest saving and the one most
  likely to be invisible; she has not seen a lighter one.
- **What has not been measured:** how long a phone takes to draw the tile. It
  is one SVG with a mask, rasterised once per page. It drew without trouble
  in headless Chromium at 360, 390 and 1280px wide; no real phone has been
  timed.
