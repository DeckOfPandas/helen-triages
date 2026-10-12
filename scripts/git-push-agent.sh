#!/bin/sh
# Push as DeckOfPandas-agentic-claude over HTTPS, without naming the credential
# and without the credential ever being in a URL. `origin` is SSH, which fails
# in the devcontainer for want of a host key, so the URL is given here.
# DECISIONS §11.
#
# USAGE:
#   sh scripts/git-push-agent.sh <refspec> [repo] [dir]
#
#   sh scripts/git-push-agent.sh my-branch:my-branch
#   sh scripts/git-push-agent.sh my-branch:my-branch helen-triages-food-private _food_drafts
#   sh scripts/git-push-agent.sh :my-branch
#
# The last form deletes the remote branch. `repo` defaults to helen-triages;
# the other two are helen-triages-food-private and
# helen-triages-cocktails-private. `dir` is the checkout to push FROM (a nested
# drafts clone) and defaults to the current directory. Nothing checks that
# `repo` and `dir` match: pushing from a drafts clone, give both, or a drafts
# branch lands in the public repo.
#
# ALLOWED, with no ask, in all three repos: pushing a branch. Pushing is not
# merging. A private drafts repo's `main` may be pushed to as well, for a small
# set of changes; a bigger footprint is a PR (DECISIONS §9.1).
#
# REFUSES, because the allow rule in .claude/settings.json runs whatever this
# accepts:
#   * a destination of `main` on helen-triages, however it is spelled:
#     `x:main`, `+x:main`, `x:refs/heads/main`, `x:heads/main` or `:main`
#     (which deletes it). Git resolves every one of those to the same branch,
#     so any destination that is `main` or ends in `/main` is refused. That
#     push moves the public `main`, which deploys, without a PR, and
#     guard-main-branch.py cannot see it: a push from a feature branch stands
#     on the feature branch.
#   * a refspec without a colon, since a bare name or `HEAD` pushes to whatever
#     the current branch is called; and one starting `-`, which git reads as
#     an option.
#   * a repo other than the three, and a `dir` that is absolute, contains `..`
#     or starts `-`.
#
# HOW IT AUTHENTICATES. A plain URL, with
# scripts/git-credential-agent-token.sh handed to git for this one invocation
# by `-c`, as an absolute path resolved from this script's location. Never
# `git config credential.helper`: the shared .git/config is read by every
# worktree, git runs a configured helper from each worktree's top level, and a
# helper path that exists on one branch fails on every other.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command instead of running it, one
# argument per line, for tests/test_agent_wrappers.py.
#
# Invoked via `sh` so it needs no execute bit.
set -eu

refuse() {
  echo "git-push-agent.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -ge 1 ] || refuse "usage: sh scripts/git-push-agent.sh <branch>:<branch> [repo] [dir]"
refspec="$1"
repo="${2:-helen-triages}"
dir="${3:-.}"

case "$refspec" in
  -*) refuse "'$refspec' starts with '-', which git would read as an option" ;;
  *:*) ;;
  *) refuse "give the refspec as <branch>:<branch>, never a bare name or HEAD" ;;
esac
case "$repo" in
  helen-triages | helen-triages-food-private | helen-triages-cocktails-private) ;;
  *) refuse "'$repo' is not one of the three repos" ;;
esac
case "$dir" in
  /* | *..* | -*) refuse "'$dir' is outside this checkout" ;;
esac

destination="${refspec##*:}"
if [ "$repo" = helen-triages ]; then
  case "$destination" in
    main | */main)
      refuse "that pushes to helen-triages' main, which deploys. main only moves by a PR Helen merges" ;;
  esac
fi

here="$(cd "$(dirname "$0")" && pwd)"

set -- git -C "$dir" \
  -c "credential.helper=!sh '${here}/git-credential-agent-token.sh'" \
  push "https://github.com/DeckOfPandas/${repo}.git" "$refspec"

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' "$@"
  exit 0
fi
exec "$@"
