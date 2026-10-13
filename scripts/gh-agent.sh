#!/bin/sh
# Run `gh` as DeckOfPandas-agentic-claude, without naming the credential at the
# call site: a command with a secret's name in it cannot be told from a leak
# without reading it closely, so the name lives here, once. DECISIONS §11.
#
# USAGE:  sh scripts/gh-agent.sh issue list --repo DeckOfPandas/helen-triages
#
# Every argument goes to gh unchanged, so this wrapper narrows nothing. The
# allow rules in .claude/settings.json name the subcommands that run unasked,
# and `pr merge` and `pr review` are denied there.
#
# There is deliberately no check that the credential is present: use it and
# read gh's own 401. The value is read from the environment at the point of
# use, handed to gh through its environment, and never echoed or written.
#
# Invoked via `sh` so it needs no execute bit.

exec env GH_TOKEN="$AGENT_GH_TOKEN" gh "$@"
