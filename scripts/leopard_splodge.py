"""Seamless black-on-black leopard tiles, drawn as crinkled, tufted splodges.

REPRODUCES NO NUMBER -- the second GENERATOR for `model_instructions/LEOPARD.md`,
written 2026-10-06 after Helen brought two reference pictures: rosettes made of
lumpy, ragged-edged blobs around an empty middle, each blob filled with a fine
crinkle a step lighter than itself. Every shape here is generated from `seed`;
nothing is traced. `scripts/build_leopard.py` writes the two files the site
ships from it; a change here changes the live print once that is re-run.

THE TILE HAS NO GROUND AND NO TONES OF ITS OWN. Everything is white at a very
low alpha, so the same file sits on the page, on the header band or on a darker
page and keeps the same distance from whatever is under it. `ground=` paints
one in, for looking at a tile by itself.

A rosette is one to three ARC BLOBS round a centre (a C, a pair, a triple) or a
solid BEAN; small lone spots fill the gaps. An arc blob is an outline walked
out and back along an arc, fat in the middle and pinched at the ends, with slow
noise for the lumps and fast jitter for the edge, and TUFTS: short strokes
leaning out of the edge, the way pile overhangs a marking. Each blob has its
own strength (`body`), so no two are quite the same black.

The CRINKLE inside a blob is one of three:
  contour   the contour lines of a noise field: wandering closed loops
  scribble  short curved strokes in every direction
  fur       short straight strokes that all lean roughly one way, the lean
            drifting slowly across the tile

The raggedness, the tufts and the strokes are geometry, so the wrapped copies
at the tile edge match exactly; the contour noise uses stitchTiles.

`ground_tile()` is a separate, tiny tile for the ground itself: `grain` (fine,
even) or `nap` (short vertical fibres). It is layered under the splodges in
CSS, so the two can be chosen apart.
"""
import base64, math, random


def _wobble(rnd, harmonics):
    """A smooth periodic noise on t in [0, 1): a few random sinusoids, about -1..1."""
    parts = [(rnd.choice(harmonics), rnd.uniform(0, 2 * math.pi), rnd.uniform(0.5, 1.0)) for _ in range(3)]
    total = sum(a for _, _, a in parts)
    return lambda t: sum(a * math.sin(2 * math.pi * k * t + p) for k, p, a in parts) / total


def _arc_blob(rnd, r, a0, a1, jitter):
    """Outline points (local coords) of one blob along the arc a0..a1 degrees of a rosette of outer radius r."""
    mid_r, half = r * rnd.uniform(0.64, 0.7), r * rnd.uniform(0.27, 0.35)
    lump, drift = _wobble(rnd, (1.5, 2.5, 3.5)), _wobble(rnd, (1, 2))
    arc_len = math.radians(a1 - a0) * mid_r
    n = max(8, int(arc_len / 3.2))
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        h = half * (math.sin(math.pi * t) ** 0.3) * (1 + 0.25 * lump(t))
        rc = mid_r * (1 + 0.07 * drift(t))
        ro = rc + h + rnd.uniform(-jitter, jitter)
        ri = rc - h + rnd.uniform(-jitter, jitter)
        outer.append((ro * math.cos(a), ro * math.sin(a)))
        inner.append((ri * math.cos(a), ri * math.sin(a)))
    return outer + inner[::-1]


