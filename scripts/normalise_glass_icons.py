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
SKIP = {"food-cloche-heart.svg", "glass-old-fashioned - Copy.svg"}


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


def check_nothing_was_dropped(source, out, paths, name):
    transforms = re.findall(r'\btransform="([^"]*)"', source)
    if len(transforms) > 1:
        raise SystemExit(
            f"{name}: {len(transforms)} transform attributes ({transforms}). "
            f"This script re-emits exactly one, on one wrapping <g>, so the "
            f"others would be silently dropped and the artwork would move."
        )
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


def normalise(text, name):
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
        out.append(f'{indent}<path class="glass-icon-line" d="{d}" />')
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
        name = p.stem.replace("glass-", "")
        svg = normalise(p.read_text(encoding="utf-8"), name)
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
