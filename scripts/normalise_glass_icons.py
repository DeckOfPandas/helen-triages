"""Normalise Helen's Inkscape glass exports into _includes/icons/glasses/.

WHAT IS WRONG WITH THEM AS EXPORTED, and why each fix is not cosmetic:

  1. `width`/`height` in MILLIMETRES. An icon that declares a physical size
     ignores its container. Stripped; the viewBox stays, so CSS decides.
  2. `stroke:#4c4c4e` hardcoded on all 104 paths. _sass/<site>/_palette.scss
     is the only place a colour is written down (three-layer rule), and JS/SVG
     read it via currentColor. Inline styles also BEAT the stylesheet, so a
     hardcoded stroke makes editing the palette appear to do nothing.
  3. A CONSTANT stroke-width across viewBoxes that run 27mm to 105mm wide.
     Rendered at a common height, a short-viewBox icon scales up more than a
     tall one, so the same 2.82 renders as a visibly different line weight per
     glass -- the same "an absolute length across a range of sizes is a range
     of different results" trap HANDOVER 13.4.1 documents for -webkit-text-
     stroke. Fixed with vector-effect="non-scaling-stroke", so the weight is
     set once in CSS and is identical on every icon whatever its viewBox.
  4. Inkscape/sodipodi metadata, empty <defs>, the XML declaration and the
     generator comment: all dropped. These are inlined into every drink page,
     so the bytes are paid for on every request.

Note the SVGs are INLINED by Liquid, not fetched by JS, so the `<svg ` vs
`<svg\\n` injection trap does not apply here -- but the output is written
with a space after `<svg` anyway, since it costs nothing and the repo has
been bitten by that assumption before.
"""
import pathlib, re, shutil, xml.dom.minidom

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "tmp" / "cocktail-glasses"   # drop new exports here
DST = ROOT / "_includes" / "icons" / "glasses"

# Not glasses. food-cloche-heart.svg is food's nav icon and already lives in
# _includes/icons/; " - Copy" is a byte-identical duplicate (checked, not
# assumed) of glass-old-fashioned.svg.
#
# The two rejected pineapples are kept in tmp/ rather than deleted, because the
# choice between them was a judgement call and the losers are the evidence for
# it. pineapple-1 is a 512x512 icon from a different family -- square canvas,
# rounded-rectangle body, stubby leaves. pineapple-2-bad-trace is Inkscape's
# Trace Bitmap output from the JPG, and it is bad for a structural reason worth
# recording: Trace Bitmap produces a FILLED OUTLINE OF THE INK, one compound
# path whose interior *is* the stroke, which is exactly why the edges looked
# right but the contents were not editable. Centreline tracing is the tool that
# would have given editable paths. Helen chose pineapple-3, 2026-08-17.
#
# THE GOBLET IS IN, AND IT IS DELIBERATELY AHEAD OF DEMAND. Nothing in the 117
# drinks asks for a goblet or a chalice, so on the collection alone it would be
# held back. Helen's call, 2026-08-17, and the reason is that the collection is
# not the inventory: "I have lots of tiki recipes that aren't in the database I
# gave you today, and given my rum obsession I bet we'll need it at some point."
# The same spec-not-inventory principle as declaring Plymouth and Genever gin
# while owning neither, and as `pudding in a glass` shipping with zero members.
# Worth knowing when it is used: the drawing is a wine-style goblet -- thin stem,
# small foot -- not the heavy-stemmed ceramic vessel "chalice" means in tiki, and
# at icon size it reads close to `wine`.
#
# shot-2.svg was an accidental duplicate (Helen, 2026-08-17) and its source is
# already gone from tmp/, so it simply stops being generated. No SKIP entry is
# needed for a file that does not exist -- adding one would be a rule guarding
# nothing, and the next person would go looking for the source it names.
SKIP = {
    "food-cloche-heart.svg",
    "glass-old-fashioned - Copy.svg",
    "glass-pineapple-1.svg",
    "glass-pineapple-2-bad-trace.svg",
}