def _bean(rnd, r, jitter):
    """Outline points of a solid lumpy spot of radius about r."""
    lump = _wobble(rnd, (2, 3, 4))
    n = max(10, int(2 * math.pi * r / 3.0))
    return [((r * (0.8 + 0.22 * lump(i / n)) + rnd.uniform(-jitter, jitter)) * math.cos(2 * math.pi * i / n),
             (r * (0.8 + 0.22 * lump(i / n)) + rnd.uniform(-jitter, jitter)) * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def _rosette(rnd, r, jitter):
    """A list of outlines making one rosette of outer radius r."""
    kind = rnd.choice(["c", "c", "pair", "pair", "pair", "triple", "triple", "bean"])
    start = rnd.uniform(0, 360)
    if kind == "bean" or r < 20:
        return [_bean(rnd, r * 0.8, jitter)]
    if kind == "c":
        return [_arc_blob(rnd, r, start, start + rnd.uniform(190, 280), jitter)]
    spans = {"pair": (115, 155), "triple": (75, 100)}[kind]
    count = 2 if kind == "pair" else 3
    out, a = [], start
    for _ in range(count):
        span = rnd.uniform(*spans)
        out.append(_arc_blob(rnd, r, a, a + span, jitter))
        a += span + rnd.uniform(14, 28)
    return out


def _images(size, step):
    """The nine nearest copies of the cell. One cell to the right is also `step` DOWN."""
    return [(i * size, i * step + j * size) for i in (-1, 0, 1) for j in (-1, 0, 1)]


def _place(rnd, size, step, pts, count, radius, min_gap, tries=60000):
    n, images = 0, _images(size, step)
    while count > 0 and n < tries:
        n += 1
        x, y, r = rnd.uniform(0, size), rnd.uniform(0, size), rnd.uniform(*radius)
        if all(min(math.hypot(x - px - ox, y - py - oy) for ox, oy in images) >= (r + pr) * min_gap
               for (px, py, pr) in pts):
            pts.append((x, y, r))
            count -= 1


def _inside(poly, x, y):
    hit, j = False, len(poly) - 1
    for i in range(len(poly)):
        (xi, yi), (xj, yj) = poly[i], poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def _tufts(rnd, poly, lean, amount, length):
    """Short strokes leaning out of the outline: 'Mx,yl dx,dy' pieces in local coords."""
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    sign = 1 if area > 0 else -1
    out = []
    for i, (x, y) in enumerate(poly):
        if rnd.random() > amount:
            continue
        (ax, ay), (bx, by) = poly[i - 1], poly[(i + 1) % len(poly)]
        tx, ty = bx - ax, by - ay
        d = math.hypot(tx, ty) or 1.0
        nx, ny = sign * ty / d, -sign * tx / d                      # outward normal
        a = math.atan2(ny, nx) + rnd.uniform(-0.5, 0.5)
        dx, dy = 0.6 * math.cos(a) + 0.8 * math.cos(lean), 0.6 * math.sin(a) + 0.8 * math.sin(lean)
        if dx * nx + dy * ny < 0.15:                                # the pile lies INTO the blob here: no overhang
            continue
        ln = rnd.uniform(*length)
        out.append(f"M{x - nx:.0f},{y - ny:.0f}l{dx * ln:.1f},{dy * ln:.1f}")
    return "".join(out)


def splodge_tile(seed=7, size=960, count=90, spots=40, crinkle="fur", ground=None,
                 body=0.04, vein=0.04, body_range=(0.3, 1.0),
                 radius=(40, 68), spot_radius=(8, 17), min_gap=0.9, jitter=1.3,
                 tuft=0.9, tuft_length=(2.0, 5.5), lean_degrees=115.0,
                 vein_frequency=0.085, columns=1):
    """`body` is the alpha of the strongest blob and `vein` of the crinkle on it;
    a blob's own strength is drawn from `body_range` and scales both.

    `columns` above 1 OFFSETS the repeat: the cell one to the right sits
    size/columns lower, so the same splodge never appears twice at one height
    until `columns` cells along. The placement wraps on that slanted lattice,
    so the seams still join; the SVG is `columns` cells wide and one tall.
    Returns (data URI, bytes, svg, width in px)."""
    rnd = random.Random(seed)
    if columns > 1 and crinkle == "contour":
        raise ValueError("the contour crinkle is a stitched noise field and cannot be offset")
    step = size / columns if columns > 1 else 0
    images = _images(size, step)
    pts = []
    _place(rnd, size, step, pts, count, radius, min_gap)
    big = len(pts)
    _place(rnd, size, step, pts, spots, spot_radius, min_gap * 1.25)

    p1, p2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)

    def lean_at(x, y):
        """The fur's direction, drifting slowly and periodically across the tile."""
        return math.radians(lean_degrees + 25 * math.sin(2 * math.pi * x / size + p1) + 15 * math.sin(4 * math.pi * y / size + p2))

    blobs, strokes = [], {0.55: [], 0.8: [], 1.0: []}
    for i, (x, y, r) in enumerate(pts):
        outlines = _rosette(rnd, r, jitter) if i < big else [_bean(rnd, r, jitter * 0.7)]
        squash, rot = rnd.uniform(0.72, 1.0), rnd.uniform(0, math.pi)
        cr, sr = math.cos(rot), math.sin(rot)
        base = rnd.uniform(*body_range)
        lean = lean_at(x, y)
        offsets = [(ox, oy) for ox, oy in images
                   if -r * 1.5 <= x + ox <= size + r * 1.5 and -r * 1.5 <= y + oy <= size + r * 1.5]
        for outline in outlines:
            strength = max(body_range[0], min(1.0, base * rnd.uniform(0.8, 1.2)))
            local = [(px * cr - py * squash * sr, px * sr + py * squash * cr) for px, py in outline]
            d = "M" + "L".join(f"{px:.1f},{py:.1f}" for px, py in local) + "Z"
            inner = f'<path d="{d}"/>'
            if tuft:
                inner += (f'<path d="{_tufts(rnd, local, lean, tuft, tuft_length)}" fill="none" stroke="#fff" '
                          f'stroke-width="{rnd.uniform(2.2, 3.2):.1f}" stroke-linecap="round"/>')
            marks = []
            if crinkle in ("fur", "scribble"):
                xs, ys = [p[0] for p in local], [p[1] for p in local]
                box = (max(xs) - min(xs)) * (max(ys) - min(ys))
                for _ in range(int(box / (26 if crinkle == "fur" else 34))):
                    px, py = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))
                    if not _inside(local, px, py):
                        continue
                    if crinkle == "fur":
                        a, ln = lean + rnd.uniform(-0.38, 0.38), rnd.uniform(3.5, 8.0)
                        marks.append((px, py, f"l{math.cos(a) * ln:.1f},{math.sin(a) * ln:.1f}"))
                    else:
                        a, ln, bend = rnd.uniform(0, 2 * math.pi), rnd.uniform(5.0, 11.0), rnd.uniform(-4.5, 4.5)
                        ex, ey = math.cos(a) * ln, math.sin(a) * ln
                        marks.append((px, py, f"q{ex / 2 - math.sin(a) * bend:.1f},{ey / 2 + math.cos(a) * bend:.1f} {ex:.1f},{ey:.1f}"))
            for ox, oy in offsets:
                blobs.append(f'<g transform="translate({x + ox:.1f},{y + oy:.1f})" opacity="{strength:.2f}">{inner}</g>')
                for px, py, tail in marks:
                    strokes[rnd.choice(list(strokes))].append(f"M{x + ox + px:.0f},{y + oy + py:.0f}{tail}")

    width = size * columns

    def laid_out(ref):
        """One cell's content, clipped to the cell and set down once per column, each a step lower."""
        if columns == 1:
            return f'<g clip-path="url(#cell)"><use href="#{ref}"/></g>'
        return "".join(f'<g transform="translate({i * size},{(i * step) % size + j * size:.1f})"><g clip-path="url(#cell)"><use href="#{ref}"/></g></g>'
                       for i in range(columns) for j in (0, -1))

    region = f'filterUnits="userSpaceOnUse" x="0" y="0" width="{size}" height="{size}" color-interpolation-filters="sRGB"'
    defs = [f'<clipPath id="cell"><rect width="{size}" height="{size}"/></clipPath>',
            f'<g id="s" fill="#fff">{"".join(blobs)}</g>',
            f'<g id="all">{laid_out("s")}</g>',
            f'<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{width}" height="{size}"><use href="#all"/></mask>']
    if crinkle == "contour":
        # The noise's value goes into alpha and a table keeps two thin bands
        # either side of the middle: closed wandering loops, like brain coral.
        defs.append(f'<filter id="c" {region}>'
                    f'<feTurbulence type="fractalNoise" baseFrequency="{vein_frequency}" numOctaves="2" seed="{seed}" stitchTiles="stitch"/>'
                    f'<feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  1 0 0 0 0"/>'
                    f'<feComponentTransfer><feFuncA type="table" tableValues="0 0 0 0 0 0 {vein} 0 0 {vein} 0 0 0 0 0 0"/></feComponentTransfer>'
                    f'</filter>')
        marks_svg = f'<rect width="{size}" height="{size}" filter="url(#c)"/>'
    else:
        defs.append('<g id="k">' + "".join(f'<path d="{"".join(ds)}" stroke-opacity="{vein * k:.3f}"/>' for k, ds in strokes.items() if ds) + '</g>')
        marks_svg = laid_out("k")
    ground_rect = f'<rect width="{width}" height="{size}" fill="{ground}"/>' if ground else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{size}" viewBox="0 0 {width} {size}">'
           f'<defs>{"".join(defs)}</defs>{ground_rect}'
           f'<use href="#all" opacity="{body}"/>'
           f'<g mask="url(#m)" fill="none" stroke="#fff" stroke-width="1" stroke-linecap="round">{marks_svg}</g></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode(), len(svg), svg, width


def ground_tile(kind="grain", size=480, strength=0.015, seed=3):
    """A texture for the ground itself, white at low alpha. `grain` is fine and even; `nap` is short vertical fibres."""
    frequency = {"grain": "0.8", "nap": "0.6 0.07"}[kind]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
           f'<filter id="g" filterUnits="userSpaceOnUse" x="0" y="0" width="{size}" height="{size}" color-interpolation-filters="sRGB">'
           f'<feTurbulence type="fractalNoise" baseFrequency="{frequency}" numOctaves="2" seed="{seed}" stitchTiles="stitch"/>'
           f'<feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  {strength * 4:.3f} 0 0 0 {-strength * 1.2:.3f}"/>'
           f'</filter><rect width="{size}" height="{size}" filter="url(#g)"/></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode(), len(svg), svg


if __name__ == "__main__":
    import sys
    uri, n, svg, _width = splodge_tile(ground="#060607")
    sys.stdout.write(svg if "--svg" in sys.argv else uri if "--uri" in sys.argv else f"{n} bytes of SVG\n")
