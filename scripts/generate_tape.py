#!/usr/bin/env python3
"""Generate a tape background SVG for assets/img/chrome/tape/ (issue #122).

The output directory moved out of assets/img/food/ in issue #374: the wordmark
is shared chrome, so there is one tape set for the whole repo rather than a copy
per site. Regenerating no longer has a "and copy it across to cocktails" step --
that chore, and the drift it was there to prevent, are both gone.

WHAT THIS IS: the tool behind the current tape-1.svg..tape-7.svg. Each file
is one polygon body (viewBox 0 0 1400 170, fill #0d0d0d) plus two kinds of
<line> texture: an edge bevel suggesting the tape sits raised off the page,
and "machine marks" -- clusters of near-vertical, slightly overlapping
scratch lines -- printed on top of it.

THE DESIGN, decided interactively against real renders, not guessed:

  - Corners: the two BOTTOM corners of the polygon can each be acute (<90,
    the bottom edge flares past the top edge) or obtuse (>90, it insets
    under it), independently -- corner_mode picks both-acute, both-obtuse,
    or one of each ("mixed"). The top edge stays flat. See make_polygon().

  - Machine marks: 5-7 narrow clusters (centred on 6), each a handful of
    jittered near-vertical lines. The tape is split into three zones --
    left flank, the "letter zone" behind the lettering, right flank -- and
    every generation guarantees at least one cluster per zone, with the
    single clearest and second-clearest cluster on the whole tape always
    landing one per flank (which flank gets which is randomised). Gaps
    between clusters are wide and irregular, closer to how a physical
    machine actually marks tape than an even scatter. See generate_marks_v3().

  - Edge bevel: a highlight pair on the top and left edges, a much subtler
    pair on bottom and right, both hard-offset with no blur -- same
    light-from-top-left, two-hard-copies logic as the wordmark's own
    punched(raised) mixin (_sass/shared/_rule.scss), not a new effect. See
    make_edge_bevel().

LEFT_FLANK_FRAC / RIGHT_FLANK_FRAC (how much of the tape's width counts as
"outside the lettering") are a guess, not measured against real font
metrics -- the source viewBox is stretched non-uniformly
(preserveAspectRatio="none") to whatever the real wordmark width ends up
being. Revisit by eye against the real render if the flank starts reading
too wide or too narrow.

HOW TO USE IT:

    python3 scripts/generate_tape.py --corner-mode both_acute --seed 30 \\
        --out assets/img/chrome/tape/tape-1.svg

    # print to stdout instead of writing a file
    python3 scripts/generate_tape.py --corner-mode mixed --seed 99

    # same corners, different marks (useful once you like a shape but want
    # to see other mark layouts on it)
    python3 scripts/generate_tape.py --corner-mode both_acute --seed 2 \\
        --marks-seed 202

--seed drives the corner shape; --marks-seed (defaults to --seed) drives
the machine marks independently, so the two can vary separately. There is
no "pick a good one automatically" mode -- generate a batch of candidates
across all three corner_modes, look at them against the real header (a
throwaway HTML mockup using the actual .site-logo-* CSS from
_sass/shared/_layout.scss is the fastest way), and hand-pick.
"""
from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

VIEWBOX_W = 1400
VIEWBOX_H = 170
TOP_Y = 28
BOT_Y = 148
TOP_MARGIN_X = 58  # top-left x; top-right x = VIEWBOX_W - TOP_MARGIN_X

STRONG_OPACITY = (0.30, 0.62)
STRONG_WIDTH = (0.7, 2.1)
STRONG_COLORS = ["#555", "#666", "#707070", "#5c5c5c"]

REGULAR_OPACITY = (0.05, 0.22)
REGULAR_WIDTH = (0.5, 1.3)
REGULAR_COLORS = ["#2e2e2e", "#323232", "#363636", "#383838", "#343434"]

LEFT_FLANK_FRAC = 0.16
RIGHT_FLANK_FRAC = 0.16

BEVEL_LIGHT_COLOR = "#8b8b8b"
BEVEL_SHADOW_COLOR = "#050505"

CORNER_MODES = ("both_acute", "both_obtuse", "mixed")


