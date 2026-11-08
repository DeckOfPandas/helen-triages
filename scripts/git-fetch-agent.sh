#!/bin/sh
# Bring a nested clone up to date as the agent account, without standing on
# `main` afterwards. A clone is stale the moment anyone merges, so fetch
# immediately before any run whose result you will act on.
#
# USAGE:  sh scripts/git-fetch-agent.sh <dir> <repo> [ref] [--keep-head]
#
# Fetches one branch (default main) into refs/remotes/origin/<ref>, DETACHES
# onto it and prints the commit: a detached HEAD cannot be committed onto by
# accident. With --keep-head it leaves HEAD alone and prints how far behind it
# is; a non-zero count means a red test may not be yours.
#
# REFUSES a `dir` outside this checkout, a repo outside GH_REPOS, a ref that
# starts `-` or contains `..`, `:` or a space, and any other fourth argument.
set -eu

WRAPPER=git-fetch-agent.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

[ "$#" -ge 2 ] && [ "$#" -le 4 ] \
  || refuse "usage: sh scripts/git-fetch-agent.sh <dir> <repo> [ref] [--keep-head]"
dir="$1"
repo="$2"
ref="${3:-main}"
keep="${4:-}"

check_dir "$dir"
check_repo "$repo"
case "$ref" in
  '' | -* | *..* | *:* | *" "*) refuse "'$ref' is not a branch name" ;;
esac
case "$keep" in
  "" | --keep-head) ;;
  *) refuse "'$keep' is not --keep-head" ;;
esac

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' git -C "$dir" fetch "https://github.com/$GH_OWNER/${repo}.git" \
    "+refs/heads/${ref}:refs/remotes/origin/${ref}"
  exit 0
fi

git -C "$dir" \
  -c "credential.helper=!sh '${here}/git-credential-agent-token.sh'" \
  fetch --quiet "https://github.com/$GH_OWNER/${repo}.git" \
  "+refs/heads/${ref}:refs/remotes/origin/${ref}"

if [ -n "$keep" ]; then
  printf 'behind origin/%s by: ' "$ref"
  git -C "$dir" rev-list --count "HEAD..origin/${ref}"
  exit 0
fi

git -C "$dir" checkout --quiet --detach "origin/${ref}"
git -C "$dir" log -1 --format='%h %ad %s' --date=short
