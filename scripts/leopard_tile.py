"""Seamless black-on-black leopard tiles as SVG data URIs.

A rosette is 3-5 thick arc fragments around an ellipse, with a smaller
off-centre blob inside. Rosettes are placed by rejection sampling with a
minimum gap and drawn with wrapped copies at +/- one tile so the edges join.
Everything is tonal: the rosette tones sit within a few L* of the ground.

Optional layers:
  sheen     a second copy of each fragment offset up-left in a lighter tone,
            the way fur catches light from top-left (matches the site's emboss)
  inner     a narrower, darker arc inside each fragment: four tones instead of two
  mottle    large soft ellipses between rosettes in a tone barely off the ground
  fur       an feTurbulence displacement on the rosette group so every edge is
            ragged like pile, plus a fine grain over the whole tile
"""
import base64, math, random


def rosette_tile(seed=11, size=720, count=26, scale=1.0, ground="#0e0e10",
                 ring="#151517", core="#121214", sheen=None, inner=None, mottle=None,
                 fur=False, fur_scale=7.0, grain=0.05, ring_width=(7, 11), min_gap=1.15):
    rnd = random.Random(seed)
    pts, tries = [], 0
    while len(pts) < count and tries < 6000:
        tries += 1
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        r = rnd.uniform(26, 44) * scale
        if all(math.hypot(min(abs(x - px), size - abs(x - px)), min(abs(y - py), size - abs(y - py))) >= (r + pr) * min_gap
               for (px, py, pr) in pts):
            pts.append((x, y, r))

    def arc_points(cx, cy, rx, ry, a0, a1, rot, steps=8):
        out = []
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            x, y = rx * math.cos(a), ry * math.sin(a)
            out.append(f"{cx + x * math.cos(rot) - y * math.sin(rot):.1f},{cy + x * math.sin(rot) + y * math.cos(rot):.1f}")
        return " ".join(out)

    def stroke(pts_str, width, colour, opacity=1.0):
        return f'<polyline points="{pts_str}" fill="none" stroke="{colour}" stroke-width="{width:.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}"/>'

    mottles, rosettes = [], []
    if mottle:
        for _ in range(int(count * 0.9)):
            mx, my = rnd.uniform(0, size), rnd.uniform(0, size)
            mrx, mry = rnd.uniform(40, 90) * scale, rnd.uniform(30, 70) * scale
            for ox in (-size, 0, size):
                for oy in (-size, 0, size):
                    mottles.append(f'<ellipse cx="{mx + ox:.1f}" cy="{my + oy:.1f}" rx="{mrx:.1f}" ry="{mry:.1f}" transform="rotate({rnd.uniform(0, 180):.0f} {mx + ox:.1f} {my + oy:.1f})" fill="{mottle}"/>')

    for (x, y, r) in pts:
        rx, ry = r, r * rnd.uniform(0.7, 0.95)
        rot = rnd.uniform(0, math.pi)
        n = rnd.choice([3, 4, 4, 5])
        a = rnd.uniform(0, 360)
        frags = []
        for _ in range(n):
            span = rnd.uniform(38, 75)
            frags.append((a, a + span))
            a += span + rnd.uniform(14, 40)
        w = rnd.uniform(*ring_width) * scale
        cx_off, cy_off = rnd.uniform(-0.18, 0.18) * r, rnd.uniform(-0.18, 0.18) * r
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                cx, cy = x + ox, y + oy
                if cx < -r * 2 or cx > size + r * 2 or cy < -r * 2 or cy > size + r * 2:
                    continue
                for (a0, a1) in frags:
                    if sheen:
                        rosettes.append(stroke(arc_points(cx - 1.3, cy - 1.3, rx, ry, a0, a1, rot), w, sheen, 0.9))
                    rosettes.append(stroke(arc_points(cx, cy, rx, ry, a0, a1, rot), w, ring))
                    if inner:
                        rosettes.append(stroke(arc_points(cx + 0.6, cy + 0.6, rx, ry, a0 + 4, a1 - 4, rot), w * 0.42, inner))
                rosettes.append(f'<ellipse cx="{cx + cx_off:.1f}" cy="{cy + cy_off:.1f}" rx="{rx * 0.42:.1f}" ry="{ry * 0.40:.1f}" transform="rotate({math.degrees(rot):.0f} {cx + cx_off:.1f} {cy + cy_off:.1f})" fill="{core}"/>')

    defs, group_attr, grain_rect = "", "", ""
    if fur:
        defs = (f'<defs>'
                f'<filter id="fur" x="-5%" y="-5%" width="110%" height="110%">'
                f'<feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="3" seed="{seed}" result="n"/>'
                f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{fur_scale}" xChannelSelector="R" yChannelSelector="G"/>'
                f'</filter>'
                f'<filter id="grain" x="0" y="0" width="100%" height="100%">'
                f'<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="{seed + 1}" stitchTiles="stitch" result="g"/>'
                f'<feColorMatrix in="g" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 {grain:.3f} 0"/>'
                f'</filter></defs>')
        group_attr = ' filter="url(#fur)"'
        grain_rect = f'<rect width="{size}" height="{size}" filter="url(#grain)"/>'

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
           f'{defs}<rect width="{size}" height="{size}" fill="{ground}"/>'
           f'<g{group_attr}>{"".join(mottles)}{"".join(rosettes)}</g>{grain_rect}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode(), len(svg)


if __name__ == "__main__":
    import sys
    uri, n = rosette_tile()
    sys.stdout.write(uri if "--uri" in sys.argv else f"{n} bytes of SVG\n")
