#!/bin/sh
# Is `main` green, i.e. is the site actually deploying? Prints the last few
# runs and one verdict line. Takes no arguments at all.
#
# WHY THIS EXISTS (2026-09-22). MANUAL §10: a red `main` is a DEPLOY OUTAGE,
# not a red build. The suite gates the deploy, so one merge that turns it red
# stops every LATER merge from going live too, and the only signal is an
# Actions email. That happened for three days, 2026-09-12 to 2026-09-15, with
# about twenty merges shipping nothing (DECISIONS §12).
#
# THE INSTRUCTION TO CHECK EXISTED AND NOBODY RAN IT, WHICH IS THE POINT OF
# THIS FILE. The manual's original form was a one-line `gh-read.sh ... --jq
# '.workflow_runs[] | {head_branch, conclusion}'`, and the brackets and pipe in
# that expression make Claude Code read the argument as a path computed at run
# time and ask Helen -- the exact friction CLAUDE.md's wrapper rule exists to
# remove. A check that costs an interruption is a check that does not happen.
# (It also spent seven days on an unmerged branch, so no session could have run
# it anyway; both halves of that are in DECISIONS §12.)
#
# USAGE:
#   sh scripts/main-ci-status.sh
#
# Reads one GitHub endpoint and writes nothing, anywhere. It takes no
# arguments, so there is no path, repo or option for a caller to influence --
# the endpoint, the branch and the count are fixed in this file. Exits 0 when
# the latest run on `main` succeeded, 1 when it did not, and 2 on a refusal,
# so a caller can branch on it without parsing the text.
#
# The repo is public, so no credential is sent: `gh-read.sh` is not used here
# precisely because this must work as a plain unauthenticated read.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command it would run and exits, for
# tests/test_agent_wrappers.py.
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

# The parsing lives in a committed python file rather than a jq expression on
# this line, for the reason in the header: a bracketed jq argument is what made
# the original check prompt.
"$@" | python3 scripts/main_ci_status.py