# FILL-BASED ARTWORK, WHICH THE REST OF THE SET IS NOT. Every glass is drawn as
# open strokes with `fill: none`; the pineapple is a single compound path whose
# lattice is negative space, so forcing the stroke class onto it would outline
# the outline and produce mush. It gets its own class instead -- see
# `.glass-icon-solid` in _sass/cocktails/_cocktail.scss -- which fills with
# currentColor so the palette rule still holds and only the technique differs.
SOLID = {"glass-pineapple-3.svg"}

# Source name -> published name, where the export carries a working title.
RENAME = {"pineapple-3": "pineapple"}


# =============================================================================
# WHY THE GUARD BELOW IS STRUCTURAL AND NOT GEOMETRIC.
# =============================================================================
# The bug this exists to catch was real and shipped: the first version of this
# script dropped Inkscape's wrapping <g transform="translate(...)">, so all 21
# icons drew hundreds of units outside their own viewBox and rendered as blank
# space. Valid XML, clean build, no console error, nothing downstream can see
# it -- the icon is simply not there.
#
# TWO GEOMETRIC GUARDS WERE TRIED FOR IT AND BOTH WERE WRONG:
#
#   1. Pair the numbers in `d` as (x, y), build a bounding box, require it to
#      overlap the viewBox. It passed on the broken file. SVG path commands
#      have variable arity -- `h` and `v` take one number, `a` takes seven --
#      so one `h` flips the parity and every coordinate after it is read on
#      the wrong axis. The box inflates until it always overlaps. A guard that
#      cannot fail, written to catch a bug that had already happened: the third
#      time this codebase has produced one (HANDOVER §12).
#   2. Drop the axes and just bound the magnitudes. Too strict in the other
#      direction, because applying one translate to a pool that mixes x and y
#      is meaningless -- it rejected correct files.
#
# Getting either right needs a real path parser, which is a lot of code to
# check a property that is not actually the thing at risk. The thing at risk is
# STRUCTURAL: elements being dropped in transit. So the guard compares what
# went in with what came out -- every path preserved verbatim, the transform
# preserved, and no second transform anywhere that this script would silently
# discard. That cannot be satisfied vacuously, and it fails on precisely the
# bug that occurred.
# =============================================================================


# A nested <g> may carry a leftover editing nudge -- Inkscape writes one when
# you move a sub-selection. Dropping it moves that part of the artwork, which is
# the thing this guard exists to prevent, so it is only tolerated when it CANNOT
# matter: strictly a translate, and smaller than one user unit on every axis.
# The smallest viewBox in the set is 28 units wide, so one unit is under 4% of
# the narrowest icon and well under a pixel at any size the site renders. Louder
# than a silent drop, and it still fails hard on a real transform.
NEGLIGIBLE_UNITS = 1.0


def _negligible_translate(t):
    m = re.fullmatch(r"\s*translate\(\s*(-?[\d.]+)\s*(?:[, ]\s*(-?[\d.]+)\s*)?\)\s*", t)
    if not m:
        return None
    dx = float(m.group(1))
    dy = float(m.group(2)) if m.group(2) else 0.0
    return (dx, dy) if abs(dx) < NEGLIGIBLE_UNITS and abs(dy) < NEGLIGIBLE_UNITS else None


