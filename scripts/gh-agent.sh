#!/bin/sh
# Run `gh` as the agent account, without naming the credential at the call
# site: a command with a secret's name in it cannot be told from a leak without
# reading it closely, so the name lives here, once.
#
# USAGE:  sh scripts/gh-agent.sh issue list --repo <owner>/<repo>
#
# Every argument goes to gh unchanged, so this narrows nothing: the allow rules
# in .claude/settings.json name the subcommands that run unasked, and `pr merge`
# and `pr review` are denied there. There is no check that the credential is
# present; use it and read gh's own 401.

exec env GH_TOKEN="$AGENT_GH_TOKEN" gh "$@"