def make_polygon(rng, corner_mode, skew_range=(4, 16)):
    """corner_mode: 'both_acute' | 'both_obtuse' | 'mixed'.
    'acute' = bottom corner angle < 90 (bottom edge flares past the top edge)
    'obtuse' = bottom corner angle > 90 (bottom edge insets under the top edge)
    """
    def mag():
        return rng.uniform(*skew_range)

    if corner_mode == "both_acute":
        skew_left, skew_right = mag(), mag()
    elif corner_mode == "both_obtuse":
        skew_left, skew_right = -mag(), -mag()
    elif corner_mode == "mixed":
        a, b = mag(), -mag()
        if rng.random() < 0.5:
            a, b = b, a
        skew_left, skew_right = a, b
    else:
        raise ValueError(f"unknown corner_mode: {corner_mode!r}, expected one of {CORNER_MODES}")

    top_left = (TOP_MARGIN_X, TOP_Y)
    top_right = (VIEWBOX_W - TOP_MARGIN_X, TOP_Y)
    bottom_left = (TOP_MARGIN_X - skew_left, BOT_Y)
    bottom_right = (VIEWBOX_W - TOP_MARGIN_X + skew_right, BOT_Y)

    points = (
        f"{top_left[0]:.1f},{top_left[1]} {top_right[0]:.1f},{top_right[1]} "
        f"{bottom_right[0]:.1f},{bottom_right[1]} {bottom_left[0]:.1f},{bottom_left[1]}"
    )
    return points, top_left, top_right, bottom_left, bottom_right


def corner_angle(corner, a, b):
    va = (a[0] - corner[0], a[1] - corner[1])
    vb = (b[0] - corner[0], b[1] - corner[1])
    dot = va[0] * vb[0] + va[1] * vb[1]
    mag_a = math.hypot(*va)
    mag_b = math.hypot(*vb)
    cos_t = max(-1, min(1, dot / (mag_a * mag_b)))
    return math.degrees(math.acos(cos_t))


# --- edge bevel: "raised off the page" -------------------------------------
#
# Same light-from-top-left convention as the wordmark's own punched(raised)
# mixin -- two hard, unblurred offset copies, light side visible and solid,
# dark side subtle rather than truly darker (against a near-black #0d0d0d
# fill, a "dark" tone that isn't pushed hard toward true black just reads
# as LIGHTER than the tape, not recessed -- see HANDOVER_v26.md 13.4.1).
#
# Because .site-logo-tape carries the whole rotate(-1.75deg) transform
# around BOTH the tape-bg and the lettering together, defining "top-left"
# in this SVG's own local, pre-rotation coordinate space keeps it
# automatically consistent with the lettering's own text-shadow (also
# defined pre-rotation) -- no compensation for the rotation needed here.

def _edge_normal_inward(p1, p2, centroid):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy) or 1
    dx, dy = dx / length, dy / length
    n1 = (-dy, dx)
    n2 = (dy, -dx)
    mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    to_centroid = (centroid[0] - mid[0], centroid[1] - mid[1])
    return n1 if (n1[0] * to_centroid[0] + n1[1] * to_centroid[1]) > 0 else n2


def make_edge_bevel(top_left, top_right, bottom_left, bottom_right):
    centroid = (
        (top_left[0] + top_right[0] + bottom_left[0] + bottom_right[0]) / 4,
        (top_left[1] + top_right[1] + bottom_left[1] + bottom_right[1]) / 4,
    )
    edges = [
        ("top", top_left, top_right),
        ("right", top_right, bottom_right),
        ("bottom", bottom_right, bottom_left),
        ("left", bottom_left, top_left),
    ]
    lit_edges = {"top", "left"}

    lines = []
    trim = 7  # shorten each bevel line so it doesn't overrun into the next corner
    for name, p1, p2 in edges:
        nx, ny = _edge_normal_inward(p1, p2, centroid)
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = math.hypot(dx, dy) or 1
        ux, uy = dx / length, dy / length
        a = (p1[0] + ux * trim, p1[1] + uy * trim)
        b = (p2[0] - ux * trim, p2[1] - uy * trim)

        lit = name in lit_edges
        color = BEVEL_LIGHT_COLOR if lit else BEVEL_SHADOW_COLOR
        # Two hard offset copies, no blur -- "stroke sets weight, two copies
        # set direction", same logic as punched(), not a soft gradient.
        passes = [(1.6, 0.62), (3.4, 0.30)] if lit else [(1.4, 0.30), (3.0, 0.16)]
        for offset, opacity in passes:
            x1, y1 = a[0] + nx * offset, a[1] + ny * offset
            x2, y2 = b[0] + nx * offset, b[1] + ny * offset
            lines.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                f'stroke="{color}" stroke-width="1.4" opacity="{opacity:.2f}"/>'
            )
    return lines


