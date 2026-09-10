#!/bin/sh
# Push as DeckOfPandas-agentic over HTTPS, without naming the credential.
#
# WHY THIS EXISTS. The companion to scripts/gh-agent.sh, added the same day
# (2026-09-10) and for the same reason: `git push "https://DeckOfPandas-agentic:
# ${AGENT_GH_TOKEN}@github.com/..."` is the documented shape, is safe, and puts
# a secret's name at the call site -- where it is indistinguishable from a leak
# until a human has run the rule in their head. Helen should not have to.
#
# `origin` is SSH and is broken inside the devcontainer (no host key, so
# `Host key verification failed`), which is why the URL is built by hand at all.
# See CLAUDE.md, Git workflow step 1a.
#
# USAGE:
#   sh scripts/git-push-agent.sh <refspec> [repo]
#
#   sh scripts/git-push-agent.sh my-branch:my-branch
#   sh scripts/git-push-agent.sh my-branch:my-branch helen-triages-food-private
#
# `repo` defaults to the public repo; the other two are
# helen-triages-food-private and helen-triages-cocktails-private, all three of
# which the agent account was invited to.
#
# PUSHING IS NOT MERGING. Pushing needs no ask in any of the three repos
# (CLAUDE.md, 2026-09-07); `main` only ever moves via a PR Helen merges, and
# committing or merging onto `main` is refused by guard-main-branch.py.
#
# Invoked via `sh` so it needs no execute bit -- CLAUDE.md forbids changing file
# permissions without asking. The token is read from the environment at the
# point of use and never echoed, logged, or written to a file.
set -eu

refspec="$1"
repo="${2:-helen-triages}"

exec git push "https://DeckOfPandas-agentic:${AGENT_GH_TOKEN}@github.com/DeckOfPandas/${repo}.git" "$refspec"
