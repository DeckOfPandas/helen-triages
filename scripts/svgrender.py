"""A minimal SVG rasteriser for the glass icons, so artwork can be MEASURED.

There is no cairosvg, rsvg-convert, ImageMagick or Inkscape available here, and
drawing an icon blind is how you ship a tiki mug with gaps in its lines. This
handles exactly the subset the glass icons use -- absolute M/L/C/Z plus the
h/v/A shorthands -- flattens curves to polylines, and rasterises either as
round-capped strokes (`render`) or as nonzero-winding fills (`render_filled`).

WHY THIS IS IN scripts/ RATHER THAN tmp/ (#498). It started as a throwaway to
answer "does this look like a tiki mug", but it has since been the only way to
answer three separate questions that reasoning got WRONG:

  - #472: which icons actually read darker, and why. Eyeballing said "the
    filled one"; measuring said the filled one AND a 46-path stroked one.
  - the double old-fashioned's size, where the viewBox numbers pointed the
    opposite way to the truth (#503).
  - the tiki mug centrelines, via scripts/trace_centrelines.py, which cannot
    work without a rasteriser.

It is not a general SVG renderer and is not trying to be: no styling, no
transforms beyond a single translate, no gradients, no text. It is enough to
turn these particular files into pixels that can be counted, which is the whole
job. Anything it cannot parse it should fail loudly on rather than silently
render wrong -- a quietly-empty raster would read as "no ink", which every
caller would interpret as a pass.
"""
import math
import pathlib
import re
import struct
import zlib


# --- path parsing -------------------------------------------------------------

TOKEN = re.compile(r'([MmLlHhVvCcSsZzAa])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)')


def _tokens(d):
    for m in TOKEN.finditer(d):
        yield m.group(1) if m.group(1) else float(m.group(2))


