#!/bin/sh
# Clone one of the three repos as DeckOfPandas-agentic over HTTPS, without
# naming the credential at the call site, and without the credential ever
# being in the URL git stores.
#
# WHY THIS EXISTS (2026-09-10). MANUAL §9.1 says a worktree gets the drinks by
# cloning the private drafts repo, and gives the SSH form. Inside the
# devcontainer SSH dies on `Host key verification failed` (CLAUDE.md, Git
# workflow step 1a), so the clone has to be HTTPS.
#
# AND WHY IT LOOKS LIKE THIS, since later the same day. The first version put
# the token in the URL's userinfo. Git stores a clone's URL as its `origin`
# remote in `.git/config`, token and all, and a routine `git remote -v` then
# printed it in full -- the leak that produced scripts/git-credential-agent-
# token.sh. So the URL here is PLAIN and the credential comes from that helper,
# passed to git for this one invocation with `-c`. The clone's `origin` is
# then a plain URL that nothing can leak, and later fetches and pushes go
# through scripts/git-fetch-agent.sh and scripts/git-push-agent.sh, which
# pass the helper the same way. Nothing is ever written into the clone's
# config.
#
# USAGE:
#   sh scripts/git-clone-agent.sh <repo> [dir]
#
#   sh scripts/git-clone-agent.sh helen-triages-cocktails-private _cocktail_drafts
#   sh scripts/git-clone-agent.sh helen-triages-food-private _food_drafts
#
# `dir` defaults to git's own choice (the repo name). Both drafts folders are
# gitignored in the public repo, so a clone there is invisible to it.
#
# CLONING IS READING. Nothing here writes to a remote. Writing to the clone
# follows the Git workflow section of CLAUDE.md: a branch, never `main`, and
# `PUBLISHING_A_DRINK.md`'s one-working-copy rule while a batch is open.
#
# EXACTLY TWO ARGUMENTS, SINCE 2026-09-11, WHEN IT BECAME ALLOW-LISTED. It used
# to pass everything after the repo straight to `git clone`, and `git clone`
# takes `--template=<dir>` (whose hooks then run) and `-c <anything>` -- so an
# allow rule on this script would have allowed running any program at all.
# Now it takes a repo from the three and an optional `dir` inside this
# checkout, and refuses anything else. AGENT_WRAPPER_DRY_RUN=1 prints the
# command instead of running it, for tests/test_agent_wrappers.py.
#
# Invoked via `sh` so it needs no execute bit -- CLAUDE.md forbids changing file
# permissions without asking.
set -eu

refuse() {
  echo "git-clone-agent.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -ge 1 ] && [ "$#" -le 2 ] || refuse "usage: sh scripts/git-clone-agent.sh <repo> [dir]"
repo="$1"
shift

case "$repo" in
  helen-triages | helen-triages-food-private | helen-triages-cocktails-private) ;;
  *) refuse "'$repo' is not one of the three repos" ;;
esac
if [ "$#" -eq 1 ]; then
  case "$1" in
    /* | *..* | -*) refuse "'$1' is outside this checkout" ;;
  esac
fi

here="$(cd "$(dirname "$0")" && pwd)"

set -- git -c "credential.helper=!sh '${here}/git-credential-agent-token.sh'" \
  clone --quiet "https://github.com/DeckOfPandas/${repo}.git" "$@"

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' "$@"
  exit 0
fi
exec "$@"
