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
     of different results" trap MANUAL 13.4.1 documents for -webkit-text-
     stroke. Fixed with vector-effect="non-scaling-stroke", so the weight is
     set once in CSS and is identical on every icon whatever its viewBox.
  4. Inkscape/sodipodi metadata, empty <defs>, the XML declaration and the
     generator comment: all dropped. These are inlined into every drink page,
     so the bytes are paid for on every request.

Note the SVGs are INLINED by Liquid, not fetched by JS, so the `<svg ` vs
`<svg\\n` injection trap does not apply here -- but the output is written
with a space after `<svg` anyway, since it costs nothing and the repo has
been bitten by that assumption before.

A WHOLESALE REGENERATION NOW REPRODUCES THE SHIPPED SET EXACTLY, and that was
not true until 2026-09-06. `_includes/icons/glasses/tiki-mug.svg` carried a
hand-added `<feMorphology operator="erode">` thinning filter that this script
does not emit, so regenerating silently stripped it and the mug rendered
heavier. Helen's redraw is line art, which has a stroke width to set and so
needs no thinning at all: the filter went with the fill, and the last divergence
went with it.

**Run `scripts/check_glass_regen.py` after touching SKIP, SOLID or RENAME.** It
resolves every archived source the way main() does and diffs against what is
published, without deleting anything. It should say "reproduces the shipped set
exactly"; if it names a divergence, something has been hand-edited since.

