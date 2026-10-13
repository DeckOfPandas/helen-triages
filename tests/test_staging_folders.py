"""Every staging folder PIPELINE.md §3 names exists in each drafts clone.

The folders are always present, drafts or no drafts (#1080). Git keeps no empty
folder, so each holds a `.gitkeep`, and this checks the placeholder, not just
the folder: a folder on disk with no tracked file in it is what a fresh clone
would not have.

The drafts repos are private and absent in CI, so each case skips with a
reason when its clone is missing (tests/test_suite_hygiene.py, #378).
"""
from __future__ import annotations

import pathlib

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parents[1]

# PIPELINE.md §3. Both repos carry the same first four, so Helen keeps track
# of the work the same way on both sites. `5-final-proofread/` is cocktails
# only; adding it to food is this dict plus a `.gitkeep`.
FOLDERS = {
    "_food_drafts": ["1-rewrite", "2-make", "3-keep", "4-promote"],
    "_cocktail_drafts": ["1-rewrite", "2-make", "3-keep", "4-promote",
                         "5-final-proofread"],
}


@pytest.mark.parametrize("clone, folder", [
    (clone, folder) for clone, folders in FOLDERS.items() for folder in folders
])
def test_every_staging_folder_exists_and_is_held_open(clone, folder):
    drafts = ROOT / clone
    if not drafts.is_dir():
        pytest.skip(f"{clone}/ is not cloned here (it is private, and absent in CI)")
    placeholder = drafts / folder / ".gitkeep"
    assert placeholder.is_file(), (
        f"{clone}/{folder}/.gitkeep is missing. PIPELINE.md §3's folders must "
        "always exist (#1080), and git keeps no empty folder -- restore the "
        "placeholder on a branch of the drafts repo. If the clone is simply "
        "old, fetch it: sh scripts/git-fetch-agent.sh <dir> <repo>, then merge."
    )


def test_the_folder_list_matches_pipeline_md():
    """The set above is PIPELINE.md §3's, not a second opinion about it."""
    pipeline = (ROOT / "model_instructions" / "PIPELINE.md").read_text(encoding="utf-8")
    for folder in {f for folders in FOLDERS.values() for f in folders}:
        assert f"`{folder}/`" in pipeline, (
            f"{folder}/ is checked here but PIPELINE.md §3 does not name it"
        )
