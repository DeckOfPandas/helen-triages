#!/bin/sh
# Clone one of the three repos as DeckOfPandas-agentic over HTTPS, without
# naming the credential at the call site.
#
# WHY THIS EXISTS (2026-09-10). MANUAL §9.1 says a worktree gets the drinks by
# cloning the private drafts repo, and gives the SSH form. Inside the
# devcontainer SSH dies on `Host key verification failed` (CLAUDE.md, Git
# workflow step 1a), so the clone has to be the HTTPS-with-token form -- and
# the first session to need it hand-wrote that URL, token name and all, into a
# tmp/ script. That is the shape scripts/gh-agent.sh and git-push-agent.sh
# exist to retire: a call site with a secret's name in it is indistinguishable
# from a leak until a human has run the rule in their head. This is the third
# wrapper, same reasoning.
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
# Invoked via `sh` so it needs no execute bit -- CLAUDE.md forbids changing file
# permissions without asking. The token is read from the environment at the
# point of use and never echoed, logged, or written to a file.
set -eu

repo="$1"
shift

exec git clone --quiet "https://DeckOfPandas-agentic:${AGENT_GH_TOKEN}@github.com/DeckOfPandas/${repo}.git" "$@"
