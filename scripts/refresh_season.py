#!/usr/bin/env python3
"""Refresh the committed copy of Is It Rhubarb Yet?'s season file.

    python3 scripts/refresh_season.py                 # from the live site
    python3 scripts/refresh_season.py --from-dir DIR  # from a Rhubarb build's
                                                      # _site/season folder

Run by hand, then ship the change as a pull request. The Jekyll build never
fetches it: a Rhubarb outage must not be able to stop a deploy here, so the
site reads only `_data/season/`. The file and its schema are validated
before anything is written, and a file that fails leaves the copy as it was.
It prints which foods were added, removed or changed, for the PR description.
A new schema version is a new path at Rhubarb and a code change here, so a
file that is not version 1 is refused.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from season_schema import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_data" / "season"
BASE = "https://deckofpandas.github.io/is-it-rhubarb-yet/season/"
FILES = ("v1.json", "v1.schema.json")
VERSION = 1


def fetch(name: str, from_dir: Path | None) -> dict:
    if from_dir is not None:
        return json.loads((from_dir / name).read_text(encoding="utf-8"))
    request = urllib.request.Request(BASE + name, headers={"User-Agent": "helen-triages season refresh"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def changes(old: dict | None, new: dict) -> list[str]:
    if old is None:
        return [f"new copy: {len(new['foods'])} foods"]
    before = {f["id"]: f for f in old["foods"]}
    after = {f["id"]: f for f in new["foods"]}
    lines = [f"added: {i}" for i in sorted(after.keys() - before.keys())]
    lines += [f"removed: {i}" for i in sorted(before.keys() - after.keys())]
    lines += [f"changed: {i}" for i in sorted(after.keys() & before.keys()) if after[i] != before[i]]
    return lines or ["no change"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--from-dir", type=Path, help="read the two files from this folder instead of the live site")
    args = parser.parse_args(argv)

    season, schema = (fetch(name, args.from_dir) for name in FILES)
    problems = validate(schema, season)
    if season.get("schema_version") != VERSION:
        problems.insert(0, f"schema_version is {season.get('schema_version')!r}, this copy is version {VERSION}")
    if problems:
        print("refresh_season.py: refused, the copy is unchanged:", file=sys.stderr)
        for p in problems[:50]:
            print("  " + p, file=sys.stderr)
        return 1

    current = OUT / FILES[0]
    old = json.loads(current.read_text(encoding="utf-8")) if current.exists() else None
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in zip(FILES, (season, schema)):
        (OUT / name).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for line in changes(old, season):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