# --- machine marks: zone-aware, clarity-ranked clusters ---------------------
#
# The tape is split into three zones -- left flank, the letter zone (behind
# the lettering), right flank. Every generation guarantees at least one
# cluster per zone, and the single clearest and second-clearest cluster on
# the whole tape always land one per flank (never both on the same side,
# never in the letter zone) -- enforced by construction, not checked after
# the fact: the two ranks are assigned high clarity values before anything
# else is drawn, and every other cluster is capped below the lower of the two.

def _clarity_style(rng, clarity):
    """clarity in [0, 1] -> opacity/width/color for one line, continuous
    rather than a hard strong/regular split -- 'second clearest' needs a
    real gradient to sit between 'clearest' and 'barely there'."""
    op_center = 0.08 + 0.60 * clarity
    op = max(0.03, min(0.80, rng.gauss(op_center, 0.07)))
    sw_center = 0.65 + 1.35 * clarity
    sw = max(0.4, rng.gauss(sw_center, 0.22))
    color = rng.choice(STRONG_COLORS) if rng.random() < clarity else rng.choice(REGULAR_COLORS)
    return op, sw, color


def _cluster_lines(rng, center_x, width, clarity):
    lines = []
    n_seams = rng.randint(1, 3)
    n_lines_per_seam_max = 5 + int(9 * clarity)
    half = width / 2
    for _ in range(n_seams):
        seam_x = center_x + rng.uniform(-half, half)
        n_lines = rng.randint(3, max(4, n_lines_per_seam_max))
        for _ in range(n_lines):
            jx = seam_x + rng.uniform(-1.3, 1.3)
            span = BOT_Y - TOP_Y
            length = rng.uniform(span * 0.15, span * 0.98)
            y1 = rng.uniform(TOP_Y, BOT_Y - length)
            y2 = y1 + length
            op, sw, color = _clarity_style(rng, clarity)
            lines.append(
                f'<line x1="{jx:.2f}" y1="{y1:.1f}" x2="{jx:.2f}" y2="{y2:.1f}" '
                f'stroke="{color}" stroke-width="{sw:.2f}" opacity="{op:.2f}"/>'
            )
    return lines


def _place_clusters_in_zone(rng, zone_start, zone_end, count, min_width=4, max_width=16, min_gap=26):
    """Narrow clusters with irregular gaps, packed left-to-right so they
    never overlap and stay inside the zone."""
    zone_w = zone_end - zone_start
    if count <= 0 or zone_w <= 0:
        return []

    widths = [rng.uniform(min_width, max_width) for _ in range(count)]
    gap_weights = [rng.uniform(0.4, 3.0) for _ in range(count + 1)]  # before/between/after
    used_w = sum(widths)
    remaining = max(zone_w - used_w, min_gap * (count - 1))
    gap_sum = sum(gap_weights) or 1
    gaps = [remaining * (w / gap_sum) for w in gap_weights]

    centers = []
    x = zone_start + gaps[0]
    for i, w in enumerate(widths):
        centers.append((x + w / 2, w))
        x += w + gaps[i + 1]
    return centers


