#!/bin/sh
# Push as DeckOfPandas-agentic over HTTPS, without naming the credential, and
# without the credential ever being in a URL.
#
# WHY THIS EXISTS. The companion to scripts/gh-agent.sh, added the same day
# (2026-09-10) and for the same reason: a call site with a secret's name in it
# is indistinguishable from a leak until a human has run the rule in her head,
# and Helen should not have to. `origin` is SSH and is broken inside the
# devcontainer (no host key, so `Host key verification failed`), which is why
# a URL is given at all. See CLAUDE.md, Git workflow step 1a.
#
# HOW IT AUTHENTICATES, SINCE LATER THE SAME DAY. The first version built the
# URL with the token in its userinfo. That shape leaked: a CLONE made the same
# way stored the URL, token included, in `.git/config`, and a routine
# `git remote -v` printed it. So the URL here is PLAIN, and the credential
# comes from scripts/git-credential-agent-token.sh, handed to git for this one
# invocation with `-c`. Git asks the helper at the moment it needs to
# authenticate, the helper reads AGENT_GH_TOKEN from the environment and
# answers on a pipe, and nothing is written into any URL or any config.
#
# PER INVOCATION, NEVER `git config credential.helper`. The shared
# /workspace/.git/config is read by the primary checkout and every worktree,
# and git runs a configured helper from each worktree's own top level -- so a
# helper path that exists on one branch fails on every other, as measured on
# 2026-09-10 ("sh: 0: cannot open scripts/git-credential-agent-token.sh"). An
# absolute path, resolved from this script's own location, passed for this
# one command, depends on nothing but the checkout it is run from.
#
# USAGE:
#   sh scripts/git-push-agent.sh <refspec> [repo] [dir]
#
#   sh scripts/git-push-agent.sh my-branch:my-branch
#   sh scripts/git-push-agent.sh my-branch:my-branch helen-triages-food-private _food_drafts
#
# `repo` defaults to the public repo; the other two are
# helen-triages-food-private and helen-triages-cocktails-private, all three of
# which the agent account was invited to. `dir` is the checkout to push FROM
# (a nested drafts clone, say) and defaults to the current directory; it is
# passed to `git -C`, since a leading `cd` is refused by
# guard-unanalyzable-bash.py.
#
# PUSHING IS NOT MERGING. Pushing needs no ask in any of the three repos
# (CLAUDE.md, 2026-09-07); `main` only ever moves via a PR Helen merges, and
# committing or merging onto `main` is refused by guard-main-branch.py.
#
# WHAT IT REFUSES, SINCE 2026-09-11, WHEN IT BECAME ALLOW-LISTED. Until then
# every push prompted Helen, and that prompt was quietly the last thing in
# front of `sh scripts/git-push-agent.sh feature:main` -- a push that moves the
# public `main`, which deploys, without a PR. guard-main-branch.py cannot see
# it: it refuses a commit or a merge while STANDING on `main`, and a push from
# a feature branch stands on the feature branch. So before the allow rule went
# in, the refusal came here:
#   * a destination of `main` on helen-triages, however spelled (`x:main`,
#     `+x:main`, `x:refs/heads/main`, `:main`, which deletes it). The private
#     repos keep Helen's 2026-08-29 grant, "Pushing to main in the private
#     repos is fine".
#   * a refspec without a colon, since `HEAD` alone pushes to whatever the
#     current branch is called; and one starting `-`, which git reads as an
#     option.
#   * a repo other than the three, and a `dir` outside this checkout.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command instead of running it, for
# tests/test_agent_wrappers.py.
#
# Invoked via `sh` so it needs no execute bit -- CLAUDE.md forbids changing file
# permissions without asking.
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

destination="${refspec#*:}"
destination="${destination#refs/heads/}"
if [ "$repo" = helen-triages ] && [ "$destination" = main ]; then
  refuse "that pushes to helen-triages' main, which deploys. main only moves by a PR Helen merges"
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
