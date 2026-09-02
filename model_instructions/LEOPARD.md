# LEOPARD — black-on-black print for the cocktails site

Written 2026-09-02, the day Helen saw the first samples and said "oh my god I'm
in love". This is how the pattern is drawn, what every dial does, what she has
chosen so far, and what must not happen to it. Read the whole thing before
touching a value.

## 1. What it is, in one paragraph

Helen's premise for the cocktails site is "black on black" (HANDOVER §9.13,
#469). Leopard is her favourite texture in real life, and black-on-black
leopard is the texture the site was missing: rosettes in a black one or two
steps lighter than the ground, visible when you look and gone when you don't.
It is a **texture, never a pattern**: if you can see it from across the room it
is too loud. The glasses stay the line work; the print is the fur they sit on.

## 2. The generator — `scripts/leopard_tile.py`

One function, `rosette_tile(...)`, returns a seamless SVG tile as a
`data:image/svg+xml;base64,...` URI plus its byte length. It is pure Python,
no dependencies, deterministic for a given `seed`. Run it bare to print the SVG
size; `--uri` prints the data URI.

How a tile is drawn:

1. **Placement.** `count` rosette centres are placed by rejection sampling in a
   `size`×`size` square (720 by default). A candidate is kept only if it is at
   least `(r_new + r_existing) * min_gap` from every accepted centre, measured
   on the torus (distance wraps at the tile edge), so the print is even and
   the seam is invisible.
2. **A rosette** is an ellipse of radius `r` (26–44px × `scale`) squashed to
   0.7–0.95 on one axis and rotated at random. Around it sit 3–5 thick arc
   fragments (spans of 38–75°, gaps of 14–40°), stroked with round caps at
   `ring_width` (7–11px × `scale`). Inside sits a smaller ellipse, the core,
   at 0.42 of the radius, offset up to 18% off centre. Real rosettes are
   broken rings with a darker centre; spots read as polka dots, so nothing
   here is a closed shape.
3. **Wrapping.** Every rosette is drawn nine times, at offsets of −size, 0
   and +size on each axis, and clipped by the tile. That is what makes the
   tile seamless; the placement on the torus is what makes it *look* seamless.
4. **Layers**, each optional, painted in this order: `mottle` (large soft
   ellipses barely off the ground, between rosettes), then per fragment the
   `sheen` copy offset 1.3px up-left, the `ring` itself, and an `inner` arc at
   0.42 of the ring width nudged down-right; then the `core`.
5. **Fur.** With `fur=True` the whole rosette group is passed through an SVG
   filter: `feTurbulence` (fractalNoise, baseFrequency 0.045, 3 octaves)
   feeding `feDisplacementMap` at `fur_scale` (7 by default, 9 for the
   extreme set), which drags every edge by a few pixels of noise so it is
   ragged like pile. A second filter lays fine grain over the whole tile:
   feTurbulence at 0.9 through an feColorMatrix that turns it into white at
   alpha `grain` (0.05). Both filters live inside the SVG, so they work when
   the SVG is used as a CSS background image; nothing external is referenced.

The SVG is ~40 KB for the plain sheen tile and ~140 KB with mottle and fur,
before base64. That is the whole cost; there are no raster images.

## 3. The tones, and the one rule about them

Every tone is solved against the ground it sits on, and the rule is that **a
card must stay the darkest thing on the page** — the inversion's structural
choice (§9.13: a card is `#17171a` on a `#0e0e10` page, and it recedes rather
than floats). So on the page ground the rosettes may rise to `#151517`
(L\* ≈ 6.5) and no further; the card at L\* 7.85 still sits below them. The one
deliberate exception is the "extreme" set, which breaks this on purpose so
Helen could see the ceiling.