def generate_marks(rng, inner_left, inner_right):
    total_w = inner_right - inner_left
    left_end = inner_left + total_w * LEFT_FLANK_FRAC
    right_start = inner_right - total_w * RIGHT_FLANK_FRAC

    n_clusters = rng.choices([5, 6, 7], weights=[1, 3, 1])[0]
    zone_counts = {"left": 1, "letter": 1, "right": 1}
    remaining = n_clusters - 3
    zone_names = ["left", "letter", "right"]
    zone_weights = [1.0, 2.2, 1.0]
    for _ in range(remaining):
        zone_counts[rng.choices(zone_names, weights=zone_weights)[0]] += 1

    left_centers = _place_clusters_in_zone(rng, inner_left, left_end, zone_counts["left"])
    letter_centers = _place_clusters_in_zone(rng, left_end, right_start, zone_counts["letter"])
    right_centers = _place_clusters_in_zone(rng, right_start, inner_right, zone_counts["right"])

    rank1_side, rank2_side = ("left", "right") if rng.random() < 0.5 else ("right", "left")

    clusters = []  # [center, width, clarity, zone]
    for zone, centers in (("left", left_centers), ("letter", letter_centers), ("right", right_centers)):
        for cx, w in centers:
            clusters.append([cx, w, None, zone])

    def assign_rank(zone, clarity_value):
        candidates = [c for c in clusters if c[3] == zone]
        rng.choice(candidates)[2] = clarity_value

    assign_rank(rank1_side, rng.uniform(0.90, 1.0))
    assign_rank(rank2_side, rng.uniform(0.76, 0.88))

    for c in clusters:
        if c[2] is None:
            c[2] = rng.uniform(0.10, 0.62)

    lines = []
    cluster_meta = []
    for cx, w, clarity, zone in clusters:
        lines += _cluster_lines(rng, cx, w, clarity)
        cluster_meta.append({"x": round(cx, 1), "zone": zone, "clarity": round(clarity, 2)})

    return lines, cluster_meta


def generate(seed, corner_mode, marks_seed=None):
    """seed drives the polygon/corners; marks_seed (defaults to seed) drives
    the machine marks separately, so the same corners can be paired with
    different mark layouts without the two draws colliding.

    Returns (svg: str, meta: dict) -- meta includes the measured corner
    angles, useful for picking/labelling candidates without eyeballing.
    """
    rng = random.Random(seed)
    points, tl, tr, bl, br = make_polygon(rng, corner_mode)

    angle_l = corner_angle(bl, br, tl)
    angle_r = corner_angle(br, bl, tr)

    inner_left = min(tl[0], bl[0]) + 3
    inner_right = max(tr[0], br[0]) - 3

    bevel_lines = make_edge_bevel(tl, tr, bl, br)

    rng = random.Random(marks_seed if marks_seed is not None else seed)
    mark_lines, cluster_meta = generate_marks(rng, inner_left, inner_right)

    lines_svg = "\n".join(bevel_lines + mark_lines)
    svg = (
        f'<svg width="100%" viewBox="0 0 {VIEWBOX_W} {VIEWBOX_H}" role="img" '
        f'xmlns="http://www.w3.org/2000/svg">\n'
        f'<title>Tape background</title>\n'
        f'<desc>Black label tape with machine marks and edge shading</desc>\n'
        f'<polygon points="{points}" fill="#0d0d0d"/>\n'
        f'{lines_svg}\n'
        f'</svg>'
    )
    meta = {
        "seed": seed,
        "marks_seed": marks_seed if marks_seed is not None else seed,
        "corner_mode": corner_mode,
        "angle_left": round(angle_l, 2),
        "angle_right": round(angle_r, 2),
        "n_lines": len(bevel_lines) + len(mark_lines),
        "n_clusters": len(cluster_meta),
        "clusters": cluster_meta,
    }
    return svg, meta


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corner-mode", required=True, choices=CORNER_MODES)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--marks-seed", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None, help="write to this file instead of stdout")
    args = parser.parse_args(argv)

    svg, meta = generate(args.seed, args.corner_mode, args.marks_seed)

    if args.out:
        args.out.write_text(svg)
        print(f"wrote {args.out} ({meta['angle_left']}deg / {meta['angle_right']}deg, {meta['n_clusters']} clusters)", file=sys.stderr)
    else:
        print(svg)


if __name__ == "__main__":
    main()
