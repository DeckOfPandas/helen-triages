"""Summarise GitHub's workflow-runs JSON for `main`, read from stdin.

USAGE:  ... | python3 scripts/main_ci_status.py <owner>/<repo>

Called by scripts/main-ci-status.sh. Prints the recent runs and one verdict
line. Exit 0 if the latest run on `main` succeeded, 1 if it did not, 2 if the
answer could not be read or held no runs.

Only a push to this repository's `main` counts. `branch=main` also matches a
fork's pull request from a branch called `main`, and Dependabot's update runs:
those are listed, marked, and kept out of the verdict. A cancelled run is not a red one: with a
concurrency group, a run waiting behind another is dropped when a newer one
arrives, and the next push runs again.
"""
from __future__ import annotations

import json
import sys


def is_main_push(run: dict, repo: str) -> bool:
    """A field GitHub did not send counts as matching, so an abbreviated
    answer is judged rather than silently emptied."""
    event = run.get("event")
    source = (run.get("head_repository") or {}).get("full_name")
    return event in (None, "push") and source in (None, repo)


def main() -> int:
    if len(sys.argv) != 2 or "/" not in sys.argv[1]:
        print("usage: ... | python3 scripts/main_ci_status.py <owner>/<repo>", file=sys.stderr)
        return 2
    repo = sys.argv[1]
    try:
        runs = json.load(sys.stdin).get("workflow_runs") or []
    except (json.JSONDecodeError, ValueError, AttributeError) as exc:
        print(f"could not read GitHub's answer: {exc}", file=sys.stderr)
        return 2

    pushes = [r for r in runs if is_main_push(r, repo)]
    if not pushes:
        print(f"No workflow runs on main came back for {repo}. This is NOT green: "
              "the question went unanswered.", file=sys.stderr)
        return 2

    for run in runs:
        mark = "" if is_main_push(run, repo) else "  [not a push to main]"
        title = (run.get("display_title") or "")[:58]
        print(f"{str(run.get('created_at'))[:16]}  {str(run.get('conclusion')):10}  {title}{mark}")

    latest = pushes[0].get("conclusion")
    print()
    if latest == "success":
        failed = sum(1 for r in pushes if r.get("conclusion") not in ("success", None))
        print(f"main is GREEN. ({failed} of the last {len(pushes)} runs were not successful.)")
        return 0
    if latest is None:
        print("The latest run on main has not finished. Look again before treating "
              "a merge as deployed.")
        return 1
    if latest == "cancelled":
        print("The latest run on main was CANCELLED: that merge has not run, so it is "
              "not deployed. Nothing is broken; the next push runs it, or it can be "
              "re-run from the Actions tab. Report it.")
        return 1
    print(f"main is {str(latest).upper()}. Report this before the work you came for: "
          "where the suite gates a deploy, nothing merged after it ships until "
          "main is green again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