def _cubic(p0, p1, p2, p3, n=28):
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def _arc(p0, rx, ry, rot, large, sweep, p1, n=28):
    """Endpoint-parameterised arc -> polyline (SVG implementation notes F.6)."""
    x0, y0 = p0
    x1, y1 = p1
    if rx == 0 or ry == 0 or (x0 == x1 and y0 == y1):
        return [p1]
    phi = math.radians(rot)
    dx2, dy2 = (x0 - x1) / 2, (y0 - y1) / 2
    x1p = math.cos(phi) * dx2 + math.sin(phi) * dy2
    y1p = -math.sin(phi) * dx2 + math.cos(phi) * dy2
    rx, ry = abs(rx), abs(ry)
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx
    cx = math.cos(phi) * cxp - math.sin(phi) * cyp + (x0 + x1) / 2
    cy = math.sin(phi) * cxp + math.cos(phi) * cyp + (y0 + y1) / 2

    def ang(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        n1 = math.hypot(ux, uy) * math.hypot(vx, vy)
        a = math.acos(max(-1.0, min(1.0, dot / n1))) if n1 else 0.0
        return -a if ux * vy - uy * vx < 0 else a

    th0 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    elif sweep and dth < 0:
        dth += 2 * math.pi
    pts = []
    for i in range(1, n + 1):
        th = th0 + dth * i / n
        pts.append((
            math.cos(phi) * rx * math.cos(th) - math.sin(phi) * ry * math.sin(th) + cx,
            math.sin(phi) * rx * math.cos(th) + math.cos(phi) * ry * math.sin(th) + cy,
        ))
    return pts


def flatten(d):
    """Path data -> list of polylines."""
    toks = list(_tokens(d))
    i = 0
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    sub = []
    out = []
    cmd = None
    prev_c2 = None

    def take(n):
        nonlocal i
        vals = toks[i:i + n]
        i += n
        return vals

    while i < len(toks):
        if isinstance(toks[i], str):
            cmd = toks[i]
            i += 1
            if cmd in 'Zz':
                if sub:
                    sub.append(start)
                    out.append(sub)
                    sub = []
                cur = start
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == 'M':
            x, y = take(2)
            if rel:
                x, y = cur[0] + x, cur[1] + y
            if sub:
                out.append(sub)
            cur = start = (x, y)
            sub = [cur]
            cmd = 'l' if rel else 'L'
        elif c == 'L':
            x, y = take(2)
            if rel:
                x, y = cur[0] + x, cur[1] + y
            cur = (x, y)
            sub.append(cur)
        elif c == 'H':
            x = take(1)[0]
            x = cur[0] + x if rel else x
            cur = (x, cur[1])
            sub.append(cur)
        elif c == 'V':
            y = take(1)[0]
            y = cur[1] + y if rel else y
            cur = (cur[0], y)
            sub.append(cur)
        elif c == 'C':
            x1, y1, x2, y2, x, y = take(6)
            if rel:
                x1, y1 = cur[0] + x1, cur[1] + y1
                x2, y2 = cur[0] + x2, cur[1] + y2
                x, y = cur[0] + x, cur[1] + y
            sub.extend(_cubic(cur, (x1, y1), (x2, y2), (x, y)))
            prev_c2 = (x2, y2)
            cur = (x, y)
        elif c == 'S':
            x2, y2, x, y = take(4)
            if rel:
                x2, y2 = cur[0] + x2, cur[1] + y2
                x, y = cur[0] + x, cur[1] + y
            x1, y1 = (2 * cur[0] - prev_c2[0], 2 * cur[1] - prev_c2[1]) if prev_c2 else cur
            sub.extend(_cubic(cur, (x1, y1), (x2, y2), (x, y)))
            prev_c2 = (x2, y2)
            cur = (x, y)
        elif c == 'A':
            rx, ry, rot, large, sweep, x, y = take(7)
            if rel:
                x, y = cur[0] + x, cur[1] + y
            sub.extend(_arc(cur, rx, ry, rot, int(large), int(sweep), (x, y)))
            cur = (x, y)
        else:
            raise SystemExit(f'unsupported command {cmd!r}')
    if sub:
        out.append(sub)
    return out


# --- rasterising ---------------------------------------------------------------

def render(paths, viewbox, height_px=420, stroke=1.6, ss=3, translate=(0, 0)):
    vx, vy, vw, vh = viewbox
    scale = height_px / vh
    W, H = int(round(vw * scale)), height_px
    sw, sh = W * ss, H * ss
    buf = bytearray(b'\xff' * (sw * sh))

    r = max(0.6, stroke * scale * ss / 2)
    r2 = r * r
    ri = int(math.ceil(r))

    def stamp(px, py):
        x0, x1 = int(px - ri), int(px + ri) + 1
        y0, y1 = int(py - ri), int(py + ri) + 1
        for yy in range(max(0, y0), min(sh, y1)):
            dy = yy + 0.5 - py
            for xx in range(max(0, x0), min(sw, x1)):
                dx = xx + 0.5 - px
                if dx * dx + dy * dy <= r2:
                    buf[yy * sw + xx] = 0

    for d in paths:
        for poly in flatten(d):
            pts = [(( x + translate[0] - vx) * scale * ss,
                    ( y + translate[1] - vy) * scale * ss) for x, y in poly]
            for a, b in zip(pts, pts[1:]):
                dist = math.hypot(b[0] - a[0], b[1] - a[1])
                steps = max(1, int(dist / (r * 0.5)))
                for s in range(steps + 1):
                    t = s / steps
                    stamp(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    # box downsample
    out = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            tot = 0
            for j in range(ss):
                row = (y * ss + j) * sw + x * ss
                for k in range(ss):
                    tot += buf[row + k]
            out[y * W + x] = tot // (ss * ss)
    return W, H, bytes(out)


def render_filled(paths, viewbox, height_px=420, ss=3, translate=(0, 0)):
    """Scanline fill, nonzero winding -- for LOOKING at fill-based artwork.

    The tiki mug's source is filled ink, so stroking its paths shows the
    outline of the drawing rather than the drawing. This renders what the
    artwork actually is.
    """
    vx, vy, vw, vh = viewbox
    scale = height_px / vh
    W, H = int(round(vw * scale)), height_px
    sw, sh = W * ss, H * ss
    buf = bytearray(b'\xff' * (sw * sh))

    edges = []
    for d in paths:
        for poly in flatten(d):
            pts = [((x + translate[0] - vx) * scale * ss,
                    (y + translate[1] - vy) * scale * ss) for x, y in poly]
            if len(pts) < 2:
                continue
            if pts[0] != pts[-1]:
                pts.append(pts[0])          # fill implies closure
            for a, b in zip(pts, pts[1:]):
                if a[1] != b[1]:
                    edges.append((a, b))

    for yy in range(sh):
        yc = yy + 0.5
        xs = []
        for a, b in edges:
            y0, y1 = a[1], b[1]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                t = (yc - y0) / (y1 - y0)
                xs.append((a[0] + (b[0] - a[0]) * t, 1 if y1 > y0 else -1))
        if not xs:
            continue
        xs.sort()
        wind = 0
        row = yy * sw
        for i in range(len(xs) - 1):
            wind += xs[i][1]
            if wind != 0:
                x0 = max(0, int(math.ceil(xs[i][0] - 0.5)))
                x1 = min(sw, int(math.ceil(xs[i + 1][0] - 0.5)))
                for xx in range(x0, x1):
                    buf[row + xx] = 0

    out = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            tot = 0
            for j in range(ss):
                r0 = (y * ss + j) * sw + x * ss
                for k in range(ss):
                    tot += buf[r0 + k]
            out[y * W + x] = tot // (ss * ss)
    return W, H, bytes(out)


def render_file_filled(svg_path, out_png, height_px=420):
    # Through parse_icon_text, not its own regexes -- this had a fourth copy of
    # the one-translate parse that #599 found wrong on four icons.
    paths, vb, translate, _ = parse_icon_text(
        pathlib.Path(svg_path).read_text(), str(svg_path))
    W, H, g = render_filled(paths, vb, height_px, translate=translate)
    write_png(out_png, W, H, g)
    return W, H


def write_png(path, W, H, gray):
    raw = b''.join(b'\x00' + gray[y * W:(y + 1) * W] for y in range(H))

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 0, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    open(path, 'wb').write(png)


def parse_icon(svg_path):
    """(paths, viewbox, translate, is_filled) for one glass icon file.

    Factored out because five callers had each grown their own copy of these
    three regexes -- the audits behind #472, the tracer, and the viewBox-margin
    guard. Copies of a parser drift, and a parser that drifts from the files it
    reads fails by returning PLAUSIBLE numbers rather than by erroring.

    The <g transform="..."> matters and is easy to forget: the normaliser leaves
    Inkscape's group offset in place rather than baking it into the path data,
    so an icon parsed without it rasterises to an empty or half-empty canvas --
    which counts as "no ink" rather than as a failure.

    THE TRANSFORM IS A STACK, NOT AN ATTRIBUTE, and reading it as one attribute
    was wrong for four of the 26 icons. This function used to pull the FIRST
    `translate(...)` out with a regex and hand it back for callers to add on.
    Four drawings nest a second group inside the first -- coupe, goblet,
    old-fashioned-double and nick-and-nora each carry a
    `<g transform="matrix(...)">` holding the bowl -- and that matrix was
    silently dropped, so every measurement taken through here read their bowls
    at the wrong size and place.

    IT FAILED IN THE DIRECTION THAT LOOKS FINE. The bowl still landed somewhere
    inside the canvas, so `test_no_glass_artwork_has_a_slack_viewbox` measured a
    healthy 97.5% fill for the coupe while 11.8 units of its rim sat outside the
    viewBox entirely, and `fit_viewbox` then clamped the canvas onto geometry it
    had mis-read. See issue #599.
    """
    return parse_icon_text(pathlib.Path(svg_path).read_text(), svg_path)


TRANSFORM_OP = re.compile(r'(translate|matrix|scale)\(([^)]*)\)')
_ELEMENT = re.compile(r'<(/?)([A-Za-z][\w:-]*)((?:"[^"]*"|[^>])*?)(/?)>', re.S)
IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def compose(m, n):
    """m then n, as SVG's (a b c d e f) column-vector convention: m applied to
    the result of n, i.e. the matrix a nested group ends up with."""
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def parse_transform(value):
    """An SVG transform attribute -> one (a, b, c, d, e, f) matrix.

    Only the three operations these drawings actually use are supported, and an
    unknown one raises rather than being skipped: silently ignoring a rotate()
    would put the artwork somewhere else and report a plausible number for it,
    which is the whole failure this function exists to stop.
    """
    m = IDENTITY
    consumed = 0
    for op, args in TRANSFORM_OP.findall(value or ''):
        nums = [float(x) for x in re.split(r'[,\s]+', args.strip()) if x]
        if op == 'translate':
            t = (1.0, 0.0, 0.0, 1.0, nums[0], nums[1] if len(nums) > 1 else 0.0)
        elif op == 'scale':
            t = (nums[0], 0.0, 0.0, nums[1] if len(nums) > 1 else nums[0], 0.0, 0.0)
        else:
            t = tuple(nums)
        m = compose(m, t)
        consumed += 1
    if (value or '').strip() and not consumed:
        raise ValueError(f'unsupported transform {value!r}')
    return m


def apply_matrix(m, x, y):
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def _placed_paths(text, label):
    """[(d, matrix)] for every <path>, each with its full ancestor transform."""
    stack = [IDENTITY]
    out = []
    for close, tag, attrs, selfclose in _ELEMENT.findall(text):
        if close:
            if tag == 'g' and len(stack) > 1:
                stack.pop()
            continue
        here = stack[-1]
        tm = re.search(r'transform="([^"]*)"', attrs)
        if tm:
            here = compose(here, parse_transform(tm.group(1)))
        if tag == 'g' and not selfclose:
            stack.append(here)
        elif tag == 'path':
            d = re.search(r'\sd="([^"]*)"', attrs)
            if d and d.group(1).strip():
                out.append((d.group(1), here))
    if not out:
        raise ValueError(f'{label}: no path data')
    return out


def _as_path_data(polylines):
    """Flattened polylines -> one `d` string, in the viewBox's own units."""
    parts = []
    for sub in polylines:
        if not sub:
            continue
        parts.append('M ' + ' L '.join(f'{x:.6f},{y:.6f}' for x, y in sub))
    return ' '.join(parts)


def parse_icon_text(text, label='<svg>'):
    """As parse_icon, but for SVG text that is not on disk yet -- which is what
    scripts/normalise_glass_icons.py needs to fit a canvas to output it has
    just built and not yet written.

    THE PATHS COME BACK ALREADY PLACED, and `translate` is therefore always
    (0, 0). Every ancestor transform is composed and baked into the geometry
    here, so a caller cannot forget to apply one and cannot apply only the
    outermost -- which is exactly the bug this replaces. The returned `d`
    strings are flattened polylines rather than the file's own curves: the
    callers are a rasteriser and a bounding box, both of which flatten anyway,
    and `fit_viewbox` never writes path data back.

    `translate` is still returned so the four existing call sites keep working
    unchanged; passing it on to render() adds nothing, which is correct now.
    """
    box = re.search(r'viewBox="([^"]+)"', text)
    if not box:
        raise ValueError(f'{label}: no viewBox')
    viewbox = [float(v) for v in box.group(1).split()]
    paths = []
    for d, m in _placed_paths(text, label):
        placed = [[apply_matrix(m, x, y) for x, y in sub] for sub in flatten(d)]
        data = _as_path_data(placed)
        if data:
            paths.append(data)
    if not paths:
        raise ValueError(f'{label}: no path data')
    return paths, viewbox, (0.0, 0.0), 'glass-icon-solid' in text


def ink_bbox_units(paths, viewbox, translate=(0, 0), probe_px=None):
    """(x0, y0, x1, y1) of the VISIBLE ink, in the viewBox's own units.

    Two traps here, and the naive implementation falls into one or the other.

    NOT A RASTER. Finding ink pixels works, but the answer depends on where the
    pixel grid falls, which depends on the viewBox, which is the thing being
    computed -- so feeding the result back in moves it. Measured over eight
    successive fits, the canvas oscillated across a ~0.1-unit band instead of
    settling. Flattening the paths is exact and has no grid to land on.

    IT USED TO CLIP TO THE VIEWBOX AND NO LONGER DOES -- issue #599. The
    argument for clipping was that some drawings extend outside their own
    canvas, that the excess "has never been visible on the site", and that
    fitting to it would reveal drawing nobody has seen. Both halves of that
    turned out to be wrong:

    - It IS visible. `.drink-card-glass svg` sets `overflow: visible` (added so
      a stroke sitting on the viewBox edge is not sheared, §9.11), and a root
      <svg> only clips because the UA stylesheet says so. Turning that off drew
      the excess on every card, which is what made the coupe sit high in its
      panel.
    - The numbers behind it were mis-measured. They came from a parser that
      dropped nested <g transform> groups (see parse_icon_text), so the figures
      quoted for the goblet and the coupe described geometry in the wrong place.

    So this measures ALL the ink, which is what a browser now paints. That is
    also strictly more idempotent than clipping was: the answer does not depend
    on the viewBox at all, so it cannot move when the viewBox does.
    """
    tx, ty = translate
    xs, ys = [], []
    for d in paths:
        for sub in flatten(d):
            for x, y in sub:
                xs.append(x + tx)
                ys.append(y + ty)
    if not xs:
        raise ValueError('no ink at all -- the file has no usable path data')
    return min(xs), min(ys), max(xs), max(ys)


def fit_viewbox(text, margin=1.4, label='<svg>'):
    """SVG text with its viewBox tightened to the artwork plus `margin` units.

    THE ARTWORK DOES NOT MOVE. Path data and the <g transform> are untouched;
    only the frame changes. So this can reframe a drawing but never distort one.

    MARGIN IS IN USER UNITS, NOT A PERCENTAGE. These icons use
    `vector-effect: non-scaling-stroke`, so the stroke is a fixed number of
    SCREEN pixels and therefore spans MORE viewBox units the smaller the icon
    renders. A percentage margin would shrink exactly when the stroke needs it
    most -- on a card -- and clip the rim. 1.2 is the set's own typical margin.

    IT GROWS AS WELL AS SHRINKS, SINCE #599, and the clamp it replaces was a
    consequence of the clip that ink_bbox_units no longer applies. The old
    reasoning was that padding an ink box which touches the clip edge pushes the
    canvas out, admitting a sliver of previously-hidden artwork, enlarging the
    box, pushing it out again -- unbounded creep, one margin per regeneration.
    That is real, and it is a property of measuring CLIPPED ink: the input moved
    when the frame moved. Measuring all the ink has no such feedback, because
    the bounding box does not depend on the viewBox at all, so one pass lands on
    the answer and a second finds it unchanged. `test_fitting_a_canvas_never_
    moves_the_artwork` asserts exactly that.

    What the clamp actually bought was a promise -- "fitting removes empty
    space, it never reveals drawing nobody has seen" -- that the site had
    already broken. `overflow: visible` on a card means the excess was on
    screen; the canvas was simply lying about where the drawing was. Growing the
    box to contain it is what makes `heights_mm` true again.
    """
    paths, viewbox, translate, _ = parse_icon_text(text, label)
    x0, y0, x1, y1 = ink_bbox_units(paths, viewbox, translate)
    new = (x0 - margin, y0 - margin,
           (x1 - x0) + 2 * margin, (y1 - y0) + 2 * margin)
    attr = 'viewBox="%s"' % ' '.join(f'{v:.4f}' for v in new)
    old = re.search(r'viewBox="[^"]+"', text).group(0)
    return text.replace(old, attr, 1), viewbox[3], new[3]


def render_file(svg_path, out_png, height_px=420, stroke=1.6):
    """Render an existing icon file, with its full transform stack applied."""
    paths, vb, translate, _ = parse_icon_text(
        pathlib.Path(svg_path).read_text(), str(svg_path))
    W, H, g = render(paths, vb, height_px, stroke, translate=translate)
    write_png(out_png, W, H, g)
    return W, H
