# LEOPARD — black-on-black print for the cocktails site

What is on the site (#733), how it is drawn, how it reaches the screen, and
what must not happen to it. Read the whole thing before touching a value.
Section numbers are cited from scripts and Sass, so they are kept as they are.

## 1. What it is, in one paragraph

Helen's premise for the cocktails site is "black on black" (MANUAL §9.13).
Leopard is her favourite texture in real life, and black-on-black leopard is
the site's texture: splodges of fur a step or two lighter than the ground,
visible when you look and gone when you don't. It is a **texture, never a
pattern**: if you can see it from across the room it is too loud. The glasses
stay the line work; the print is the fur they sit on.

## 2. What is live

| what | value | where |
|---|---|---|
| the print | `assets/img/cocktails/leopard-fur.svg`, 2880 × 960px, drawn at strength 1.5 | drawn once into a picture by `assets/js/ground-print.js` (§7), which `_sass/cocktails/_leopard.scss` lays on `body` |
| the ground's texture | `assets/img/cocktails/leopard-nap.svg`, 480 × 480px, at full strength; half at 600px wide and under | under the print, in the same picture |
| the page ground | `$color-paper: #030304` | `_sass/cocktails/_palette.scss` |
| header and footer | `$color-chrome-ground: #060607`, flat, no print | `_palette.scss`; reaches `shared/_layout.scss` as `--chrome-ground` and `--footer-band` (§6) |
| cards | `$color-surface: #0d0d0f` | `_palette.scss`; every surface on the site, not only cards |

The three colours are always in that order, each lighter than the one before:
page, band, card. A card sits light on the fur.

**Neither SVG has a colour in it.** Both are white at very low alpha, so the
print keeps the same distance from whatever is under it and the page's
darkness is one palette variable.

**Both files are generated**, never hand-edited:

    python3 scripts/build_leopard.py --write    regenerate both files and the version
    python3 scripts/build_leopard.py --check    exit 1 if either differs from the generator

`--write` also writes `_sass/cocktails/_leopard-version.scss`, a hash of the
two files. Commit all three together. Run `--check` by hand after touching the
generator; the suite does not run it, and the script's docstring says why.
`tests/test_site_config.py` checks three things: the stylesheet lays the
picture at the fur file's own size, the files it names exist and it never
loads one with `url()`, and the version is the hash of the committed files.

The fur tile is about half a megabyte as written and the heaviest thing a
cocktails page loads, once. §9 says where the weight is.

## 3. The generator — `scripts/leopard_splodge.py`

Pure Python, no dependencies, deterministic for a given `seed`. Its docstring
is the spec; this is the shape of it.

1. **Placement.** Rosette centres are placed by rejection sampling in a 960px
   cell, each kept only if it clears every accepted one by `min_gap`. Small
   lone spots are placed afterwards in what is left.
2. **A rosette** is one to three arc blobs round an empty middle (a C, a
   pair, a triple) or a solid bean. A blob is an outline walked out and back
   along an arc: fat in the middle, pinched at the ends, slow noise for the
   lumps, fast jitter for the edge. Every shape is generated from the seed;
   nothing is traced from a picture.
3. **Tufts.** Short strokes overhang each blob's edge on the side the fur
   leans towards, and not on the other: pile lying one way over a marking.
4. **Each blob has its own strength**, so no two are quite the same black.
5. **The crinkle** inside a blob is `fur`: short straight strokes that all
   lean roughly one way, the lean drifting slowly across the tile. `scribble`
   and `contour` are the generator's other two and ship nowhere.
6. **The offset repeat.** With `columns=3` the cell one to the right sits a
   third of a cell lower, and the placement wraps on that slanted lattice so
   every seam still joins. The same splodge comes back at the same height
   2880px along instead of 960px. The SVG is three cells wide and one tall.
7. **Everything is geometry** (the ragged edges, the tufts, the strokes), so
   the copies at a seam match exactly.

`ground_tile()` in the same file draws the ground's own texture: `nap`, short
vertical fibres, or `grain`, fine and even. It is a separate, tiny tile.

`scripts/leopard_tile.py` is an earlier generator: broken rings with a core
and a sheen. Nothing ships from it.

## 4. The settings, and the candidates page

The settings `scripts/build_leopard.py` passes are Helen's, each chosen by
looking at the real pages:

- the `fur` crinkle, on the page ground;
- the repeat offset over three columns, so a large splodge is not seen twice
  at one height either side of the card grid;
- the `nap` ground texture;
- header and footer as flat bands, with no print and no nap: "I prefer the
  flat";
- cards solid and lighter than the page: "I like the cards sitting light on
  the leopard."

A change to any of them is hers to make, on a candidates page (MANUAL
§13.11): the real index and a real drink page, the real compiled CSS, a bar
of switches. `scripts/leopard_candidates.py` builds it and is committed so
that the next round starts from a script that exists; a mock script kept in
`tmp/` is lost with it. Its docstring says what state it is in and what to
change first.

## 5. Where it goes, and where it never goes

- **On `body`, and only there.** `background-repeat: repeat`, the picture at
  the fur tile's own size in px. **Never scale it with the viewport**; a print
  has a real size, like fur does.
- **Not on the header or the footer.** The two bands are flat: no print, and
  no nap.
- **Never on a card, never behind small text on a card.** Cards stay solid.
  Never on the tape. Never on hover (nothing on a card moves under the cursor
  except colour).
- **The recipe text on a drink page sits directly on the print.** That is
  part of what Helen chose.
- **Not on paper.** `shared/_print.scss` sets `background: transparent` on
  `html` and `body`, which takes the picture with it.
- **Not on food.** Food's stylesheet declares no print, so the script draws
  none; the tiles are white on black and would do nothing on a light ground.

## 6. How the two bands work

`shared/_layout.scss` reads two custom properties and falls back when a site
sets neither, so food's header and footer are unaffected:

- `.site-header { background: var(--chrome-ground, $color-surface) }`
- `.site-footer { border-image: var(--footer-band, none) }`

Cocktails sets both in `_leopard.scss`. Without a band the footer has no
ground and the print shows through it. The band is a gradient used as a
border-image with a 100vw outset: the first pixel is the rule along the top,
the rest is the ground. It is a border-image rather than a 100vw
pseudo-element because an outset is paint, not layout, and cannot give the
page a sideways scroll. It replaces the footer's dashed, column-width top
border with a solid full-width one, which is what Helen saw and chose.

## 7. How it reaches the screen — drawn once on the device, and kept

**The stylesheet does not load the SVGs.** An SVG used as a CSS background is
not a picture the browser slides about; it is redrawn for every strip of page
that scrolls into view, and this one is many thousands of strokes. Two
`url()`s on `body` made the page slow to load and scrolling judder on Helen's
phone and her laptop.

Shipping a bitmap instead would break the site's oldest principle. Helen:
"one of the very coolest things I wanted to achieve here was great styling
with zero images — basically no annoying dependencies, meaning fewer
device/software/network bugs." So `assets/js/ground-print.js`:

1. reads six custom properties `_leopard.scss` declares on `:root`: the two
   file names (`--ground-print`, `--ground-nap`), the ground colour
   (`--ground-print-ground`), the version (`--ground-print-version`) and the
   two strengths (`--ground-print-strength`, `--ground-nap-strength`);
2. asks IndexedDB for a picture kept under exactly that request, and if there
   is one, hands it to the stylesheet as `--ground-picture` and stops;
3. otherwise waits for the page to finish loading, draws ground, nap and fur
   into a canvas once, at the fur tile's own size in CSS pixels, turns that
   into a PNG in memory, hands it over, and keeps it. One picture is kept;
   the store is emptied before a new one goes in.

The repo ships no image, and a browser draws the leopard once per change of
artwork, not once per scroll.

What follows from that, and should not be "fixed":

- **The picture is deliberately not sharpened for a dense screen.** One CSS
  pixel per picture pixel. Helen: "I quite like the softness of drawn once on
  a mobile." Three times the pixels each way is also nine times the memory.
- **The ground is plain until the picture arrives**: for a moment on every
  page, for a second or so on the first visit, and for good with scripts off
  or a canvas that will not draw. None of those is an error.
- **The nap is baked into the picture**, and the kept picture's key carries
  the site, the version, both strengths and the ground colour.
- **A browser with no IndexedDB** (private mode, blocked site data) draws on
  every page load instead.
- **Never bump `--ground-print-version` by hand.** It is the build script's
  hash. If it does not change when the artwork does, every browser that has
  visited goes on showing the old leopard.

## 8. Strength, and what a phone gets

Both files are white at a few percent alpha, so drawing the same file twice is
very nearly twice as light. `ground-print.js` takes a strength and draws that
many passes (1.5 is one full pass and one at half; the ceiling is 4). A
stronger or fainter leopard is a number in `_leopard.scss`, not new artwork.

- **The fur is 1.5 everywhere**: "for all: mobile, ipad and desktop."
- **The nap is 1, and 0.5 on a phone**: "nap half for phone, everything else
  is the same. Ipad is same as desktop." That is `--ground-nap-strength` in a
  media query, and it is the only thing a phone gets differently.
- **A phone is 600px wide and under**, `shared/_layout.scss`'s own phone
  block. The narrowest iPad is 744px.
- **"A darker nap" is a fainter nap.** The nap is white fibres; with the
  ground three steps from pure black there is nothing below it to draw.
- **The darkness of everything is the palette**: page, band and card (§2),
  and the washes Sass mixes over the card colour, which follow it. The aim is
  "'black on black', ish"; pure black for the page was offered and not taken.

## 9. Traps

- **Do not hand-edit an SVG.** Change the generator, run the build script,
  commit the two SVGs and the version partial together.
- **Do not put the SVG back in a `url()`.** It is the obvious simplification
  of `_leopard.scss` and it is the judder of §7; a test refuses it.
- **Do not reinstate "a card is the darkest thing on the page"** from an old
  comment. The page is darker than a card (§2).
- **`min_gap`** below about 0.85 lets rosettes touch and the print turns to
  camouflage; above about 1.2 it turns to polka dots.
- **`count` and `radius` fight over the same cell.** The sampler gives up
  quietly at its `tries` cap; a sparse tile means it ran out of room.
- **The `contour` crinkle cannot be offset.** It is a stitched noise field,
  periodic in the plain cell, and the generator refuses the combination.
- **A change of `seed` is a different leopard.** Every splodge moves. That is
  a design decision and needs Helen to look at it, not a refactor.
- **Where the weight is**, if it is ever wanted back: about half the fur tile
  is the crinkle strokes. Fewer strokes per blob (`box / 26` in
  `splodge_tile`) is the cheapest saving and the one most likely to be
  invisible; Helen has not seen a lighter one. Drawing the tufts clear of
  their blobs to drop the mask is not a saving to try again: "it all looks
  like spiders."
- **A headless desktop browser taking a screenshot says nothing about
  scrolling on a phone.** For anything that paints a lot, put it in front of
  Helen's phone before it merges: a bundle of the real build published as an
  Artifact does that without a deploy.
