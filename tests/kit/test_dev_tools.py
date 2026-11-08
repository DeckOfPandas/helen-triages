"""tools/dev/: the scripts parse, and refuse bad arguments before needing a browser.

Taking a real screenshot needs WITH_PLAYWRIGHT=1, so it is not tested here.
"""
from __future__ import annotations

import shutil
import subprocess

import pytest

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


@pytest.mark.parametrize("script", ["shoot.js", "slice-png.js", "crop.js", "styles.js", "gaps.js"])
def test_parses(kit_root, script):
    subprocess.run([NODE, "--check", str(kit_root / "tools" / "dev" / script)], check=True)


@pytest.mark.parametrize("script,args", [
    ("shoot.js", []),
    ("shoot.js", ["http://127.0.0.1:9000"]),
    ("shoot.js", ["http://127.0.0.1:9000", "a/b"]),
    ("shoot.js", ["http://127.0.0.1:9000", "x", "--scheme", "sepia"]),
    ("shoot.js", ["http://127.0.0.1:9000", "x", "--click"]),
    ("shoot.js", ["http://127.0.0.1:9000", "x", "--type"]),
    ("shoot.js", ["http://127.0.0.1:9000", "x", "--engine", "firefox"]),
    ("shoot.js", ["http://127.0.0.1:9000", "x", "/about/"]),
    ("crop.js", []),
    ("crop.js", ["http://127.0.0.1:9000", "x"]),
    ("crop.js", ["http://127.0.0.1:9000", "a/b", "h1"]),
    ("crop.js", ["http://127.0.0.1:9000", "x", "h1", "/about/"]),
    ("crop.js", ["http://127.0.0.1:9000", "x", "h1", "a/", "b/"]),
    ("crop.js", ["http://127.0.0.1:9000", "x", "h1", "--width", "wide"]),
    ("crop.js", ["http://127.0.0.1:9000", "x", "h1", "--width", "50"]),
    ("crop.js", ["http://127.0.0.1:9000", "x", "h1", "--engine", "firefox"]),
    ("crop.js", ["http://127.0.0.1:9000", "x", "h1", "--type-into", ".box"]),
    ("crop.js", ["http://127.0.0.1:9000", "x", "h1", "--out", "/etc/x.png"]),
    ("crop.js", ["http://127.0.0.1:9000", "x", "h1", "--click"]),
    ("gaps.js", []),
    ("gaps.js", ["http://127.0.0.1:9000"]),
    ("gaps.js", ["http://127.0.0.1:9000", "main", "/about/"]),
    ("gaps.js", ["http://127.0.0.1:9000", "main", "a/", "b/"]),
    ("gaps.js", ["http://127.0.0.1:9000", "main", "--width", "50"]),
    ("gaps.js", ["http://127.0.0.1:9000", "main", "--depth", "9"]),
    ("gaps.js", ["http://127.0.0.1:9000", "main", "--depth", "x"]),
    ("gaps.js", ["http://127.0.0.1:9000", "main", "--engine", "firefox"]),
    ("gaps.js", ["http://127.0.0.1:9000", "main", "--out", "x"]),
    ("styles.js", []),
    ("styles.js", ["http://127.0.0.1:9000"]),
    ("styles.js", ["http://127.0.0.1:9000", "h1", "/about/"]),
    ("styles.js", ["http://127.0.0.1:9000", "h1", "a/", "b/"]),
    ("styles.js", ["http://127.0.0.1:9000", "h1", "--width", "0"]),
    ("styles.js", ["http://127.0.0.1:9000", "h1", "--props", "font-size;x"]),
    ("styles.js", ["http://127.0.0.1:9000", "h1", "--props"]),
    ("styles.js", ["http://127.0.0.1:9000", "h1", "--engine", "firefox"]),
    ("slice-png.js", []),
    ("slice-png.js", ["shot.png"]),
    ("slice-png.js", ["tmp/../x.png"]),
    ("slice-png.js", ["tmp/x.jpg"]),
    ("slice-png.js", ["tmp/x.png", "10"]),
])
def test_refuses(kit_root, tmp_path, script, args):
    done = subprocess.run([NODE, str(kit_root / "tools" / "dev" / script), *args],
                          cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert done.returncode == 2, done.stderr
    assert "usage" in done.stderr or "must be" in done.stderr, done.stderr


@pytest.mark.parametrize("script,args", [
    ("crop.js", ["http://127.0.0.1:9", "x", "h1"]),
    ("crop.js", ["http://127.0.0.1:9", "x", ".a b", "about/", "--width", "390", "--engine", "webkit",
                 "--type-into", "input", "ch"]),
    ("styles.js", ["http://127.0.0.1:9", "h1", ".", "--props", "font-size,line-height", "--width", "390"]),
    ("crop.js", ["http://127.0.0.1:9", "x", ".panel", ".", "--click", ".menu-button"]),
    ("gaps.js", ["http://127.0.0.1:9", "main", "about/", "--width", "390", "--depth", "2"]),
])
def test_accepts(kit_root, tmp_path, script, args):
    """Past the argument checks: it fails later, on no browser or no server."""
    done = subprocess.run([NODE, str(kit_root / "tools" / "dev" / script), *args],
                          cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert done.returncode != 2 and "usage" not in done.stderr, done.stderr


# --- inkbox.py: a PNG's ink bands, standard library only ---------------------------

def _png(path, width: int, height: int, ink: set[tuple[int, int]]) -> None:
    """An 8-bit greyscale PNG: white ground, black where `ink` says."""
    import struct
    import zlib
    rows = b"".join(b"\x00" + bytes(0 if (x, y) in ink else 255 for x in range(width))
                    for y in range(height))
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def inkbox(kit_root, cwd, *args):
    return subprocess.run(["python3", str(kit_root / "tools" / "dev" / "inkbox.py"), *args],
                          cwd=cwd, capture_output=True, text=True, timeout=30)


def test_inkbox_finds_two_marks_and_their_centres(kit_root, tmp_path):
    (tmp_path / "tmp").mkdir()
    ink = {(x, y) for x in range(2, 5) for y in range(10, 20)} | {(x, y) for x in range(30, 33) for y in range(4, 8)}
    _png(tmp_path / "tmp" / "two.png", 40, 30, ink)
    done = inkbox(kit_root, tmp_path, "tmp/two.png", "5")
    assert done.returncode == 0, done.stderr
    lines = done.stdout.splitlines()
    assert "bands=2" in lines[0]
    assert "x    2-   4  y   10-  19  centre    14.5" in lines[1]
    assert "x   30-  32  y    4-   7  centre     5.5" in lines[2]
    assert "bands=1" in inkbox(kit_root, tmp_path, "tmp/two.png", "30").stdout


@pytest.mark.parametrize("args", [[], ["x.png"], ["tmp/../x.png"], ["/etc/x.png"], ["tmp/x.jpg"],
                                  ["tmp/x.png", "-1"], ["tmp/x.png", "a"], ["tmp/x.png", "1", "2"]])
def test_inkbox_refuses(kit_root, tmp_path, args):
    done = inkbox(kit_root, tmp_path, *args)
    assert done.returncode == 2 and "usage" in done.stderr, done.stderr
