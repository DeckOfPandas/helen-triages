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
    text = open(svg_path).read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', text).group(1).split()]
    tr = re.search(r'transform="translate\(([-\d.]+)[, ]+([-\d.]+)\)"', text)
    translate = (float(tr.group(1)), float(tr.group(2))) if tr else (0, 0)
    paths = re.findall(r'\sd="([^"]+)"', text)
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

    The <g transform="translate(...)"> matters and is easy to forget: the
    normaliser leaves Inkscape's group offset in place rather than baking it
    into the path data, so an icon parsed without it rasterises to an empty or
    half-empty canvas -- which counts as "no ink" rather than as a failure.
    """
    text = pathlib.Path(svg_path).read_text()
    box = re.search(r'viewBox="([^"]+)"', text)
    if not box:
        raise ValueError(f'{svg_path}: no viewBox')
    viewbox = [float(v) for v in box.group(1).split()]
    tr = re.search(r'transform="translate\(([-\d.]+)[, ]+([-\d.]+)\)"', text)
    translate = (float(tr.group(1)), float(tr.group(2))) if tr else (0.0, 0.0)
    paths = re.findall(r'\sd="([^"]+)"', text)
    if not paths:
        raise ValueError(f'{svg_path}: no path data')
    return paths, viewbox, translate, 'glass-icon-solid' in text


def render_file(svg_path, out_png, height_px=420, stroke=1.6):
    """Render an existing icon file (single optional <g transform=translate>)."""
    text = open(svg_path).read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', text).group(1).split()]
    tr = re.search(r'transform="translate\(([-\d.]+)[, ]+([-\d.]+)\)"', text)
    translate = (float(tr.group(1)), float(tr.group(2))) if tr else (0, 0)
    paths = re.findall(r'\sd="([^"]+)"', text)
    W, H, g = render(paths, vb, height_px, stroke, translate=translate)
    write_png(out_png, W, H, g)
    return W, H