def check_nothing_was_dropped(source, out, paths, name):
    transforms = re.findall(r'\btransform="([^"]*)"', source)
    if len(transforms) > 1:
        # The first is the wrapping translate this script re-emits; any others
        # must each be provably too small to see before they may be discarded.
        offenders = [t for t in transforms[1:] if _negligible_translate(t) is None]
        if offenders:
            raise SystemExit(
                f"{name}: {len(transforms)} transform attributes ({transforms}). "
                f"This script re-emits exactly one, on one wrapping <g>, so "
                f"{offenders} would be silently dropped and the artwork would "
                f"move. Flatten them in Inkscape first (select all, then "
                f"Object > Ungroup until only one group remains)."
            )
        for t in transforms[1:]:
            dx, dy = _negligible_translate(t)
            print(f"   note {name}: dropped nested {t} "
                  f"({dx:+g},{dy:+g} units, under {NEGLIGIBLE_UNITS} -- invisible)")
    for d in paths:
        if re.sub(r"\s+", " ", d).strip() not in out:
            raise SystemExit(f"{name}: a <path d> did not survive normalisation")
    if out.count("<path") != len(paths):
        raise SystemExit(
            f"{name}: {len(paths)} paths in, {out.count('<path')} out"
        )
    if transforms and 'transform="' not in out:
        raise SystemExit(
            f"{name}: source has transform {transforms[0]!r} and the output has "
            f"none. This is the exact bug the guard exists for -- the artwork "
            f"will draw outside its viewBox and the icon will render blank."
        )


def normalise(text, name, line_class="glass-icon-line"):
    vb = re.search(r'viewBox="([^"]+)"', text)
    if not vb:
        raise SystemExit(f"{name}: no viewBox, cannot scale without one")

    paths = re.findall(r"<path\b[^>]*?\bd=\"([^\"]+)\"[^>]*/?>", text, re.S)
    if not paths:
        raise SystemExit(f"{name}: no <path d=...> found -- has the export changed?")

    # THE TRANSFORM IS LOAD-BEARING AND DROPPING IT BREAKS EVERY ICON SILENTLY.
    # Inkscape writes its artwork at document coordinates and pulls it back into
    # the viewBox with a translate on a wrapping <g>. Keep the paths' own `d`
    # untouched and re-emit that translate, rather than trying to rewrite ~104
    # path strings by hand. The first version of this script dropped the <g>;
    # every icon then drew hundreds of units outside its own viewBox and
    # rendered as blank space, with no error from Jekyll, Sass or the browser.
    g = re.search(r'<g\b[^>]*\btransform="translate\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)"', text)
    dx, dy = (float(g.group(1)), float(g.group(2))) if g else (0.0, 0.0)

    # The guard for exactly that failure. A rendered icon must actually overlap
    # the box it declares -- checked here, at generation, because nothing
    # downstream can see it: the SVG is valid XML, the page builds, the CSS
    # applies, and the only symptom is an empty gap next to the title.
    out = [
        f'<svg viewBox="{vb.group(1)}" class="glass-icon glass-icon--{name}"',
        '     role="img" aria-hidden="true" focusable="false">',
    ]
    indent = "  "
    if dx or dy:
        out.append(f'  <g transform="translate({dx:g},{dy:g})">')
        indent = "    "
    for d in paths:
        d = re.sub(r"\s+", " ", d).strip()
        out.append(f'{indent}<path class="{line_class}" d="{d}" />')
    if dx or dy:
        out.append("  </g>")
    out.append("</svg>")
    result = "\n".join(out) + "\n"
    check_nothing_was_dropped(text, result, paths, name)
    return result


def main():
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)

    written = []
    for p in sorted(SRC.glob("*.svg")):
        if p.name in SKIP:
            continue
        name = RENAME.get(p.stem.replace("glass-", ""), p.stem.replace("glass-", ""))
        cls = "glass-icon-solid" if p.name in SOLID else "glass-icon-line"
        svg = normalise(p.read_text(encoding="utf-8"), name, cls)
        target = DST / f"{name}.svg"
        target.write_text(svg, encoding="utf-8")
        xml.dom.minidom.parseString(svg)          # must be well-formed XML
        written.append((target.name, len(svg), p.stat().st_size))

    print(f"{len(written)} icons -> {DST.relative_to(ROOT)}")
    before = sum(w[2] for w in written)
    after = sum(w[1] for w in written)
    for n, a, b in written:
        print(f"   {n:<22} {b:>6} -> {a:>5} bytes")
    print(f"\n   total {before} -> {after} bytes ({100 - after * 100 // before}% smaller)")


main()
