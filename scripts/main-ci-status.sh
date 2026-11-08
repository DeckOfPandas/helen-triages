#!/bin/sh
# Is `main` green? Prints the last few CI runs on `main` and one verdict line.
# Where the suite gates a deploy, a red `main` is an outage: every later merge
# ships nothing until it is green again.
#
# USAGE:  sh scripts/main-ci-status.sh [<repo>]
#
# <repo> is a bare name from GH_REPOS, the first by default. Reads one GitHub
# endpoint through gh-agent.sh with GET, and writes nothing. Exits 0 when the
# latest run on `main` succeeded, 1 when it did not (still running, cancelled
# or red: the verdict says which), and 2 on a refusal or an unreadable answer.
# scripts/main_ci_status.py does the reading, so no jq expression is needed
# on the command line.
set -eu

WRAPPER=main-ci-status.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

[ "$#" -le 1 ] || refuse "usage: sh scripts/main-ci-status.sh [<repo>]"
repo="${1:-$DEFAULT_REPO}"
check_repo "$repo"

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' sh "$here/gh-agent.sh" api --method GET \
    "repos/$GH_OWNER/$repo/actions/runs?branch=main&per_page=10" \
    python3 "$here/main_ci_status.py" "$GH_OWNER/$repo"
  exit 0
fi

sh "$here/gh-agent.sh" api --method GET "repos/$GH_OWNER/$repo/actions/runs?branch=main&per_page=10" \
  | python3 "$here/main_ci_status.py" "$GH_OWNER/$repo"
