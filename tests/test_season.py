"""The committed copy of Is It Rhubarb Yet?'s season file.

`_data/season/` is refreshed by hand with scripts/refresh_season.py and
shipped as a pull request; the build never fetches it, so a Rhubarb outage
cannot stop a deploy. These tests hold the copy to its schema and the
refresh script to its refusals.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import refresh_season  # noqa: E402
from season_schema import validate  # noqa: E402

pytestmark = pytest.mark.food

SEASON_DIR = ROOT / "_data" / "season"
SEASON = json.loads((SEASON_DIR / "v1.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((SEASON_DIR / "v1.schema.json").read_text(encoding="utf-8"))


# --- the committed copy --------------------------------------------------------

def test_the_season_copy_matches_its_schema():
    problems = validate(SCHEMA, SEASON)
    assert not problems, (
        "_data/season/v1.json does not match _data/season/v1.schema.json:\n  "
        + "\n  ".join(problems[:40])
        + "\n\nBoth come from Is It Rhubarb Yet? together. Refresh them with "
          "`python3 scripts/refresh_season.py`, which refuses a file that does "
          "not match, rather than editing either by hand."
    )


def test_the_season_copy_is_the_version_this_site_reads():
    assert SEASON["schema_version"] == refresh_season.VERSION == SCHEMA["properties"]["schema_version"]["const"], (
        f"schema_version is {SEASON['schema_version']!r}; this site reads version "
        f"{refresh_season.VERSION}. A new version is a new file at Rhubarb and a "
        "code change here, not a refresh."
    )
    assert len(SEASON["foods"]) > 100, "the season copy holds almost no foods: was it truncated?"


def test_the_schema_check_catches_a_wrong_file_and_refuses_an_unknown_keyword():
    good = {"schema_version": 1, "foods": [{"id": "a", "name": "A", "aliases": [], "glasshouse": False,
                                            "never": False, "months": ["out"] * 12}]}
    assert validate(SCHEMA, good) == []
    food = good["foods"][0]
    for bad, expect in [
        ({**good, "schema_version": 2}, "must be 1"),
        ({**good, "extra": 1}, 'unexpected "extra"'),
        ({**good, "foods": [{**food, "months": ["ripe"] * 12}]}, "is not one of"),
        ({**good, "foods": [{**food, "months": ["out"] * 11}]}, "fewer than 12"),
        ({**good, "foods": [{**food, "glasshouse": 1}]}, "must be boolean"),
        ({**good, "foods": [{**food, "id": "Not An Id"}]}, "does not match"),
    ]:
        problems = validate(SCHEMA, bad)
        assert any(expect in p for p in problems), (expect, problems)
    refused = validate({"type": "string", "format": "date"}, "x")
    assert any('"format" is not supported' in p for p in refused), refused


# --- the refresh script --------------------------------------------------------

def _source(tmp_path: Path, season: dict) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    (src / "v1.json").write_text(json.dumps(season))
    (src / "v1.schema.json").write_text(json.dumps(SCHEMA))
    return src


def test_refresh_writes_a_valid_file_and_says_what_changed(tmp_path, monkeypatch, capsys):
    out = tmp_path / "out"
    monkeypatch.setattr(refresh_season, "OUT", out)
    first = {"schema_version": 1, "foods": SEASON["foods"][:3]}
    assert refresh_season.main(["--from-dir", str(_source(tmp_path, first))]) == 0
    assert json.loads((out / "v1.json").read_text()) == first
    assert json.loads((out / "v1.schema.json").read_text()) == SCHEMA
    assert "new copy: 3 foods" in capsys.readouterr().out

    second = {"schema_version": 1, "foods": SEASON["foods"][1:4]}
    (tmp_path / "src" / "v1.json").write_text(json.dumps(second))
    assert refresh_season.main(["--from-dir", str(tmp_path / "src")]) == 0
    said = capsys.readouterr().out
    assert f"removed: {first['foods'][0]['id']}" in said
    assert f"added: {second['foods'][-1]['id']}" in said


@pytest.mark.parametrize("season, expect", [
    ({"schema_version": 1, "foods": [{"id": "x"}]}, 'missing "name"'),
    ({"schema_version": 2, "foods": []}, "this copy is version 1"),
])
def test_refresh_refuses_a_bad_file_and_leaves_the_copy_alone(tmp_path, monkeypatch, capsys, season, expect):
    out = tmp_path / "out"
    out.mkdir()
    (out / "v1.json").write_text("the old copy")
    monkeypatch.setattr(refresh_season, "OUT", out)
    assert refresh_season.main(["--from-dir", str(_source(tmp_path, season))]) == 1
    assert expect in capsys.readouterr().err
    assert (out / "v1.json").read_text() == "the old copy"
    assert not (out / "v1.schema.json").exists()
