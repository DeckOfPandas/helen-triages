#!/bin/sh
# Clone one of the three repos as DeckOfPandas-agentic-claude over HTTPS,
# without naming the credential and without the credential ever being in the
# URL git stores. SSH fails in the devcontainer for want of a host key.
# MANUAL §9.1.
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
# Cloning is reading: nothing here writes to a remote.
#
# REFUSES anything but a repo from the three and an optional `dir` that is
# relative, has no `..` and does not start `-`. `git clone` takes
# `--template=<dir>`, whose hooks then run, and `-c <anything>`, so passing
# further arguments through would let the allow rule run any program.
#
# HOW IT AUTHENTICATES. A plain URL, and scripts/git-credential-agent-token.sh
# passed to git for this one invocation with `-c`. Git stores a clone's URL as
# its `origin` remote in `.git/config`, where `git remote -v` prints it, so a
# token in the URL is a token on disk. Later fetches and pushes go through
# git-fetch-agent.sh and git-push-agent.sh, which pass the helper the same
# way; nothing is written into the clone's config.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command instead of running it, one
# argument per line, for tests/test_agent_wrappers.py.
#
# Invoked via `sh` so it needs no execute bit.
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
