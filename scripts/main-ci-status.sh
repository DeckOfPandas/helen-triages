#!/bin/sh
# Is `main` green, i.e. is the site actually deploying? Prints the last few
# runs and one verdict line. A red `main` is a deploy outage, not a red build:
# the suite gates the deploy, so one merge that turns it red stops every later
# merge going live too, silently. MANUAL §10, DECISIONS §12.
#
# USAGE:
#   sh scripts/main-ci-status.sh
#
# Reads one GitHub endpoint and writes nothing, anywhere. It takes no
# arguments, so there is no path, repo or option for a caller to influence:
# the endpoint, the branch and the count are fixed in this file. Exits 0 when
# the latest run on `main` succeeded, 1 when it did not, and 2 on a refusal.
#
# "Did not" covers three things, and the verdict line says which: still
# running, cancelled (that merge is not deployed, nothing is broken), and red.
# `branch=main` in the URL also matches a fork's pull request from a branch
# called `main`; scripts/main_ci_status.py keeps those out of the verdict.
#
# The repo is public, so no credential is sent; gh-read.sh is not used, so
# this works as a plain unauthenticated read.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command instead of running it, one
# argument per line, for tests/test_agent_wrappers.py.
set -eu

refuse() {
  echo "main-ci-status.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -eq 0 ] || refuse "takes no arguments; got $#"

URL='https://api.github.com/repos/DeckOfPandas/helen-triages/actions/runs?branch=main&per_page=10'

set -- curl --silent --show-error --max-time 30 --proto '=https' "$URL"

# One token per line, matching the other wrappers, so a test can assert on the
# argument list rather than parsing a sentence.
if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' "$@"
  exit 0
fi

# The parsing lives in a committed python file, not a jq expression on this
# line: a bracketed jq argument given to a wrapper prompts.
"$@" | python3 scripts/main_ci_status.py
