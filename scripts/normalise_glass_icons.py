"""Normalise Helen's Inkscape glass exports into _includes/icons/glasses/.

    python3 scripts/normalise_glass_icons.py

No flags. It reads every `.svg` in the gitignored inbox `tmp/cocktail-glasses/`
except the names in SKIP, then EMPTIES `_includes/icons/glasses/` and writes
one icon per source, named for the source without its `glass-` prefix. The
inbox is not the archive: that is `_design_sources/cocktails/glasses/`, and
regenerating the whole set means copying the archive into the inbox first. It
refuses to run on an empty inbox. To publish one new drawing, import this
module and call `normalise()` on that file; importing runs nothing.

Run `scripts/check_glass_regen.py` after touching SKIP, SOLID or RENAME. It
resolves every archived source the way `main()` does and diffs against what is
published, deleting nothing. A wholesale regeneration must reproduce the
shipped set exactly; a divergence means an icon was hand-edited.

What it changes in an export, and why each matters:

  1. `width`/`height` in millimetres are dropped and the viewBox kept. An icon
     that declares a physical size ignores its container.
  2. The hardcoded stroke colour goes, and each path takes the class
     `glass-icon-line`, which strokes with currentColor. The palette is the
     only place a colour is written, and an inline style beats the stylesheet.
  3. The constant stroke-width goes. ViewBoxes differ in size, so one width in
     user units renders at a different weight on each glass; the class sets
     `vector-effect: non-scaling-stroke` and one weight for the whole set.
  4. Inkscape/sodipodi metadata, empty <defs>, the XML declaration and the
     generator comment are dropped: the icons are inlined into every page.
  5. The viewBox is fitted to the artwork (`svgrender.fit_viewbox`).

What it preserves, and `normalise` raises if it has not: every `<path d>`
verbatim, and every `transform`, whether on a wrapping <g>, a nested <g> or a
path. A <circle> becomes a two-arc path; any other shape is refused by name.
"""
import pathlib, re, shutil, xml.dom.minidom
import xml.etree.ElementTree as ET
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import svgrender

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "tmp" / "cocktail-glasses"   # drop new exports here
DST = ROOT / "_includes" / "icons" / "glasses"

# Not glasses. Both guard this script's inbox, not the archive: a food icon
# exported into the same folder, and an Inkscape "- Copy" duplicate. The
# archive holds one source per glass (DECISIONS §9), so no glass needs an entry.
SKIP = {
    "food-cloche-heart.svg",
    "glass-old-fashioned - Copy.svg",
}

# Fill-only artwork (stock icons usually are): a compound path whose interior
# is the ink, so the stroke class would outline the outline. A name here
# publishes that drawing with `.glass-icon-solid` (_sass/cocktails/
# _cocktail.scss), which fills with currentColor. Empty: the whole set is line
# art. A filled icon is heavier and its ink scales with the drawing, so ask
# "must this be redrawn" before "can this be traced" (MANUAL §9).
SOLID = set()

# Source name -> published name, for an export that carries a working title.
# Empty: every archived source has its published name. Rename here, not only
# the published file: icons are regenerated wholesale, so a renamed output
# with no entry comes back under its old name on the next run.
RENAME = {}


# The guards are structural, not geometric: they compare what went in with
# what came out. A dropped wrapping <g transform> draws the artwork outside
# its viewBox and the icon renders blank, with valid XML and a clean build.
# Bounding the numbers in `d` instead needs a real path parser, because path
# commands have variable arity. Nested transforms are re-emitted as found,
# however small: one moves a subset of the paths relative to the rest, and
# dropping a 0.33-unit translate makes the absinthe glass asymmetrical.


# A <circle> is artwork too. Everything here reads <path> only, so a circle
# becomes the equivalent two-arc <path> before anything else looks at the
# text, and every guard then covers it; svgrender reads <path> only as well.
# A filled circle is a dot and takes `glass-icon-dot` beside the line class,
# which restores the fill `.glass-icon-line` removes. Any other shape is
# refused by name, not dropped.
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
                # A transform can sit on the path itself, not only on a <g>.
                # One with a negative y scale flips the drawing if it is lost.
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

    # The paths' own `d` is untouched and the group structure is re-emitted:
    # Inkscape writes artwork at document coordinates and pulls it back into
    # the viewBox with a translate on a wrapping <g>.
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

    # Fit the canvas to the artwork. A glass drawn by editing a taller one
    # keeps the taller canvas, and `heights_mm` scales the viewBox, so the
    # empty space is lost height. Unconditional: only the frame moves, never
    # the path data. test_no_glass_artwork_has_a_slack_viewbox (#503) is the
    # backstop for artwork that never came through here.
    fitted, old_h, new_h = svgrender.fit_viewbox(result, label=name)
    change = (old_h / new_h - 1) * 100 if new_h else 0
    if abs(change) >= 1:
        print(f"  {name}: canvas fitted, renders {change:+.1f}%")
    return fitted


def refuse_if_no_input(usable, *, src, dst, doing, extra=""):
    """Stop before a destructive step when there is nothing to put back (#537).

    For a script whose output is tracked and whose input is not:
    `tmp/cocktail-glasses` is a gitignored inbox, empty most of the time and
    absent in a fresh worktree, so "no input" is the normal state. Call this
    before deleting, not after.

    `usable` is the already-filtered list, so each caller keeps its own idea
    of what counts. Raises SystemExit.
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


# Not tidiness: main() starts with `shutil.rmtree(DST)`, so a bare call here
# would delete every published icon on `import normalise_glass_icons`.
if __name__ == "__main__":
    main()
