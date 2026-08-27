"""Derive real stroke centrelines from FILLED, uniform-width icon artwork.

Written for the tiki mug (#355) and kept because the problem recurs: stock
glass artwork is very often fill-only, and a fill cannot take a stroke-width
because there is no centreline in it to give a width to. Three careful hand
redraws missed before this was written. The problem was not care, it is method
-- eyeballing a 30-stroke drawing reproduces the parts you notice and quietly
normalises the parts you do not.

  1. rasterise the original FILLED, at high resolution -- it is filled ink, so
     this is the drawing as drawn;
  2. thin it to a one-pixel skeleton (Zhang-Suen), which for a constant-width
     stroke IS its centreline;
  3. walk the skeleton into polylines (see `trace` -- the obvious algorithm
     does not work, and the docstring says why);
  4. prune spurs, simplify each polyline (Ramer-Douglas-Peucker), map back into
     viewBox units and emit.

WHEN THIS IS VALID, AND WHEN IT IS NOT. The medial axis of a CONSTANT-width
stroke is that stroke's centreline, which is exactly what is wanted. On
artwork with varying weight it is not: the skeleton still comes out, it is
just no longer the line the artist drew, and nothing here can tell you that
happened. Check the source is uniform width before trusting the output --
for the tiki mug every cap was a 0.85-radius arc, so the ink was a uniform
1.7 units throughout.

THE OUTPUT IS POLYLINES, not curves, so it is wordier than a hand drawing --
46 paths against a set median of 4 for the mug, which is a real cost and is
what #355 is still open about. At icon size the difference between a fitted
curve and a 0.2-unit-tolerance polyline is not visible, but the path count is
not free. Consider whether a simplified redraw would serve better before
reaching for this.

Usage:
    python3 scripts/trace_centrelines.py IN.svg -o OUT.svg
    python3 scripts/trace_centrelines.py IN.svg            # stats only, no write
"""
import argparse
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import svgrender

# Defaults tuned on the tiki mug at 48x84 units. HEIGHT_PX wants to put roughly
# ten pixels across the ink -- too coarse and thinning eats detail, too fine and
# it is slow for no gain.
HEIGHT_PX = 760
RDP_TOL_PX = 1.6                # ~0.18 units at the default height
MIN_BRANCH_PX = 7               # shorter than half a stroke width is a spur


def rasterise(src, height_px):
    """The source, filled, as a 1-bit grid. ss=1 deliberately: supersampling
    would antialias the edges, and thinning wants a hard binary boundary."""
    paths, viewbox, translate, _ = svgrender.parse_icon(src)
    W, H, gray = svgrender.render_filled(paths, viewbox, height_px, ss=1,
                                         translate=translate)
    grid = bytearray(W * H)
    for i, v in enumerate(gray):
        grid[i] = 1 if v < 128 else 0
    return W, H, grid, viewbox


def zhang_suen(W, H, g):
    def nb(i):
        return (g[i - W], g[i - W + 1], g[i + 1], g[i + W + 1],
                g[i + W], g[i + W - 1], g[i - 1], g[i - W - 1])

    changed = True
    rounds = 0
    while changed:
        changed = False
        for step in (0, 1):
            doomed = []
            for y in range(1, H - 1):
                base = y * W
                for x in range(1, W - 1):
                    i = base + x
                    if not g[i]:
                        continue
                    p = nb(i)
                    c = sum(p)
                    if c < 2 or c > 6:
                        continue
                    trans = sum(1 for k in range(8)
                                if p[k] == 0 and p[(k + 1) % 8] == 1)
                    if trans != 1:
                        continue
                    if step == 0:
                        if p[0] * p[2] * p[4] or p[2] * p[4] * p[6]:
                            continue
                    else:
                        if p[0] * p[2] * p[6] or p[0] * p[4] * p[6]:
                            continue
                    doomed.append(i)
            if doomed:
                changed = True
                for i in doomed:
                    g[i] = 0
        rounds += 1
        if rounds > 60:
            break
    return g


NEIGHBOURS = None


def build_neighbours(W, H, g):
    """Adjacency over the skeleton, closed under itself.

    Built in two passes on purpose: the ink set is collected first, then
    neighbours are filtered to members of THAT set. A single pass reading g
    directly can hand back a border pixel that was never given an entry, and
    the walk then dies with a KeyError halfway through a stroke.
    """
    offs = (-W, -W + 1, 1, W + 1, W, W - 1, -1, -W - 1)
    ink = {y * W + x
           for y in range(1, H - 1)
           for x in range(1, W - 1)
           if g[y * W + x]}
    return {i: [i + o for o in offs if (i + o) in ink] for i in ink}


