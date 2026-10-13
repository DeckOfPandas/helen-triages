#!/bin/sh
# Bring a drafts clone up to date as DeckOfPandas-agentic-claude, without
# naming the credential, without the credential ever being in a URL, and
# without standing on `main`. Fetch immediately before any run whose result you
# will act on: a clone is stale the moment anyone merges. MANUAL §9.1.
#
# USAGE:
#   sh scripts/git-fetch-agent.sh <dir> <repo> [ref] [--keep-head]
#
#   sh scripts/git-fetch-agent.sh _cocktail_drafts helen-triages-cocktails-private
#   sh scripts/git-fetch-agent.sh _food_drafts helen-triages-food-private
#   sh scripts/git-fetch-agent.sh _cocktail_drafts helen-triages-cocktails-private some/branch
#   sh scripts/git-fetch-agent.sh _cocktail_drafts helen-triages-cocktails-private main --keep-head
#
# `ref` defaults to `main`. It fetches that one branch into
# `refs/remotes/origin/<ref>`, DETACHES onto it and prints the commit it landed
# on: a detached HEAD cannot be committed onto by accident.
#
# `--keep-head`, as the fourth argument, fetches and leaves HEAD where it is,
# then prints how many commits HEAD is behind the fetched ref. Use it mid-work
# on a branch; a non-zero count means a red test may not be yours.
#
# REFUSES, because the allow rule in .claude/settings.json runs whatever this
# accepts: a `dir` that is absolute, contains `..` or starts `-` (it would
# fetch into, and detach, another repo on the disk); a repo outside the three;
# a `ref` starting `-` or containing `..`, `:` or a space (an option, or a
# second refspec); a fourth argument other than `--keep-head`.
#
# HOW IT AUTHENTICATES. A plain URL, and scripts/git-credential-agent-token.sh
# passed to git for this one invocation with `-c`; see git-push-agent.sh for
# why never `git config`.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the fetch instead of running it, one argument
# per line, for tests/test_agent_wrappers.py.
#
# Invoked via `sh` so it needs no execute bit.
set -eu

refuse() {
  echo "git-fetch-agent.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -ge 2 ] && [ "$#" -le 4 ] \
  || refuse "usage: sh scripts/git-fetch-agent.sh <dir> <repo> [ref] [--keep-head]"
dir="$1"
repo="$2"
ref="${3:-main}"
keep="${4:-}"

case "$dir" in
  /* | *..* | -*) refuse "'$dir' is outside this checkout" ;;
esac
case "$repo" in
  helen-triages | helen-triages-food-private | helen-triages-cocktails-private) ;;
  *) refuse "'$repo' is not one of the three repos" ;;
esac
case "$ref" in
  -* | *..* | *:* | *" "*) refuse "'$ref' is not a branch name" ;;
esac
case "$keep" in
  "" | --keep-head) ;;
  *) refuse "'$keep' is not --keep-head" ;;
esac

here="$(cd "$(dirname "$0")" && pwd)"

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' git -C "$dir" fetch "https://github.com/DeckOfPandas/${repo}.git" \
    "+refs/heads/${ref}:refs/remotes/origin/${ref}"
  exit 0
fi

git -C "$dir" \
  -c "credential.helper=!sh '${here}/git-credential-agent-token.sh'" \
  fetch --quiet "https://github.com/DeckOfPandas/${repo}.git" \
  "+refs/heads/${ref}:refs/remotes/origin/${ref}"

if [ -n "$keep" ]; then
  printf 'behind origin/%s by: ' "$ref"
  git -C "$dir" rev-list --count "HEAD..origin/${ref}"
  exit 0
fi

git -C "$dir" checkout --quiet --detach "origin/${ref}"

# What you actually got, so a stale clone is visible rather than assumed.
git -C "$dir" log -1 --format='%h %ad %s' --date=short
