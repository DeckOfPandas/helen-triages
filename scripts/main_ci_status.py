"""Summarise GitHub's workflow-runs JSON for `main`, read from stdin.

Called only by `scripts/main-ci-status.sh`, which does the fetching. The split
exists so the parsing is a committed file rather than a `--jq` expression on a
command line: a bracketed jq argument makes Claude Code read it as a path
computed at run time and prompt Helen, which is what stopped the original form
of this check from ever being run (MANUAL §10, DECISIONS §12).

Prints the recent runs and one verdict line. Exit 0 if the latest run on `main`
succeeded, 1 if it did not, 2 if the input could not be read -- so a caller can
branch on the status without parsing the text.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        runs = json.load(sys.stdin).get("workflow_runs") or []
    except (json.JSONDecodeError, ValueError, AttributeError) as exc:
        print(f"could not read GitHub's response: {exc}", file=sys.stderr)
        return 2

    if not runs:
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
        print(f"{str(run.get('created_at'))[:16]}  {conclusion:10}  {title}")

    latest = runs[0].get("conclusion")
    unsuccessful = [r for r in runs if r.get("conclusion") not in ("success", None)]
    print()
    if latest == "success":
        print(f"main is GREEN -- merges are deploying. "
              f"({len(unsuccessful)} of the last {len(runs)} runs were not successful.)")
        return 0
    if latest is None:
        print("The latest run on main has not finished yet. Look again before "
              "treating a merge as deployed.")
        return 1
    print(f"main is {str(latest).upper()} -- THIS IS A DEPLOY OUTAGE.")
    print("The suite gates the deploy, so every later merge builds nothing and")
    print("ships nothing until main is green again. Report this before the work")
    print("you came for (MANUAL 10, DECISIONS 12).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