def trace(adj, W):
    """Skeleton -> polylines, by direction-preserving greedy walk.

    THE OBVIOUS ALGORITHM DOES NOT WORK HERE. Splitting the graph at every
    pixel whose degree is not 2 assumes a 4-connected skeleton; a Zhang-Suen
    skeleton is 8-connected, so a pixel on a plain diagonal run routinely has
    three neighbours and nearly every pixel classifies as a junction. That
    version returned 2,966 polylines for a drawing with about thirty strokes.

    What is actually wanted is not the graph's topology, it is long drawable
    strokes. So: start at an endpoint where there is one, and at each step take
    the unvisited neighbour whose direction best continues the current one.
    Strokes then run straight THROUGH crossings instead of stopping at them,
    which is also what the original drawing does.
    """
    unvisited = set(adj)
    polys = []

    def degree(i):
        return sum(1 for n in adj[i] if n in unvisited)

    def step_dir(a, b):
        return ((b % W) - (a % W), (b // W) - (a // W))

    while unvisited:
        # prefer a free end; fall back to any pixel (closed loops have none)
        start = min(unvisited, key=degree)
        pts = [start]
        unvisited.discard(start)
        prev_dir = None
        cur = start
        while True:
            options = [n for n in adj[cur] if n in unvisited]
            if not options:
                break
            if prev_dir is None:
                nxt = options[0]
            else:
                def score(n):
                    dx, dy = step_dir(cur, n)
                    m = math.hypot(dx, dy) or 1
                    pm = math.hypot(*prev_dir) or 1
                    return (dx * prev_dir[0] + dy * prev_dir[1]) / (m * pm)
                nxt = max(options, key=score)
            prev_dir = step_dir(cur, nxt)
            unvisited.discard(nxt)
            pts.append(nxt)
            cur = nxt
        polys.append(pts)

    return polys


def rdp(pts, tol):
    if len(pts) < 3:
        return pts
    x0, y0 = pts[0]
    x1, y1 = pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    worst, wi = -1, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        if n == 0:
            d = math.hypot(px - x0, py - y0)
        else:
            d = abs(dy * px - dx * py + x1 * y0 - y1 * x0) / n
        if d > worst:
            worst, wi = d, i
    if worst <= tol:
        return [pts[0], pts[-1]]
    return rdp(pts[:wi + 1], tol)[:-1] + rdp(pts[wi:], tol)


def to_paths(polys, W, viewbox, height_px, rdp_tol):
    """Skeleton pixel runs -> `d` strings in the source's own viewBox units."""
    scale = height_px / viewbox[3]
    out, total = [], 0
    for poly in polys:
        pts = [((p % W) + 0.5, (p // W) + 0.5) for p in poly]
        pts = rdp(pts, rdp_tol)
        total += len(pts)
        u = [(x / scale + viewbox[0], y / scale + viewbox[1]) for x, y in pts]
        d = 'M ' + ' L '.join(f'{x:.2f},{y:.2f}' for x, y in u)
        if poly[0] == poly[-1]:
            d += ' Z'
        out.append(d)
    return out, total


def as_svg(paths, viewbox):
    lines = [f'<svg viewBox="{" ".join(f"{v:g}" for v in viewbox)}"',
             '     role="img" aria-hidden="true" focusable="false">']
    lines += [f'  <path class="glass-icon-line" d="{d}" />' for d in paths]
    lines.append('</svg>')
    return '\n'.join(lines) + '\n'


def trace_file(src, height_px=HEIGHT_PX, rdp_tol=RDP_TOL_PX,
               min_branch=MIN_BRANCH_PX, report=print):
    W, H, g, viewbox = rasterise(src, height_px)
    report(f'raster {W}x{H}, ink pixels {sum(g)}')
    g = zhang_suen(W, H, g)
    report(f'skeleton pixels {sum(g)}')
    polys = trace(build_neighbours(W, H, g), W)
    report(f'{len(polys)} raw polylines')
    kept = [p for p in polys if len(p) >= min_branch]
    report(f'{len(kept)} after dropping runs shorter than {min_branch}px')
    paths, total = to_paths(kept, W, viewbox, height_px, rdp_tol)
    report(f'{total} points after simplification')
    return paths, viewbox


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('source', help='filled, uniform-width SVG to trace')
    ap.add_argument('-o', '--output', help='write an SVG here (default: dry run)')
    ap.add_argument('--height', type=int, default=HEIGHT_PX,
                    help=f'raster height in px (default {HEIGHT_PX})')
    ap.add_argument('--rdp-tol', type=float, default=RDP_TOL_PX,
                    help=f'simplification tolerance in px (default {RDP_TOL_PX})')
    ap.add_argument('--min-branch', type=int, default=MIN_BRANCH_PX,
                    help=f'drop runs shorter than this (default {MIN_BRANCH_PX})')
    args = ap.parse_args(argv)

    paths, viewbox = trace_file(args.source, args.height, args.rdp_tol,
                                args.min_branch)
    if not args.output:
        print(f'\n{len(paths)} paths -- dry run, nothing written. '
              f'Pass -o to save, and LOOK at the result before trusting it.')
        return
    pathlib.Path(args.output).write_text(as_svg(paths, viewbox))
    print(f'\nwrote {args.output} ({len(paths)} paths)')


# Guarded, and not decoratively: scripts/normalise_glass_icons.py had a bare
# main() at import once, and importing it to read a constant deleted all 26
# icons (its first act is shutil.rmtree). Every script here stays importable.
if __name__ == '__main__':
    main()
