"""Write the two leopard tiles the cocktails site ships, from Helen's chosen settings.

REPRODUCES NO NUMBER -- it GENERATES `assets/img/cocktails/leopard-fur.svg` and
`leopard-nap.svg`, which `_sass/cocktails/_leopard.scss` lays on the page ground.
Run `--check` by hand after touching `scripts/leopard_splodge.py`. The suite
does NOT run it: a byte comparison of ten thousand rounded sines is one libm
away from a red `main`, and a red `main` stops the deploy. What the suite does
check (`tests/test_site_config.py`) is that the stylesheet's tile sizes are the
files' own.

The settings are Helen's, 2026-10-06, each chosen by looking (LEOPARD.md
section 4): the FUR crinkle, the repeat OFFSET over three columns, and the NAP
ground texture. Neither tile has a ground or a tone of its own -- they are
white at very low alpha -- so the darkness of the page is `$color-paper` in
`_sass/cocktails/_palette.scss` and nothing here.

    python3 scripts/build_leopard.py --write    regenerate both files
    python3 scripts/build_leopard.py --check    exit 1 if either differs
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from leopard_splodge import splodge_tile, ground_tile

OUT = os.path.join(ROOT, "assets", "img", "cocktails")

# Three columns: the repeat to the right sits a third of a tile lower, so a
# splodge comes back at the same height 2880px along rather than 960px.
FUR_COLUMNS = 3


def tiles():
    _uri, _n, fur, width = splodge_tile(crinkle="fur", columns=FUR_COLUMNS)
    _uri, _n, nap = ground_tile("nap")
    return {"leopard-fur.svg": fur + "\n", "leopard-nap.svg": nap + "\n"}, width


def stale():
    out = []
    for name, svg in tiles()[0].items():
        path = os.path.join(OUT, name)
        if not os.path.exists(path):
            out.append(name + " is missing")
            continue
        with open(path, encoding="utf-8") as fh:
            if fh.read() != svg:
                out.append(name + " differs from what the generator draws")
    return out


if __name__ == "__main__":
    if "--write" in sys.argv:
        os.makedirs(OUT, exist_ok=True)
        for name, svg in tiles()[0].items():
            with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
                fh.write(svg)
            sys.stdout.write(f"{name}: {len(svg) / 1024:.0f} KB\n")
    elif "--check" in sys.argv:
        problems = stale()
        for p in problems:
            sys.stdout.write(p + "\n")
        sys.exit(1 if problems else 0)
    else:
        sys.stdout.write(__doc__)
