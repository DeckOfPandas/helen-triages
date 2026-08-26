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
import xml.etree.ElementTree as ET

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
#
# `mule-mug` -> `mug`, 2026-08-26. The drawing is a plain tapered mug with a
# handle, and the ONLY thing that ever made it a Moscow Mule's mug is that a
# real one is copper -- which a monochrome line icon cannot say. It had no
# drink using it, and Apple and Ginger Mulled Wine wanted exactly this shape:
# Helen, asked whether to draw a new one, "I actually use a mug for this like I
# do for tea!". One drawing serves both, since a Mule in line art is also just
# a mug.
#
# THIS ENTRY IS THE POINT, not the git mv that went with it. Icons are
# regenerated WHOLESALE from tmp/cocktail-glasses/, so renaming only the
# published file would have resurrected `mule-mug.svg` the next time this
# script ran -- and `mug.svg` would have vanished with nothing to say why.
# Rename here, where the mapping survives a regeneration.
RENAME = {"pineapple-3": "pineapple", "mule-mug": "mug"}


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


# =============================================================================
# NESTED TRANSFORMS ARE PRESERVED, NOT DROPPED, AND THE SIZE OF ONE IS NOT THE
# POINT. This was got wrong once, on 2026-08-17, and the wrong version shipped.
#
# glass-absinthe.svg wraps 2 of its 6 paths in a second
# <g transform="translate(-0.3313235)">. The first fix allowed a nested
# translate to be DISCARDED when it was smaller than one user unit, reasoning
# that 0.33 units is 0.28px at render size and therefore invisible.
#
# That reasoning is wrong, and measurably so. A nested transform applies to a
# SUBSET of the paths, so its entire purpose is to move that subset RELATIVE to
# the rest. Absolute magnitude is the wrong test: what matters is that the
# offset is differential. Those two paths are the small marks on the absinthe
# glass's stem, and shifting them by a quarter of a pixel while the other four
# stayed put moved them off-centre by unequal amounts.
#
# Measured, because "looks fine" is what produced the bug: mirror-symmetry
# residual went from 0.27% in Helen's export -- the same as every other glass,
# which sit between 0.37% and 0.96% -- to 7.60% after normalisation. Helen saw
# it instantly on the page: "Absinthe glass is asymmetrical."
#
# So the group STRUCTURE is now re-emitted as it was found, nesting and all.
# That is also simpler than the alternative of baking a translate into the path
# data, which would need a real path parser -- the very thing the guard below
# was written to avoid.
# =============================================================================


def _emit(el, out, indent, line_class, seen_paths):
    """Re-emit the artwork tree, keeping <g transform> nesting exactly as found."""
    for child in el:
        tag = child.tag.split("}")[-1]
        if tag == "g":
            transform = child.get("transform")
            if transform:
                out.append(f'{indent}<g transform="{transform}">')
                _emit(child, out, indent + "  ", line_class, seen_paths)
                out.append(f"{indent}</g>")
            else:
                # A group with no transform carries no geometry; flatten it.
                _emit(child, out, indent, line_class, seen_paths)
        elif tag == "path":
            d = re.sub(r"\s+", " ", child.get("d", "")).strip()
            if d:
                out.append(f'{indent}<path class="{line_class}" d="{d}" />')
                seen_paths.append(d)
        else:
            # defs, sodipodi:namedview, metadata: no artwork, dropped on purpose.
            _emit(child, out, indent, line_class, seen_paths)


def check_nothing_was_dropped(source, out, paths, name):
    src_transforms = re.findall(r'\btransform="([^"]*)"', source)
    out_transforms = re.findall(r'\btransform="([^"]*)"', out)
    if len(src_transforms) != len(out_transforms):
        raise SystemExit(
            f"{name}: {len(src_transforms)} transform(s) in, "
            f"{len(out_transforms)} out ({src_transforms} vs {out_transforms}). "
            f"Every transform must survive -- a nested one moves a SUBSET of "
            f"the paths relative to the rest, so dropping it breaks alignment "
            f"no matter how small it looks. This is the absinthe bug."
        )
    for d in paths:
        if re.sub(r"\s+", " ", d).strip() not in out:
            raise SystemExit(f"{name}: a <path d> did not survive normalisation")
    if out.count("<path") != len(paths):
        raise SystemExit(
            f"{name}: {len(paths)} paths in, {out.count('<path')} out"
        )
    if src_transforms and 'transform="' not in out:
        raise SystemExit(
            f"{name}: source has transform {src_transforms[0]!r} and the output "
            f"has none. This is the exact bug the guard exists for -- the "
            f"artwork will draw outside its viewBox and the icon renders blank."
        )


def normalise(text, name, line_class="glass-icon-line"):
    vb = re.search(r'viewBox="([^"]+)"', text)
    if not vb:
        raise SystemExit(f"{name}: no viewBox, cannot scale without one")

    paths = re.findall(r"<path\b[^>]*?\bd=\"([^\"]+)\"[^>]*/?>", text, re.S)
    if not paths:
        raise SystemExit(f"{name}: no <path d=...> found -- has the export changed?")

    # THE TRANSFORMS ARE LOAD-BEARING AND DROPPING ONE BREAKS AN ICON SILENTLY.
    # Inkscape writes its artwork at document coordinates and pulls it back into
    # the viewBox with a translate on a wrapping <g>. Keep the paths' own `d`
    # untouched and re-emit the group structure, rather than trying to rewrite
    # ~104 path strings by hand. Two separate bugs have come from getting this
    # wrong: dropping the OUTER <g> made every icon draw hundreds of units
    # outside its viewBox and render as blank space, and dropping a NESTED one
    # made the absinthe glass visibly asymmetrical. See the header above.
    out = [
        f'<svg viewBox="{vb.group(1)}" class="glass-icon glass-icon--{name}"',
        '     role="img" aria-hidden="true" focusable="false">',
    ]
    seen = []
    _emit(ET.fromstring(text), out, "  ", line_class, seen)
    out.append("</svg>")
    result = "\n".join(out) + "\n"

    # The guards. A rendered icon must actually carry the artwork it declares --
    # checked here, at generation, because nothing downstream can see it: the
    # SVG is valid XML, the page builds, the CSS applies, and the only symptom
    # is an empty gap next to the title, or a drawing subtly out of true.
    if len(seen) != len(paths):
        raise SystemExit(
            f"{name}: {len(paths)} <path d> in the source, {len(seen)} emitted."
        )
    for d in paths:
        if re.sub(r"\s+", " ", d).strip() not in result:
            raise SystemExit(f"{name}: a <path d> did not survive normalisation")
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
