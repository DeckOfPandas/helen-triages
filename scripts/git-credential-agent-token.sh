#!/bin/sh
# Git credential helper for AGENT_GH_TOKEN. Git calls it at the moment it needs
# to authenticate; the token is read from the environment here and handed to
# git over a pipe. It is never in a URL and never in `.git/config`, where
# `git remote -v` or `git config -l` would print it. DECISIONS §11.
#
# You do not call this, and you do not `git config` it. The three git wrappers
# (scripts/git-clone-agent.sh, git-fetch-agent.sh, git-push-agent.sh) pass it
# to git for one invocation each, with `-c credential.helper=...` and an
# absolute path resolved from their own location, against a plain URL.
# Configured in the shared .git/config instead, git runs it by relative path
# from each worktree's top level and fails wherever the file is absent.
#
# This is the one script that prints the token: to git's pipe, never to a
# terminal. guard-token-expansion.py does not flag a script's own printf.
#
# Only answers `get`. `store` and `erase` are git offering to cache what it
# just used; answering nothing means nothing is ever written down.
#
# The username is the agent account's. GitHub authenticates the token, not this
# name, so a stale name here fails nothing; keep it right anyway.
#
# Invoked as `sh <path>` by the wrappers, so it needs no execute bit.
case "$1" in
    get)
        printf 'username=%s\n' "DeckOfPandas-agentic-claude"
        printf 'password=%s\n' "${AGENT_GH_TOKEN}"
        ;;
esac
