#!/bin/sh
# Bring a drafts clone up to date as DeckOfPandas-agentic, without naming the
# credential at the call site, without the credential ever being in a URL, and
# without standing on `main`.
#
# WHY THIS EXISTS (2026-09-10). The fourth wrapper, and it completes an obvious
# set: scripts/gh-agent.sh talks to the API, git-clone-agent.sh gets a repo,
# git-push-agent.sh sends a branch -- and nothing FETCHED. So a session that
# cloned yesterday and needed today's drinks hand-wrote an HTTPS-with-token URL
# again, which is precisely the shape those three exist to retire: a call site
# with a secret's name in it is indistinguishable from a leak until a human has
# run the rule in her head.
#
# AND FETCHING IS NOT OPTIONAL HERE. MANUAL §9.1: "Always `git fetch`
# immediately before any run whose result you will act on -- before reporting a
# failure, before calling a change safe, before pushing. Not at the start of the
# session: a clone is stale the moment anyone merges, which with two agents is
# several times an afternoon, and the symptom is a handful of test_cocktails.py
# failures naming real drinks that read exactly like a regression."
#
# HOW IT AUTHENTICATES. A PLAIN url, and scripts/git-credential-agent-token.sh
# passed to git for this one invocation with `-c`, resolved to an absolute
# path from this script's own location -- see git-push-agent.sh for why per
# invocation and never `git config`. The token is never in a URL and never on
# disk.
#
# USAGE:
#   sh scripts/git-fetch-agent.sh <dir> <repo> [ref]
#
#   sh scripts/git-fetch-agent.sh _cocktail_drafts helen-triages-cocktails-private
#   sh scripts/git-fetch-agent.sh _food_drafts helen-triages-food-private
#   sh scripts/git-fetch-agent.sh _cocktail_drafts helen-triages-cocktails-private some/branch
#
# IT DETACHES ONTO THE FETCHED REF RATHER THAN CHECKING OUT A BRANCH, which is
# MANUAL §9.1's own instruction -- "to bring a test clone up to date without
# standing on `main`: git checkout --detach origin/main". A detached HEAD cannot
# be committed onto by accident, which is the property that matters in a repo
# whose `main` is protected by a rule and a hook.
#
# `git -C` rather than `cd`, so the command stays one statically-analysable
# thing (guard-unanalyzable-bash.py refuses a leading `cd`), and so
# guard-main-branch.py resolves the RIGHT repository -- it reads `-C` as of
# 2026-09-10.
#
# Invoked via `sh` so it needs no execute bit.
set -eu

dir="$1"
repo="$2"
ref="${3:-main}"

here="$(cd "$(dirname "$0")" && pwd)"

git -C "$dir" \
  -c "credential.helper=!sh '${here}/git-credential-agent-token.sh'" \
  fetch --quiet "https://github.com/DeckOfPandas/${repo}.git" \
  "+refs/heads/${ref}:refs/remotes/origin/${ref}"

git -C "$dir" checkout --quiet --detach "origin/${ref}"

# What you actually got, so a stale clone is visible rather than assumed.
git -C "$dir" log -1 --format='%h %ad %s' --date=short
