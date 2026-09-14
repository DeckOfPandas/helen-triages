#!/usr/bin/env python3
"""Print the INK bounding boxes of a PNG, band by band.

    python3 scripts/browser/inkbox.py <file.png> [min-gap-between-bands]

crop.sh prints an element's BOX in CSS px, which answers "is this element on
the cards' edge". It cannot answer "is this glass centred on that arrow",
because that is a question about INK -- a glyph never fills its line box and a
drawing need not fill its viewBox. This does: it decodes the PNG by hand (there
is no PIL in the devcontainer), treats anything far from the image's most common
colour as ink, splits the image into column bands separated by blank columns,
and prints each band's vertical extent and centre in device pixels.

MEASURE IN ONE IMAGE. Crop the element that CONTAINS every mark being compared
and read their bands from that single crop. An element screenshot pads its box
by about a pixel, so cropping two elements separately and subtracting their
page positions is wrong by that padding -- which at small sizes is most of the
answer. The nav lettering's first correction (2026-09-14) was made that way and
was a pixel short; the one-image reading is what found it. See `.site-nav-word`
in _sass/shared/_layout.scss.

`min-gap` is how many blank columns may sit inside one band before it is split
into two: small (4-6) to separate a bracket from the word inside it, large (30)
to treat a whole word as one object. Crops are at deviceScaleFactor 2, so halve
a difference to get CSS px.
"""
import struct
import sys
import zlib


def read_png(path):
    with open(path, "rb") as fh:
        data = fh.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a png"
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
    assert depth == 8, f"only 8-bit supported, got {depth}"
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


def main():
    path = sys.argv[1]
    min_gap = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    w, h, channels, ctype, palette, buf = read_png(path)
    stride = w * channels

    def pixel(x, y):
        i = y * stride + x * channels
        if ctype == 3:
            j = buf[i] * 3
            return palette[j], palette[j + 1], palette[j + 2]
        if channels == 1:
            v = buf[i]
            return v, v, v
        if channels == 2:
            v = buf[i]
            return v, v, v
        return buf[i], buf[i + 1], buf[i + 2]

    # The ground is the most common colour; ink is anything far from it.
    counts = {}
    for y in range(0, h, max(1, h // 40) or 1):
        for x in range(0, w, max(1, w // 40) or 1):
            c = pixel(x, y)
            counts[c] = counts.get(c, 0) + 1
    ground = max(counts, key=counts.get)
    gl = luminance(ground)

    def is_ink(x, y):
        return abs(luminance(pixel(x, y)) - gl) > 40

    cols = [any(is_ink(x, y) for y in range(h)) for x in range(w)]
    bands = []
    start = None
    for x, ink in enumerate(cols):
        if ink and start is None:
            start = x
        elif not ink and start is not None:
            bands.append((start, x - 1))
            start = None
    if start is not None:
        bands.append((start, w - 1))

    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] <= min_gap:
            merged[-1] = (merged[-1][0], b[1])
        else:
            merged.append(b)

    print(f"{path}: {w}x{h} ground={ground} bands={len(merged)}")
    for x0, x1 in merged:
        top = bot = None
        for y in range(h):
            if any(is_ink(x, y) for x in range(x0, x1 + 1)):
                if top is None:
                    top = y
                bot = y
        print(f"  x {x0:4d}-{x1:4d}  y {top:4d}-{bot:4d}  "
              f"centre {(top + bot) / 2:7.1f}  height {bot - top + 1:4d}")


main()
