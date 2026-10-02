"""Summarise GitHub's workflow-runs JSON for `main`, read from stdin.

Called only by `scripts/main-ci-status.sh`, which does the fetching. The split
exists so the parsing is a committed file rather than a `--jq` expression on a
command line: a bracketed jq argument makes Claude Code read it as a path
computed at run time and prompt Helen, which is what stopped the original form
of this check from ever being run (MANUAL §10, DECISIONS §12).

Prints the recent runs and one verdict line. Exit 0 if the latest run on `main`
succeeded, 1 if it did not, 2 if the input could not be read -- so a caller can
branch on the status without parsing the text.

TWO THINGS IT LEARNED ON 2026-10-02, both from one evening's runs.

ONLY A PUSH TO THIS REPOSITORY'S `main` IS A DEPLOY. The endpoint filters on
`branch=main`, and that matches a pull request whose HEAD branch is called
`main` -- which is every pull request from a fork that never made a branch.
#1274 came from `Jah-yee:main`, and its run sat in this list as
`action_required` and then `failure`. Had it been the newest row, this script
would have announced a deploy outage over a stranger's fork. So a run counts
only if it is a `push` from this repository; the rest are listed, marked, and
kept out of the verdict.

A CANCELLED RUN IS NOT A RED ONE, and the old message said it was. Every run
shares one concurrency group, so a deploy waiting behind another is dropped
when a newer run arrives (DECISIONS §12). That merge is then NOT DEPLOYED --
which needs saying -- but nothing is broken and the next push deploys it, so
"every later merge ships nothing" was false and, worse, cried outage over
something a re-run fixes.
"""
from __future__ import annotations

import json
import sys

REPO = "DeckOfPandas/helen-triages"


def is_deploy(run) -> bool:
    """A push to this repository's `main`. A field GitHub did not send is
    treated as matching, so an abbreviated answer is judged rather than
    silently emptied."""
    event = run.get("event")
    source = (run.get("head_repository") or {}).get("full_name")
    return event in (None, "push") and source in (None, REPO)


def main() -> int:
    try:
        runs = json.load(sys.stdin).get("workflow_runs") or []
    except (json.JSONDecodeError, ValueError, AttributeError) as exc:
        print(f"could not read GitHub's response: {exc}", file=sys.stderr)
        return 2

    deploys = [r for r in runs if is_deploy(r)]
    if not deploys:
        # An empty list is not "all clear" -- it means the question was not
        # answered, which is the failure mode this repository names everywhere.
        print("No workflow runs returned for main. This is NOT a green result:",
              file=sys.stderr)
        print("the check did not run, rather than running and finding nothing.",
              file=sys.stderr)
        return 2

    for run in runs:
        conclusion = str(run.get("conclusion"))
        title = (run.get("display_title") or "")[:58]
        mark = "" if is_deploy(run) else "  [a pull request, not a deploy]"
        print(f"{str(run.get('created_at'))[:16]}  {conclusion:10}  {title}{mark}")

    latest = deploys[0].get("conclusion")
    unsuccessful = [r for r in deploys if r.get("conclusion") not in ("success", None)]
    print()
    if latest == "success":
        print(f"main is GREEN -- merges are deploying. "
              f"({len(unsuccessful)} of the last {len(deploys)} runs were not successful.)")
        return 0
    if latest is None:
        print("The latest run on main has not finished yet. Look again before "
              "treating a merge as deployed.")
        return 1
    if latest == "cancelled":
        print("The latest run on main was CANCELLED -- that merge is NOT DEPLOYED.")
        print("This is not a red suite: a newer run took its place in the queue")
        print("before it started (DECISIONS 12). The next push to main deploys")
        print("it, or Helen can re-run it in the Actions tab. Report it; nothing")
        print("needs fixing.")
        return 1
    print(f"main is {str(latest).upper()} -- THIS IS A DEPLOY OUTAGE.")
    print("The suite gates the deploy, so every later merge builds nothing and")
    print("ships nothing until main is green again. Report this before the work")
    print("you came for (MANUAL 10, DECISIONS 12).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
