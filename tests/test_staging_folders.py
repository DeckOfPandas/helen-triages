"""Every staging folder PIPELINE.md §3 names exists in each drafts clone.

Helen, #1080: "These folders should always be present even if they don't
contain any drafts." Git keeps no empty folder, so each holds a `.gitkeep`
(added 2026-09-15 on both private repos); a folder that exists only because a
draft happens to sit in it disappears the day that draft is promoted or binned.

So this checks the placeholder, not just the folder: a folder on disk with no
tracked file in it is exactly what a fresh clone would not have.

The drafts repos are private and absent in CI, so each case SKIPS with a reason
when its clone is missing -- a skip reads as "did not run", never as "checked
and clean" (tests/test_suite_hygiene.py, #378). On Helen's machine, and in any
worktree that has cloned the drafts, it runs.
"""
from __future__ import annotations

import pathlib

import pytest

pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parents[1]

# PIPELINE.md §3. Drinks skip 1-rewrite/ ("they're not as annoying as food
# recipes") and keep the same numbers for the rest.
# `5-final-proofread/` IS DRINKS-ONLY FOR NOW, 2026-09-18. Helen asked for it
# on the drinks side, where a seventeen-drink batch had just produced ten
# bounce-backs in one sitting; food has not hit that yet and an empty folder on
# a site that does not use it is clutter she would see every day. One name
# means one stage on both sites where a folder exists on both -- adding it to
# food later is this dict plus a `.gitkeep`.
FOLDERS = {
    "_food_drafts": ["1-rewrite", "2-make", "3-keep", "4-promote"],
    "_cocktail_drafts": ["2-make", "3-keep", "4-promote", "5-final-proofread"],
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
