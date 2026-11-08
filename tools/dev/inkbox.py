#!/usr/bin/env python3
"""Print the INK bounding boxes of a PNG, band by band.

    python3 tools/dev/inkbox.py tmp/<file>.png [<min-gap>]

crop.js prints an element's BOX, which answers "is this element on the
card's edge". It cannot answer "is this icon centred on that arrow", because
that is a question about ink: a glyph never fills its line box and a drawing
need not fill its viewBox. This decodes the PNG by hand (standard library
only), treats anything far from the image's most common colour as ink, splits
the image into column bands separated by blank columns, and prints each band's
vertical extent and centre in device pixels.

Measure in one image: crop the element holding every mark being compared and
read their bands from that one crop. An element screenshot pads its box by
about a pixel, so subtracting two separate crops' page positions is wrong by
that padding.

<min-gap> (default 10) is how many blank columns may sit inside one band
before it splits: 4-6 separates a bracket from the word inside it, 30 treats a
word as one object. crop.js shoots at 2x, so halve a difference for CSS px.

The input must be a .png under tmp/. Reads that file and writes nothing.
"""
import re
import struct
import sys
import zlib

USAGE = "usage: python3 tools/dev/inkbox.py tmp/<file>.png [<min-gap>]"


def refuse(message):
    print(f"inkbox.py: {message}\n{USAGE}", file=sys.stderr)
    sys.exit(2)


def parse(argv):
    if not 1 <= len(argv) <= 2:
        refuse("give one .png under tmp/, and optionally a minimum gap")
    path = argv[0]
    if not re.fullmatch(r"tmp/[A-Za-z0-9._/-]+\.png", path) or ".." in path:
        refuse(f"'{path}' must be a .png under tmp/")
    gap = argv[1] if len(argv) == 2 else "10"
    if not gap.isdigit() or not 0 <= int(gap) <= 1000:
        refuse(f"the minimum gap must be a whole number from 0 to 1000, not '{gap}'")
    return path, int(gap)


def read_png(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        refuse(f"'{path}' is not a PNG")
    pos = 8
    idat = b""
    width = height = depth = ctype = None
    palette = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, ctype = struct.unpack(">IIBB", body[:10])
        elif kind == b"PLTE":
            palette = body
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if depth != 8:
        refuse(f"only 8-bit PNGs are read, and this one is {depth}-bit")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = width * channels
    out = bytearray(height * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        filt = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if filt == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filt == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filt == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return width, height, channels, ctype, palette, out


def luminance(px):
    return 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]


def bands(path, min_gap):
    w, h, channels, ctype, palette, buf = read_png(path)
    stride = w * channels

    def pixel(x, y):
        i = y * stride + x * channels
        if ctype == 3:
            j = buf[i] * 3
            return palette[j], palette[j + 1], palette[j + 2]
        if channels in (1, 2):
            return buf[i], buf[i], buf[i]
        return buf[i], buf[i + 1], buf[i + 2]

    # The ground is the most common colour; ink is anything far from it.
    counts = {}
    for y in range(0, h, max(1, h // 40)):
        for x in range(0, w, max(1, w // 40)):
            c = pixel(x, y)
            counts[c] = counts.get(c, 0) + 1
    ground = max(counts, key=counts.get)
    gl = luminance(ground)

    def is_ink(x, y):
        return abs(luminance(pixel(x, y)) - gl) > 40

    cols = [any(is_ink(x, y) for y in range(h)) for x in range(w)]
    found, start = [], None
    for x, ink in enumerate(cols):
        if ink and start is None:
            start = x
        elif not ink and start is not None:
            found.append((start, x - 1))
            start = None
    if start is not None:
        found.append((start, w - 1))
    merged = []
    for b in found:
        if merged and b[0] - merged[-1][1] <= min_gap:
            merged[-1] = (merged[-1][0], b[1])
        else:
            merged.append(b)

    lines = [f"{path}: {w}x{h} ground={ground} bands={len(merged)}"]
    for x0, x1 in merged:
        rows = [y for y in range(h) if any(is_ink(x, y) for x in range(x0, x1 + 1))]
        top, bot = rows[0], rows[-1]
        lines.append(f"  x {x0:4d}-{x1:4d}  y {top:4d}-{bot:4d}  "
                     f"centre {(top + bot) / 2:7.1f}  height {bot - top + 1:4d}")
    return lines


if __name__ == "__main__":
    print("\n".join(bands(*parse(sys.argv[1:]))))
