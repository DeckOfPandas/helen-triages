#!/bin/sh
# Run `gh` as DeckOfPandas-agentic, without naming the credential at the call site.
#
# WHY THIS EXISTS (2026-09-10, Helen's call). The sanctioned shape for gh was
# `GH_TOKEN="$AGENT_GH_TOKEN" gh ...` -- an environment assignment, which passes
# the value into gh and never prints it. That is genuinely safe, and it was still
# the wrong thing to type, for exactly the reason Helen retired the last "safe"
# token expansion on 2026-09-09: from the outside a command with a secret's name
# in it is indistinguishable from a leak until you have run the rule in your head.
# She should not have to clear a call to find out it was fine. So the name lives
# here, once, in a file that can be read once -- and every call site is plain.
#
# USE IT AS:  sh scripts/gh-agent.sh issue list --repo DeckOfPandas/helen-triages
# Invoked via `sh`, deliberately: no execute bit, so it never needs a chmod
# (CLAUDE.md -- file permissions are Helen's call, every single time).
#
# There is deliberately no check that the credential is present. CLAUDE.md:
# don't probe for a credential, use it and read the result -- gh's own 401 is a
# better answer than any test here, and a probe is the thing that keeps going
# wrong. The value is read from the environment at the point of use, handed to
# gh through its own environment, and never echoed, logged, or written to a file.

exec env GH_TOKEN="$AGENT_GH_TOKEN" gh "$@"