| set | ground | ring | core | sheen | inner | mottle |
|---|---|---|---|---|---|---|
| sheen (round 1's L3, **chosen**) | `#0e0e10` | `#151517` | `#121214` | `#1c1c20` | — | — |
| more shades | `#0e0e10` | `#161619` | `#101012` | `#1d1d22` | `#121214` | `#111113` |
| extreme | `#0e0e10` | `#1b1b1f` | `#0b0b0d` | `#26262b` | `#141416` | `#121214` |
| furry | as "more shades" + `fur=True` | | | | | |
| furry, extreme | as "extreme" + `fur=True, fur_scale=9` | | | | | |

For the header and footer bands the ground is `#17171a` and every tone moves
up by the same step (ring `#1d1d21`, core `#1a1a1e`, sheen `#25252a` for the
sheen set; see `tmp/mock/leopard_v2.py`'s `PATTERNS` for the others), so the
print keeps the same distance from whatever it sits on.

A **sheen** copy is what "brought it to life" (Helen, round 1): a lighter
stroke offset up-left is the site's own emboss light source applied to fur.
Keep it. Keep it up-left.

## 4. What Helen has chosen so far

- Round 1 (2026-09-02, six tonal variants, cards section only): **L3, sheen.**
  "The sheen really brings it to life." She then asked for more: a more
  extreme pattern, more shades of black, print in the page gutters, a
  leopardy header and footer, and "can you make it... furry?"
- Round 2 (same day): five patterns × four placements. Not yet decided at the
  time of writing. **Record the decision here when she makes it**, and move
  the chosen values into `_sass/cocktails/_palette.scss` beside the greys they
  are solved against.

**STATUS, 2026-09-02: HELEN HOLDS THIS. DO NOT SHIP ANY OF IT.** Her words:
"Leave leopard with me. Write instructions for it, but don't ship anything."
Nothing under `_sass/` or `assets/img/` carries a leopard tile, and nothing
should until she says which pattern and which placement. `tmp/` is
gitignored, so the round-two mock script is not in the repo; the generator in
`scripts/leopard_tile.py` and the tone table in §3 are enough to rebuild any
of the twenty combinations. If you are an agent reading this because a task
mentions leopard, the task is to help her decide, not to build.

## 5. Placing it on the site (when it ships)

- The tile is a CSS `background-image` on the element whose ground it
  replaces, `background-repeat: repeat`, `background-size: 720px 720px`. Do
  not scale it with the viewport; rosettes have a real size like fur does.
- **Page ground:** on `body`. **Gutters only:** on `body`, with `main`
  painted solid `$color-paper` so the content column is a sheet laid on fur.
  **Cards section only:** a `::before` on `.drink-cards` at `z-index: -1`
  inside a `main` that establishes a stacking context. **Chrome:** the
  header band and, if the footer becomes a band, the footer, with the tile
  solved for `#17171a`.
- Generate at build time, not by hand: a small script that writes
  `assets/img/cocktails/leopard-paper.svg` and `leopard-chrome.svg` from the
  palette's values, so a tone change is one edit. The SVGs are plain files
  and go through `HTF.siteAsset` like every other piece of site artwork (§3).
- **Never behind small text on a card.** Cards stay solid. Never on the tape.
  Never on hover (nothing on a card moves under the cursor except colour).
  Not on paper: the print stylesheet strips it.

## 6. Traps

- The rosette tones are *lighter* than the ground, so on a light site this
  whole file inverts; do not port the values to food. Food has no leopard.
- `min_gap` below ~1.1 lets rosettes touch and the print turns to camouflage.
  Above ~1.4 it turns to polka dots. Both are wrong in the same way: real
  leopard is dense but every rosette is its own shape.
- `count` and `scale` fight over the same square: at `scale 1.4` more than
  ~18 rosettes will not place and the sampler gives up quietly at the `tries`
  cap. If a tile comes out sparse, that is why.
- The fur filter samples noise outside the tile's edge, so the displaced
  rosettes at the seam do not match their wrapped copies *exactly*. At
  `fur_scale` 7–9 the mismatch is a couple of pixels and invisible at tile
  size; at 20 it is not. If a seam ever shows, lower `fur_scale`, do not
  enlarge the filter region.
- `stitchTiles="stitch"` is set on the grain turbulence so the grain itself
  tiles; without it there is a faint square grid over the page.