"""
import pathlib, re, shutil, xml.dom.minidom
import xml.etree.ElementTree as ET
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import svgrender

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
#
# ONE SOURCE PER GLASS SINCE 2026-09-29, SO THE GLASS ENTRIES ARE GONE.
# This set held twenty superseded drawings, each skipped by name so that a
# wholesale regeneration could not pick an old version over its redraw -- and
# it had to, because `sorted()` puts glass-coupe-2.svg BEFORE glass-coupe.svg
# ('-' is 0x2D, '.' is 0x2E), so the original would be written last and win.
#
# Helen, 2026-09-29: "Shall we clear out the earlier versions of drawings we've
# updated? ... we're using tiki mug 9 so delete the others." It is the
# old-fashioned collapse of 2026-08-26 applied to the whole set ("delete all
# other versions of old fashioned (and rocks) glasses you have anywhere, then
# add just these two"): the superseded sources were deleted, every live one
# renamed to its plain published name, and with one file per glass there is
# nothing to skip and nothing to rename. The best answer to a disambiguation
# rule is not having anything to disambiguate. GIT HISTORY IS THE RECORD OF
# WHAT WAS TRIED NOW: `git log --diff-filter=D -- _design_sources/` lists
# every one, and `git show <sha>^:<path>` brings one back.
#
# THE TWO LEFT guard this script's own inbox rather than the archive: a food
# icon exported into the same folder, and an Inkscape "- Copy" duplicate.
SKIP = {
    "food-cloche-heart.svg",
    "glass-old-fashioned - Copy.svg",
}

# FILL-BASED ARTWORK, WHICH THE REST OF THE SET IS NOT. Every glass is drawn as
# open strokes with `fill: none`; a fill-based drawing is a compound path whose
# interior lattice is negative space, so forcing the stroke class onto it would
# outline the outline and produce mush. Those get their own class instead -- see
# `.glass-icon-solid` in _sass/cocktails/_cocktail.scss -- which fills with
# currentColor so the palette rule still holds and only the technique differs.
#
# READ THE HISTORY BELOW AS HISTORY. It is written about the pineapple and the
# coconut and both LEFT this set on 2026-09-05, redrawn by Helen as line art;
# only the tiki mug is still filled. It is kept because the reasoning is about
# the technique rather than about those two drawings, and the last paragraph --
# ask "must this be redrawn" before "can this be traced" -- is the standing rule
# for whatever arrives next.
#
# THE TIKI MUG JOINED IT 2026-08-26, and it was always this case -- nobody had
# looked. Its source is fill-only in exactly the pineapple's way: one style
# rule, `.a{fill:#231f20;}`, and not a single stroke in the file (it is a stock
# icon, <title>100icons20172</title>). Published with the stroke class, all 27
# paths drew the OUTLINE OF THE INK -- a hollow double line around every
# stroke. Helen spotted it on the design page: "the lines outline the shape of
# the mug as enclosed areas, but they're not filled."
#
# AND THEN IT LEFT AGAIN, the same day. Filling was the right fix for the
# artwork that existed, but it could not give the mug a stroke WIDTH -- there
# was no centreline to give a width to -- so it read about 2.8x heavier than
# every stroked glass beside it and got heavier as it grew, while theirs stayed
# put. Helen: "The tiki mug has lots of gaps in its lines. Are you able to
# redraw it?"
#
# glass-tiki-mug-2.svg is that redraw: real centrelines, twelve of them, same
# viewBox, so the mug rejoins the set on one weight set once in CSS. The
# fill-based original is kept in _design_sources as the record and is SKIPped
# above. The set is back to one member.
#
# AND IT IS THE DEFAULT FOR FILL-ONLY ARTWORK AGAIN, 2026-08-31, with all three
# of Helen's new drawings in it. They were traced first and that was the wrong
# call -- hers, plainly: "you redrew these three new ones, right? They're not
# right." Tracing IS a redraw. It broke lines at junctions and lost the
# pineapple's umbrella stem, and none of that was necessary, because filling
# shows the drawing she actually made.
#
# SO ASK "MUST THIS BE REDRAWN" BEFORE ASKING "CAN THIS BE TRACED". Tracing is
# the answer when a fill is unusable, not when a fill is merely heavier. The
# tiki mug in #355 is still the case that needs it: that drawing is a stock
# icon whose weight Helen rejected outright. Hers are hers, and what they
# should look like is her call to make by looking, not one to pre-empt with a
# transformation she did not ask for.
#
# The weight cost, measured, so the trade is visible rather than argued -- ink
# width as a fraction of canvas height, against a stroked icon's ~0.65% at card
# size: pineapple 1.3% (~2x), coconut 2.5% (~3.9x), tiki mug 4.2% (~6.5x). A
# filled icon's ink also scales WITH the drawing, where `non-scaling-stroke`
# holds a stroked one at a constant screen weight -- so the gap widens as the
# icon grows. That is the thing to look at on /dev/card-glasses/, and it is a
# reason to redraw only if it actually looks wrong.
# EMPTY SINCE 2026-09-06, AND THAT IS THE END OF A THREE-DRAWING STORY. Helen
# redrew the pineapple and the coconut on 2026-09-05 and the tiki mug the next
# day, so every one of the 27 glasses is now open line art and NOTHING is
# published with the solid class. `.glass-icon-solid` went from
# _sass/cocktails/_cocktail.scss in the same commit, along with the tiki mug's
# hand-applied `feMorphology` thinning filter -- a filled drawing needs thinning
# because its ink scales with it, and a stroked one does not.
#
# KEPT RATHER THAN DELETED, because fill-only artwork is a thing that arrives
# from outside (stock icons are nearly always fill-only) and this is the switch
# that publishes it correctly. Adding a name here is still the right answer the
# next time one does; it would need `.glass-icon-solid` restoring too, and the
# reasoning for both is in this file's header.
SOLID = set()

# Source name -> published name, where the export carries a working title.
#
# TWO KINDS OF ENTRY LIVE HERE, and they arrived from two branches on the same
# day. Keeping both comments because they answer different questions.
#
# 1. VERSIONED REDRAWS. Helen saves a new attempt beside the old rather than
#    over it, so the source that WINS carries a version suffix the published
#    icon must not. Deliberately not automated by stripping a trailing `-<n>`:
#    `pineapple-3` beat `pineapple-1` on a judgement call and the losers are
#    kept as the evidence for it, so which numbered file is current is a fact
#    about this repo's history, not a pattern.
#
# 2. A RENAMED GLASS. `mule-mug` -> `mug`, 2026-08-26. The drawing is a plain
#    tapered mug with a handle, and the ONLY thing that ever made it a Moscow
#    Mule's mug is that a real one is copper -- which a monochrome line icon
#    cannot say. It had no drink using it, and Apple and Ginger Mulled Wine
#    wanted exactly this shape: Helen, asked whether to draw a new one, "I
#    actually use a mug for this like I do for tea!". One drawing serves both,
#    since a Mule in line art is also just a mug.
#
#    THAT ENTRY IS THE POINT, not the git mv that went with it. Icons are
#    regenerated WHOLESALE, so renaming only the published file would have
#    resurrected `mule-mug.svg` the next time this script ran -- and `mug.svg`
#    would have vanished with nothing to say why. Rename here, where the
#    mapping survives a regeneration.
#
# EMPTY SINCE 2026-09-29, when every live source took its published name (see
# SKIP above). Thirteen entries went, `tiki-9` -> `tiki-mug` and `mule-mug` ->
# `mug` among them; `git log -S` on this file has each one's reasoning. The
# map stays because the next redraw arrives with a working title again -- add
# its line here, or better, rename the file and delete the one it replaces.
#
# `mule-mug` IS A REAL PUBLISHED NAME AGAIN SINCE 2026-10-02, and that is not
# the old entry coming back: Helen drew the Moscow Mule its own mug (a barrel
# body, nine dimples), so `glass-mule-mug.svg` in the archive publishes as
# `mule-mug.svg` under its own name, beside `mug.svg`. Paragraph 2 above is
# the history of the PLAIN mug's source, which once carried that working title.
RENAME = {}

# NOT IN THAT PASS, AND DELIBERATELY: `old-fashioned-double` carries the set's
# two largest open ends (3.92 units each, on the base) and Helen looked at it
# and ruled it correct as drawn -- 2026-08-31, "I decided old fashioned double
# was correct as it was". So a gap here is not automatically a fault, which is
# exactly why the check that comes out of this is hers to grant exemptions
# from rather than something to fix on sight.


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
#      time this codebase has produced one (MANUAL §12).
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


# =============================================================================
# A <circle> IS ARTWORK TOO, AND IT USED TO VANISH WITHOUT A WORD -- 2026-10-02.
# =============================================================================
# Helen's mule mug carries nine dimples, each a <circle>. Everything here reads
# <path> and nothing else: `_emit` fell through to its "defs, metadata" branch
# and dropped all nine, and no guard noticed, because each guard counts paths
# and transforms and a circle is neither. The mug would have published smooth.
#
# So a circle becomes the equivalent two-arc <path> BEFORE anything else looks
# at the text, and from there every existing guard covers it. Her source file
# is not touched. svgrender reads <path> only as well, so this is also what
# lets the canvas fit, the base centre and the gap check see the dimples.
#
# A FILLED circle is a DOT, and gets `glass-icon-dot` beside the line class.
# The site draws at a thin fixed stroke and `.glass-icon-line` is `fill: none`,
# so a dot of radius 1 renders as a solid speck on a card and as a hollow ring
# on anything larger. The class restores the fill she drew.
#
# ANY OTHER SHAPE IS REFUSED BY NAME rather than dropped. The next drawing that
# uses a <rect> or an <ellipse> should stop here and say so.
CIRCLE = re.compile(r"<circle\b((?:\"[^\"]*\"|[^>\"])*?)/?>(?:\s*</circle>)?", re.S)
UNREAD_SHAPES = re.compile(
    r"<(?:svg:)?(ellipse|rect|line|polyline|polygon|text|use|image)\b")
DOT_MARK = "data-glass-dot"


def circles_to_paths(text, name):
    def convert(match):
        attrs = match.group(1)

        def number(key, default=None):
            found = re.search(rf'(?<![\w:-]){key}="([^"]+)"', attrs)
            if not found:
                if default is None:
                    raise SystemExit(f"{name}: a <circle> has no `{key}`")
                return default
            return float(found.group(1))

        cx, cy, r = number("cx", 0.0), number("cy", 0.0), number("r")
        d = (f"M {cx - r:.5f},{cy:.5f} a {r:g},{r:g} 0 1,0 {2 * r:g},0 "
             f"a {r:g},{r:g} 0 1,0 {-2 * r:g},0 z")
        transform = re.search(r'\btransform="[^"]*"', attrs)
        fill = re.search(r'(?<![\w-])fill\s*[:=]\s*"?\s*([^;"\s]+)', attrs)
        dot = f' {DOT_MARK}="1"' if fill and fill.group(1) != "none" else ""
        extra = f" {transform.group(0)}" if transform else ""
        return f'<path{dot}{extra} d="{d}" />'

    text = CIRCLE.sub(convert, text)
    unread = UNREAD_SHAPES.search(text)
    if unread:
        raise SystemExit(
            f"{name}: the drawing uses <{unread.group(1)}>, which this script "
            f"does not read and would drop without saying so. Convert it to a "
            f"path in Inkscape (Path > Object to Path), or teach "
            f"circles_to_paths() the shape."
        )
    return text


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
                # A TRANSFORM CAN SIT ON THE PATH ITSELF, not only on a <g>, and
                # dropping it is the absinthe bug one level down -- 2026-08-31,
                # found on Helen's pineapple, whose single path carries
                # matrix(0.1333,0,0,-0.1333,0,192). That matrix has a NEGATIVE y
                # scale, so losing it does not nudge the drawing, it flips it and
                # throws it off the canvas.
                #
                # It was invisible until now because every earlier export put its
                # transform on a group. check_nothing_was_dropped counts
                # transforms in against transforms out and caught this on the
                # first drawing that did otherwise, which is what that guard is
                # for -- it fired before anything was published.
                transform = child.get("transform")
                attr = f' transform="{transform}"' if transform else ""
                # A filled <circle> in the source: see circles_to_paths.
                cls = (f"{line_class} glass-icon-dot"
                       if child.get(DOT_MARK) else line_class)
                out.append(f'{indent}<path class="{cls}"{attr} d="{d}" />')
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

    # Before anything counts a path: see circles_to_paths.
    text = circles_to_paths(text, name)

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

    # 5. FIT THE CANVAS TO THE ARTWORK. Added 2026-08-27, and it is the one
    #    step here that exists because of how the drawings are MADE rather
    #    than how Inkscape exports them.
    #
    #    Helen builds a new glass by editing an existing one -- "I am not able
    #    to do anything other than this as I can't draw" -- so a shortened
    #    drawing keeps the taller drawing's canvas. `heights_mm` scales the
    #    VIEWBOX, so that leftover empty space is lost height: the coupe was
    #    declared the same 150mm as the highball and rendered 15% shorter than
    #    it, across 40 drinks, and the goblet was 29% short. Neither was
    #    noticeable by looking at one glass, because nothing was out of
    #    proportion WITHIN the drawing -- only between it and its own frame.
    #
    #    Doing it here rather than asking for tidier exports is the point. It
    #    is deterministic, it cannot distort artwork (the path data and the <g>
    #    transform are untouched; only the frame moves), and it means the
    #    failure mode simply cannot reach the site again.
    #
    #    UNCONDITIONAL, NOT "WHEN IT LOOKS WRONG". Measured across the set
    #    before choosing: 23 of 26 icons move by 0.4% or less, so a blanket
    #    rule costs almost nothing and a conditional one would need a threshold
    #    that is itself a guess. tests/test_cocktails.py's slack-viewBox guard
    #    (#503) stays as the backstop for artwork that never came through here.
    fitted, old_h, new_h = svgrender.fit_viewbox(result, label=name)
    change = (old_h / new_h - 1) * 100 if new_h else 0
    if abs(change) >= 1:
        print(f"  {name}: canvas fitted, renders {change:+.1f}%")
    return fitted


def refuse_if_no_input(usable, *, src, dst, doing, extra=""):
    """Stop before a destructive step when there is nothing to put back.

    > A DESTRUCTIVE STEP THAT RUNS BEFORE ITS INPUTS ARE CHECKED WILL
    > EVENTUALLY RUN WITH NO INPUTS.

    Issue #537, and this exists as a shared function rather than as a check
    written twice because it has already been learned twice. On 2026-08-27 this
    script emptied `_includes/icons/glasses/` with an empty SRC and wrote
    nothing back: 26 published icons gone, `0 icons ->` printed as though that
    were a result, then a ZeroDivisionError from the summary line. The day
    before, the same directory went to an import running a bare `main()` --
    different mechanism, identical outcome, and the `__main__` guard that fixed
    it did nothing for this.

    The shape to recognise, which is what makes this reusable: a script whose
    OUTPUT is tracked and whose INPUT is not. `tmp/cocktail-glasses` is a
    gitignored inbox that is legitimately empty most of the time and absent
    entirely in a fresh worktree, so "no input" is the NORMAL state and running
    the rebuild is the exception. Anything with that shape needs this call
    before it deletes, not after.

    `usable` is the already-filtered list, so each caller keeps its own idea of
    what counts (this script drops SKIP names; the candidates drawer does not).

    Raises SystemExit -- the caller has not deleted anything yet, so there is
    nothing to unwind.
    """
    if usable:
        return
    missing = " (directory does not exist)" if not src.is_dir() else ""
    raise SystemExit(
        f"{src.relative_to(ROOT)} has no usable .svg files{missing}, so there "
        f"is nothing to {doing}.\n\n"
        f"REFUSING TO CONTINUE, because the next step empties "
        f"{dst.relative_to(ROOT)}." + (f" {extra}" if extra else "")
    )


def main():
    sources = sorted(SRC.glob("*.svg")) if SRC.is_dir() else []
    usable = [s for s in sources if s.name not in SKIP]
    refuse_if_no_input(
        usable, src=SRC, dst=DST, doing="normalise",
        extra=(
            "That would leave the site with no glass icons at all. Drop the "
            "Inkscape exports into tmp/cocktail-glasses/ first.\n\n"
            "This is an inbox, not an archive -- the archive is "
            "_design_sources/cocktails/glasses/. Regenerating the whole set "
            "means copying the archive into the inbox first."
        ),
    )

    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)

    written = []
    for p in usable:
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


# THE GUARD IS NOT TIDINESS. A bare `main()` here means IMPORTING this module
# runs it, and the first thing main() does is `shutil.rmtree(DST)` -- so
# `import normalise_glass_icons`, to reuse normalise() on a single new drawing,
# deletes all 26 published icons before the importer's first line executes.
# That happened on 2026-08-26, from a script whose whole purpose was to avoid
# regenerating the set. Recoverable, since everything in DST is committed, but
# silent and instant, and nothing about the traceback points at the import.
#
# Reuse the functions freely now: importing this module does nothing on its own.
if __name__ == "__main__":
    main()
